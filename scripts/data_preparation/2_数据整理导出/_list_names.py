import pandas as pd

df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')

all_names = sorted(set(df['名称1'].unique()) | set(df['名称2'].unique()))
print(f'所有化合物名称 ({len(all_names)} 个):')
for n in all_names:
    print(f'  {n}')
