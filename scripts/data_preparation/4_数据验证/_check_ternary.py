# -*- coding: utf-8 -*-
import pandas as pd
df = pd.read_excel('VLE_三元体系数据/A_三元完整数据汇总.xlsx', engine='openpyxl')
print('SMILES 样例:')
for col in ['smiles1','smiles2','smiles3']:
    vals = df[col].dropna().unique()[:3]
    print(f'  {col}: {vals}')
    empty = ((df[col].isna()) | (df[col].astype(str).str.strip()=='')).sum()
    print(f'    空值: {empty}/{len(df)}')
print()
print('一致性检验分布:')
g_col = df.columns[9]  # 一致性检验方法一
h_col = df.columns[10]  # 一致性检验方法二
print(f'  G列名: {g_col}, H列名: {h_col}')
print(f'  G: {df[g_col].value_counts().to_dict()}')
print(f'  H: {df[h_col].value_counts().to_dict()}')
print()
print('Top 5 体系:')
for (n1,n2,n3),cnt in df.groupby(['名称1','名称2','名称3']).size().sort_values(ascending=False).head(5).items():
    print(f'  {n1}+{n2}+{n3}: {cnt}点')
print()
print('前3行样例:')
print(df[['名称1','smiles1','名称2','smiles2','名称3','smiles3','压强','温度','X1','X2','Y1','Y2','DOI']].head(3).to_string())
