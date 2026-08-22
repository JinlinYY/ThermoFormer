# -*- coding: utf-8 -*-
"""
严格按照 A-L 列格式整理数据,同时保留 DOI。
列顺序: A名称1 B分子式1 Csmiles1 D名称2 E分子式2 Fsmiles2
        G一致性检验方法一 H一致性检验方法二 I压强 J温度 KX1 LY1 M DOI
"""
import pandas as pd

# 读取整理好的数据
df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')

# 严格按照 A-L 顺序排列列,加上 DOI
cols = [
    '名称1',      # A
    '分子式1',    # B
    'smiles1',    # C
    '名称2',      # D
    '分子式2',    # E
    'smiles2',    # F
    '一致性检验方法一',  # G (Fredenslund)
    '一致性检验方法二',  # H (Herington)
    '压强',       # I
    '温度',       # J
    'X1',         # K
    'Y1',         # L
    'DOI',        # M (用户要求必须有)
]

# 确保列顺序
df = df[cols].copy()

# 清洗: 去除 X1 Y1 空值,确保 X1 Y1 在 [0,1]
df = df.dropna(subset=['压强', '温度', 'X1', 'Y1']).copy()
df = df[(df['X1'] >= 0) & (df['X1'] <= 1)].copy()
df = df[(df['Y1'] >= 0) & (df['Y1'] <= 1)].copy()

# 填充空值: smiles 空填 "", 一致性检验空填 "无法判定"
df['smiles1'] = df['smiles1'].fillna('')
df['smiles2'] = df['smiles2'].fillna('')
df['一致性检验方法一'] = df['一致性检验方法一'].fillna('无法判定')
df['一致性检验方法二'] = df['一致性检验方法二'].fillna('无法判定')

# 去重
df = df.drop_duplicates(subset=['名称1', '名称2', '压强', '温度', 'X1', 'Y1', 'DOI'])

# 单位检查
print(f'压强范围: {df["压强"].min():.2f} ~ {df["压强"].max():.2f} mmHg')
print(f'温度范围: {df["温度"].min():.2f} ~ {df["温度"].max():.2f} °C')
print(f'X1 范围: {df["X1"].min():.4f} ~ {df["X1"].max():.4f}')
print(f'Y1 范围: {df["Y1"].min():.4f} ~ {df["Y1"].max():.4f}')

# 数值保留适当小数位
df['压强'] = df['压强'].round(3)
df['温度'] = df['温度'].round(3)
df['X1'] = df['X1'].round(6)
df['Y1'] = df['Y1'].round(6)

print(f'\n最终: {len(df)} 行, {df["DOI"].nunique()} 篇 DOI')

# 按体系分组统计
sys_grp = df.groupby(['名称1', '名称2'])
print(f'体系数: {sys_grp.ngroups}')

# 一致性检验统计
print('\n一致性检验统计:')
print(f'  Fredenslund(G):')
for k, v in df['一致性检验方法一'].value_counts().items():
    print(f'    {k}: {v} 行')
print(f'  Herington(H):')
for k, v in df['一致性检验方法二'].value_counts().items():
    print(f'    {k}: {v} 行')

# 保存 Excel
out = 'VLE_二元体系数据_严格格式.xlsx'
df.to_excel(out, index=False, engine='openpyxl')
print(f'\n已保存: {out}')

# 保存 CSV
out_csv = 'VLE_二元体系数据_严格格式.csv'
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f'已保存: {out_csv}')

# 打印前 3 行示例
print('\n前 3 行数据样例:')
print(df.head(3).to_string())
