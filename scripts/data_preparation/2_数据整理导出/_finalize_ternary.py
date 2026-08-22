# -*- coding: utf-8 -*-
"""
三元 VLE 数据完整整理:
1. 加载 vle_ternary_expand.csv
2. 中文名映射
3. 一致性检验 (Fredenslund 三元点检验 + Herington 面积检验)
4. SMILES 补全 (PubChem CID 查询)
5. 严格格式导出 Excel
"""
from __future__ import annotations
import json, time, re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

WORK = Path(__file__).resolve().parent
EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
ANTOINE_RAW = json.load(open(WORK / "_antoine_cn_full.json", "r", encoding="utf-8"))
ANTOINE_CN = ANTOINE_RAW["log10(P_mmHg)_A_minus_B_over_TdegC_plus_C"]

df = pd.read_csv(WORK / "vle_ternary_expand.csv", encoding="utf-8-sig")
print(f"读取: {len(df)} 行, {df['DOI'].nunique()} DOI")

# ====== 1. 中文名映射 ======
def to_cn(name):
    if pd.isna(name): return name
    s = str(name).strip()
    return EN_TO_CN.get(s, s)

for col in ['名称1','名称2','名称3']:
    df[col] = df[col].apply(to_cn)
print(f"中文名映射完成")

# ====== 2. 清洗 ======
df = df.dropna(subset=['压强','温度','X1','X2','Y1','Y2']).copy()
df['X3'] = 1 - df['X1'] - df['X2']
df['Y3'] = 1 - df['Y1'] - df['Y2']
# 过滤不合理
df = df[(df['X1']>=0)&(df['X1']<=1)&(df['X2']>=0)&(df['X2']<=1)&(df['X3']>=-0.001)&(df['X3']<=1)]
df = df[(df['Y1']>=0)&(df['Y1']<=1)&(df['Y2']>=0)&(df['Y2']<=1)&(df['Y3']>=-0.001)&(df['Y3']<=1)]
df = df.drop_duplicates(subset=['名称1','名称2','名称3','压强','温度','X1','X2','Y1','Y2','DOI'])
df = df.reset_index(drop=True)
print(f"清洗后: {len(df)} 行, {df['DOI'].nunique()} DOI, {df.groupby(['名称1','名称2','名称3']).ngroups} 体系")

# ====== 3. Antoine 饱和蒸气压 ======
def antoine_p_sat(name, T_C):
    if name not in ANTOINE_CN:
        return None
    A, B, C = ANTOINE_CN[name]
    T_C = np.asarray(T_C, dtype=float)
    denom = T_C + C
    denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
    p = 10.0 ** (A - B / denom)
    return np.where(np.isfinite(p) & (p > 1e-6) & (p < 1e7), p, np.nan)

# ====== 4. Fredenslund 三元点检验 ======
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
    # 2D 二次多项式拟合
    A_mat=np.column_stack([np.ones_like(x1m),x1m,x2m,x1m**2,x2m**2,x1m*x2m])
    try:
        a,*_=np.linalg.lstsq(A_mat,gE_RT,rcond=None)
    except: return 0
    gE_calc=A_mat@a
    dg_dx1=a[1]+2*a[3]*x1m+a[5]*x2m
    dg_dx2=a[2]+2*a[4]*x2m+a[5]*x1m
    ln_g1_calc=gE_calc+(1-x1m)*dg_dx1-x2m*dg_dx2
    ln_g2_calc=gE_calc-x1m*dg_dx1+(1-x2m)*dg_dx2
    ln_g3_calc=gE_calc-x1m*dg_dx1-x2m*dg_dx2
    g1_calc=np.exp(np.clip(ln_g1_calc,-50,50))
    g2_calc=np.exp(np.clip(ln_g2_calc,-50,50))
    y1_calc=(g1_calc*x1m*P1)/Pm
    y2_calc=(g2_calc*x2m*P2)/Pm
    y1_calc=np.clip(y1_calc,0,1); y2_calc=np.clip(y2_calc,0,1)
    d1=np.abs(y1m-y1_calc); d2=np.abs(y2m-y2_calc)
    delta=np.maximum(d1,d2)
    pass_rate=np.mean(delta<0.01)
    if pass_rate>0.9: return 1
    if pass_rate>0.8 and delta.mean()<0.015: return 1
    return -1

# ====== 5. Herington 面积检验（三元简化版） ======
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
    ln_r12=np.log(gamma1/gamma2); ln_r13=np.log(gamma1/gamma3); ln_r23=np.log(gamma2/gamma3)
    if not np.all(np.isfinite(ln_r12)) or not np.all(np.isfinite(ln_r13)) or not np.all(np.isfinite(ln_r23)): return 0
    try:
        from scipy.integrate import trapezoid
        # 方向1: 沿 x1 积分 ln(g1/g2)
        idx1=np.argsort(x1m)
        a1n=trapezoid(ln_r12[idx1],x1m[idx1]); a1t=trapezoid(np.abs(ln_r12[idx1]),x1m[idx1])
        if a1t<1e-8: return 0
        D1=100.0*abs(a1n)/a1t
        # 方向2: 沿 x2 积分 ln(g1/g3)
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

# ====== 6. 按体系做一致性检验 ======
print("\n按体系计算一致性检验...")
groups = df.groupby(['名称1','名称2','名称3'])
ng = groups.ngroups
new_G = np.zeros(len(df), dtype=int)
new_H = np.zeros(len(df), dtype=int)
pass_G = pass_H = valid_sys = 0
no_antoine = []

for i, ((n1,n2,n3), g) in enumerate(groups, 1):
    if i % 20 == 0 or i == ng:
        print(f"  进度 {i}/{ng}")
    idx = g.index.to_numpy()
    gG = fredenslund_ternary(g['X1'].values, g['X2'].values,
                             g['Y1'].values, g['Y2'].values,
                             g['温度'].values, g['压强'].values, n1, n2, n3)
    gH = herington_ternary(g['X1'].values, g['X2'].values,
                            g['Y1'].values, g['Y2'].values,
                            g['温度'].values, g['压强'].values, n1, n2, n3)
    new_G[idx] = gG; new_H[idx] = gH
    if gG != 0: valid_sys += 1
    if gG == 1: pass_G += 1
    if gH == 1: pass_H += 1
    if gG == 0 and gH == 0:
        no_antoine.append((n1, n2, n3, len(g)))

df['一致性检验方法一'] = new_G
df['一致性检验方法二'] = new_H
print(f"\n一致性检验完成:")
print(f"  Fredenslund: 通过={pass_G}, 不通过={valid_sys-pass_G}, 无法判定={ng-valid_sys}")
print(f"  Herington:   通过={pass_H}, 不通过={valid_sys-pass_H}, 无法判定={ng-valid_sys}")
if no_antoine:
    print(f"  无 Antoine 参数体系 ({len(no_antoine)}): {no_antoine[:5]}")

# ====== 7. SMILES 补全 ======
print("\n补全 SMILES...")
# 尝试用 CAS 号查 PubChem
CAS_TO_SMILES = {}
need_cas = set()
for col in ['CAS1','CAS2','CAS3']:
    for cas in df[col].dropna().unique():
        if cas and cas not in CAS_TO_SMILES:
            need_cas.add(cas)
print(f"需查 CAS: {len(need_cas)} 个")

sess = requests.Session()
sess.headers.update({"User-Agent": "smiles-fill/1.0"})
for i, cas in enumerate(sorted(need_cas), 1):
    if i % 50 == 0:
        print(f"  SMILES 查询: {i}/{len(need_cas)}")
    try:
        r = sess.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/property/IsomericSMILES/JSON",
                     timeout=15)
        time.sleep(0.3)
        if r.status_code == 200:
            data = r.json()
            smi = data.get("PropertyTable",{}).get("Properties",[{}])[0].get("IsomericSMILES","")
            if smi:
                CAS_TO_SMILES[cas] = smi
    except:
        pass
print(f"  SMILES 获取: {len(CAS_TO_SMILES)}/{len(need_cas)}")

for col, cas_col, smi_col in [('名称1','CAS1','smiles1'),('名称2','CAS2','smiles2'),('名称3','CAS3','smiles3')]:
    df[smi_col] = df[cas_col].map(CAS_TO_SMILES).fillna(df[smi_col])

# ====== 8. 严格格式导出 ======
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

# ====== 9. 导出 Excel ======
OUT_DIR = WORK / "VLE_三元体系数据"
OUT_DIR.mkdir(exist_ok=True)

# A. 完整数据
with pd.ExcelWriter(OUT_DIR / "A_三元完整数据汇总.xlsx", engine="openpyxl") as w:
    df_out.to_excel(w, sheet_name="三元VLE数据", index=False)
    
    # 体系统计
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
    
    # 概览
    overview = pd.DataFrame([
        {'项目':'总数据点','数值':len(df_out)},
        {'项目':'总DOI数','数值':df_out['DOI'].nunique()},
        {'项目':'总体系数','数值':ng},
        {'项目':'化合物种类','数值':len(set(df_out['名称1'])|set(df_out['名称2'])|set(df_out['名称3']))},
        {'项目':'Fredenslund通过','数值':pass_G},
        {'项目':'Fredenslund不通过','数值':valid_sys-pass_G},
        {'项目':'Fredenslund无法判定','数值':ng-valid_sys},
        {'项目':'Herington通过','数值':pass_H},
        {'项目':'Herington不通过','数值':valid_sys-pass_H},
        {'项目':'Herington无法判定','数值':ng-valid_sys},
    ])
    overview.to_excel(w, sheet_name="数据概览", index=False)

# B. 通过一致性检验的子集
df_pass = df_out[(df_out['一致性检验方法一']==1)|(df_out['一致性检验方法二']==1)]
with pd.ExcelWriter(OUT_DIR / "B_三元通过一致性检验.xlsx", engine="openpyxl") as w:
    df_pass.to_excel(w, sheet_name="通过检验数据", index=False)
print(f"\n导出完成:")
print(f"  A_三元完整数据汇总.xlsx: {len(df_out)} 行, {ng} 体系, {df_out['DOI'].nunique()} DOI")
print(f"  B_三元通过一致性检验.xlsx: {len(df_pass)} 行")
print(f"  Fredenslund: 通过={pass_G} ({pass_G/ng*100:.1f}%), 不通过={valid_sys-pass_G} ({(valid_sys-pass_G)/ng*100:.1f}%), 无法判定={ng-valid_sys} ({(ng-valid_sys)/ng*100:.1f}%)")
print(f"  Herington:   通过={pass_H} ({pass_H/ng*100:.1f}%), 不通过={valid_sys-pass_H} ({(valid_sys-pass_H)/ng*100:.1f}%), 无法判定={ng-valid_sys} ({(ng-valid_sys)/ng*100:.1f}%)")

# 列出 Top 15 体系
print(f"\nTop 15 体系 (按数据点数):")
for _, r in stats_df.head(15).iterrows():
    print(f"  {r['体系']}: {r['数据点数']} 点, G={r['Fredenslund(G)']}, H={r['Herington(H)']}")
