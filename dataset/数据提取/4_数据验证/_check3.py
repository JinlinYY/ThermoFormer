import pandas as pd
df = pd.read_csv('vle_binary_expand.csv', encoding='utf-8-sig')
print(f'CSV: {len(df)} rows')
doi_col = [c for c in df.columns if 'DOI' in c.upper()][0]
print(f'DOIs: {df[doi_col].nunique()}')
systems = df.groupby(['名称1','名称2']).size().reset_index(name='count')
print(f'Systems: {len(systems)}')
print(f'\nTop 20 systems:')
for _, r in systems.sort_values('count', ascending=False).head(20).iterrows():
    print(f'  {r["名称1"]} + {r["名称2"]}: {r["count"]}')
