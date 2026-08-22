import pandas as pd
fld = r'VLE_按体系分类整理_V3_扩展Antoine'
df_all = pd.read_excel(fld + r'\A_完整数据汇总.xlsx', engine='openpyxl')

print('===== 1. 水体系（名称含 水） =====')
water_mask = df_all['名称1'].str.contains('水', na=False) | df_all['名称2'].str.contains('水', na=False)
print('水体系数据点数:', water_mask.sum())
df_water = df_all[water_mask]
print('水体系组合数:', df_water[['名称1','名称2']].drop_duplicates().shape[0])
print('水体系组合示例（前20个）:')
print(df_water[['名称1','名称2']].drop_duplicates().head(20).to_string())
print()

print('===== 2. 醇体系（名称含 醇） =====')
alcohol_mask = df_all['名称1'].str.contains('醇', na=False) | df_all['名称2'].str.contains('醇', na=False)
print('醇体系数据点数:', alcohol_mask.sum())
df_alc = df_all[alcohol_mask]
print('醇体系组合数:', df_alc[['名称1','名称2']].drop_duplicates().shape[0])
print('醇体系组合示例（前20个）:')
print(df_alc[['名称1','名称2']].drop_duplicates().head(20).to_string())
print()

print('===== 3. 水或醇体系总占比 =====')
print('水+醇总点数:', (water_mask | alcohol_mask).sum())
print('总点数:', len(df_all))
print('占比: {:.1f}%'.format((water_mask | alcohol_mask).sum() / len(df_all) * 100))
