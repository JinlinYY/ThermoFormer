# -*- coding: utf-8 -*-
"""
从已跑过的 387 篇 ThermoML 文献中提取三元 VLE 数据。

格式（严格遵循之前的 A-L + DOI 模式，扩展为 3 组分）:
  A 名称1, B 分子式1, C smiles1,
  D 名称2, E 分子式2, F smiles2,
  G 名称3, H 分子式3, I smiles3,
  J 一致性检验方法一 (Fredenslund 三元点检验),
  K 一致性检验方法二 (Herington 面积检验·二元子体系法),
  L 压强 (mmHg), M 温度 (°C),
  N X1, O X2, (X3=1-X1-X2 不单独列出)
  P Y1, Q Y2, (Y3=1-Y1-Y2 不单独列出)
  R DOI
"""
from __future__ import annotations
import json, time, sys, re
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ---- thermoml-io ----
import thermoml_io as tml
from thermoml_io.classification import classify_property, normalize_term

# ============================================================
# 配置
# ============================================================
WORK = Path(__file__).resolve().parent
XML_BASE = "https://trc.nist.gov/ThermoML"
KPA_TO_MMHG = 7.50061683
GAS_PHASES = {"gas", "vapor", "vapour"}

# 已跑过的 DOI 列表（从二元数据中取）
df_bin = pd.read_csv(WORK / "vle_binary_expand.csv", encoding="utf-8-sig")
ALL_DOIS = sorted(df_bin["DOI"].unique().tolist())
print(f"已跑过 DOI 数: {len(ALL_DOIS)}")

# 加载中英文映射 + Antoine 参数
EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
ANTOINE_RAW = json.load(open(WORK / "_antoine_cn_full.json", "r", encoding="utf-8"))
ANTOINE_CN = ANTOINE_RAW["log10(P_mmHg)_A_minus_B_over_TdegC_plus_C"]

OUT_CSV = WORK / "vle_ternary_expand.csv"
CACHE_FILE = WORK / "vle_ternary_cache.json"

# ============================================================
# HTTP 会话（限流 + 重试）
# ============================================================
def build_session(rate_limit=0.4, retries=3):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "thermoml-ternary/1.0 (research)",
        "Accept": "application/xml",
    })
    retry = Retry(total=retries, connect=retries, read=retries,
                  backoff_factor=1.5,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess._rate_limit = rate_limit
    sess._last_request_ts = 0.0
    return sess

def polite_get(sess, url, *, timeout=90, **kwargs):
    elapsed = time.monotonic() - sess._last_request_ts
    if elapsed < sess._rate_limit:
        time.sleep(sess._rate_limit - elapsed)
    resp = sess.get(url, timeout=timeout, **kwargs)
    sess._last_request_ts = time.monotonic()
    return resp

def fetch_xml_bytes(sess, doi):
    url = f"{XML_BASE}/{doi}.xml"
    resp = polite_get(sess, url, timeout=90)
    resp.raise_for_status()
    return resp.content

# ============================================================
# 辅助函数（与 binary 版一致）
# ============================================================
def _is_liquid(phase):
    return bool(phase) and normalize_term(phase).startswith("liquid")

def _is_gas(phase):
    return bool(phase) and normalize_term(phase) in GAS_PHASES

def _is_mole_fraction(definition):
    return normalize_term(definition.name).startswith("mole_fraction")

def classify_property(prop, ds):
    """判断 property 是否为 VLE 的气相摩尔分数。"""
    nm = normalize_term(prop.name)
    if not nm.startswith("mole_fraction"):
        return "OTHER"
    if _is_gas(prop.phase):
        return "VLE"
    if _is_liquid(prop.phase):
        return "LIQUID_X"
    return "OTHER"

def to_cn(name):
    if pd.isna(name):
        return name
    s = str(name).strip()
    return EN_TO_CN.get(s, s)

# ============================================================
# 三元 VLE 提取核心
# ============================================================
def extract_ternary_vle_rows(doc, doi, xml_url):
    """从 ThermoMLDocument 中抽取三元 VLE 实验点。

    核心逻辑：
    1. 筛选 system_type == "ternary" 的数据集（3 个组分）
    2. 收集液相摩尔分数变量 x1, x2（x3=1-x1-x2）
    3. 收集气相摩尔分数 y1, y2（y3=1-y1-y2）
    4. 按点序号合并兄弟数据集
    5. 要求四项齐全 (x1, x2, y1, y2, T, P)
    """
    rows = []
    citation = doc.citation
    doi_str = citation.normalized_doi or doi

    # 1) 收集候选三元数据集
    candidates = []
    for ds in doc.datasets:
        if ds.system_type != "ternary":
            continue
        cids = list(dict.fromkeys(ds.component_ids))
        if len(cids) != 3:
            continue
        # 必须有至少一个液相摩尔分数
        has_liq_mf = any(
            (_is_mole_fraction(v) and _is_liquid(v.phase)) or
            (_is_mole_fraction(p) and _is_liquid(p.phase))
            for v in ds.variables for p in ds.properties
        )
        if not has_liq_mf:
            continue
        candidates.append((ds, cids))

    if not candidates:
        return rows

    # 2) 按组分集合分组
    groups = defaultdict(list)
    for ds, cids in candidates:
        groups[frozenset(cids)].append((ds, cids))

    for comp_set, members in groups.items():
        cids = members[0][1]
        # 取组分对象
        comps = [doc.compound(cid) for cid in cids]
        # 排序：按 OrgNum（保证顺序稳定）
        comp_info = []
        for i, cid in enumerate(cids):
            comp = doc.compound(cid)
            comp_info.append({
                "cid": cid,
                "name": comp.preferred_name if comp else f"Unknown_{cid}",
                "formula": comp.formula if comp else "",
                "cas": comp.cas_registry_number if comp else "",
            })

        # 整组必须含至少一个 VLE 性质（气相摩尔分数）
        has_vle = any(
            classify_property(p, ds) == "VLE"
            for ds, _ in members
            for p in ds.properties
        )
        if not has_vle:
            continue

        # 按点数分桶
        by_len = defaultdict(list)
        for m in members:
            by_len[len(m[0].points)].append(m)

        for bucket in by_len.values():
            if len(bucket) == 1:
                subgroups = [bucket]
            else:
                # 简单处理：同点数的合并为一个组
                subgroups = [bucket]

            for grp in subgroups:
                n_pts = len(grp[0][0].points)
                for i in range(n_pts):
                    # 收集所有组分的液相和气相摩尔分数
                    x_vals = {cid: None for cid in cids}
                    y_vals = {cid: None for cid in cids}
                    t_k = None
                    p_kpa = None

                    for ds, _ in grp:
                        pt = ds.points[i]
                        var_def = {v.number: v for v in ds.variables}
                        prop_def = {p.number: p for p in ds.properties}

                        # 变量
                        for mv in pt.variable_values:
                            d = var_def.get(mv.number)
                            if d is None:
                                continue
                            nm = normalize_term(d.name)
                            if nm.startswith("mole_fraction"):
                                if _is_liquid(d.phase) and d.component_id:
                                    if x_vals.get(d.component_id) is None:
                                        x_vals[d.component_id] = mv.value
                                elif _is_gas(d.phase) and d.component_id:
                                    if y_vals.get(d.component_id) is None:
                                        y_vals[d.component_id] = mv.value
                            elif "temperature" in nm:
                                if t_k is None:
                                    t_k = mv.value
                            elif "pressure" in nm:
                                if p_kpa is None:
                                    p_kpa = mv.value

                        # 属性
                        for mv in pt.property_values:
                            d = prop_def.get(mv.number)
                            if d is None:
                                continue
                            nm = normalize_term(d.name)
                            if nm.startswith("mole_fraction"):
                                if _is_liquid(d.phase) and d.component_id:
                                    if x_vals.get(d.component_id) is None:
                                        x_vals[d.component_id] = mv.value
                                elif _is_gas(d.phase) and d.component_id:
                                    if y_vals.get(d.component_id) is None:
                                        y_vals[d.component_id] = mv.value
                            elif "temperature" in nm:
                                if t_k is None:
                                    t_k = mv.value
                            elif "pressure" in nm:
                                if p_kpa is None:
                                    p_kpa = mv.value

                    # 约束回退
                    if t_k is None or p_kpa is None:
                        for ds, _ in grp:
                            for c in ds.constraints:
                                cn = normalize_term(c.name)
                                if "temperature" in cn and t_k is None and c.value is not None:
                                    t_k = c.value
                                elif "pressure" in cn and p_kpa is None and c.value is not None:
                                    p_kpa = c.value

                    # 必须至少有 2 个液相 + 2 个气相摩尔分数
                    x_known = {k: v for k, v in x_vals.items() if v is not None}
                    y_known = {k: v for k, v in y_vals.items() if v is not None}
                    if len(x_known) < 2 or len(y_known) < 2:
                        continue
                    if t_k is None or p_kpa is None:
                        continue

                    # 确定组分顺序：按 cids 原始顺序
                    # x1, x2 来自前两个已知组分；x3 = 1 - x1 - x2
                    ordered_cids = [cid for cid in cids if x_known.get(cid) is not None]
                    if len(ordered_cids) < 2:
                        continue
                    # 补全第三个组分（如果只有 2 个 x 已知，第三个可以算出来）
                    cid1, cid2 = ordered_cids[0], ordered_cids[1]
                    # 如果有第三个组分也有 x 值，用它；否则用 1-x1-x2
                    x1 = float(x_known[cid1])
                    x2 = float(x_known[cid2])
                    # y
                    if cid1 in y_known and cid2 in y_known:
                        y1 = float(y_known[cid1])
                        y2 = float(y_known[cid2])
                    else:
                        continue

                    # 范围检查
                    if not (0 <= x1 <= 1 and 0 <= x2 <= 1 and x1 + x2 <= 1.001):
                        continue
                    if not (0 <= y1 <= 1 and 0 <= y2 <= 1 and y1 + y2 <= 1.001):
                        continue

                    t_c = float(t_k) - 273.15
                    p_mmhg = float(p_kpa) * KPA_TO_MMHG

                    comp1 = doc.compound(cid1)
                    comp2 = doc.compound(cid2)
                    # 第三个组分
                    cid3 = None
                    for c in cids:
                        if c != cid1 and c != cid2:
                            cid3 = c
                            break
                    comp3 = doc.compound(cid3) if cid3 else None

                    rows.append({
                        "名称1": comp1.preferred_name if comp1 else "",
                        "分子式1": comp1.formula if comp1 else "",
                        "smiles1": "",
                        "名称2": comp2.preferred_name if comp2 else "",
                        "分子式2": comp2.formula if comp2 else "",
                        "smiles2": "",
                        "名称3": comp3.preferred_name if comp3 else "",
                        "分子式3": comp3.formula if comp3 else "",
                        "smiles3": "",
                        "一致性检验方法一": 0,
                        "一致性检验方法二": 0,
                        "压强": round(p_mmhg, 4),
                        "温度": round(t_c, 3),
                        "X1": round(x1, 6),
                        "X2": round(x2, 6),
                        "Y1": round(y1, 6),
                        "Y2": round(y2, 6),
                        "CAS1": comp1.cas_registry_number if comp1 else "",
                        "CAS2": comp2.cas_registry_number if comp2 else "",
                        "CAS3": comp3.cas_registry_number if comp3 else "",
                        "DOI": doi_str,
                    })
    return rows


# ============================================================
# 三元一致性检验
# ============================================================
def antoine_p_sat_cn(name, T_C):
    if name not in ANTOINE_CN:
        return None
    A, B, C = ANTOINE_CN[name]
    T_C = np.asarray(T_C, dtype=float)
    denom = T_C + C
    denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
    p = 10.0 ** (A - B / denom)
    return np.where(np.isfinite(p) & (p > 1e-6) & (p < 1e7), p, np.nan)

def fredenslund_ternary(x1, x2, y1, y2, T, P, n1, n2, n3):
    """三元 Fredenslund 点检验。

    使用 2D Margules 多项式拟合 gE/RT = f(x1, x2)，
    反算 y1_calc, y2_calc，逐点残差判定。
    """
    n = len(x1)
    if n < 6:
        return 0
    x1 = np.asarray(x1, float); x2 = np.asarray(x2, float)
    y1 = np.asarray(y1, float); y2 = np.asarray(y2, float)
    T = np.asarray(T, float); P = np.asarray(P, float)

    P1s = antoine_p_sat_cn(n1, T)
    P2s = antoine_p_sat_cn(n2, T)
    P3s = antoine_p_sat_cn(n3, T)
    if P1s is None or P2s is None or P3s is None:
        return 0

    valid = np.isfinite(P1s) & np.isfinite(P2s) & np.isfinite(P3s)
    valid &= (P1s > 0) & (P2s > 0) & (P3s > 0)
    if valid.sum() < 6:
        return 0

    x1v = x1[valid]; x2v = x2[valid]; y1v = y1[valid]; y2v = y2[valid]
    Tv = T[valid]; Pv = P[valid]
    P1m = P1s[valid]; P2m = P2s[valid]; P3m = P3s[valid]
    x3v = 1.0 - x1v - x2v

    mask = (x1v > 1e-6) & (x1v < 1-1e-6) & (x2v > 1e-6) & (x2v < 1-1e-6) & (x3v > 1e-6)
    if mask.sum() < 6:
        return 0

    x1m = x1v[mask]; x2m = x2v[mask]; x3m = x3v[mask]
    y1m = y1v[mask]; y2m = y2v[mask]
    Tm = Tv[mask]; Pm = Pv[mask]
    P1 = P1m[mask]; P2 = P2m[mask]; P3 = P3m[mask]

    # 活度系数
    gamma1 = (Pm * y1m) / (x1m * P1)
    gamma2 = (Pm * y2m) / (x2m * P2)
    gamma3 = (Pm * (1 - y1m - y2m)) / (x3m * P3)

    if np.any(~np.isfinite(gamma1)) or np.any(gamma1 <= 0) or \
       np.any(~np.isfinite(gamma2)) or np.any(gamma2 <= 0) or \
       np.any(~np.isfinite(gamma3)) or np.any(gamma3 <= 0):
        return 0

    ln_g1 = np.log(gamma1); ln_g2 = np.log(gamma2); ln_g3 = np.log(gamma3)
    gE_RT = x1m * ln_g1 + x2m * ln_g2 + x3m * ln_g3

    # 2D 多项式拟合: gE/RT = a0 + a1*x1 + a2*x2 + a3*x1^2 + a4*x2^2 + a5*x1*x2
    # (最低 6 参数需要 >= 6 点)
    A_mat = np.column_stack([np.ones_like(x1m), x1m, x2m, x1m**2, x2m**2, x1m*x2m])
    try:
        a, *_ = np.linalg.lstsq(A_mat, gE_RT, rcond=None)
    except Exception:
        return 0

    gE_calc = A_mat @ a

    # 数值偏导反算 y
    # dgE/dx1 at constant x2, dgE/dx2 at constant x1
    dg_dx1 = a[1] + 2*a[3]*x1m + a[5]*x2m
    dg_dx2 = a[2] + 2*a[4]*x2m + a[5]*x1m

    # ln gamma_i = gE + (delta_i1 - x1)*dgEx1 + (delta_i2 - x2)*dgEx2
    # 但三元体系更复杂，用简化公式:
    ln_g1_calc = gE_calc + (1 - x1m) * dg_dx1 - x2m * dg_dx2
    ln_g2_calc = gE_calc - x1m * dg_dx1 + (1 - x2m) * dg_dx2
    ln_g3_calc = gE_calc - x1m * dg_dx1 - x2m * dg_dx2

    g1_calc = np.exp(np.clip(ln_g1_calc, -50, 50))
    g2_calc = np.exp(np.clip(ln_g2_calc, -50, 50))
    g3_calc = np.exp(np.clip(ln_g3_calc, -50, 50))

    y1_calc = (g1_calc * x1m * P1) / Pm
    y2_calc = (g2_calc * x2m * P2) / Pm
    y1_calc = np.clip(y1_calc, 0, 1)
    y2_calc = np.clip(y2_calc, 0, 1)

    d1 = np.abs(y1m - y1_calc)
    d2 = np.abs(y2m - y2_calc)
    delta = np.maximum(d1, d2)

    pass_rate = np.mean(delta < 0.01)
    if pass_rate > 0.9:
        return 1
    if pass_rate > 0.8 and delta.mean() < 0.015:
        return 1
    return -1


def herington_ternary(x1, x2, y1, y2, T, P, n1, n2, n3):
    """三元 Herington 面积检验（简化版）。

    对三元体系，沿 x1 轴（固定 x2/x3 比例）和 x2 轴分别做面积积分，
    取两个方向的 D-J 判据均通过才视为通过。
    """
    n = len(x1)
    if n < 6:
        return 0
    x1 = np.asarray(x1, float); x2 = np.asarray(x2, float)
    y1 = np.asarray(y1, float); y2 = np.asarray(y2, float)
    T = np.asarray(T, float); P = np.asarray(P, float)

    P1s = antoine_p_sat_cn(n1, T)
    P2s = antoine_p_sat_cn(n2, T)
    P3s = antoine_p_sat_cn(n3, T)
    if P1s is None or P2s is None or P3s is None:
        return 0

    valid = np.isfinite(P1s) & np.isfinite(P2s) & np.isfinite(P3s)
    valid &= (P1s > 0) & (P2s > 0) & (P3s > 0)
    if valid.sum() < 6:
        return 0

    x1v = x1[valid]; x2v = x2[valid]; y1v = y1[valid]; y2v = y2[valid]
    Tv = T[valid]; Pv = P[valid]
    P1m = P1s[valid]; P2m = P2s[valid]; P3m = P3s[valid]
    x3v = 1.0 - x1v - x2v

    mask = (x1v > 1e-6) & (x2v > 1e-6) & (x3v > 1e-6) & (y1v > 1e-6) & (y2v > 1e-6)
    if mask.sum() < 6:
        return 0

    x1m = x1v[mask]; x2m = x2v[mask]; x3m = x3v[mask]
    y1m = y1v[mask]; y2m = y2v[mask]
    Tm = Tv[mask]; Pm = Pv[mask]
    P1 = P1m[mask]; P2 = P2m[mask]; P3 = P3m[mask]

    gamma1 = (Pm * y1m) / (x1m * P1)
    gamma2 = (Pm * y2m) / (x2m * P2)
    gamma3 = (Pm * (1 - y1m - y2m)) / (x3m * P3)

    if np.any(gamma1 <= 0) or np.any(gamma2 <= 0) or np.any(gamma3 <= 0):
        return 0

    ln_ratio_12 = np.log(gamma1 / gamma2)
    ln_ratio_13 = np.log(gamma1 / gamma3)
    ln_ratio_23 = np.log(gamma2 / gamma3)

    if not np.all(np.isfinite(ln_ratio_12)) or \
       not np.all(np.isfinite(ln_ratio_13)) or \
       not np.all(np.isfinite(ln_ratio_23)):
        return 0

    # 方向 1: 沿 x1 排序积分 ln(g1/g2)
    idx1 = np.argsort(x1m)
    try:
        from scipy.integrate import trapezoid
        area_net_1 = float(trapezoid(ln_ratio_12[idx1], x1m[idx1]))
        area_total_1 = float(trapezoid(np.abs(ln_ratio_12[idx1]), x1m[idx1]))
    except Exception:
        return 0

    if area_total_1 < 1e-8:
        return 0
    D1 = 100.0 * abs(area_net_1) / area_total_1

    # 方向 2: 沿 x2 排序积分 ln(g1/g3)
    idx2 = np.argsort(x2m)
    try:
        area_net_2 = float(trapezoid(ln_ratio_13[idx2], x2m[idx2]))
        area_total_2 = float(trapezoid(np.abs(ln_ratio_13[idx2]), x2m[idx2]))
    except Exception:
        return 0

    if area_total_2 < 1e-8:
        return 0
    D2 = 100.0 * abs(area_net_2) / area_total_2

    T_mean = Tm.mean()
    if T_mean <= 0 or len(Tm) < 2:
        return 0
    J = 150.0 * (Tm.max() - Tm.min()) / T_mean

    # 两个方向都通过才算通过
    if abs(D1 - J) < 10 and abs(D2 - J) < 10:
        return 1
    return -1


# ============================================================
# 主流程
# ============================================================
def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

def main():
    cache = load_cache()
    print(f"缓存状态: {len(cache)} 条")

    # 只跑未处理的 DOI
    todo = [d for d in ALL_DOIS if d not in cache]
    print(f"待处理: {len(todo)} / {len(ALL_DOIS)} DOI")

    if not todo:
        print("全部已处理，直接输出 CSV")
        if OUT_CSV.exists():
            df = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
            print(f"现有 CSV: {len(df)} 行, {df['DOI'].nunique()} DOI")
            return df
        else:
            print("CSV 不存在，重新提取...")
            todo = ALL_DOIS
            cache = {}

    sess = build_session(rate_limit=0.4)
    all_rows = []

    # 如果 CSV 已存在，先加载已有行
    if OUT_CSV.exists() and not todo == ALL_DOIS:
        try:
            old_df = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
            all_rows = old_df.to_dict("records")
            print(f"加载已有行: {len(all_rows)}")
        except Exception:
            pass

    batch_rows = []
    for i, doi in enumerate(todo, 1):
        try:
            xml_bytes = fetch_xml_bytes(sess, doi)
            doc = tml.parse_thermoml(xml_bytes, source_label=f"{XML_BASE}/{doi}.xml")
            rows = extract_ternary_vle_rows(doc, doi, f"{XML_BASE}/{doi}.xml")
            cache[doi] = {"status": "ok" if rows else "empty", "n_rows": len(rows)}
            batch_rows.extend(rows)
            if rows:
                print(f"  [{i}/{len(todo)}] {doi}: {len(rows)} 行三元 VLE")
        except Exception as e:
            cache[doi] = {"status": "error", "msg": f"{type(e).__name__}: {e}"}

        # 每 50 篇写入一次
        if i % 50 == 0 or i == len(todo):
            all_rows.extend(batch_rows)
            df_tmp = pd.DataFrame(all_rows)
            df_tmp.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
            save_cache(cache)
            n_ok = sum(1 for v in cache.values() if v["status"] == "ok")
            n_empty = sum(1 for v in cache.values() if v["status"] == "empty")
            n_err = sum(1 for v in cache.values() if v["status"] == "error")
            print(f"  进度: {i}/{len(todo)} | ok={n_ok} empty={n_empty} err={n_err} | 总行数={len(all_rows)}")
            batch_rows = []

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("无三元 VLE 数据！")
        return df

    print(f"\n===== 三元 VLE 提取完成 =====")
    print(f"总行数: {len(df)}, DOI 数: {df['DOI'].nunique()}")
    print(f"体系数: {df.groupby(['名称1','名称2','名称3']).ngroups}")
    return df


if __name__ == "__main__":
    df = main()
    if df is not None and not df.empty:
        print(f"\n输出: {OUT_CSV}")
        print(f"列: {list(df.columns)}")
