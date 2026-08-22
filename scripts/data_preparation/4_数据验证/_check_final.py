import pandas as pd
df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')
print(f'总行数: {len(df)}')
doi_col = [c for c in df.columns if 'DOI' in c.upper()][0]
print(f'DOI数: {df[doi_col].nunique()}')

g_counts = df['一致性检验方法一'].value_counts()
h_counts = df['一致性检验方法二'].value_counts()
print(f'\nFredenslund:')
for k,v in g_counts.items():
    print(f'  {k}: {v}')
print(f'\nHerington:')
for k,v in h_counts.items():
    print(f'  {k}: {v}')

print(f'\nsmiles1 非空: {df["smiles1"].notna().sum()}/{len(df)}')
print(f'smiles2 非空: {df["smiles2"].notna().sum()}/{len(df)}')

# 列出有检验结果的体系
valid = df[df['一致性检验方法一'] != '无法判定']
print(f'\n有 Fredenslund 结果的体系: {valid.groupby(["名称1","名称2"]).ngroups}')
