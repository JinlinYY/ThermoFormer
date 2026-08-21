# -*- coding: utf-8 -*-
"""
数据集描述 + 分布特征统计分析（生成文字 + 可视化HTML）.
数据源: VLE_按体系分类整理_V3_扩展Antoine / A_完整数据汇总.xlsx
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

OUT_DIR = Path('VLE_按体系分类整理_V3_扩展Antoine')
df = pd.read_excel(OUT_DIR / 'A_完整数据汇总.xlsx', engine='openpyxl')

# ====== 1. 基础统计 ======
n_rows = len(df)
n_doi = df['DOI'].nunique()
sys_grp = df.groupby(['名称1', '名称2'])
n_sys = sys_grp.ngroups

compounds = sorted(set(df['名称1']) | set(df['名称2']))
n_comp = len(compounds)

# 每篇 DOI 数据点
doi_pts = df.groupby('DOI').size()
# 每个体系数据点
sys_pts = sys_grp.size()

# 一致性检验体系维度
sG = sys_grp['一致性检验方法一'].first()
sH = sys_grp['一致性检验方法二'].first()

# 压强单位换算 kPa
P_kPa = df['压强'] * 0.1333223684

# T 统计 (°C -> K)
T_C = df['温度']
T_K = T_C + 273.15

# ====== 2. 化合物分类 ======
# 粗略类型标签
def compound_type(name: str) -> str:
    n = name.lower()
    if any(k in name for k in ['氟','全氟','fluo','R1','R2','R3','R134','R125','R227','R218','R23','R32','三氟','五氟','六氟','八氟','七氟','四氟','二氟','HFC','R1234']):
        return '含氟/制冷剂'
    if any(k in name for k in ['醇','ol']):
        return '醇类'
    if any(k in name for k in ['酸','ate']) and ('酯' not in name) and ('盐酸' not in name) and ('硫酸' not in name) and ('硝酸' not in name):
        return '羧酸类'
    if '酯' in name or 'acet' in n or 'ester' in n:
        return '酯类'
    if '酮' in name or 'one' in n:
        return '酮类'
    if '醚' in name or 'ether' in n or 'furan' in n or '烷'==name[-1] and 'diox' in n or '氧杂' in name:
        return '醚类'
    if any(k in name for k in ['苯','甲苯','二甲苯','三甲苯','乙苯','异丙苯','naphth','萘','蒽','菲','phen']):
        return '芳香烃类'
    if any(k in name for k in ['噻吩','硫醇','硫杂','二硫','二硫化碳','亚砜','砜','sulf']):
        return '含硫化合物'
    if any(k in name for k in ['胺','吡啶','吡咯','吗啉','腈','imine','amide','脲','N-']):
        return '含氮化合物'
    if any(k in name for k in ['氯','溴','碘']):
        return '卤代烃(非氟)'
    if any(k in name for k in ['烷','烯','炔','cyclohex','环戊','环丙','dodec','undec','癸','壬','辛','庚','己','戊','丁','丙','乙','甲']) and not any(k in name for k in ['醇','酸','酯','酮','醚']):
        return '脂肪烃类'
    if any(k in name for k in ['水','氮','氧','氩','氙','氦','氢','二氧化碳','一氧化','二氧化硫','硫化氢','一氧化碳']):
        return '气体/无机物'
    if any(k in name for k in ['咪唑','膦','离子']):
        return '离子液体'
    if any(k in name for k in ['甘油','乙二醇','二醇']):
        return '多元醇'
    return '其他'

df['组分1类型'] = df['名称1'].apply(compound_type)
df['组分2类型'] = df['名称2'].apply(compound_type)

# 二元体系类型 (按 "类型1 + 类型2")
def sys_type(r):
    t1, t2 = r['组分1类型'], r['组分2类型']
    a, b = sorted([t1, t2])
    return f'{a} + {b}'

sys_type_row = df.apply(sys_type, axis=1)
type_rows = sys_type_row.value_counts()

# 按体系维度
sys_type_unique = []
for (n1,n2), g in sys_grp:
    t1 = compound_type(n1); t2 = compound_type(n2)
    a,b = sorted([t1,t2])
    sys_type_unique.append(f'{a}+{b}')
type_sys = pd.Series(sys_type_unique).value_counts()

# ====== 3. 分位数表 ======
def pct(series):
    return pd.Series({
        'min': series.min(),
        'p01': series.quantile(0.01),
        'p05': series.quantile(0.05),
        'p25': series.quantile(0.25),
        'median': series.median(),
        'p75': series.quantile(0.75),
        'p95': series.quantile(0.95),
        'p99': series.quantile(0.99),
        'max': series.max(),
        'mean': series.mean(),
        'std': series.std(),
    })
T_stats = pct(T_C)
P_stats = pct(df['压强'])
Pk_stats = pct(P_kPa)
X1_stats = pct(df['X1'])
Y1_stats = pct(df['Y1'])
stats_df = pd.DataFrame({'温度(°C)': T_stats.round(2),
                         '压强(mmHg)': P_stats.round(3),
                         '压强(kPa)': Pk_stats.round(2),
                         'X1(液相摩尔分数)': X1_stats.round(4),
                         'Y1(气相摩尔分数)': Y1_stats.round(4)})

# ====== 4. 数据密度分段 ======
# 温度段分段 (°C)
T_bins = [-200, -80, 0, 30, 60, 100, 150, 200, 300, 500, 1500]
T_labels = ['<-80', '-80~0', '0~30', '30~60', '60~100', '100~150', '150~200', '200~300', '300~500', '>500']
T_seg = pd.cut(T_C, bins=T_bins, labels=T_labels, include_lowest=True).value_counts().sort_index()

# 压强段 (kPa, 等价于 mmHg → kPa)
P_bins = [0, 10, 100, 500, 1000, 3000, 10000, 60000]
P_labels = ['<10', '10~100', '100~500', '500~1000', '1~3 MPa', '3~10 MPa', '>10 MPa']
P_seg = pd.cut(P_kPa, bins=P_bins, labels=P_labels, include_lowest=True).value_counts().sort_index()

# ====== 5. Top 20 体系 (按行数) ======
top_sys = sys_pts.sort_values(ascending=False).head(20)

# ====== 6. 保存 JSON 报告 ======
report = {
    "basic": {
        "总行数": int(n_rows),
        "总DOI数": int(n_doi),
        "总体系数": int(n_sys),
        "化合物种类": int(n_comp),
        "平均每DOI数据点": float(round(doi_pts.mean(),1)),
        "平均每体系数据点": float(round(sys_pts.mean(),1)),
        "每DOI数据点中位数": int(doi_pts.median()),
        "每体系数据点中位数": int(sys_pts.median()),
    },
    "consistency_test": {
        "Fredenslund_通过_体系": int((sG==1).sum()),
        "Fredenslund_不通过_体系": int((sG==-1).sum()),
        "Fredenslund_无法判定_体系": int((sG==0).sum()),
        "Herington_通过_体系": int((sH==1).sum()),
        "Herington_不通过_体系": int((sH==-1).sum()),
        "Herington_无法判定_体系": int((sH==0).sum()),
        "Fredenslund_通过_行数": int((df['一致性检验方法一']==1).sum()),
        "Fredenslund_不通过_行数": int((df['一致性检验方法一']==-1).sum()),
        "Fredenslund_无法判定_行数": int((df['一致性检验方法一']==0).sum()),
        "Herington_通过_行数": int((df['一致性检验方法二']==1).sum()),
        "Herington_不通过_行数": int((df['一致性检验方法二']==-1).sum()),
        "Herington_无法判定_行数": int((df['一致性检验方法二']==0).sum()),
    },
    "system_type_distribution_system_dim": type_sys.to_dict(),
    "system_type_distribution_row_dim": type_rows.to_dict(),
    "temperature_seg_C": {k: int(v) for k,v in T_seg.items()},
    "pressure_seg_kPa": {k: int(v) for k,v in P_seg.items()},
    "quantiles": json.loads(stats_df.to_json(force_ascii=False)),
    "top20_systems": {f'{a} + {b}': int(v) for (a,b), v in top_sys.items()},
    "compound_frequency": pd.concat([df['名称1'],df['名称2']]).value_counts().head(30).to_dict(),
}
with open(OUT_DIR / 'dataset_profile.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print('统计结果写入 dataset_profile.json')
