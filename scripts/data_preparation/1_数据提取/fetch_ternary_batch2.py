# -*- coding: utf-8 -*-
"""
批次 2: 跑 500 篇新文献，提取三元 VLE 数据。
- 从 _all_handles.json 提取完整 DOI
- 过滤已处理的 387 篇
- 下载 XML，解析，提取三元 VLE
- 同时检查 4+ 组分体系
- 每 50 篇写 CSV + 汇报
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import thermoml_io as tml
from thermoml_io.classification import classify_property, normalize_term

WORK = Path(__file__).resolve().parent
XML_BASE = "https://trc.nist.gov/ThermoML"
KPA_TO_MMHG = 7.50061683
GAS_PHASES = {"gas", "vapor", "vapour"}
BATCH_SIZE = 500

# ====== 加载已处理 DOI ======
df_ternary = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
done_dois = set(df_ternary["DOI"].unique())
df_bin = pd.read_csv(WORK / "vle_binary_expand.csv", encoding="utf-8-sig")
done_dois |= set(df_bin["DOI"].unique())
print(f"已处理 DOI: {len(done_dois)}")

# ====== 加载全量 handle ======
handles = json.loads((WORK / "_all_handles.json").read_text(encoding="utf-8"))
all_dois = []
for h in handles:
    if "/" in h:
        doi = h.split("/", 1)[1]  # 10.1016/j.fluid.xxx
    else:
        doi = h
    all_dois.append(doi)
print(f"全量 DOI: {len(all_dois)}")

# 过滤已处理
todo = [d for d in all_dois if d not in done_dois]
print(f"未处理: {len(todo)}")
todo = todo[:BATCH_SIZE]
print(f"本批次处理: {len(todo)} DOI")

# ====== HTTP 会话 ======
def build_session(rate_limit=0.4, retries=3):
    sess = requests.Session()
    sess.headers.update({"User-Agent": "ternary-batch2/1.0", "Accept": "application/xml"})
    retry = Retry(total=retries, connect=retries, read=retries, backoff_factor=1.5,
                  status_forcelist=(429,500,502,503,504), allowed_methods=frozenset(["GET"]))
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter); sess.mount("http://", adapter)
    sess._rate_limit = rate_limit; sess._last_request_ts = 0.0
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

# ====== 辅助 ======
def _is_liquid(phase):
    return bool(phase) and normalize_term(phase).startswith("liquid")
def _is_gas(phase):
    return bool(phase) and normalize_term(phase) in GAS_PHASES
def _is_mole_fraction(definition):
    return normalize_term(definition.name).startswith("mole_fraction")

# ====== 三元 VLE 提取 ======
def extract_ternary_vle_rows(doc, doi):
    rows = []
    doi_str = doc.citation.normalized_doi or doi

    candidates = []
    for ds in doc.datasets:
        if ds.system_type != "ternary":
            continue
        cids = list(dict.fromkeys(ds.component_ids))
        if len(cids) != 3:
            continue
        has_liq = any(
            (_is_mole_fraction(v) and _is_liquid(v.phase)) or
            (_is_mole_fraction(p) and _is_liquid(p.phase))
            for v in ds.variables for p in ds.properties
        )
        if not has_liq:
            continue
        candidates.append((ds, cids))

    if not candidates:
        return rows

    groups = defaultdict(list)
    for ds, cids in candidates:
        groups[frozenset(cids)].append((ds, cids))

    for comp_set, members in groups.items():
        cids = members[0][1]
        has_vle = any(classify_property(p, ds) == "VLE" for ds, _ in members for p in ds.properties)
        if not has_vle:
            continue

        by_len = defaultdict(list)
        for m in members:
            by_len[len(m[0].points)].append(m)

        for bucket in by_len.values():
            n_pts = len(bucket[0][0].points)
            for i in range(n_pts):
                x_vals = {cid: None for cid in cids}
                y_vals = {cid: None for cid in cids}
                t_k = None; p_kpa = None

                for ds, _ in bucket:
                    pt = ds.points[i]
                    var_def = {v.number: v for v in ds.variables}
                    prop_def = {p.number: p for p in ds.properties}

                    for mv in pt.variable_values:
                        d = var_def.get(mv.number)
                        if d is None: continue
                        nm = normalize_term(d.name)
                        if nm.startswith("mole_fraction"):
                            if _is_liquid(d.phase) and d.component_id:
                                if x_vals.get(d.component_id) is None:
                                    x_vals[d.component_id] = float(mv.value) if mv.value else None
                            elif _is_gas(d.phase) and d.component_id:
                                if y_vals.get(d.component_id) is None:
                                    y_vals[d.component_id] = float(mv.value) if mv.value else None
                        elif "temperature" in nm and t_k is None:
                            t_k = float(mv.value) if mv.value else None
                        elif "pressure" in nm and p_kpa is None:
                            p_kpa = float(mv.value) if mv.value else None

                    for mv in pt.property_values:
                        d = prop_def.get(mv.number)
                        if d is None: continue
                        nm = normalize_term(d.name)
                        if nm.startswith("mole_fraction"):
                            if _is_liquid(d.phase) and d.component_id:
                                if x_vals.get(d.component_id) is None:
                                    x_vals[d.component_id] = float(mv.value) if mv.value else None
                            elif _is_gas(d.phase) and d.component_id:
                                if y_vals.get(d.component_id) is None:
                                    y_vals[d.component_id] = float(mv.value) if mv.value else None
                        elif "temperature" in nm and t_k is None:
                            t_k = float(mv.value) if mv.value else None
                        elif "pressure" in nm and p_kpa is None:
                            p_kpa = float(mv.value) if mv.value else None

                if t_k is None or p_kpa is None:
                    for ds, _ in bucket:
                        for c in ds.constraints:
                            cn = normalize_term(c.name)
                            if "temperature" in cn and t_k is None and c.value is not None:
                                t_k = float(c.value)
                            elif "pressure" in cn and p_kpa is None and c.value is not None:
                                p_kpa = float(c.value)

                x_known = {k: v for k, v in x_vals.items() if v is not None}
                y_known = {k: v for k, v in y_vals.items() if v is not None}
                if len(x_known) < 2 or len(y_known) < 2:
                    continue
                if t_k is None or p_kpa is None:
                    continue

                ordered = [cid for cid in cids if x_known.get(cid) is not None]
                if len(ordered) < 2:
                    continue
                cid1, cid2 = ordered[0], ordered[1]
                x1 = float(x_known[cid1]); x2 = float(x_known[cid2])
                if cid1 in y_known and cid2 in y_known:
                    y1 = float(y_known[cid1]); y2 = float(y_known[cid2])
                else:
                    continue

                if not (0 <= x1 <= 1 and 0 <= x2 <= 1 and x1 + x2 <= 1.001):
                    continue
                if not (0 <= y1 <= 1 and 0 <= y2 <= 1 and y1 + y2 <= 1.001):
                    continue

                t_c = t_k - 273.15
                p_mmhg = p_kpa * KPA_TO_MMHG

                comp1 = doc.compound(cid1); comp2 = doc.compound(cid2)
                cid3 = None
                for c in cids:
                    if c != cid1 and c != cid2:
                        cid3 = c; break
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
                    "X1": round(x1, 6), "X2": round(x2, 6),
                    "Y1": round(y1, 6), "Y2": round(y2, 6),
                    "DOI": doi_str,
                })
    return rows

# ====== 四元检查 ======
def check_quaternary(doc, doi):
    """检查 XML 中是否有 4 组分 VLE 数据。"""
    for ds in doc.datasets:
        cids = list(dict.fromkeys(ds.component_ids))
        if len(cids) >= 4:
            return True
    return False

# ====== 缓存 ======
CACHE_FILE = WORK / "vle_ternary_batch2_cache.json"
OUT_CSV = WORK / "vle_ternary_batch2.csv"

def load_cache():
    if CACHE_FILE.exists():
        try: return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except: return {}
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

# ====== 主流程 ======
def main():
    cache = load_cache()
    todo_fresh = [d for d in todo if d not in cache]
    print(f"缓存: {len(cache)} 条, 本批次待处理: {len(todo_fresh)}")

    sess = build_session(rate_limit=0.4)
    all_rows = []
    batch_rows = []
    n_ok = n_empty = n_err = n_quat = 0

    for i, doi in enumerate(todo_fresh, 1):
        try:
            xml_bytes = fetch_xml_bytes(sess, doi)
            doc = tml.parse_thermoml(xml_bytes, source_label=f"{XML_BASE}/{doi}.xml")
            rows = extract_ternary_vle_rows(doc, doi)
            has_quat = check_quaternary(doc, doi)

            if rows:
                batch_rows.extend(rows)
                n_ok += 1
                print(f"  [{i}/{len(todo_fresh)}] {doi}: {len(rows)} 行三元 VLE")
            else:
                n_empty += 1
            if has_quat:
                n_quat += 1
                print(f"    ⚠️ 发现 4+ 组分体系!")
            cache[doi] = {"status": "ok" if rows else "empty", "n_rows": len(rows), "quaternary": has_quat}
        except Exception as e:
            n_err += 1
            cache[doi] = {"status": "error", "msg": f"{type(e).__name__}: {e}"}

        # 每 50 篇写入
        if i % 50 == 0 or i == len(todo_fresh):
            all_rows.extend(batch_rows)
            df_tmp = pd.DataFrame(all_rows)
            df_tmp.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
            save_cache(cache)
            print(f"  >>> 进度: {i}/{len(todo_fresh)} | ok={n_ok} empty={n_empty} err={n_err} quat={n_quat} | 总行数={len(all_rows)}")
            batch_rows = []

    print(f"\n===== 批次 2 完成 =====")
    print(f"处理: {len(todo_fresh)} DOI")
    print(f"有三元 VLE: {n_ok}")
    print(f"无三元 VLE: {n_empty}")
    print(f"错误: {n_err}")
    print(f"含 4+ 组分: {n_quat}")
    print(f"新三元 VLE 行数: {len(all_rows)}")
    return all_rows

if __name__ == "__main__":
    rows = main()
    if rows:
        df = pd.DataFrame(rows)
        print(f"\n新数据 DOI 数: {df['DOI'].nunique()}")
        print(f"新数据体系数: {df.groupby(['名称1','名称2','名称3']).ngroups}")
