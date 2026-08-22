# -*- coding: utf-8 -*-
"""
修复三元 VLE 的 SMILES:
1. 从原始 CSV 读英文化合物名
2. 用二元数据的英文名->SMILES 映射
3. PubChem 查询补全剩余
4. 中文名映射后重新导出
"""
import json, time
from pathlib import Path
import pandas as pd
import requests

WORK = Path(__file__).resolve().parent

# 读原始 CSV（英文名）
df_raw = pd.read_csv(WORK / "vle_ternary_expand.csv", encoding="utf-8-sig")
print(f"原始三元 CSV: {len(df_raw)} 行")

# 从二元原始 CSV 建英文名->SMILES 映射
df_bin = pd.read_csv(WORK / "vle_binary_expand.csv", encoding="utf-8-sig")
en_to_smiles = {}
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2')]:
    for _, r in df_bin[[col_n, col_s]].drop_duplicates().iterrows():
        name = str(r[col_n]).strip()
        smi = str(r[col_s]).strip() if pd.notna(r[col_s]) else ""
        if name and smi and smi != "nan":
            en_to_smiles[name] = smi
print(f"二元英文名->SMILES 映射: {len(en_to_smiles)} 种")

# 用 CAS 号也建映射
en_to_cas = {}
for col_n, col_c in [('名称1','CAS1'),('名称2','CAS2')]:
    for _, r in df_bin[[col_n, col_c]].drop_duplicates().iterrows():
        name = str(r[col_n]).strip()
        cas = str(r[col_c]).strip() if pd.notna(r[col_c]) else ""
        if name and cas and cas != "nan":
            en_to_cas[name] = cas

# 填充 SMILES
for col_n, col_s, col_cas in [('名称1','smiles1','CAS1'),('名称2','smiles2','CAS2'),('名称3','smiles3','CAS3')]:
    df_raw[col_s] = ""  # 清空
    for idx in df_raw.index:
        en_name = str(df_raw.loc[idx, col_n]).strip()
        if en_name in en_to_smiles:
            df_raw.loc[idx, col_s] = en_to_smiles[en_name]

# 统计已填充
for col_s in ['smiles1','smiles2','smiles3']:
    n = (df_raw[col_s].astype(str).str.strip() != "").sum()
    print(f"  {col_s} 从二元复用: {n}/{len(df_raw)} ({n/len(df_raw)*100:.1f}%)")

# 未填充的 -> PubChem 查询
need = set()
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for name, smi in zip(df_raw[col_n], df_raw[col_s]):
        if str(smi).strip() == "":
            need.add(str(name).strip())
need -= set(en_to_smiles.keys())
print(f"需 PubChem 查询: {len(need)} 个英文名")

sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-smiles-fix/1.0"})
pubchem_map = {}
for i, name in enumerate(sorted(need), 1):
    if i % 20 == 0:
        print(f"  PubChem: {i}/{len(need)}")
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
print(f"PubChem 获取: {len(pubchem_map)}/{len(need)}")

# 应用 PubChem SMILES
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df_raw.index:
        if str(df_raw.loc[idx, col_s]).strip() == "":
            name = str(df_raw.loc[idx, col_n]).strip()
            if name in pubchem_map:
                df_raw.loc[idx, col_s] = pubchem_map[name]

# 统计
for col_s in ['smiles1','smiles2','smiles3']:
    n = (df_raw[col_s].astype(str).str.strip() != "").sum()
    print(f"  {col_s} 最终: {n}/{len(df_raw)} ({n/len(df_raw)*100:.1f}%)")

# ====== 中文名映射 ======
EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
def to_cn(name):
    if pd.isna(name): return name
    s = str(name).strip()
    return EN_TO_CN.get(s, s)
for col in ['名称1','名称2','名称3']:
    df_raw[col] = df_raw[col].apply(to_cn)

# ====== 清洗（与之前一致）======
df = df_raw.dropna(subset=['压强','温度','X1','X2','Y1','Y2']).copy()
df['X3'] = 1 - df['X1'] - df['X2']
df['Y3'] = 1 - df['Y1'] - df['Y2']
df = df[(df['X1']>=0)&(df['X1']<=1)&(df['X2']>=0)&(df['X2']<=1)&(df['X3']>=-0.001)&(df['X3']<=1)]
df = df[(df['Y1']>=0)&(df['Y1']<=1)&(df['Y2']>=0)&(df['Y2']<=1)&(df['Y3']>=-0.001)&(df['Y3']<=1)]
df = df.drop_duplicates(subset=['名称1','名称2','名称3','压强','温度','X1','X2','Y1','Y2','DOI'])
df = df.reset_index(drop=True)
print(f"\n清洗后: {len(df)} 行, {df['DOI'].nunique()} DOI, {df.groupby(['名称1','名称2','名称3']).ngroups} 体系")

# ====== 一致性检验（从 V3 Excel 读取已有结果）======
df_v3 = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
# 按 DOI+压强+温度+X1+X2+Y1+Y2 做关联
key_cols = ['DOI','压强','温度','X1','X2','Y1','Y2']
df_v3_keys = df_v3[key_cols + ['一致性检验方法一','一致性检验方法二']].copy()
df = df.merge(df_v3_keys, on=key_cols, how='left')
print(f"关联一致性检验: G非空={df['一致性检验方法一'].notna().sum()}, H非空={df['一致性检验方法二'].notna().sum()}")

# ====== 导出 ======
cols_out = [
    '名称1','分子式1','smiles1',
    '名称2','分子式2','smiles2',
    '名称3','分子式3','smiles3',
    '一致性检验方法一','一致性检验方法二',
    '压强','温度',
    'X1','X2','Y1','Y2',
    'DOI'
]
df_out = df[cols_out].copy()
df_out['压强'] = df_out['压强'].round(3)
df_out['温度'] = df_out['温度'].round(3)

OUT_DIR = WORK / "VLE_三元体系数据"
OUT_DIR.mkdir(exist_ok=True)

with pd.ExcelWriter(OUT_DIR / "A_三元完整数据汇总.xlsx", engine="openpyxl") as w:
    df_out.to_excel(w, sheet_name="三元VLE数据", index=False)
    
    stats = []
    for (n1,n2,n3), g in df_out.groupby(['名称1','名称2','名称3']):
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
        {'项目':'总数据点','数值':len(df_out)},
        {'项目':'总DOI数','数值':df_out['DOI'].nunique()},
        {'项目':'总体系数','数值':ng},
        {'项目':'化合物种类','数值':len(set(df_out['名称1'])|set(df_out['名称2'])|set(df_out['名称3']))},
        {'项目':'Fredenslund通过','数值':nG_pass},
        {'项目':'Fredenslund不通过','数值':nG_fail},
        {'项目':'Fredenslund无法判定','数值':nG_unk},
        {'项目':'Herington通过','数值':nH_pass},
        {'项目':'Herington不通过','数值':nH_fail},
        {'项目':'Herington无法判定','数值':nH_unk},
    ])
    overview.to_excel(w, sheet_name="数据概览", index=False)

df_pass = df_out[(df_out['一致性检验方法一']==1)|(df_out['一致性检验方法二']==1)]
with pd.ExcelWriter(OUT_DIR / "B_三元通过一致性检验.xlsx", engine="openpyxl") as w:
    df_pass.to_excel(w, sheet_name="通过检验数据", index=False)

print(f"\n===== 导出完成 =====")
print(f"A_三元完整数据汇总.xlsx: {len(df_out)} 行, {ng} 体系, {df_out['DOI'].nunique()} DOI")
print(f"B_三元通过一致性检验.xlsx: {len(df_pass)} 行")
print(f"Fredenslund: 通过={nG_pass}, 不通过={nG_fail}, 无法判定={nG_unk}")
print(f"Herington:   通过={nH_pass}, 不通过={nH_fail}, 无法判定={nH_unk}")
