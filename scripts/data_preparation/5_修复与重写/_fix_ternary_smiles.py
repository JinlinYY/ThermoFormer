# -*- coding: utf-8 -*-
"""
修复三元 VLE:
1. 用化合物名称查 PubChem 补 SMILES
2. 从二元数据中复用已有 SMILES
3. 重新导出 Excel
"""
import json, time
from pathlib import Path
import pandas as pd
import requests

WORK = Path(__file__).resolve().parent

# 读三元数据
df = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
# 确保 SMILES 列为字符串类型（避免 float64 赋值冲突）
for col in ['smiles1','smiles2','smiles3']:
    df[col] = df[col].astype(str).replace('nan','')
print(f"三元数据: {len(df)} 行, {df['DOI'].nunique()} DOI")

# 从二元数据中复用 SMILES 映射
df_bin = pd.read_excel(WORK / "VLE_按体系分类整理_V3_扩展Antoine/A_完整数据汇总.xlsx", engine="openpyxl")
name_to_smiles = {}
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2')]:
    for _, r in df_bin[[col_n, col_s]].drop_duplicates().iterrows():
        name = r[col_n]
        smi = r[col_s]
        if pd.notna(name) and pd.notna(smi) and str(smi).strip():
            name_to_smiles[str(name).strip()] = str(smi).strip()
print(f"从二元数据复用 SMILES 映射: {len(name_to_smiles)} 种化合物")

# 用名称直接映射
filled = 0
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    mask = (df[col_s].astype(str).str.strip() == '') | (df[col_s].astype(str) == 'nan')
    for idx in df[mask].index:
        name = str(df.loc[idx, col_n]).strip()
        if name in name_to_smiles:
            df.loc[idx, col_s] = name_to_smiles[name]
            filled += 1
print(f"从二元复用填充: {filled} 个")

# 仍未填充的 -> PubChem 查询
need_names = set()
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for name, smi in zip(df[col_n], df[col_s]):
        s = str(smi).strip()
        if pd.notna(name) and (s == '' or s == 'nan'):
            need_names.add(str(name).strip())
# 去掉已知无法查的
need_names -= set(name_to_smiles.keys())
print(f"需 PubChem 查询: {len(need_names)} 个化合物")

# PubChem 查询
sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-smiles/1.0"})
pubchem_map = {}
for i, name in enumerate(sorted(need_names), 1):
    if i % 20 == 0:
        print(f"  PubChem: {i}/{len(need_names)}")
    try:
        r = sess.get(
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/property/IsomericSMILES/JSON",
            timeout=15)
        time.sleep(0.3)
        if r.status_code == 200:
            data = r.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props and props[0].get("IsomericSMILES"):
                pubchem_map[name] = props[0]["IsomericSMILES"]
    except:
        pass
print(f"PubChem 获取: {len(pubchem_map)}/{len(need_names)}")

# 应用 PubChem SMILES
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    mask = (df[col_s].astype(str).str.strip() == '') | (df[col_s].astype(str) == 'nan')
    for idx in df[mask].index:
        name = str(df.loc[idx, col_n]).strip()
        if name in pubchem_map:
            df.loc[idx, col_s] = pubchem_map[name]

# 统计
for col_s in ['smiles1','smiles2','smiles3']:
    n_filled = (df[col_s].astype(str).str.strip().ne('') & df[col_s].astype(str).str.strip().ne('nan')).sum()
    print(f"  {col_s}: {n_filled}/{len(df)} ({n_filled/len(df)*100:.1f}%)")

# 导出
with pd.ExcelWriter(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl") as w:
    df.to_excel(w, sheet_name="三元VLE数据", index=False)
    
    # 体系统计
    stats = []
    for (n1,n2,n3), g in df.groupby(['名称1','名称2','名称3']):
        stats.append({
            '体系': f'{n1} + {n2} + {n3}',
            '数据点数': len(g),
            '文献数': g['DOI'].nunique(),
            'Fredenslund(G)': int(g['一致性检验方法一'].iloc[0]),
            'Herington(H)': int(g['一致性检验方法二'].iloc[0]),
            '温度范围(°C)': f"{g['温度'].min():.1f} ~ {g['温度'].max():.1f}",
            '压强范围(mmHg)': f"{g['压强'].min():.1f} ~ {g['压强'].max():.1f}",
        })
    stats_df = pd.DataFrame(stats).sort_values('数据点数', ascending=False)
    stats_df.to_excel(w, sheet_name="体系统计", index=False)
    
    ng = len(stats)
    nG_pass = int((stats_df['Fredenslund(G)']==1).sum())
    nG_fail = int((stats_df['Fredenslund(G)']==-1).sum())
    nG_unk = int((stats_df['Fredenslund(G)']==0).sum())
    nH_pass = int((stats_df['Herington(H)']==1).sum())
    nH_fail = int((stats_df['Herington(H)']==-1).sum())
    nH_unk = int((stats_df['Herington(H)']==0).sum())
    
    overview = pd.DataFrame([
        {'项目':'总数据点','数值':len(df)},
        {'项目':'总DOI数','数值':df['DOI'].nunique()},
        {'项目':'总体系数','数值':ng},
        {'项目':'化合物种类','数值':len(set(df['名称1'])|set(df['名称2'])|set(df['名称3']))},
        {'项目':'Fredenslund通过','数值':nG_pass},
        {'项目':'Fredenslund不通过','数值':nG_fail},
        {'项目':'Fredenslund无法判定','数值':nG_unk},
        {'项目':'Herington通过','数值':nH_pass},
        {'项目':'Herington不通过','数值':nH_fail},
        {'项目':'Herington无法判定','数值':nH_unk},
    ])
    overview.to_excel(w, sheet_name="数据概览", index=False)

# B. 通过子集
df_pass = df[(df['一致性检验方法一']==1)|(df['一致性检验方法二']==1)]
with pd.ExcelWriter(WORK / "VLE_三元体系数据/B_三元通过一致性检验.xlsx", engine="openpyxl") as w:
    df_pass.to_excel(w, sheet_name="通过检验数据", index=False)

print(f"\n导出完成:")
print(f"  A_三元完整数据汇总.xlsx: {len(df)} 行, {ng} 体系, {df['DOI'].nunique()} DOI")
print(f"  B_三元通过一致性检验.xlsx: {len(df_pass)} 行")
print(f"  Fredenslund: 通过={nG_pass}, 不通过={nG_fail}, 无法判定={nG_unk}")
print(f"  Herington:   通过={nH_pass}, 不通过={nH_fail}, 无法判定={nH_unk}")
