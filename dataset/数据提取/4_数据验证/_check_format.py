# -*- coding: utf-8 -*-
"""
检查现有 CSV 的格式,确保符合要求。
"""
import pandas as pd

df = pd.read_csv('vle_binary_expand.csv', encoding='utf-8-sig')
print('列:', list(df.columns))
print(f'行数: {len(df)}')
print(f'DOI: {df["DOI"].nunique()}')
print(f'体系: {df.groupby(["名称1","名称2"]).ngroups}')

# 检查必要列
required = ['名称1','分子式1','smiles1','名称2','分子式2','smiles2',
            '一致性检验方法一','一致性检验方法二','压强','温度','X1','Y1','DOI']
for col in required:
    if col in df.columns:
        missing = df[col].isna().sum()
        print(f'  {col}: {len(df)} 行, {missing} 空')
    else:
        print(f'  {col}: 缺失!')

# 检查单位
print(f'\n压强范围: {df["压强"].min():.2f} ~ {df["压强"].max():.2f} mmHg')
print(f'温度范围: {df["温度"].min():.2f} ~ {df["温度"].max():.2f} °C')
print(f'X1范围: {df["X1"].min():.4f} ~ {df["X1"].max():.4f}')
print(f'Y1范围: {df["Y1"].min():.4f} ~ {df["Y1"].max():.4f}')

# 一致性检验
print(f'\nFredenslund 方法一 unique: {df["一致性检验方法一"].unique()[:10]}')
print(f'Herington 方法二 unique: {df["一致性检验方法二"].unique()[:10]}')

# 保存为 Excel
out = 'vle_binary_data_summary.xlsx'
df.to_excel(out, index=False, engine='openpyxl')
print(f'\n已保存: {out}')
