import pandas as pd

df = pd.read_excel('VLE_按体系分类整理_V2/A_完整数据汇总.xlsx', engine='openpyxl')

rows = []
for (n1, n2), g in df.groupby(['名称1', '名称2']):
    G = int(g['一致性检验方法一'].iloc[0])
    H = int(g['一致性检验方法二'].iloc[0])
    G_txt = {1:'通过', -1:'不通过', 0:'无法判定'}[G]
    H_txt = {1:'通过', -1:'不通过', 0:'无法判定'}[H]
    rows.append({
        'n1': n1, 'n2': n2,
        'points': len(g),
        'G': G, 'H': H,
        'G_txt': G_txt, 'H_txt': H_txt,
    })
s = pd.DataFrame(rows)

print(f'总体系数: {len(s)}')
print(f'总数据行数: {len(df)}')
print()

for col, lab in [('G','Fredenslund(方法一)'), ('H','Herington(方法二)')]:
    print(f'[体系维度] {lab}:')
    vc = s[col+'_txt'].value_counts()
    for k in ['通过','不通过','无法判定']:
        v = vc.get(k, 0)
        pct = v / len(s) * 100
        bar = '█' * int(pct/2)
        print(f'  {k}: {v} 体系 ({pct:5.1f}%) {bar}')
    print()

# 哪些化合物导致无法判定? 现有 Antoine 参数化合物
ANTOINE_CN = ['水','甲醇','乙醇','1-丙醇','2-丙醇','1-丁醇','2-丁醇','异丁醇','叔丁醇',
              '1-戊醇','1-己醇','1-辛醇','1-癸醇',
              '乙酸','甲酸','丙酸','丙酮','苯','甲苯','环己烷','异辛烷',
              '乙腈','三氯甲烷','二氯甲烷','四氯化碳','二乙醚','四氢呋喃',
              '吡啶','苯胺','乙二醇','丙三醇','环己醇','二甲基亚砜','丁酮',
              '二氧化碳','氨','1-己烯','乙酸乙酯','乙酸甲酯','正庚烷',
              '正辛烷','正己烷','2-丁酮','1-十一醇']
antoine_set = set(ANTOINE_CN)
antoine_in_data = set()
for n in list(s['n1']) + list(s['n2']):
    if n in antoine_set:
        antoine_in_data.add(n)

print(f'Antoine 参数库: {len(antoine_set)} 化合物')
print(f'在数据中出现的 Antoine 化合物: {len(antoine_in_data)} 种')
print('  ' + ', '.join(sorted(antoine_in_data - set())))
print()

# 无法判定体系: 两端至少一端没有 Antoine 参数
no_antoine_names = set()
for _, r in s[s['G']==0].iterrows():
    a, b = r['n1'], r['n2']
    if a not in antoine_set or b not in antoine_set:
        if a not in antoine_set:
            no_antoine_names.add(a)
        if b not in antoine_set:
            no_antoine_names.add(b)
print(f'无 Antoine 参数的化合物数: {len(no_antoine_names)}')
print('前 60 种:')
for n in sorted(no_antoine_names)[:60]:
    print(f'  · {n}')

# 不通过/通过 的体系
valid = s[s['G'] != 0].sort_values('points', ascending=False)
print(f'\n有 Fredenslund 结果的 {len(valid)} 个体系:')
for _, r in valid.iterrows():
    print(f'  {r["n1"]} + {r["n2"]}: {r["points"]} 点, G={r["G_txt"]}, H={r["H_txt"]}')
