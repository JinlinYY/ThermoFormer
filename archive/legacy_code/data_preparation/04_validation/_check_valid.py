import pandas as pd

df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')
print(f'总行数: {len(df)}')

# 筛选有一致性检验结果的数据
valid = df[df['一致性检验方法一'] != '无法判定'].copy()
print(f'有检验结果: {len(valid)} 行, {valid["DOI"].nunique()} DOI, {valid.groupby(["名称1","名称2"]).ngroups} 体系')

# 按体系分组统计
stats = valid.groupby(["名称1","名称2"]).agg(
    数据点数=("X1","count"),
    文献数=("DOI","nunique"),
    Fredenslund=("一致性检验方法一","first"),
    Herington=("一致性检验方法二","first")
).reset_index().sort_values("数据点数", ascending=False)

print(f'\n有检验结果的体系统计:')
for _, r in stats.iterrows():
    print(f'  {r["名称1"]} + {r["名称2"]}: {r["数据点数"]}点, {r["文献数"]}篇, F={r["Fredenslund"]}, H={r["Herington"]}')

# 保存高质量数据
valid.to_excel('vle_validated_systems.xlsx', index=False, engine='openpyxl')
valid.to_csv('vle_validated_systems.csv', index=False, encoding='utf-8-sig')
print(f'\n已保存: vle_validated_systems.xlsx ({len(valid)} 行)')
