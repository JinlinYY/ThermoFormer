# -*- coding: utf-8 -*-
"""
用扩展 Antoine 库(404 种化合物, 98.5% 覆盖)重新计算
Fredenslund 方法一 + Herington 方法二 一致性检验, 然后按分类导出 Excel。
格式: 中文名 + 一致性检验(1/-1/0) + A-L 列 + DOI
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# ========== 1. 加载 ==========
EN_TO_CN = json.load(open('_en_to_cn_full.json', 'r', encoding='utf-8'))
antoine_raw = json.load(open('_antoine_cn_full.json', 'r', encoding='utf-8'))
ANTOINE_CN = antoine_raw['log10(P_mmHg)_A_minus_B_over_TdegC_plus_C']

df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')
print(f'读取数据: {len(df)} 行')

# 中文名化
def to_cn(n):
    if pd.isna(n):
        return n
    s = str(n).strip()
    return EN_TO_CN.get(s, s)

df['名称1'] = df['名称1'].apply(to_cn)
df['名称2'] = df['名称2'].apply(to_cn)

# ========== 2. 清洗 ==========
df = df.dropna(subset=['压强','温度','X1','Y1']).copy()
df = df[(df['X1']>=0)&(df['X1']<=1)&(df['Y1']>=0)&(df['Y1']<=1)].copy()
df['smiles1'] = df['smiles1'].fillna('')
df['smiles2'] = df['smiles2'].fillna('')
df['压强'] = df['压强'].round(3)
df['温度'] = df['温度'].round(3)
df['X1'] = df['X1'].round(6)
df['Y1'] = df['Y1'].round(6)
df = df.drop_duplicates(subset=['名称1','名称2','压强','温度','X1','Y1','DOI'])
df = df.reset_index(drop=True)
print(f'清洗后: {len(df)} 行, {df["DOI"].nunique()} DOI')

# ========== 3. 一致性检验函数 ==========
def antoine_p_sat_cn(name, T_C):
    """饱和蒸气压(mmHg). name 用中文名查. 向量式 T_C."""
    if name not in ANTOINE_CN:
        return None
    A, B, C = ANTOINE_CN[name]
    T_C = np.asarray(T_C, dtype=float)
    denom = T_C + C
    denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
    p = 10.0 ** (A - B / denom)
    # 防异常: 如果 T 超出 Antoine 范围, 给出非正的危险值
    return np.where(np.isfinite(p) & (p > 1e-6) & (p < 1e7), p, np.nan)

def legendre_poly(t, order):
    P = [np.ones_like(t)]
    if order >= 1:
        P.append(t)
    for n in range(2, order + 1):
        Pn = ((2 * n - 1) * t * P[-1] - (n - 1) * P[-2]) / n
        P.append(Pn)
    return P

def legendre_deriv(t, order):
    # 递推到 order+1 阶, 返回 0..order 的导数
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
            # dP_n/dt = n * (t P_{n-1} - P_{n-2} 加权) = n P_{n-1} + t dP_{n-1} - dP_{n-2}? 直接用递推公式:
            # (2n+1) P_n = dP_{n+1}/dt - dP_{n-1}/dt
            # => dP_n/dt = (2n-1) P_{n-1} + dP_{n-2}/dt
            val = (2 * n - 1) * P[n-1] + (dP_list[n-2] if n >= 2 else np.zeros_like(t))
            dP_list.append(val)
    return dP_list

def fredenslund_test(x1, y1, T, P, name1, name2):
    n = len(x1)
    if n < 5:
        return 0
    T = np.asarray(T, dtype=float)
    P = np.asarray(P, dtype=float)
    x1 = np.asarray(x1, dtype=float)
    y1 = np.asarray(y1, dtype=float)
    P1_sat = antoine_p_sat_cn(name1, T)
    P2_sat = antoine_p_sat_cn(name2, T)
    if P1_sat is None or P2_sat is None:
        return 0
    # 过滤饱和蒸气压失败的点
    valid = np.isfinite(P1_sat) & np.isfinite(P2_sat) & (P1_sat > 0) & (P2_sat > 0)
    if valid.sum() < 5:
        return 0
    T = T[valid]; P = P[valid]; x1 = x1[valid]; y1 = y1[valid]
    P1_sat = P1_sat[valid]; P2_sat = P2_sat[valid]
    mask = (x1 > 1e-6) & (x1 < 1-1e-6) & (y1 > 1e-6) & (y1 < 1-1e-6)
    if mask.sum() < 5:
        return 0
    x1m = x1[mask]; y1m = y1[mask]; Tm = T[mask]; Pm = P[mask]
    P1m = P1_sat[mask]; P2m = P2_sat[mask]
    gamma1 = (Pm * y1m) / (x1m * P1m)
    gamma2 = (Pm * (1-y1m)) / ((1-x1m) * P2m)
    if np.any(~np.isfinite(gamma1)) or np.any(~np.isfinite(gamma2)) or \
       np.any(gamma1 <= 0) or np.any(gamma2 <= 0):
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
    g1_calc = np.exp(np.clip(ln_g1_calc, -50, 50))
    denom = Pm.copy()
    denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
    y1_calc = (g1_calc * x1m * P1m) / denom
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
    P1_sat = antoine_p_sat_cn(name1, T)
    P2_sat = antoine_p_sat_cn(name2, T)
    if P1_sat is None or P2_sat is None:
        return 0
    valid = np.isfinite(P1_sat) & np.isfinite(P2_sat) & (P1_sat > 0) & (P2_sat > 0)
    if valid.sum() < 5:
        return 0
    T = T[valid]; P = P[valid]; x1 = x1[valid]; y1 = y1[valid]
    P1_sat = P1_sat[valid]; P2_sat = P2_sat[valid]
    mask = (x1 > 1e-6) & (x1 < 1-1e-6) & (y1 > 1e-6) & (y1 < 1-1e-6)
    if mask.sum() < 5:
        return 0
    x1m = x1[mask]; y1m = y1[mask]; Tm = T[mask]; Pm = P[mask]
    P1m = P1_sat[mask]; P2m = P2_sat[mask]
    gamma1 = (Pm * y1m) / (x1m * P1m)
    gamma2 = (Pm * (1-y1m)) / ((1-x1m) * P2m)
    if np.any(~np.isfinite(gamma1)) or np.any(~np.isfinite(gamma2)) or \
       np.any(gamma1 <= 0) or np.any(gamma2 <= 0):
        return 0
    ln_ratio = np.log(gamma1 / gamma2)
    if not np.all(np.isfinite(ln_ratio)):
        return 0
    idx = np.argsort(x1m)
    xs = x1m[idx]; ln_s = ln_ratio[idx]
    try:
        from scipy.integrate import trapezoid
        area_net = float(trapezoid(ln_s, xs))
        area_total = float(trapezoid(np.abs(ln_s), xs))
    except Exception:
        return 0
    if not np.isfinite(area_net) or not np.isfinite(area_total):
        return 0
    if area_total < 1e-8:
        return 0
    D = 100.0 * abs(area_net) / area_total
    T_mean = Tm.mean()
    if T_mean <= 0 or len(Tm) < 2:
        return 0
    J = 150.0 * (Tm.max() - Tm.min()) / T_mean
    if abs(D - J) < 10:
        return 1
    return -1

# ========== 4. 按体系做一致性检验 ==========
print('\n按体系重新计算一致性检验 (扩展 Antoine 库)...')
groups = df.groupby(['名称1', '名称2'])
new_G = np.zeros(len(df), dtype=int)
new_H = np.zeros(len(df), dtype=int)

ng = groups.ngroups
total_sys = 0
valid_sys = 0
pass_G = 0; pass_H = 0
sys_names_nohit = []
for i, ((n1, n2), g) in enumerate(groups, 1):
    if i % 50 == 0 or i == ng:
        print(f'  进度 {i}/{ng}')
    total_sys += 1
    idx = g.index.to_numpy()
    gG = fredenslund_test(g['X1'].values, g['Y1'].values,
                          g['温度'].values, g['压强'].values, n1, n2)
    gH = herington_test(g['X1'].values, g['Y1'].values,
                        g['温度'].values, g['压强'].values, n1, n2)
    new_G[idx] = gG
    new_H[idx] = gH
    if gG != 0:
        valid_sys += 1
    if gG == 1: pass_G += 1
    if gH == 1: pass_H += 1
    if gG == 0 and gH == 0:
        sys_names_nohit.append((n1, n2, len(g)))

df['一致性检验方法一'] = new_G
df['一致性检验方法二'] = new_H

# 列顺序 A-L + DOI
cols_order = [
    '名称1','分子式1','smiles1',
    '名称2','分子式2','smiles2',
    '一致性检验方法一','一致性检验方法二',
    '压强','温度','X1','Y1','DOI'
]
df = df[cols_order].copy()

print(f'\n检验完成. 总体系: {total_sys}')
for col, lab in [('一致性检验方法一', 'Fredenslund'), ('一致性检验方法二', 'Herington')]:
    print(f'  {lab} (体系维度):')
    tmp = df.groupby(['名称1','名称2'])[col].first()
    vc = tmp.value_counts()
    map_ = {1: '通过', -1: '不通过', 0: '无法判定'}
    for k in [1, -1, 0]:
        v = vc.get(k, 0)
        print(f'    {map_[k]}: {v} 体系 ({v/total_sys*100:.1f}%)')
for col, lab in [('一致性检验方法一', 'Fredenslund'), ('一致性检验方法二', 'Herington')]:
    print(f'  {lab} (行维度):')
    vc = df[col].value_counts()
    map_ = {1: '通过', -1: '不通过', 0: '无法判定'}
    for k in [1, -1, 0]:
        v = vc.get(k, 0)
        print(f'    {map_[k]}: {v} 行 ({v/len(df)*100:.1f}%)')

# ========== 5. 按体系统计匹配 ==========
def sys_match(row, pairs):
    r1, r2 = row['名称1'], row['名称2']
    for (a, b) in pairs:
        if (r1 == a and r2 == b) or (r1 == b and r2 == a):
            return True
    return False

BATCH1 = [
    ('丙酮','苯'), ('丙酮','正己烷'), ('丙酮','乙酸乙酯'),
    ('乙酸乙酯','苯'), ('四氢呋喃','苯'), ('吡啶','甲苯'),
    ('N,N-二甲基甲酰胺','乙酸乙酯'), ('氯仿','丙酮'), ('二甲基亚砜','苯'),
]
BATCH2 = [
    ('噻吩','正庚烷'), ('苯','甲苯'), ('乙酸乙酯','乙酸正丙酯'),
    ('乙酸','乙酸乙酯'), ('二甲基亚砜','乙酸乙酯'), ('乙腈','正己烷'),
    ('正庚烷','甲苯'), ('噻吩','苯'),
]
C1_PAIRS = [
    ('正己烷','正庚烷'), ('正己烷','正辛烷'), ('正庚烷','正辛烷'),
    ('正己烷','环己烷'), ('正庚烷','环己烷'), ('正辛烷','环己烷'),
    ('环己烷','甲基环己烷'), ('正己烷','2,3-二甲基丁烷'),
    ('正辛烷','异辛烷'), ('甲基环己烷','乙基环己烷'),
    ('乙烷','丙烷'), ('丙烷','丁烷'),
    ('环己烷','环戊烷'), ('正己烷','正癸烷'),
    ('正己烷','苯'), ('正庚烷','苯'), ('正辛烷','苯'), ('环己烷','苯'),
    ('正己烷','甲苯'), ('正庚烷','甲苯'), ('环己烷','甲苯'), ('甲基环己烷','苯'),
    ('异辛烷','苯'), ('异辛烷','甲苯'), ('环己烷','乙苯'),
    ('正己烷','乙苯'), ('正庚烷','乙苯'),
    ('甲基环己烷','甲苯'), ('正癸烷','苯'),
    ('正己烷','邻二甲苯'), ('正庚烷','邻二甲苯'), ('环己烷','邻二甲苯'),
    ('正己烷','对二甲苯'), ('环己烷','间二甲苯'),
    ('环己烷','异丙苯'), ('正己烷','氯苯'), ('正庚烷','氯苯'),
    ('环己烷','氯苯'), ('环己烷','溴苯'),
    ('苯','甲苯'), ('苯','乙苯'), ('甲苯','乙苯'),
    ('苯','邻二甲苯'), ('甲苯','邻二甲苯'), ('苯','对二甲苯'),
    ('甲苯','对二甲苯'), ('苯','间二甲苯'), ('甲苯','间二甲苯'),
    ('苯','异丙苯'), ('乙苯','邻二甲苯'), ('乙苯','对二甲苯'),
    ('邻二甲苯','对二甲苯'), ('苯','1,2,4-三甲苯'), ('苯','1,3,5-三甲苯'),
    ('甲苯','1,2,4-三甲苯'),
    ('苯','氯苯'), ('甲苯','氯苯'), ('苯','溴苯'), ('甲苯','溴苯'),
    ('苯','硝基苯'),
    ('苯','苯乙烯'), ('甲苯','苯乙烯'),
]
C2_PAIRS = [
    ('四氢呋喃','甲醇'), ('四氢呋喃','乙醇'), ('四氢呋喃','1-丙醇'),
    ('四氢呋喃','2-丙醇'), ('四氢呋喃','1-丁醇'), ('四氢呋喃','1-己醇'),
    ('二乙醚','甲醇'), ('二乙醚','乙醇'), ('二异丙醚','乙醇'),
    ('二异丙醚','1-丙醇'), ('二丁醚','乙醇'), ('二丁醚','1-丁醇'),
    ('1,4-二噁烷','甲醇'), ('1,4-二噁烷','乙醇'), ('1,4-二噁烷','水'),
    ('苯甲醚','乙醇'), ('苯甲醚','1-丙醇'),
    ('2-甲氧基-2-甲基丙烷','乙醇'),
    ('四氢呋喃','苯'), ('四氢呋喃','甲苯'), ('二乙醚','苯'),
    ('二异丙醚','苯'), ('苯甲醚','苯'), ('苯甲醚','甲苯'),
    ('1,4-二噁烷','苯'), ('1,4-二噁烷','甲苯'),
    ('四氢吡喃','苯'),
    ('乙酸乙酯','甲醇'), ('乙酸乙酯','乙醇'), ('乙酸乙酯','1-丙醇'),
    ('乙酸乙酯','2-丙醇'), ('乙酸乙酯','1-丁醇'),
    ('乙酸甲酯','甲醇'), ('乙酸甲酯','乙醇'),
    ('乙酸正丙酯','1-丙醇'), ('乙酸正丙酯','乙醇'),
    ('乙酸正丁酯','1-丁醇'), ('乙酸正丁酯','乙醇'),
    ('甲酸乙酯','乙醇'), ('甲酸乙酯','甲醇'), ('甲酸甲酯','甲醇'),
    ('丙酸乙酯','乙醇'), ('丙酸乙酯','甲醇'),
    ('丙酸甲酯','甲醇'), ('苯甲酸乙酯','乙醇'), ('苯甲酸甲酯','甲醇'),
    ('乙酸乙酯','苯'), ('乙酸乙酯','甲苯'), ('乙酸甲酯','苯'),
    ('乙酸正丙酯','苯'), ('乙酸正丁酯','苯'),
    ('甲酸乙酯','苯'), ('苯甲酸乙酯','苯'),
    ('吡啶','甲醇'), ('吡啶','乙醇'), ('吡啶','1-丙醇'),
    ('三乙胺','甲醇'), ('三乙胺','乙醇'), ('苯胺','甲醇'), ('苯胺','乙醇'),
    ('N,N-二甲基甲酰胺','甲醇'), ('N,N-二甲基甲酰胺','乙醇'),
    ('N-甲基吡咯烷酮','甲醇'), ('N-甲基吡咯烷酮','乙醇'),
    ('吗啉','乙醇'), ('吗啉','甲醇'),
    ('环己胺','甲醇'), ('环己胺','乙醇'),
    ('吡啶','苯'), ('吡啶','甲苯'), ('苯胺','苯'), ('苯胺','甲苯'),
    ('三乙胺','苯'), ('N,N-二甲基甲酰胺','苯'), ('N-甲基吡咯烷酮','苯'),
]
C3_PAIRS = [
    ('乙酸乙酯','丙酮'), ('乙酸甲酯','丙酮'), ('乙酸正丙酯','丙酮'),
    ('乙酸正丁酯','丙酮'), ('甲酸乙酯','丙酮'),
    ('乙酸乙酯','丁酮'), ('乙酸甲酯','丁酮'),
    ('乙酸乙酯','环己酮'), ('乙酸乙酯','苯乙酮'),
    ('乙酸乙酯','乙酸甲酯'), ('乙酸乙酯','乙酸正丙酯'),
    ('乙酸乙酯','乙酸正丁酯'), ('乙酸甲酯','乙酸正丙酯'),
    ('乙酸正丙酯','乙酸正丁酯'), ('乙酸乙酯','甲酸乙酯'),
    ('乙酸甲酯','甲酸甲酯'), ('丙酸乙酯','乙酸乙酯'),
    ('苯甲酸乙酯','乙酸乙酯'), ('苯甲酸甲酯','乙酸甲酯'),
    ('乙酸乙酯','正己烷'), ('乙酸乙酯','正庚烷'), ('乙酸乙酯','环己烷'),
    ('乙酸甲酯','正己烷'), ('乙酸正丙酯','正己烷'),
    ('乙酸正丁酯','正己烷'), ('甲酸乙酯','正己烷'),
    ('丙酸乙酯','正己烷'), ('苯甲酸乙酯','正己烷'),
    ('乙酸乙酯','异辛烷'), ('乙酸乙酯','甲基环己烷'),
]
C4_PAIRS = [
    ('乙酸','甲醇'), ('乙酸','乙醇'), ('乙酸','1-丙醇'), ('乙酸','2-丙醇'),
    ('乙酸','1-丁醇'), ('乙酸','1-戊醇'), ('乙酸','1-己醇'),
    ('丙酸','甲醇'), ('丙酸','乙醇'), ('丙酸','1-丙醇'),
    ('丁酸','甲醇'), ('丁酸','乙醇'), ('丁酸','1-丁醇'),
    ('甲酸','甲醇'), ('甲酸','乙醇'),
    ('苯甲酸','甲醇'), ('苯甲酸','乙醇'),
    ('丙烯酸','甲醇'), ('丙烯酸','乙醇'),
    ('氯乙酸','甲醇'), ('氯乙酸','乙醇'),
    ('三氟乙酸','甲醇'), ('三氟乙酸','乙醇'),
    ('己酸','乙醇'),
    ('乙酸','氯乙酸'), ('氯乙酸','二氯乙酸'),
    ('乙酸','丙酸'), ('乙酸','丁酸'), ('丙酸','丁酸'),
    ('乙酸','乙酸乙酯'), ('乙酸','乙酸甲酯'), ('乙酸','乙酸正丙酯'),
    ('丙酸','丙酸乙酯'), ('丁酸','丁酸甲酯'),
    ('苯甲酸','苯甲酸甲酯'), ('苯甲酸','苯甲酸乙酯'),
    ('N,N-二甲基乙酰胺','乙酸'), ('N-甲基乙酰胺','乙酸'),
    ('N-甲基甲酰胺','甲酸'),
]
C5_PAIRS = [
    ('二氯甲烷','甲醇'), ('二氯甲烷','乙醇'), ('氯仿','甲醇'),
    ('氯仿','乙醇'), ('氯仿','2-丙醇'), ('四氯化碳','甲醇'),
    ('四氯化碳','乙醇'), ('四氯化碳','1-丙醇'),
    ('1,2-二氯乙烷','甲醇'), ('1,2-二氯乙烷','乙醇'),
    ('1,1,1-三氯乙烷','乙醇'),
    ('氯苯','甲醇'), ('氯苯','乙醇'), ('溴苯','甲醇'),
    ('氟苯','乙醇'), ('二溴甲烷','乙醇'),
    ('氯仿','丙酮'), ('二氯甲烷','丙酮'), ('四氯化碳','丙酮'),
    ('1,2-二氯乙烷','丙酮'), ('氯苯','丙酮'),
    ('氯仿','乙酸乙酯'), ('二氯甲烷','乙酸乙酯'),
    ('四氯化碳','乙酸乙酯'),
    ('氯仿','乙酸'), ('二氯甲烷','乙酸'),
    ('氯仿','正己烷'), ('二氯甲烷','正己烷'),
    ('四氯化碳','正己烷'), ('四氯化碳','正庚烷'),
    ('1,2-二氯乙烷','正己烷'), ('1,2-二溴乙烷','正己烷'),
    ('氯苯','正己烷'), ('氯苯','环己烷'), ('溴苯','正己烷'),
    ('1-氯丁烷','正己烷'), ('1-氯戊烷','正辛烷'),
    ('氯仿','苯'), ('二氯甲烷','苯'), ('四氯化碳','苯'),
    ('1,2-二氯乙烷','苯'), ('氯苯','苯'), ('溴苯','苯'),
    ('氯苯','甲苯'), ('溴苯','甲苯'), ('氟苯','苯'),
    ('氯仿','乙腈'), ('二氯甲烷','乙腈'), ('四氯化碳','乙腈'),
    ('氯苯','硝基苯'), ('二氯甲烷','二甲基亚砜'),
]
C6_PAIRS = [
    ('噻吩','正己烷'), ('噻吩','正庚烷'), ('噻吩','正辛烷'),
    ('噻吩','环己烷'), ('噻吩','甲基环己烷'),
    ('噻吩','苯'), ('噻吩','甲苯'), ('噻吩','乙苯'),
    ('噻吩','2-甲基戊烷'), ('噻吩','异辛烷'),
    ('2-甲基噻吩','正己烷'), ('2-甲基噻吩','苯'),
    ('3-甲基噻吩','正己烷'), ('3-甲基噻吩','苯'),
    ('2,5-二甲基噻吩','正己烷'),
    ('苯并噻吩','苯'), ('苯并噻吩','甲苯'),
    ('四氢噻吩','正己烷'), ('四氢噻吩','苯'),
    ('二甲基亚砜','甲醇'), ('二甲基亚砜','乙醇'),
    ('二甲基亚砜','1-丙醇'), ('二甲基亚砜','水'),
    ('二甲基亚砜','丙酮'), ('二甲基亚砜','苯'),
    ('二甲基亚砜','甲苯'), ('二甲基亚砜','乙酸乙酯'),
    ('二甲基亚砜','乙腈'), ('二甲基亚砜','二氯甲烷'),
    ('二甲基亚砜','N,N-二甲基甲酰胺'),
    ('二硫化碳','甲醇'), ('二硫化碳','乙醇'),
    ('二硫化碳','丙酮'), ('二硫化碳','苯'),
    ('二硫化碳','正己烷'), ('二硫化碳','乙酸乙酯'),
    ('二硫化碳','甲苯'), ('二硫化碳','环己烷'),
    ('环丁砜','甲醇'), ('环丁砜','乙醇'), ('环丁砜','苯'),
    ('环丁砜','甲苯'), ('环丁砜','水'),
    ('1-丁硫醇','正己烷'), ('1-丁硫醇','苯'),
    ('1-戊硫醇','正庚烷'),
]
C8_PAIRS = [
    ('水','氯化钠'), ('水','氯化钾'), ('水','氯化钙'),
    ('水','硫酸钠'), ('水','硝酸钠'), ('水','氯化镁'),
    ('水','氯化锌'), ('水','硫酸'), ('水','盐酸'),
    ('水','硝酸'), ('水','氢氧化钾'), ('水','醋酸钠'),
    ('甲醇','氯化锂'), ('甲醇','碘化钠'), ('甲醇','氯化钙'),
    ('乙醇','氯化铜'), ('乙醇','氯化锌'), ('乙醇','氯化钠'),
    ('乙酸','醋酸钠'), ('乙二醇','氯化钠'), ('乙二醇','氯化锂'),
    ('甘油','氯化钠'), ('1-丙醇','氯化钙'),
]

CATEGORIES = [
    ('00_第一批优先体系_9种', BATCH1),
    ('01_第二批体系_8种', BATCH2),
    ('1_脂肪烃_脂肪烃_芳香烃', C1_PAIRS),
    ('2_醚酯胺_醇_芳香烃', C2_PAIRS),
    ('3_酯_酮_烷烃_醇', C3_PAIRS),
    ('4_羧酸_酯_醇基组合', C4_PAIRS),
    ('5_卤代烃_极性分子_烃', C5_PAIRS),
    ('6_含硫体系', C6_PAIRS),
    ('8_电解质VLE', C8_PAIRS),
]

# ========== 6. 导出 ==========
OUT_DIR = Path('VLE_按体系分类整理_V3_扩展Antoine')
OUT_DIR.mkdir(exist_ok=True)

df.to_excel(OUT_DIR / 'A_完整数据汇总.xlsx', index=False, engine='openpyxl')
df.to_csv(OUT_DIR / 'A_完整数据汇总.csv', index=False, encoding='utf-8-sig')
print(f'\nA_完整数据汇总: {len(df)} 行, {df["DOI"].nunique()} DOI')

summary_rows = []
total_in = 0
for cat_name, pairs in CATEGORIES:
    mask = df.apply(lambda r: sys_match(r, pairs), axis=1)
    sub = df[mask].copy()
    sys_df = pd.DataFrame(columns=['体系','数据点数','文献数','Fredenslund(G)','Herington(H)'])
    if len(sub) > 0:
        stats = []
        for (n1, n2), g in sub.groupby(['名称1', '名称2']):
            stats.append({
                '体系': f'{n1} + {n2}',
                '数据点数': len(g),
                '文献数': g['DOI'].nunique(),
                'Fredenslund(G)': int(g['一致性检验方法一'].iloc[0]),
                'Herington(H)': int(g['一致性检验方法二'].iloc[0]),
            })
        sys_df = pd.DataFrame(stats).sort_values('数据点数', ascending=False)
    fname = f'{cat_name}_数据.xlsx'
    with pd.ExcelWriter(OUT_DIR / fname, engine='openpyxl') as w:
        sub.to_excel(w, sheet_name='数据明细', index=False)
        sys_df.to_excel(w, sheet_name='体系统计', index=False)
    n_sys = len(sys_df)
    n_row = len(sub)
    total_in += n_row
    n_paper = sub['DOI'].nunique()
    summary_rows.append({
        '类别': cat_name,
        '体系数': n_sys,
        '数据点数': n_row,
        '文献数': n_paper,
        'Fredenslund通过体系': int((sys_df['Fredenslund(G)']==1).sum()),
        'Herington通过体系': int((sys_df['Herington(H)']==1).sum()),
        '包含体系': '；'.join(sys_df['体系'].tolist()[:12]),
        '文件名': fname,
    })
    print(f'  {cat_name}: {n_sys} 体系, {n_row} 行, {n_paper} DOI, G通过={int((sys_df["Fredenslund(G)"]==1).sum())}, H通过={int((sys_df["Herington(H)"]==1).sum())}')

summary_df = pd.DataFrame(summary_rows)
with pd.ExcelWriter(OUT_DIR / 'Z_分类总览.xlsx', engine='openpyxl') as w:
    overview = pd.DataFrame([
        {'项目':'总行数','数值':len(df)},
        {'项目':'总DOI数','数值':df['DOI'].nunique()},
        {'项目':'总体系数','数值':df.groupby(['名称1','名称2']).ngroups},
        {'项目':'分类覆盖行数','数值':total_in},
        {'项目':'Antoine库化合物数','数值':len(ANTOINE_CN)},
        {'项目':'有Fredenslund结果(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法一'].first()!=0).sum())},
        {'项目':'Fredenslund通过(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法一'].first()==1).sum())},
        {'项目':'Fredenslund不通过(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法一'].first()==-1).sum())},
        {'项目':'Fredenslund无法判定(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法一'].first()==0).sum())},
        {'项目':'有Herington结果(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法二'].first()!=0).sum())},
        {'项目':'Herington通过(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法二'].first()==1).sum())},
        {'项目':'Herington不通过(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法二'].first()==-1).sum())},
        {'项目':'Herington无法判定(体系)','数值':int((df.groupby(['名称1','名称2'])['一致性检验方法二'].first()==0).sum())},
    ])
    overview.to_excel(w, sheet_name='数据概览', index=False)
    summary_df.to_excel(w, sheet_name='分类总览', index=False)

print(f'\n完成, 输出目录: {OUT_DIR.resolve()}')
