# -*- coding: utf-8 -*-
"""
把当前 CSV + 缓存中的数据整理成 Excel。
严格按格式: 名称1, 分子式1, smiles1, 名称2, 分子式2, smiles2,
            一致性检验方法一, 一致性检验方法二, 压强, 温度, X1, Y1, DOI
只整理第二批指定体系。
"""
from __future__ import annotations

import json, re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

# 加载已有的 CSV
df = pd.read_csv("vle_binary_expand.csv", encoding="utf-8-sig")
print(f"已有 CSV: {len(df)} 行")

# 读取第二批体系列表
user_systems = []
with open("_user_systems.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("+")]
        if len(parts) == 2:
            user_systems.append(tuple(parts))
print(f"指定体系: {len(user_systems)} 个")

# 中文→ThermoML 英文名映射
from _export_selected_v2 import cn_to_en

# 构建英文版体系列表
user_systems_en = []
for cn1, cn2 in user_systems:
    en1 = cn_to_en(cn1)
    en2 = cn_to_en(cn2)
    if en1 and en2:
        user_systems_en.append((en1, en2, cn1, cn2))

print(f"可映射的体系: {len(user_systems_en)} 个")

# 筛选数据
def match_df(df, en1, en2):
    mask1 = (df["名称1"] == en1) & (df["名称2"] == en2)
    mask2 = (df["名称1"] == en2) & (df["名称2"] == en1)
    return df[mask1 | mask2].copy()

found_systems = {}
for en1, en2, cn1, cn2 in user_systems_en:
    sub = match_df(df, en1, en2)
    if len(sub) > 0:
        found_systems[(cn1, cn2)] = sub

print(f"\n找到: {len(found_systems)} 个体系")
for (cn1, cn2), sub in sorted(found_systems.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {cn1} + {cn2}: {len(sub)} 行")

# 一致性检验
from _export_by_system import fredenslund_test, herington_test

print("\n对找到的体系做一致性检验 ...")
sys_results = {}
for i, ((cn1, cn2), sub) in enumerate(found_systems.items(), 1):
    en1 = cn_to_en(cn1)
    en2 = cn_to_en(cn2)
    x1 = sub["X1"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
    y1 = sub["Y1"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
    T = sub["温度"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
    P = sub["压强"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
    G = fredenslund_test(x1, y1, T, P, en1, en2)
    H = herington_test(x1, y1, T, P, en1, en2)
    sys_results[(cn1, cn2)] = (G, H)
    if i % 10 == 0:
        print(f"  进度 {i}/{len(found_systems)}")

for (cn1, cn2), sub in found_systems.items():
    G, H = sys_results[(cn1, cn2)]
    sub.loc[:, "一致性检验方法一"] = G
    sub.loc[:, "一致性检验方法二"] = H

# 导出
OUT_DIR = Path("vle_batch2_selected")
OUT_DIR.mkdir(exist_ok=True)
out_cols = ["名称1","分子式1","smiles1","名称2","分子式2","smiles2",
            "一致性检验方法一","一致性检验方法二","压强","温度","X1","Y1","DOI"]

print(f"\n导出 Excel ...")
summary = []
for (cn1, cn2), sub_df in sorted(found_systems.items(), key=lambda x: len(x[1]), reverse=True):
    safe = f"{cn1}_{cn2}".replace("/","-").replace(" ","_")
    safe = re.sub(r'[\\/:*?"<>|]', '_', safe)
    if len(safe) > 190:
        safe = safe[:190]
    fname = safe + ".xlsx"
    sub_df[out_cols].to_excel(OUT_DIR / fname, sheet_name="VLE数据", index=False)
    summary.append({
        "体系": f"{cn1} + {cn2}",
        "数据点数": len(sub_df),
        "文献数": sub_df["DOI"].nunique(),
        "Fredenslund": sub_df["一致性检验方法一"].iloc[0],
        "Herington": sub_df["一致性检验方法二"].iloc[0],
        "文件名": fname,
    })

summary_df = pd.DataFrame(summary).sort_values("数据点数", ascending=False)
with pd.ExcelWriter(OUT_DIR / "_体系汇总索引.xlsx", engine="openpyxl") as w:
    summary_df.to_excel(w, sheet_name="体系汇总", index=False)

# 未找到的
not_found = [(cn1, cn2) for cn1, cn2 in user_systems if (cn1, cn2) not in found_systems]
not_found_df = pd.DataFrame(not_found, columns=["组分1","组分2"])
with pd.ExcelWriter(OUT_DIR / "_未找到体系.xlsx", engine="openpyxl") as w:
    not_found_df.to_excel(w, sheet_name="未找到", index=False)

print(f"\n{'='*60}")
print(f"导出完成:")
print(f"  找到: {len(found_systems)} 个体系, 共 {sum(len(v) for v in found_systems.values())} 行")
print(f"  未找到: {len(not_found)} 个体系")
print(f"  位置: {OUT_DIR.absolute()}")
print(f"\nTop 10:")
for _, r in summary_df.head(10).iterrows():
    print(f"  {r['体系']}: {r['数据点数']} 点, {r['文献数']} 篇, G={r['Fredenslund']}, H={r['Herington']}")
