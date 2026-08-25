import pandas as pd
import os

fld = r'VLE_按体系分类整理_V3_扩展Antoine'

# 读完整汇总
df_all = pd.read_excel(fld + r'\A_完整数据汇总.xlsx', engine='openpyxl')
print(f'A_完整数据汇总: {len(df_all)} 行')

# 读所有分类文件的数据明细
files = [
    '00_第一批优先体系_9种_数据.xlsx',
    '01_第二批体系_8种_数据.xlsx',
    '1_脂肪烃_脂肪烃_芳香烃_数据.xlsx',
    '2_醚酯胺_醇_芳香烃_数据.xlsx',
    '3_酯_酮_烷烃_醇_数据.xlsx',
    '4_羧酸_酯_醇基组合_数据.xlsx',
    '5_卤代烃_极性分子_烃_数据.xlsx',
    '6_含硫体系_数据.xlsx',
    '8_电解质VLE_数据.xlsx',
    '99_其他未分类体系_670个_数据.xlsx',
]

all_parts = []
for f in files:
    path = os.path.join(fld, f)
    if not os.path.exists(path):
        continue
    df = pd.read_excel(path, sheet_name='数据明细', engine='openpyxl')
    if len(df) > 0:
        df['来源文件'] = f
        all_parts.append(df)

df_parts = pd.concat(all_parts, ignore_index=True)
print(f'各分类文件合计: {len(df_parts)} 行')

# 检查重复
key_cols = ['名称1','分子式1','名称2','分子式2','压强','温度','X1','Y1','DOI']
dup = df_parts.duplicated(subset=key_cols, keep=False)
print(f'重复行数(按关键字段): {dup.sum()}')

# 看哪些文件之间有重叠
df_dup = df_parts[dup].copy()
print()
print('===== 重复数据分布 =====')
print(df_dup.groupby('来源文件').size().to_string())
print()
print('===== 重复数据示例(前10行) =====')
print(df_dup[['名称1','名称2','压强','温度','X1','Y1','DOI','来源文件']].head(10).to_string())

# 最终确认：汇总是否去重
print()
print('===== 结论 =====')
print(f'A_完整数据汇总.xlsx: {len(df_all)} 行 (去重后)')
print(f'各分类文件合计: {len(df_parts)} 行 (含重复)')
print(f'重复行数: {dup.sum()}')
print(f'去重后应剩: {len(df_parts) - dup.sum()//2} 行 (估算)')
