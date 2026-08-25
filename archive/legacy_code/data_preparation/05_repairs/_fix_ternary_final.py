# -*- coding: utf-8 -*-
"""
最终修复: 从 V3 二元 Excel 读 SMILES 映射(中文名->SMILES),
直接在已有的三元 Excel 上补 SMILES 列并重新导出.
"""
import json, time
from pathlib import Path
import pandas as pd
import requests

WORK = Path(__file__).resolve().parent

# 读已有三元 Excel（含一致性检验结果）
df = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
# SMILES 列转 str
for c in ['smiles1','smiles2','smiles3']:
    df[c] = df[c].fillna('').astype(str).replace('nan','')
print(f"三元数据: {len(df)} 行")

# 从 V3 二元 Excel 读中文名->SMILES
df_bin = pd.read_excel(WORK / "VLE_按体系分类整理_V3_扩展Antoine/A_完整数据汇总.xlsx", engine="openpyxl")
cn_to_smiles = {}
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2')]:
    for _, r in df_bin[[col_n, col_s]].drop_duplicates().iterrows():
        name = str(r[col_n]).strip()
        smi = str(r[col_s]).strip() if pd.notna(r[col_s]) else ""
        if name and smi and smi != "nan" and len(smi) > 2:
            cn_to_smiles[name] = smi
print(f"V3 二元中文名->SMILES 映射: {len(cn_to_smiles)} 种")

# 填充
filled = 0
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            name = str(df.loc[idx, col_n]).strip()
            if name in cn_to_smiles:
                df.loc[idx, col_s] = cn_to_smiles[name]
                filled += 1
print(f"从 V3 二元复用填充: {filled} 个")

# 未填充的 -> PubChem 按英文名查询
# 先反查英文名
EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
CN_TO_EN = {v: k for k, v in EN_TO_CN.items()}

need_cn = set()
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            need_cn.add(str(df.loc[idx, col_n]).strip())
need_cn -= set(cn_to_smiles.keys())
# 转英文名
need_en = set()
for cn in need_cn:
    if cn in CN_TO_EN:
        need_en.add(CN_TO_EN[cn])
    else:
        need_en.add(cn)  # 可能本来就是英文
print(f"需 PubChem 查询: {len(need_en)} 个化合物")

sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-smiles-final/1.0"})
pubchem_map = {}
failed = []
for i, name in enumerate(sorted(need_en), 1):
    if i % 20 == 0:
        print(f"  PubChem: {i}/{len(need_en)}, 已获取 {len(pubchem_map)}")
    try:
        r = sess.get(
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/property/IsomericSMILES/JSON",
            timeout=20)
        time.sleep(0.35)
        if r.status_code == 200:
            data = r.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props and props[0].get("IsomericSMILES"):
                pubchem_map[name] = props[0]["IsomericSMILES"]
            else:
                failed.append(name)
        else:
            failed.append(name)
    except Exception as e:
        failed.append(name)
print(f"PubChem 获取: {len(pubchem_map)}/{len(need_en)}")
if failed:
    print(f"  失败 ({len(failed)}): {failed[:10]}...")

# 应用 PubChem SMILES
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            cn = str(df.loc[idx, col_n]).strip()
            en = CN_TO_EN.get(cn, cn)
            if en in pubchem_map:
                df.loc[idx, col_s] = pubchem_map[en]

# 统计
for col_s in ['smiles1','smiles2','smiles3']:
    n = (df[col_s].str.strip() != '').sum()
    print(f"  {col_s}: {n}/{len(df)} ({n/len(df)*100:.1f}%)")

# 重新导出
OUT_DIR = WORK / "VLE_三元体系数据"
with pd.ExcelWriter(OUT_DIR / "A_三元完整数据汇总.xlsx", engine="openpyxl") as w:
    df.to_excel(w, sheet_name="三元VLE数据", index=False)
    
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

print(f"\n===== 最终导出 =====")
print(f"A_三元完整数据汇总.xlsx: {len(df)} 行, {ng} 体系, {df['DOI'].nunique()} DOI")
print(f"Fredenslund: 通过={nG_pass}, 不通过={nG_fail}, 无法判定={nG_unk}")
print(f"Herington:   通过={nH_pass}, 不通过={nH_fail}, 无法判定={nH_unk}")

# Top 10
print(f"\nTop 10 体系:")
for _, r in stats_df.head(10).iterrows():
    print(f"  {r['体系']}: {r['数据点数']}点, G={r['Fredenslund(G)']}, H={r['Herington(H)']}")
