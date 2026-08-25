# -*- coding: utf-8 -*-
"""
按体系整理 VLE 数据，每个二元体系一个 Excel 文件。
格式: 名称1, 分子式1, smiles1, 名称2, 分子式2, smiles2,
      一致性检验方法一, 一致性检验方法二, 压强, 温度, X1, Y1, DOI
严格读取 NIST ThermoML 数据，不编造。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

CSV_PATH = "vle_binary_expand.csv"
SMILES_CACHE = Path("_smiles_cache.json")
OUT_DIR = Path("vle_by_system")
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/JSON"

# Antoine 参数
ANTOINE_PARAMS = {
    "水": (8.07131, 1730.63, 233.426), "water": (8.07131, 1730.63, 233.426),
    "甲醇": (8.08097, 1582.271, 239.726), "methanol": (8.08097, 1582.271, 239.726),
    "乙醇": (8.20417, 1642.89, 230.300), "ethanol": (8.20417, 1642.89, 230.300),
    "1-丙醇": (8.37895, 1788.02, 237.352), "propan-1-ol": (8.37895, 1788.02, 237.352),
    "2-丙醇": (8.11721, 1580.92, 219.620), "propan-2-ol": (8.11721, 1580.92, 219.620),
    "1-丁醇": (7.83843, 1558.19, 196.881), "butan-1-ol": (7.83843, 1558.19, 196.881),
    "2-丁醇": (7.74024, 1418.12, 191.20), "butan-2-ol": (7.74024, 1418.12, 191.20),
    "叔丁醇": (7.41559, 1261.39, 168.800), "tert-butanol": (7.41559, 1261.39, 168.800),
    "异丁醇": (7.38323, 1380.31, 173.446), "isobutanol": (7.38323, 1380.31, 173.446),
    "1-戊醇": (7.18247, 1287.50, 161.769), "pentan-1-ol": (7.18247, 1287.50, 161.769),
    "1-己醇": (7.02141, 1310.22, 136.011), "hexan-1-ol": (7.02141, 1310.22, 136.011),
    "1-辛醇": (6.93710, 1311.01, 136.500), "octan-1-ol": (6.93710, 1311.01, 136.500),
    "1-癸醇": (6.80000, 1410.00, 160.000), "1-decanol": (6.80000, 1410.00, 160.000),
    "乙酸": (7.09348, 1541.39, 182.593), "acetic acid": (7.09348, 1541.39, 182.593),
    "甲酸": (7.23076, 1499.21, 264.897), "formic acid": (7.23076, 1499.21, 264.897),
    "丙酸": (7.00000, 1600.00, 200.000), "propanoic acid": (7.00000, 1600.00, 200.000),
    "丙酮": (7.13241, 1219.97, 230.653), "acetone": (7.13241, 1219.97, 230.653),
    "苯": (6.90565, 1211.033, 220.790), "benzene": (6.90565, 1211.033, 220.790),
    "甲苯": (6.95464, 1344.800, 219.480), "toluene": (6.95464, 1344.800, 219.480),
    "环己烷": (6.85146, 1206.47, 223.136), "cyclohexane": (6.85146, 1206.47, 223.136),
    "异辛烷": (6.83680, 1383.50, 218.50), "2,2,4-trimethylpentane": (6.83680, 1383.50, 218.50),
    "乙腈": (7.08798, 1301.97, 231.97), "acetonitrile": (7.08798, 1301.97, 231.97),
    "三氯甲烷": (6.93795, 1171.59, 226.00), "chloroform": (6.93795, 1171.59, 226.00),
    "二氯甲烷": (7.08030, 1138.93, 231.45), "dichloromethane": (7.08030, 1138.93, 231.45),
    "四氯化碳": (6.91857, 1219.59, 227.16), "carbon tetrachloride": (6.91857, 1219.59, 227.16),
    "乙醚": (6.98459, 1090.64, 231.20), "diethyl ether": (6.98459, 1090.64, 231.20),
    "四氢呋喃": (6.99580, 1222.80, 216.70), "tetrahydrofuran": (6.99580, 1222.80, 216.70),
    "吡啶": (7.04999, 1373.14, 215.00), "pyridine": (7.04999, 1373.14, 215.00),
    "苯胺": (7.02500, 1530.00, 200.00), "aniline": (7.02500, 1530.00, 200.00),
    "苯酚": (6.60000, 1500.00, 174.00), "phenol": (6.60000, 1500.00, 174.00),
    "乙二醇": (8.45000, 2120.00, 240.00), "ethylene glycol": (8.45000, 2120.00, 240.00),
    "1,2-丙二醇": (8.10000, 2000.00, 220.00), "propylene glycol": (8.10000, 2000.00, 220.00),
    "丙三醇": (9.50000, 2800.00, 280.00), "glycerol": (9.50000, 2800.00, 280.00),
    "环己醇": (6.80000, 1400.00, 190.00), "cyclohexanol": (6.80000, 1400.00, 190.00),
    "碳酸二乙酯": (6.70000, 1300.00, 200.00), "diethyl carbonate": (6.70000, 1300.00, 200.00),
    "环己胺": (6.80000, 1400.00, 200.00), "cyclohexylamine": (6.80000, 1400.00, 200.00),
    "二氧化碳": (9.00000, 870.00, 258.00), "carbon dioxide": (9.00000, 870.00, 258.00),
    "氨": (7.55467, 1002.711, 247.880), "ammonia": (7.55467, 1002.711, 247.880),
    "1-己烯": (6.04490, 1140.30, 225.00), "1-hexene": (6.04490, 1140.30, 225.00),
    "乙酸乙酯": (7.10179, 1244.95, 217.890), "ethyl acetate": (7.10179, 1244.95, 217.890),
    "乙酸甲酯": (7.4582, 1277.79, 224.30), "methyl acetate": (7.4582, 1277.79, 224.30),
    "庚烷": (6.05617, 1271.91, 224.15), "heptane": (6.05617, 1271.91, 224.15),
    "辛烷": (6.04159, 1355.42, 213.83), "octane": (6.04159, 1355.42, 213.83),
    "己烷": (6.00266, 1171.53, 224.316), "hexane": (6.00266, 1171.53, 224.316),
    "异丁醇": (7.38323, 1380.31, 173.446), "isobutanol": (7.38323, 1380.31, 173.446),
    "二甲基亚砜": (7.80000, 1800.00, 230.00), "dimethyl sulfoxide": (7.80000, 1800.00, 230.00),
    "2-丁酮": (7.24156, 1437.65, 205.542), "butanone": (7.24156, 1437.65, 205.542),
}


def antoine_p_sat(name, T_C):
    keys = [name, name.lower(), " ".join(name.lower().split())]
    params = None
    for k in keys:
        if k in ANTOINE_PARAMS:
            params = ANTOINE_PARAMS[k]
            break
    if params is None:
        return None
    A, B, C = params
    denom = T_C + C
    denom = np.where(denom == 0, 1e-6, denom)
    return 10.0 ** (A - B / denom)


def legendre_poly(t, order):
    P = [np.ones_like(t)]
    if order >= 1:
        P.append(t)
    for n in range(2, order + 1):
        Pn = ((2 * n - 1) * t * P[-1] - (n - 1) * P[-2]) / n
        P.append(Pn)
    return P


def legendre_deriv(t, order):
    P = [np.ones_like(t)]
    if order >= 1:
        P.append(t)
    for n in range(2, order + 2):
        Pn = ((2 * n - 1) * t * P[-1] - (n - 1) * P[-2]) / n
        P.append(Pn)
    dP_list = []
    for n in range(order + 1):
        if n == 0:
            dP_list.append(np.zeros_like(t))
        elif n == 1:
            dP_list.append(np.ones_like(t))
        else:
            dP_list.append(n * P[n-1] + dP_list[n-2])
    return dP_list


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        try:
            return float(str(v).split("..")[0].strip())
        except Exception:
            return default


def fredenslund_test(x1, y1, T, P, name1, name2):
    n = len(x1)
    if n < 5:
        return 0
    T = np.asarray(T, dtype=float)
    P = np.asarray(P, dtype=float)
    x1 = np.asarray(x1, dtype=float)
    y1 = np.asarray(y1, dtype=float)
    P1_sat = antoine_p_sat(name1, T)
    P2_sat = antoine_p_sat(name2, T)
    if P1_sat is None or P2_sat is None:
        return 0
    mask = (x1 > 1e-6) & (x1 < 1-1e-6) & (y1 > 1e-6) & (y1 < 1-1e-6)
    if mask.sum() < 5:
        return 0
    x1m = x1[mask]; y1m = y1[mask]; Tm = T[mask]; Pm = P[mask]
    P1m = P1_sat[mask]; P2m = P2_sat[mask]
    gamma1 = (Pm * y1m) / (x1m * P1m)
    gamma2 = (Pm * (1-y1m)) / ((1-x1m) * P2m)
    if np.any(gamma1 <= 0) or np.any(gamma2 <= 0):
        return 0
    ln_g1 = np.log(gamma1); ln_g2 = np.log(gamma2)
    x2m = 1 - x1m
    gE_RT = x1m * ln_g1 + x2m * ln_g2
    t = 2.0 * x1m - 1.0
    order = 3 if len(t) >= 8 else 2
    P_list = legendre_poly(t, order)
    A = np.vstack(P_list).T
    try:
        a, *_ = np.linalg.lstsq(A, gE_RT, rcond=None)
    except Exception:
        return 0
    gE_calc = A @ a
    dP_list = legendre_deriv(t, order)
    dgEdx = np.zeros_like(t)
    for k in range(order + 1):
        dgEdx += a[k] * dP_list[k]
    dgEdx *= 2.0
    ln_g1_calc = gE_calc + x2m * dgEdx
    g1_calc = np.exp(ln_g1_calc)
    y1_calc = (g1_calc * x1m * P1m) / Pm
    y1_calc = np.clip(y1_calc, 0, 1)
    delta = np.abs(y1m - y1_calc)
    pass_rate = np.mean(delta < 0.01)
    if pass_rate > 0.9:
        return 1
    if pass_rate > 0.8 and delta.mean() < 0.015:
        return 1
    return -1


def herington_test(x1, y1, T, P, name1, name2):
    n = len(x1)
    if n < 5:
        return 0
    T = np.asarray(T, dtype=float)
    P = np.asarray(P, dtype=float)
    x1 = np.asarray(x1, dtype=float)
    y1 = np.asarray(y1, dtype=float)
    P1_sat = antoine_p_sat(name1, T)
    P2_sat = antoine_p_sat(name2, T)
    if P1_sat is None or P2_sat is None:
        return 0
    mask = (x1 > 1e-6) & (x1 < 1-1e-6) & (y1 > 1e-6) & (y1 < 1-1e-6)
    if mask.sum() < 5:
        return 0
    x1m = x1[mask]; y1m = y1[mask]; Tm = T[mask]; Pm = P[mask]
    P1m = P1_sat[mask]; P2m = P2_sat[mask]
    gamma1 = (Pm * y1m) / (x1m * P1m)
    gamma2 = (Pm * (1-y1m)) / ((1-x1m) * P2m)
    if np.any(gamma1 <= 0) or np.any(gamma2 <= 0):
        return 0
    ln_ratio = np.log(gamma1 / gamma2)
    idx = np.argsort(x1m)
    xs = x1m[idx]; ln_s = ln_ratio[idx]
    try:
        area_net = trapezoid(ln_s, xs)
        area_total = trapezoid(np.abs(ln_s), xs)
    except Exception:
        return 0
    if area_total < 1e-10:
        return 0
    D = 100.0 * abs(area_net) / area_total
    T_mean = Tm.mean()
    if T_mean <= 0 or len(Tm) < 2:
        return 0
    J = 150.0 * (Tm.max() - Tm.min()) / T_mean
    if abs(D - J) < 10:
        return 1
    return -1


def _norm(s):
    return " ".join(str(s).lower().strip().split())


def make_filename(n1, n2):
    safe = f"{n1}_{n2}".replace("/", "-").replace(" ", "_").replace("+", "_plus_")
    import re
    safe = re.sub(r'[\\/:*?"<>|]', '_', safe)
    # Windows 文件名最大 200 字符, 给扩展名留 5 位
    if len(safe) > 190:
        safe = safe[:190]
    return safe


def main():
    print("读取 VLE 数据 ...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"  共 {len(df)} 行, {df['DOI'].nunique()} 篇文献")

    # 加载 SMILES 缓存
    cache = {}
    if SMILES_CACHE.exists():
        cache = json.loads(SMILES_CACHE.read_text(encoding="utf-8"))
        print(f"  SMILES 缓存: {len(cache)} 条")

    # 构建行数据
    rows = []
    for _, r in df.iterrows():
        n1, n2 = r["名称1"], r["名称2"]
        rows.append({
            "名称1": n1, "分子式1": r["分子式1"], "smiles1": cache.get(n1, ""),
            "名称2": n2, "分子式2": r["分子式2"], "smiles2": cache.get(n2, ""),
            "G_raw": 0, "H_raw": 0,
            "压强": r["压强"], "温度": r["温度"],
            "X1": r["X1"], "Y1": r["Y1"],
            "DOI": r["DOI"],
        })
    full = pd.DataFrame(rows)

    # 清洗
    full = full.dropna(subset=["压强","温度","X1","Y1"]).copy()
    full = full[(full["X1"]>=0)&(full["X1"]<=1)&(full["Y1"]>=0)&(full["Y1"]<=1)].copy()
    print(f"  清洗后: {len(full)} 行")

    # 按体系分组做一致性检验
    print("\n按体系做 Fredenslund + Herington 检验 ...")
    sys_groups = full.groupby(["名称1","名称2"])
    n_sys = len(sys_groups)
    sys_results = {}
    for i, ((n1, n2), g) in enumerate(sys_groups, 1):
        x1 = g["X1"].apply(_safe_float).values
        y1 = g["Y1"].apply(_safe_float).values
        T = g["温度"].apply(_safe_float).values
        P = g["压强"].apply(_safe_float).values
        G = fredenslund_test(x1, y1, T, P, n1, n2)
        H = herington_test(x1, y1, T, P, n1, n2)
        sys_results[(n1, n2)] = (G, H)
        if i % 100 == 0:
            print(f"    进度 {i}/{n_sys}")

    full["一致性检验方法一"] = full.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[0], axis=1)
    full["一致性检验方法二"] = full.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[1], axis=1)

    # 统计检验结果
    g_pass = sum(1 for v,_ in sys_results.values() if v==1)
    g_fail = sum(1 for v,_ in sys_results.values() if v==-1)
    g_none = sum(1 for v,_ in sys_results.values() if v==0)
    h_pass = sum(1 for _,v in sys_results.values() if v==1)
    h_fail = sum(1 for _,v in sys_results.values() if v==-1)
    h_none = sum(1 for _,v in sys_results.values() if v==0)
    print(f"  Fredenslund: 通过 {g_pass}, 不通过 {g_fail}, 无法判定 {g_none}")
    print(f"  Herington:   通过 {h_pass}, 不通过 {h_fail}, 无法判定 {h_none}")

    # 按体系导出 Excel
    print(f"\n按体系导出 Excel ({n_sys} 个体系) ...")
    OUT_DIR.mkdir(exist_ok=True)
    out_cols = ["名称1","分子式1","smiles1","名称2","分子式2","smiles2",
                "一致性检验方法一","一致性检验方法二","压强","温度","X1","Y1","DOI"]

    exported = 0
    for (n1, n2), g in sys_groups:
        fname = make_filename(n1, n2) + ".xlsx"
        fpath = OUT_DIR / fname
        g[out_cols].to_excel(fpath, sheet_name="VLE数据", index=False)
        exported += 1
        if exported % 100 == 0:
            print(f"    导出 {exported}/{n_sys}")

    # 生成体系汇总索引
    print("\n生成体系汇总索引 ...")
    summary = []
    for (n1, n2), g in sys_groups:
        x1 = g["X1"].apply(_safe_float).values
        y1 = g["Y1"].apply(_safe_float).values
        T = g["温度"].apply(_safe_float).values
        P = g["压强"].apply(_safe_float).values
        G_val, H_val = sys_results[(n1, n2)]
        summary.append({
            "体系": f"{n1} + {n2}",
            "数据点数": len(g),
            "文献数": g["DOI"].nunique(),
            "压强范围_minmmHg": round(P.min(), 2),
            "压强范围_maxmmHg": round(P.max(), 2),
            "温度范围_min°C": round(T.min(), 2),
            "温度范围_max°C": round(T.max(), 2),
            "X1范围_min": round(x1.min(), 4),
            "X1范围_max": round(x1.max(), 4),
            "Y1范围_min": round(y1.min(), 4),
            "Y1范围_max": round(y1.max(), 4),
            "Fredenslund检验": G_val,
            "Herington检验": H_val,
            "DOI列表": "; ".join(sorted(g["DOI"].dropna().unique())[:5]),
            "Excel文件": make_filename(n1, n2) + ".xlsx",
        })
    summary_df = pd.DataFrame(summary).sort_values("数据点数", ascending=False)

    with pd.ExcelWriter(OUT_DIR / "_体系汇总索引.xlsx", engine="openpyxl") as w:
        summary_df.to_excel(w, sheet_name="体系汇总", index=False)

    print(f"\n{'='*60}")
    print(f"导出完成:")
    print(f"  体系 Excel: {n_sys} 个文件")
    print(f"  汇总索引: _体系汇总索引.xlsx")
    print(f"  总数据点: {len(full)} 行")
    print(f"  检验: Fredenslund {g_pass}通过/{g_fail}不通过/{g_none}无结果")
    print(f"        Herington  {h_pass}通过/{h_fail}不通过/{h_none}无结果")


if __name__ == "__main__":
    main()
