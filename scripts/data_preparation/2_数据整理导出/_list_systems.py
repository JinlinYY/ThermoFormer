# -*- coding: utf-8 -*-
import pandas as pd
df = pd.read_csv('vle_binary_expand.csv', encoding='utf-8-sig')
systems = df.groupby(['名称1','名称2']).agg(
    数据点数=('X1','size'),
    文献数=('DOI','nunique'),
    压强最小=('压强','min'),
    压强最大=('压强','max'),
    温度最小=('温度','min'),
    温度最大=('温度','max'),
).reset_index()
print(f'总体系数: {len(systems)}')
print(f'总数据点: {len(df)}')
print(f'总文献: {df["DOI"].nunique()}')
print()
print('体系列表 (按数据点数排序, Top 30):')
for _, r in systems.sort_values('数据点数', ascending=False).head(30).iterrows():
    P_range = f"{r['压强最小']:.1f}-{r['压强最大']:.1f}"
    T_range = f"{r['温度最小']:.2f}-{r['温度最大']:.2f}"
    print(f"  {r['名称1']} + {r['名称2']}: {r['数据点数']}点, {r['文献数']}篇, P={P_range}mmHg, T={T_range}°C")
