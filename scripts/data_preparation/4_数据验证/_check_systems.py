import pandas as pd

df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')

# 中文名化 (用映射)
import json
EN_TO_CN = json.load(open('_en_to_cn_full.json', 'r', encoding='utf-8'))
def to_cn(name):
    if name in EN_TO_CN:
        return EN_TO_CN[name]
    return name
df['名称1'] = df['名称1'].apply(to_cn)
df['名称2'] = df['名称2'].apply(to_cn)

# 构建所有体系
all_systems = set()
for n1, n2 in zip(df['名称1'], df['名称2']):
    all_systems.add((n1, n2) if n1 <= n2 else (n2, n1))

print(f'总体系数: {len(all_systems)}')
print()

# 检查第一批 9 种
BATCH1 = [
    ('丙酮','苯'), ('丙酮','正己烷'), ('丙酮','乙酸乙酯'),
    ('乙酸乙酯','苯'), ('四氢呋喃','苯'), ('吡啶','甲苯'),
    ('N,N-二甲基甲酰胺','乙酸乙酯'), ('氯仿','丙酮'), ('二甲基亚砜','苯'),
]
print('第一批 9 个体系检查:')
for a, b in BATCH1:
    key = (a, b) if a <= b else (b, a)
    found = key in all_systems
    cnt = sum(1 for n1, n2 in zip(df['名称1'], df['名称2'])
              if (n1 == a and n2 == b) or (n1 == b and n2 == a))
    print(f'  {a} + {b}: {"有" if found else "无"} ({cnt} 行)')

print()

# 检查第二批 8 种
BATCH2 = [
    ('噻吩','正庚烷'), ('苯','甲苯'), ('乙酸乙酯','乙酸正丙酯'),
    ('乙酸','乙酸乙酯'), ('二甲基亚砜','乙酸乙酯'), ('乙腈','正己烷'),
    ('正庚烷','甲苯'), ('噻吩','苯'),
]
print('第二批 8 个体系检查:')
for a, b in BATCH2:
    key = (a, b) if a <= b else (b, a)
    found = key in all_systems
    cnt = sum(1 for n1, n2 in zip(df['名称1'], df['名称2'])
              if (n1 == a and n2 == b) or (n1 == b and n2 == a))
    print(f'  {a} + {b}: {"有" if found else "无"} ({cnt} 行)')
