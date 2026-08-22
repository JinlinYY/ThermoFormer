import pandas as pd
fld = r'VLE_按体系分类整理_V3_扩展Antoine'
df_all = pd.read_excel(fld + r'\A_完整数据汇总.xlsx', engine='openpyxl')

# 检查电解质相关组分（盐、离子液体、酸根等）
print('===== 检查可能的电解质相关组分 =====')
keywords = ['盐','氯','钠','钾','钙','硫酸','硝酸','盐酸','离子','IL','咪唑','吡啶','胆碱','氨基酸','铵','胺盐']
found = []
for kw in keywords:
    mask = df_all['名称1'].str.contains(kw, na=False) | df_all['名称2'].str.contains(kw, na=False)
    if mask.sum() > 0:
        found.append((kw, mask.sum()))
        subset = df_all[mask][['名称1','名称2']].drop_duplicates()
        print(f'--- 关键词「{kw}」: {mask.sum()} 行 ---')
        print(subset.head(5).to_string())
        print()

print('===== 总览 =====')
print('关键词命中统计:', found)
print('A_完整数据汇总.xlsx 总行数:', len(df_all))
