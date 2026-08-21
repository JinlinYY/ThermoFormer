import pandas as pd
import os

fld = r'VLE_按体系分类整理_V3_扩展Antoine'

# 1. 读完整汇总
df_all = pd.read_excel(fld + r'\A_完整数据汇总.xlsx', engine='openpyxl')
print('===== A_完整数据汇总.xlsx =====')
print('总行数:', len(df_all))
print()

# 2. 逐个读分类文件，统计行数
print('===== 各分类文件数据点数 =====')
total = 0
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
for f in files:
    path = os.path.join(fld, f)
    if not os.path.exists(path):
        print(f'  {f}: 文件不存在')
        continue
    xl = pd.ExcelFile(path, engine='openpyxl')
    # 找数据明细sheet
    sheet_name = xl.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet_name, engine='openpyxl')
    n = len(df)
    total += n
    print(f'  {f}: {n} 行  (sheets: {xl.sheet_names})')

print()
print(f'各分类文件行数合计: {total}')
print(f'A_完整数据汇总.xlsx 行数: {len(df_all)}')
print(f'是否一致: {total == len(df_all)}')

# 3. 检查是否有重叠（用水体系做交叉验证）
print()
print('===== 验证水体系是否在汇总中 =====')
water_in_all = df_all[df_all['名称1'].str.contains('水', na=False) | df_all['名称2'].str.contains('水', na=False)]
print(f'A_完整数据汇总中水体系: {len(water_in_all)} 行')
print()
print('===== 验证醇体系是否在汇总中 =====')
alc_in_all = df_all[df_all['名称1'].str.contains('醇', na=False) | df_all['名称2'].str.contains('醇', na=False)]
print(f'A_完整数据汇总中醇体系: {len(alc_in_all)} 行')
