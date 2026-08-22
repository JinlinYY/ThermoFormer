# -*- coding: utf-8 -*-
"""
对现有 CSV 数据进行后处理:
1. 补全 SMILES (PubChem 查询, 带缓存)
2. 按体系做 Fredenslund + Herington 一致性检验
3. 生成整理好的 Excel
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ==== SMILES 获取 ====
SMILES_CACHE = Path("_smiles_cache.json")
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/JSON"

def load_smiles_cache():
    if SMILES_CACHE.exists():
        return json.loads(SMILES_CACHE.read_text(encoding="utf-8"))
    return {}

def save_smiles_cache(cache):
    SMILES_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def get_smiles(name, cache):
    if name in cache:
        return cache[name]
    try:
        url = PUBCHEM_URL.format(name=requests.utils.quote(name))
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            smiles = data["PropertyTable"]["Properties"][0].get("IsomericSMILES", "")
            cache[name] = smiles
            return smiles
        else:
            cache[name] = ""
            return ""
    except Exception:
        cache[name] = ""
        return ""

# ==== Antoine 参数 ====
ANTOINE_PARAMS = {
    "水": (8.07131, 1730.63, 233.426), "water": (8.07131, 1730.63, 233.426),
    "甲醇": (8.08097, 1582.271, 239.726), "methanol": (8.08097, 1582.271, 239.726),
    "乙醇": (8.20417, 1642.89, 230.300), "ethanol": (8.20417, 1642.89, 230.300),
    "1-丙醇": (8.37895, 1788.02, 237.352), "propan-1-ol": (8.37895, 1788.02, 237.352),
    "2-丙醇": (8.11721, 1580.92, 219.620), "propan-2-ol": (8.11721, 1580.92, 219.620),
    "1-丁醇": (7.83843, 1558.19, 196.881), "butan-1-ol": (7.83843, 1558.19, 196.881),
    "丙酮": (7.13241, 1219.97, 230.653), "acetone": (7.13241, 1219.97, 230.653),
    "苯": (6.90565, 1211.033, 220.790), "benzene": (6.90565, 1211.033, 220.790),
    "甲苯": (6.95464, 1344.800, 219.480), "toluene": (6.95464, 1344.800, 219.480),
    "环己烷": (6.85146, 1206.47, 223.136), "cyclohexane": (6.85146, 1206.47, 223.136),
    "乙腈": (7.08798, 1301.97, 231.97), "acetonitrile": (7.08798, 1301.97, 231.97),
    "三氯甲烷": (6.93795, 1171.59, 226.00), "chloroform": (6.93795, 1171.59, 226.00),
    "四氢呋喃": (6.99580, 1222.80, 216.70), "tetrahydrofuran": (6.99580, 1222.80, 216.70),
    "吡啶": (7.04999, 1373.14, 215.00), "pyridine": (7.04999, 1373.14, 215.00),
    "乙酸乙酯": (7.10179, 1244.95, 217.890), "ethyl acetate": (7.10179, 1244.95, 217.890),
    "乙酸甲酯": (7.4582, 1277.79, 224.30), "methyl acetate": (7.4582, 1277.79, 224.30),
    "庚烷": (6.05617, 1271.91, 224.15), "heptane": (6.05617, 1271.91, 224.15),
    "辛烷": (6.04159, 1355.42, 213.83), "octane": (6.04159, 1355.42, 213.83),
    "己烷": (6.00266, 1171.53, 224.316), "hexane": (6.00266, 1171.53, 224.316),
    "二甲基亚砜": (7.80000, 1800.00, 230.00), "dimethyl sulfoxide": (7.80000, 1800.00, 230.00),
    "二氧化碳": (9.00000, 870.00, 258.00), "carbon dioxide": (9.00000, 870.00, 258.00),
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
    from scipy.integrate import trapezoid
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

# ==== 主流程 ====
def main():
    print("读取 VLE 数据 ...")
    df = pd.read_csv("vle_binary_expand.csv", encoding="utf-8-sig")
    print(f"  共 {len(df)} 行, {df['DOI'].nunique()} 篇文献")
    
    # 清洗
    df = df.dropna(subset=["压强","温度","X1","Y1"]).copy()
    df = df[(df["X1"]>=0)&(df["X1"]<=1)&(df["Y1"]>=0)&(df["Y1"]<=1)].copy()
    print(f"  清洗后: {len(df)} 行")
    
    # ==== Step 1: 补全 SMILES ====
    print("\n==== Step 1: 补全 SMILES ====")
    smiles_cache = load_smiles_cache()
    all_names = set(df["名称1"].unique()) | set(df["名称2"].unique())
    print(f"  需要查询 {len(all_names)} 个化合物")
    
    for i, name in enumerate(sorted(all_names), 1):
        if name not in smiles_cache or not smiles_cache[name]:
            get_smiles(name, smiles_cache)
            time.sleep(0.1)
        if i % 50 == 0:
            print(f"  {i}/{len(all_names)}")
    
    save_smiles_cache(smiles_cache)
    print(f"  SMILES 缓存: {len(smiles_cache)} 条")
    
    # 填充 SMILES
    df["smiles1"] = df["名称1"].map(smiles_cache)
    df["smiles2"] = df["名称2"].map(smiles_cache)
    print(f"  smiles1 非空: {df['smiles1'].notna().sum()}")
    print(f"  smiles2 非空: {df['smiles2'].notna().sum()}")
    
    # ==== Step 2: 一致性检验 ====
    print("\n==== Step 2: 一致性检验 ====")
    sys_results = {}
    groups = df.groupby(["名称1","名称2"])
    n_sys = len(groups)
    print(f"  共 {n_sys} 个体系")
    
    for i, ((n1, n2), sub) in enumerate(groups, 1):
        x1 = sub["X1"].values
        y1 = sub["Y1"].values
        T = sub["温度"].values
        P = sub["压强"].values
        G = fredenslund_test(x1, y1, T, P, n1, n2)
        H = herington_test(x1, y1, T, P, n1, n2)
        sys_results[(n1, n2)] = (G, H)
        if i % 100 == 0:
            print(f"  {i}/{n_sys}")
    
    G_vals = [v[0] for v in sys_results.values()]
    H_vals = [v[1] for v in sys_results.values()]
    print(f"  Fredenslund: 通过={sum(1 for v in G_vals if v==1)}, 不通过={sum(1 for v in G_vals if v==-1)}, 无法判定={sum(1 for v in G_vals if v==0)}")
    print(f"  Herington:   通过={sum(1 for v in H_vals if v==1)}, 不通过={sum(1 for v in H_vals if v==-1)}, 无法判定={sum(1 for v in H_vals if v==0)}")
    
    df["一致性检验方法一"] = df.apply(lambda r: sys_results.get((r["名称1"], r["名称2"]), (0,0))[0], axis=1)
    df["一致性检验方法二"] = df.apply(lambda r: sys_results.get((r["名称1"], r["名称2"]), (0,0))[1], axis=1)
    
    # ==== Step 3: 格式化列 ====
    print("\n==== Step 3: 格式化 ====")
    final_cols = ['名称1','分子式1','smiles1','名称2','分子式2','smiles2',
                  '一致性检验方法一','一致性检验方法二','压强','温度','X1','Y1','DOI']
    # 转换一致性检验结果: 1→通过, -1→不通过, 0→无法判定
    df["一致性检验方法一"] = df["一致性检验方法一"].map({1: "通过", -1: "不通过", 0: "无法判定"})
    df["一致性检验方法二"] = df["一致性检验方法二"].map({1: "通过", -1: "不通过", 0: "无法判定"})
    
    # 保留需要的列
    df_final = df[final_cols].copy()
    
    # 去重
    df_final = df_final.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
    print(f"  最终: {len(df_final)} 行, {df_final['DOI'].nunique()} DOI")
    
    # ==== Step 4: 保存 ====
    out_xlsx = "vle_binary_data_organized.xlsx"
    df_final.to_excel(out_xlsx, index=False, engine="openpyxl")
    print(f"\n已保存: {out_xlsx}")
    
    # 同时保存 CSV
    out_csv = "vle_binary_data_organized.csv"
    df_final.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"已保存: {out_csv}")
    
    # 打印部分体系统计
    print("\n体系统计 (前 30):")
    sys_stats = df_final.groupby(["名称1","名称2"]).agg(
        数据点数=("X1","count"),
        文献数=("DOI","nunique")
    ).reset_index().sort_values("数据点数", ascending=False)
    for _, r in sys_stats.head(30).iterrows():
        print(f"  {r['名称1']} + {r['名称2']}: {r['数据点数']} 点, {r['文献数']} 篇")

if __name__ == "__main__":
    main()
