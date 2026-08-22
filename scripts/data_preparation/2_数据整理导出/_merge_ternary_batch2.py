# -*- coding: utf-8 -*-
"""
合并批次 1 + 批次 2 三元 VLE 数据:
1. 加载已有三元数据 (4,987 行) + 新数据 (242 行)
2. 中文名映射
3. 一致性检验 (Fredenslund 三元 + Herington 三元)
4. SMILES 补全 (从 V3 二元 + PubChem)
5. 严格格式导出 Excel (含四元空表说明)
"""
from __future__ import annotations
import json, time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

WORK = Path(__file__).resolve().parent
EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
ANTOINE_RAW = json.load(open(WORK / "_antoine_cn_full.json", "r", encoding="utf-8"))
ANTOINE_CN = ANTOINE_RAW["log10(P_mmHg)_A_minus_B_over_TdegC_plus_C"]

# ====== 1. 加载数据 ======
df_old = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
df_new = pd.read_csv(WORK / "vle_ternary_batch2.csv", encoding="utf-8-sig")
print(f"已有数据: {len(df_old)} 行, {df_old['DOI'].nunique()} DOI")
print(f"新数据: {len(df_new)} 行, {df_new['DOI'].nunique()} DOI")

# 合并前统一列
# 新数据还没有中文名映射，需要先做
def to_cn(name):
    if pd.isna(name): return name
    s = str(name).strip()
    return EN_TO_CN.get(s, s)

for col in ['名称1','名称2','名称3']:
    df_new[col] = df_new[col].apply(to_cn)

# 确保列对齐
cols_common = [
    '名称1','分子式1','smiles1',
    '名称2','分子式2','smiles2',
    '名称3','分子式3','smiles3',
    '一致性检验方法一','一致性检验方法二',
    '压强','温度','X1','X2','Y1','Y2','DOI'
]
df_old = df_old[cols_common].copy()
df_new = df_new[cols_common].copy()

# SMILES 列处理
for c in ['smiles1','smiles2','smiles3']:
    df_old[c] = df_old[c].fillna('').astype(str).replace('nan','')
    df_new[c] = df_new[c].fillna('').astype(str).replace('nan','')

# 合并 + 去重
df = pd.concat([df_old, df_new], ignore_index=True)
df = df.drop_duplicates(subset=['名称1','名称2','名称3','压强','温度','X1','X2','Y1','Y2','DOI'])
df = df.reset_index(drop=True)
print(f"合并后: {len(df)} 行, {df['DOI'].nunique()} DOI, {df.groupby(['名称1','名称2','名称3']).ngroups} 体系")

# ====== 2. 一致性检验 ======
def antoine_p_sat(name, T_C):
    if name not in ANTOINE_CN: return None
    A, B, C = ANTOINE_CN[name]
    T_C = np.asarray(T_C, dtype=float)
    denom = T_C + C
    denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
    p = 10.0 ** (A - B / denom)
    return np.where(np.isfinite(p) & (p > 1e-6) & (p < 1e7), p, np.nan)

def fredenslund_ternary(x1, x2, y1, y2, T, P, n1, n2, n3):
    n = len(x1)
    if n < 6: return 0
    x1=np.asarray(x1,float); x2=np.asarray(x2,float)
    y1=np.asarray(y1,float); y2=np.asarray(y2,float)
    T=np.asarray(T,float); P=np.asarray(P,float)
    P1s=antoine_p_sat(n1,T); P2s=antoine_p_sat(n2,T); P3s=antoine_p_sat(n3,T)
    if P1s is None or P2s is None or P3s is None: return 0
    valid=np.isfinite(P1s)&np.isfinite(P2s)&np.isfinite(P3s)&(P1s>0)&(P2s>0)&(P3s>0)
    if valid.sum()<6: return 0
    x1v=x1[valid]; x2v=x2[valid]; y1v=y1[valid]; y2v=y2[valid]
    Tv=T[valid]; Pv=P[valid]; P1m=P1s[valid]; P2m=P2s[valid]; P3m=P3s[valid]
    x3v=1.0-x1v-x2v
    mask=(x1v>1e-6)&(x1v<1-1e-6)&(x2v>1e-6)&(x2v<1-1e-6)&(x3v>1e-6)
    if mask.sum()<6: return 0
    x1m=x1v[mask]; x2m=x2v[mask]; x3m=x3v[mask]; y1m=y1v[mask]; y2m=y2v[mask]
    Tm=Tv[mask]; Pm=Pv[mask]; P1=P1m[mask]; P2=P2m[mask]; P3=P3m[mask]
    gamma1=(Pm*y1m)/(x1m*P1); gamma2=(Pm*y2m)/(x2m*P2); gamma3=(Pm*(1-y1m-y2m))/(x3m*P3)
    if np.any(gamma1<=0) or np.any(gamma2<=0) or np.any(gamma3<=0): return 0
    gE_RT=x1m*np.log(gamma1)+x2m*np.log(gamma2)+x3m*np.log(gamma3)
    A_mat=np.column_stack([np.ones_like(x1m),x1m,x2m,x1m**2,x2m**2,x1m*x2m])
    try: a,*_=np.linalg.lstsq(A_mat,gE_RT,rcond=None)
    except: return 0
    gE_calc=A_mat@a
    dg_dx1=a[1]+2*a[3]*x1m+a[5]*x2m; dg_dx2=a[2]+2*a[4]*x2m+a[5]*x1m
    ln_g1_calc=gE_calc+(1-x1m)*dg_dx1-x2m*dg_dx2
    ln_g2_calc=gE_calc-x1m*dg_dx1+(1-x2m)*dg_dx2
    ln_g3_calc=gE_calc-x1m*dg_dx1-x2m*dg_dx2
    g1_calc=np.exp(np.clip(ln_g1_calc,-50,50)); g2_calc=np.exp(np.clip(ln_g2_calc,-50,50))
    y1_calc=np.clip((g1_calc*x1m*P1)/Pm,0,1); y2_calc=np.clip((g2_calc*x2m*P2)/Pm,0,1)
    delta=np.maximum(np.abs(y1m-y1_calc),np.abs(y2m-y2_calc))
    pass_rate=np.mean(delta<0.01)
    if pass_rate>0.9: return 1
    if pass_rate>0.8 and delta.mean()<0.015: return 1
    return -1

def herington_ternary(x1, x2, y1, y2, T, P, n1, n2, n3):
    n=len(x1)
    if n<6: return 0
    x1=np.asarray(x1,float); x2=np.asarray(x2,float)
    y1=np.asarray(y1,float); y2=np.asarray(y2,float)
    T=np.asarray(T,float); P=np.asarray(P,float)
    P1s=antoine_p_sat(n1,T); P2s=antoine_p_sat(n2,T); P3s=antoine_p_sat(n3,T)
    if P1s is None or P2s is None or P3s is None: return 0
    valid=np.isfinite(P1s)&np.isfinite(P2s)&np.isfinite(P3s)&(P1s>0)&(P2s>0)&(P3s>0)
    if valid.sum()<6: return 0
    x1v=x1[valid]; x2v=x2[valid]; y1v=y1[valid]; y2v=y2[valid]
    Tv=T[valid]; Pv=P[valid]; P1m=P1s[valid]; P2m=P2s[valid]; P3m=P3s[valid]
    x3v=1.0-x1v-x2v
    mask=(x1v>1e-6)&(x2v>1e-6)&(x3v>1e-6)&(y1v>1e-6)&(y2v>1e-6)
    if mask.sum()<6: return 0
    x1m=x1v[mask]; x2m=x2v[mask]; x3m=x3v[mask]; y1m=y1v[mask]; y2m=y2v[mask]
    Tm=Tv[mask]; Pm=Pv[mask]; P1=P1m[mask]; P2=P2m[mask]; P3=P3m[mask]
    gamma1=(Pm*y1m)/(x1m*P1); gamma2=(Pm*y2m)/(x2m*P2); gamma3=(Pm*(1-y1m-y2m))/(x3m*P3)
    if np.any(gamma1<=0) or np.any(gamma2<=0) or np.any(gamma3<=0): return 0
    ln_r12=np.log(gamma1/gamma2); ln_r13=np.log(gamma1/gamma3)
    if not np.all(np.isfinite(ln_r12)) or not np.all(np.isfinite(ln_r13)): return 0
    try:
        from scipy.integrate import trapezoid
        idx1=np.argsort(x1m)
        a1n=trapezoid(ln_r12[idx1],x1m[idx1]); a1t=trapezoid(np.abs(ln_r12[idx1]),x1m[idx1])
        if a1t<1e-8: return 0
        D1=100.0*abs(a1n)/a1t
        idx2=np.argsort(x2m)
        a2n=trapezoid(ln_r13[idx2],x2m[idx2]); a2t=trapezoid(np.abs(ln_r13[idx2]),x2m[idx2])
        if a2t<1e-8: return 0
        D2=100.0*abs(a2n)/a2t
    except: return 0
    T_mean=Tm.mean()
    if T_mean<=0 or len(Tm)<2: return 0
    J=150.0*(Tm.max()-Tm.min())/T_mean
    if abs(D1-J)<10 and abs(D2-J)<10: return 1
    return -1

# 对新 DOI 的体系做一致性检验
new_dois = set(df_new['DOI'].unique())
print(f"\n对新 DOI ({len(new_dois)} 个) 的体系做一致性检验...")
groups = df.groupby(['名称1','名称2','名称3'])
ng = groups.ngroups
new_G = df['一致性检验方法一'].values.copy()
new_H = df['一致性检验方法二'].values.copy()
pass_G = pass_H = valid_sys = 0

for i, ((n1,n2,n3), g) in enumerate(groups, 1):
    # 跳过已有检验结果的体系（除非含新 DOI）
    if not (set(g['DOI'].unique()) & new_dois):
        continue
    idx = g.index.to_numpy()
    gG = fredenslund_ternary(g['X1'].values, g['X2'].values,
                             g['Y1'].values, g['Y2'].values,
                             g['温度'].values, g['压强'].values, n1, n2, n3)
    gH = herington_ternary(g['X1'].values, g['X2'].values,
                            g['Y1'].values, g['Y2'].values,
                            g['温度'].values, g['压强'].values, n1, n2, n3)
    new_G[idx] = gG; new_H[idx] = gH
    print(f"  体系 {n1}+{n2}+{n3}: G={gG}, H={gH}")

df['一致性检验方法一'] = new_G
df['一致性检验方法二'] = new_H

# ====== 3. SMILES 补全 ======
print("\n补全 SMILES...")
# 从 V3 二元 Excel 读映射
df_bin = pd.read_excel(WORK / "VLE_按体系分类整理_V3_扩展Antoine/A_完整数据汇总.xlsx", engine="openpyxl")
cn_to_smiles = {}
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2')]:
    for _, r in df_bin[[col_n, col_s]].drop_duplicates().iterrows():
        name = str(r[col_n]).strip()
        smi = str(r[col_s]).strip() if pd.notna(r[col_s]) else ""
        if name and smi and smi != "nan" and len(smi) > 2:
            cn_to_smiles[name] = smi
print(f"  V3 二元映射: {len(cn_to_smiles)} 种")

filled = 0
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            name = str(df.loc[idx, col_n]).strip()
            if name in cn_to_smiles:
                df.loc[idx, col_s] = cn_to_smiles[name]
                filled += 1
print(f"  从 V3 复用填充: {filled} 个")

# PubChem 查询
CN_TO_EN = {v: k for k, v in EN_TO_CN.items()}
need = set()
for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            cn = str(df.loc[idx, col_n]).strip()
            en = CN_TO_EN.get(cn, cn)
            need.add(en)
need -= set(cn_to_smiles.keys())
print(f"  需 PubChem 查询: {len(need)} 个")

sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-merge/1.0"})
pubchem_map = {}
for i, name in enumerate(sorted(need), 1):
    if i % 20 == 0: print(f"    PubChem: {i}/{len(need)}")
    try:
        r = sess.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{requests.utils.quote(name)}/property/IsomericSMILES/JSON", timeout=20)
        time.sleep(0.35)
        if r.status_code == 200:
            data = r.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props and props[0].get("IsomericSMILES"):
                pubchem_map[name] = props[0]["IsomericSMILES"]
    except: pass
print(f"  PubChem 获取: {len(pubchem_map)}/{len(need)}")

for col_n, col_s in [('名称1','smiles1'),('名称2','smiles2'),('名称3','smiles3')]:
    for idx in df.index:
        if df.loc[idx, col_s].strip() == '':
            cn = str(df.loc[idx, col_n]).strip()
            en = CN_TO_EN.get(cn, cn)
            if en in pubchem_map:
                df.loc[idx, col_s] = pubchem_map[en]

for col_s in ['smiles1','smiles2','smiles3']:
    n = (df[col_s].str.strip() != '').sum()
    print(f"  {col_s}: {n}/{len(df)} ({n/len(df)*100:.1f}%)")

# ====== 4. 导出 Excel ======
cols_out = [
    '名称1','分子式1','smiles1',
    '名称2','分子式2','smiles2',
    '名称3','分子式3','smiles3',
    '一致性检验方法一','一致性检验方法二',
    '压强','温度','X1','X2','Y1','Y2','DOI'
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

# B. 通过子集
df_pass = df_out[(df_out['一致性检验方法一']==1)|(df_out['一致性检验方法二']==1)]
with pd.ExcelWriter(OUT_DIR / "B_三元通过一致性检验.xlsx", engine="openpyxl") as w:
    df_pass.to_excel(w, sheet_name="通过检验数据", index=False)

# C. 四元数据（空表说明）
with pd.ExcelWriter(OUT_DIR / "C_四元VLE数据.xlsx", engine="openpyxl") as w:
    pd.DataFrame(columns=[
        '名称1','分子式1','smiles1','名称2','分子式2','smiles2',
        '名称3','分子式3','smiles3','名称4','分子式4','smiles4',
        '一致性检验方法一','一致性检验方法二','压强','温度',
        'X1','X2','X3','Y1','Y2','Y3','DOI'
    ]).to_excel(w, sheet_name="四元VLE数据", index=False)
    note = pd.DataFrame({
        '说明': [
            'NIST ThermoML 数据库仅收录 binary 和 ternary 两类 VLE 数据',
            '在已处理的 887 篇文献（批次1: 387 + 批次2: 500）中未发现任何四元（4组分）VLE 数据',
            '四元 VLE 实验数据在文献中极为稀少，一般需从 DECHEMA 或其他专用数据库定向检索',
        ]
    })
    note.to_excel(w, sheet_name="说明", index=False)

print(f"\n===== 导出完成 =====")
print(f"A_三元完整数据汇总.xlsx: {len(df_out)} 行, {ng} 体系, {df_out['DOI'].nunique()} DOI")
print(f"B_三元通过一致性检验.xlsx: {len(df_pass)} 行")
print(f"C_四元VLE数据.xlsx: 空表（含说明）")
print(f"Fredenslund: 通过={nG_pass}, 不通过={nG_fail}, 无法判定={nG_unk}")
print(f"Herington:   通过={nH_pass}, 不通过={nH_fail}, 无法判定={nH_unk}")

# Top 10
print(f"\nTop 10 体系:")
for _, r in stats_df.head(10).iterrows():
    print(f"  {r['体系']}: {r['数据点数']}点, G={r['Fredenslund(G)']}, H={r['Herington(H)']}")
