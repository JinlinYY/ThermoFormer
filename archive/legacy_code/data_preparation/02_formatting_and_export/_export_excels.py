import pandas as pd

df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')

# 筛选: 至少一种检验方法通过
passed = df[(df['一致性检验方法一'] == '通过') | (df['一致性检验方法二'] == '通过')].copy()
print(f'至少一种通过: {len(passed)} 行, {passed.groupby(["名称1","名称2"]).ngroups} 体系')

# 筛选: 两种都通过
both_pass = df[(df['一致性检验方法一'] == '通过') & (df['一致性检验方法二'] == '通过')].copy()
print(f'两种都通过: {len(both_pass)} 行')

# 筛选: 两种都不通过
both_fail = df[(df['一致性检验方法一'] == '不通过') & (df['一致性检验方法二'] == '不通过')].copy()
print(f'两种都不通过: {len(both_fail)} 行')

# 筛选: 有效 (有检验结果)
valid = df[df['一致性检验方法一'] != '无法判定'].copy()
print(f'有检验结果: {len(valid)} 行')

# 保存全部数据
df.to_excel('VLE_全部数据_387文献_715体系.xlsx', index=False, engine='openpyxl')

# 保存有检验结果的数据
valid.to_excel('VLE_有检验结果_71文献_47体系.xlsx', index=False, engine='openpyxl')

# 保存通过检验的数据
if len(passed) > 0:
    passed.to_excel('VLE_通过一致性检验.xlsx', index=False, engine='openpyxl')
    print(f'\n已保存: VLE_通过一致性检验.xlsx')

print(f'\n文件列表:')
print(f'  VLE_全部数据_387文献_715体系.xlsx ({len(df)} 行)')
print(f'  VLE_有检验结果_71文献_47体系.xlsx ({len(valid)} 行)')
