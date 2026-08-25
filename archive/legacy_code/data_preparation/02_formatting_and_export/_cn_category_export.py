# -*- coding: utf-8 -*-
"""
按用户要求重新整理:
1. 名称尽量用中文名
2. 一致性检验: 通过=1, 不通过=-1, 无法判定=0
3. 按图片中的体系分类(1-6类 + 电解质 + 第一批 + 第二批)分别导出 Excel
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import numpy as np

# ========== 1. 中英文映射 ==========
CN_TO_EN = {
    "水": "water", "甲醇": "methanol", "乙醇": "ethanol",
    "1-丙醇": "propan-1-ol", "正丙醇": "propan-1-ol",
    "2-丙醇": "propan-2-ol", "异丙醇": "propan-2-ol",
    "1-丁醇": "butan-1-ol", "正丁醇": "butan-1-ol",
    "2-丁醇": "butan-2-ol",
    "异丁醇": "2-methylpropan-1-ol",
    "叔丁醇": "2-methylpropan-2-ol",
    "1-戊醇": "pentan-1-ol", "正戊醇": "pentan-1-ol",
    "2-戊醇": "pentan-2-ol",
    "1-己醇": "hexan-1-ol", "正己醇": "hexan-1-ol",
    "2-己醇": "hexan-2-ol",
    "1-辛醇": "octan-1-ol", "正辛醇": "octan-1-ol",
    "2-辛醇": "octan-2-ol",
    "1-癸醇": "decan-1-ol",
    "1-庚醇": "heptan-1-ol",
    "1-十二醇": "dodecan-1-ol",
    "2-乙基-1-己醇": "2-ethyl-1-hexanol",
    "甲酸": "formic acid", "乙酸": "acetic acid",
    "丙酸": "propanoic acid",
    "正丁酸": "butanoic acid", "丁酸": "butanoic acid",
    "正戊酸": "pentanoic acid", "戊酸": "pentanoic acid",
    "正己酸": "hexanoic acid", "己酸": "hexanoic acid",
    "正癸酸": "decanoic acid",
    "正十六酸": "hexadecanoic acid",
    "正十八酸": "octadecanoic acid",
    "丙烯酸": "acrylic acid",
    "苯甲酸": "benzoic acid",
    "三氟乙酸": "trifluoroethanoic acid",
    "二氯乙酸": "2,2-dichloroacetic acid",
    "氯乙酸": "chloroethanoic acid",
    "丙酮酸": "pyruvic acid",
    "乙酸乙酯": "ethyl acetate",
    "乙酸甲酯": "methyl acetate",
    "乙酸正丙酯": "propyl ethanoate",
    "乙酸正丁酯": "butyl ethanoate",
    "甲酸乙酯": "ethyl formate",
    "甲酸甲酯": "methyl formate",
    "甲酸正丙酯": "propyl methanoate",
    "甲酸正丁酯": "butyl methanoate",
    "丙酸乙酯": "ethyl propanoate",
    "丙酸甲酯": "methyl propanoate",
    "丙酸正丁酯": "butyl propanoate",
    "苯甲酸乙酯": "ethyl benzoate",
    "苯甲酸甲酯": "methyl benzoate",
    "2-甲基丙酸乙酯": "ethyl 2-methylpropanoate",
    "2-甲基丁酸乙酯": "ethyl 2-methylbutanoate",
    "2-甲基丁酸甲酯": "methyl 2-methylbutanoate",
    "丙酮": "acetone",
    "丁酮": "butanone", "2-丁酮": "butanone",
    "2-戊酮": "pentan-2-one",
    "3-戊酮": "pentan-3-one",
    "2-己酮": "hexan-2-one",
    "2-庚酮": "heptan-2-one",
    "2-辛酮": "octan-2-one",
    "2-壬酮": "nonan-2-one",
    "环己酮": "cyclohexanone",
    "甲基环己酮": "methylcyclohexanone",
    "苯乙酮": "acetophenone",
    "苯甲醛": "benzaldehyde",
    "苯": "benzene", "甲苯": "toluene",
    "乙苯": "ethylbenzene",
    "邻二甲苯": "1,2-dimethylbenzene",
    "间二甲苯": "1,3-dimethylbenzene",
    "对二甲苯": "1,4-dimethylbenzene",
    "1,2,3-三甲苯": "1,2,3-trimethylbenzene",
    "1,2,4-三甲苯": "1,2,4-trimethylbenzene",
    "1,3,5-三甲苯": "1,3,5-trimethylbenzene",
    "异丙苯": "isopropylbenzene",
    "正丙苯": "n-propylbenzene",
    "正丁苯": "butylbenzene",
    "叔丁苯": "tert-butylbenzene",
    "氯苯": "chlorobenzene",
    "溴苯": "bromobenzene",
    "氟苯": "fluorobenzene",
    "碘苯": "iodobenzene",
    "硝基苯": "nitrobenzene",
    "己烷": "hexane", "正己烷": "hexane",
    "庚烷": "heptane", "正庚烷": "heptane",
    "辛烷": "octane", "正辛烷": "octane",
    "壬烷": "nonane", "正壬烷": "nonane",
    "癸烷": "decane", "正癸烷": "decane",
    "十一烷": "undecane",
    "十二烷": "dodecane",
    "十四烷": "tetradecane",
    "十六烷": "hexadecane",
    "异辛烷": "2,2,4-trimethylpentane",
    "2,3-二甲基丁烷": "2,3-dimethylbutane",
    "2-甲基丁烷": "2-methylbutane",
    "2-甲基戊烷": "2-methylpentane",
    "3-甲基戊烷": "3-methylpentane",
    "2,4-二甲基戊烷": "2,4-dimethylpentane",
    "环戊烷": "cyclopentane",
    "环己烷": "cyclohexane",
    "甲基环己烷": "methylcyclohexane",
    "乙基环己烷": "ethylcyclohexane",
    "丁基环己烷": "butylcyclohexane",
    "环己烯": "cyclohexene",
    "1-丁烯": "1-butene",
    "1-己烯": "1-hexene",
    "1-辛烯": "1-octene",
    "乙烯": "ethene",
    "丙烯": "propene",
    "丁烷": "butane",
    "丙烷": "propane",
    "甲烷": "methane",
    "乙烷": "ethane",
    "二氯甲烷": "dichloromethane",
    "氯仿": "chloroform", "三氯甲烷": "chloroform",
    "四氯化碳": "carbon tetrachloride",
    "1,2-二氯乙烷": "1,2-dichloroethane",
    "1,1,1-三氯乙烷": "1,1,1-trichloroethane",
    "1,1,2-三氯乙烷": "1,1,2-trichloroethane",
    "1,1,2,2-四氯乙烷": "1,1,2,2-tetrachloroethane",
    "二溴甲烷": "dibromomethane",
    "三溴甲烷": "bromoform",
    "溴氯甲烷": "bromochloromethane",
    "1,2-二溴乙烷": "1,2-dibromoethane",
    "六氟乙烷": "hexafluoroethane",
    "六氟丙烯": "hexafluoropropene",
    "八氟丙烷": "octafluoropropane",
    "全氟丁烷": "decafluorobutane",
    "全氟己烷": "perfluorohexane",
    "全氟庚烷": "hexadecafluoroheptane",
    "全氟辛烷": "octadecafluorooctane",
    "氨": "ammonia",
    "二乙醚": "diethyl ether", "乙醚": "diethyl ether",
    "甲基叔丁基醚": "tert-butyl methyl ether",
    "二丁醚": "dibutyl ether",
    "二异丙醚": "diisopropyl ether",
    "二丙醚": "dipropyl ether",
    "苯甲醚": "anisole",
    "四氢呋喃": "tetrahydrofuran", "THF": "tetrahydrofuran",
    "1,4-二噁烷": "1,4-dioxane",
    "1,3-二噁烷": "1,3-dioxane",
    "1,3-二噁茂烷": "1,3-dioxolane",
    "吡啶": "pyridine",
    "哌啶": "piperidine",
    "吡咯烷": "pyrrolidine",
    "吗啉": "morpholine",
    "苯胺": "aniline",
    "三乙胺": "triethylamine",
    "正丁胺": "butylamine",
    "环己胺": "cyclohexylamine",
    "N-甲基-2-吡咯烷酮": "N-methylpyrrolidone", "NMP": "N-methylpyrrolidone",
    "N,N-二甲基甲酰胺": "dimethylformamide", "DMF": "dimethylformamide",
    "N,N-二甲基乙酰胺": "N,N-dimethylethanamide",
    "二硫化碳": "carbon disulfide",
    "噻吩": "thiophene",
    "2-甲基噻吩": "2-methylthiophene",
    "3-甲基噻吩": "3-methylthiophene",
    "苯并噻吩": "benzo[b]thiophene",
    "四氢噻吩": "tetrahydrothiophene",
    "二甲基亚砜": "dimethyl sulfoxide", "DMSO": "dimethyl sulfoxide",
    "乙腈": "acetonitrile",
    "硝基甲烷": "nitromethane",
    "硝基乙烷": "nitroethane",
    "乙二醇": "ethylene glycol",
    "1,2-丙二醇": "propane-1,2-diol",
    "1,3-丙二醇": "propan-1,3-diol",
    "丙三醇": "glycerol", "甘油": "glycerol",
    "1,2-丁二醇": "2,3-butanediol",
    "环己醇": "cyclohexanol",
    "环戊醇": "cyclopentanol",
    "2-甲氧基乙醇": "2-methoxyethanol",
    "1-甲氧基-2-丙醇": "1-methoxy-2-propanol",
    "2-乙氧基乙醇": "2-ethoxyethan-1-ol",
    "二乙醇胺": "diethanolamine",
    "碳酸二甲酯": "dimethyl carbonate",
    "碳酸二乙酯": "diethyl carbonate",
    "碳酸丙烯酯": "propylene carbonate",
    "二甲基砜": "sulfolane",
    "氮气": "nitrogen",
    "氧气": "oxygen",
    "氢气": "hydrogen",
    "氦气": "helium",
    "氩气": "argon",
    "氙气": "xenon",
    "二氧化碳": "carbon dioxide",
    "一氧化碳": "carbon monoxide",
    "硫化氢": "hydrogen sulfide",
    "二氧化硫": "sulfur dioxide",
    "三氯乙烯": "trichloroethene",
    "四氯乙烯": "tetrachloroethene",
    "乙酸丙酯": "propyl ethanoate",
    "2-丁炔": "2-butyne",
    "1-丁炔": "1-butyne",
    "1-己炔": "1-hexyne",
    "2-己炔": "2-hexyne",
    "3-己炔": "3-hexyne",
    "2-丁炔-1-醇": "but-2-yn-1-ol",
    "丙炔": "propyne",
    "乙炔": "ethyne",
    "异戊二烯": "isoprene",
    "1,3-丁二烯": "1,3-butadiene",
    "苯乙烯": "styrene",
    "丙烯腈": "acrylonitrile",
    "丁腈": "butanenitrile",
    "丙腈": "propanenitrile",
    "己腈": "hexanenitrile",
    "1-十一醇": "1-undecanol",
    "2,3-二甲基-2-丁烯": "2,3-dimethyl-2-butene",
    "氟乙烷": "fluoroethane",
    "二氟甲烷": "difluoromethane",
    "1,1,1,2-四氟乙烷": "1,1,1,2-tetrafluoroethane",
    "1,1-二氟乙烷": "1,1-difluoroethane",
    "三氟甲烷": "trifluoromethane",
    "2,3,3,3-四氟-1-丙烯": "2,3,3,3-tetrafluoropropene",
    "反式-1,3,3,3-四氟丙烯": "trans-1,3,3,3-tetrafluoropropene",
    "二甲基醚": "dimethyl ether",
    "氯二氟甲烷": "chlorodifluoromethane",
    "外-四氢二环戊二烯": "exo-tetrahydrodicyclopentadiene",
    "内-四氢二环戊二烯": "endo-tetrahydrodicyclopentadiene",
    "七氟丙烷": "heptafluoropropane",
    "环氧乙烷": "oxirane",
    "己内酰胺": "caprolactam",
    "五氟乙烷": "pentafluoroethane",
    "丙烯": "propene",
    "丁烯": "1-butene",
}

# 构建反向映射 英文->中文 (取第一个中文)
EN_TO_CN = {}
for cn, en in CN_TO_EN.items():
    if en not in EN_TO_CN:
        EN_TO_CN[en] = cn

def try_cn(name):
    if pd.isna(name):
        return name
    name = str(name).strip()
    if name in EN_TO_CN:
        return EN_TO_CN[name]
    # 直接就是中文名(即不在 EN_TO_CN 中但是个中文名)
    return name


# ========== 2. 加载数据 ==========
df = pd.read_csv('vle_binary_data_organized.csv', encoding='utf-8-sig')
print(f'加载: {len(df)} 行')

# 列顺序严格按 A-L + M DOI
cols_order = [
    '名称1',      # A
    '分子式1',    # B
    'smiles1',    # C
    '名称2',      # D
    '分子式2',    # E
    'smiles2',    # F
    '一致性检验方法一',  # G Fredenslund
    '一致性检验方法二',  # H Herington
    '压强',       # I mmHg
    '温度',       # J °C
    'X1',         # K 液相摩尔分数
    'Y1',         # L 气相摩尔分数
    'DOI',        # M
]
df = df[cols_order].copy()

# ========== 3. 名称改中文名 ==========
df['名称1'] = df['名称1'].apply(try_cn)
df['名称2'] = df['名称2'].apply(try_cn)

# ========== 4. 一致性检验改为数字 ==========
G_MAP = {'通过': 1, '不通过': -1, '无法判定': 0}
H_MAP = {'通过': 1, '不通过': -1, '无法判定': 0}
df['一致性检验方法一'] = df['一致性检验方法一'].map(G_MAP).fillna(0).astype(int)
df['一致性检验方法二'] = df['一致性检验方法二'].map(H_MAP).fillna(0).astype(int)

# ========== 5. 清洗 ==========
df = df.dropna(subset=['压强','温度','X1','Y1'])
df = df[(df['X1']>=0)&(df['X1']<=1)&(df['Y1']>=0)&(df['Y1']<=1)]
df['smiles1'] = df['smiles1'].fillna('')
df['smiles2'] = df['smiles2'].fillna('')
df = df.drop_duplicates(subset=['名称1','名称2','压强','温度','X1','Y1','DOI'])
df = df.reset_index(drop=True)

print(f'清洗后: {len(df)} 行, {df["DOI"].nunique()} DOI')
print(f'中文名化: 名称1 中英比 {sum(df["名称1"].apply(lambda x: x in EN_TO_CN))}/{len(df)}')

# ========== 6. 体系分类 (按图片) ==========
# 先做体系名归一化
def system_key(n1, n2):
    if (n1, n2) <= (n2, n1):
        return (n1, n2)
    return (n2, n1)

# 批定义 (用中文名 -> 英文名, 匹配时两端都做)
def match_system(row, target_list):
    r1 = row['名称1']
    r2 = row['名称2']
    for (a, b) in target_list:
        if (r1 == a and r2 == b) or (r1 == b and r2 == a):
            return True
        # 英文名匹配
        ae = CN_TO_EN.get(a, a)
        be = CN_TO_EN.get(b, b)
        re1 = CN_TO_EN.get(r1, r1)
        re2 = CN_TO_EN.get(r2, r2)
        if (re1 == ae and re2 == be) or (re1 == be and re2 == ae):
            return True
    return False

# --- 第一批优先体系 ---
BATCH1 = [
    ('丙酮','苯'), ('丙酮','正己烷'), ('丙酮','乙酸乙酯'),
    ('乙酸乙酯','苯'), ('四氢呋喃','苯'), ('吡啶','甲苯'),
    ('N,N-二甲基甲酰胺','乙酸乙酯'), ('氯仿','丙酮'), ('二甲基亚砜','苯'),
]
# --- 第二批体系 ---
BATCH2 = [
    ('噻吩','正庚烷'), ('苯','甲苯'), ('乙酸乙酯','乙酸正丙酯'),
    ('乙酸','乙酸乙酯'), ('二甲基亚砜','乙酸乙酯'), ('乙腈','正己烷'),
    ('正庚烷','甲苯'), ('噻吩','苯'),
]
# --- 1. 脂肪烃-脂肪烃 / 脂肪烃-芳香烃 / 芳香烃-芳香烃 ---
C1_HYDROCARBONS = [
    ('正己烷','苯'), ('正庚烷','苯'), ('正辛烷','苯'), ('环己烷','苯'),
    ('正己烷','甲苯'), ('正庚烷','甲苯'), ('正辛烷','甲苯'), ('环己烷','甲苯'),
    ('苯','甲苯'), ('苯','乙苯'), ('苯','邻二甲苯'), ('甲苯','乙苯'),
    ('甲苯','邻二甲苯'), ('正己烷','正庚烷'), ('正己烷','正辛烷'),
    ('正庚烷','正辛烷'), ('环己烷','正己烷'), ('环己烷','正庚烷'),
    ('环己烷','甲基环己烷'), ('己烷','庚烷'),
    ('己烷','环己烷'), ('庚烷','环己烷'), ('庚烷','甲苯'),
    ('己烷','甲苯'), ('苯','环己烷'),
]
# --- 2. 醚、酯、胺与醇/芳香烃 ---
C2_ETHER_ESTER_AMINE = [
    ('四氢呋喃','乙醇'), ('四氢呋喃','甲醇'), ('四氢呋喃','1-丙醇'),
    ('乙醚','乙醇'), ('乙醚','甲醇'), ('二异丙醚','乙醇'),
    ('乙酸乙酯','乙醇'), ('乙酸乙酯','甲醇'), ('乙酸乙酯','1-丙醇'),
    ('乙酸乙酯','2-丙醇'), ('乙酸甲酯','甲醇'), ('乙酸甲酯','乙醇'),
    ('乙酸正丙酯','1-丙醇'), ('乙酸正丙酯','乙醇'), ('乙酸正丙酯','1-丁醇'),
    ('乙酸正丁酯','1-丁醇'), ('甲酸乙酯','乙醇'),
    ('吡啶','乙醇'), ('吡啶','甲醇'), ('吡啶','甲苯'),
    ('三乙胺','乙醇'), ('苯胺','甲醇'), ('苯胺','乙醇'),
    ('N,N-二甲基甲酰胺','乙酸乙酯'), ('N-甲基-2-吡咯烷酮','乙醇'),
    ('四氢呋喃','苯'), ('二乙醚','甲苯'), ('吡啶','苯'),
    ('苯胺','甲苯'), ('N,N-二甲基甲酰胺','甲醇'),
]
# --- 3. 酯与酮、酯、烷烃及醇 ---
C3_ESTER = [
    ('乙酸乙酯','丙酮'), ('乙酸甲酯','丙酮'), ('乙酸正丙酯','丙酮'),
    ('乙酸乙酯','丁酮'), ('乙酸乙酯','苯乙酮'),
    ('乙酸乙酯','乙酸甲酯'), ('乙酸乙酯','乙酸正丙酯'),
    ('乙酸乙酯','乙酸正丁酯'), ('乙酸甲酯','乙酸正丙酯'),
    ('乙酸正丙酯','乙酸正丁酯'), ('乙酸乙酯','己烷'),
    ('乙酸乙酯','环己烷'), ('乙酸乙酯','正庚烷'), ('乙酸甲酯','己烷'),
    ('乙酸正丙酯','己烷'), ('甲酸乙酯','己烷'),
    ('丙酸乙酯','乙醇'), ('丙酸乙酯','甲醇'), ('丙酸乙酯','己烷'),
    ('苯甲酸乙酯','乙醇'), ('苯甲酸乙酯','甲醇'), ('苯甲酸乙酯','苯'),
]
# --- 4. 羧酸、酯与醇基等组合 ---
C4_ACID = [
    ('乙酸','甲醇'), ('乙酸','乙醇'), ('乙酸','1-丙醇'), ('乙酸','2-丙醇'),
    ('乙酸','1-丁醇'), ('丙酸','甲醇'), ('丙酸','乙醇'),
    ('丁酸','甲醇'), ('丁酸','乙醇'), ('甲酸','甲醇'),
    ('甲酸','乙醇'), ('苯甲酸','甲醇'), ('苯甲酸','乙醇'),
    ('乙酸','乙酸乙酯'), ('丙酸','丙酸乙酯'), ('丁酸','丁酸甲酯'),
    ('丙烯酸','甲醇'), ('丙烯酸','乙醇'),
    ('三氟乙酸','甲醇'), ('氯乙酸','二氯乙酸'),
]
# --- 5. 卤代烃-极性分子 / 卤代烃-烃 ---
C5_HALO = [
    ('氯仿','丙酮'), ('氯仿','甲醇'), ('氯仿','乙醇'), ('氯仿','苯'),
    ('二氯甲烷','甲醇'), ('二氯甲烷','乙醇'), ('二氯甲烷','丙酮'),
    ('四氯化碳','甲醇'), ('四氯化碳','乙醇'), ('四氯化碳','苯'),
    ('1,2-二氯乙烷','甲醇'), ('1,2-二氯乙烷','乙醇'),
    ('氯苯','苯'), ('氯苯','甲苯'), ('氯苯','甲醇'),
    ('溴苯','苯'), ('溴苯','甲苯'),
    ('氯仿','正己烷'), ('二氯甲烷','正己烷'), ('四氯化碳','正己烷'),
    ('1,2-二氯乙烷','正己烷'),
    ('氯苯','正己烷'), ('氯苯','环己烷'),
]
# --- 6. 含硫体系 ---
C6_SULFUR = [
    ('二甲基亚砜','甲醇'), ('二甲基亚砜','乙醇'), ('二甲基亚砜','水'),
    ('二甲基亚砜','丙酮'), ('二甲基亚砜','苯'), ('二甲基亚砜','乙酸乙酯'),
    ('二甲基亚砜','甲苯'), ('噻吩','正己烷'), ('噻吩','正庚烷'),
    ('噻吩','苯'), ('噻吩','甲苯'), ('噻吩','环己烷'),
    ('二硫化碳','甲醇'), ('二硫化碳','乙醇'), ('二硫化碳','丙酮'),
    ('二硫化碳','苯'), ('二硫化碳','正己烷'),
    ('二甲基砜','甲醇'), ('二甲基砜','乙醇'),
    ('四氢噻吩','苯'), ('苯并噻吩','萘'),
]
# --- 8. 电解质 VLE ---
C8_ELECTROLYTE = [
    ('水','氯化钠'), ('水','氯化钾'), ('水','氯化钙'), ('水','硫酸钠'),
    ('水','硝酸钠'), ('水','氯化镁'), ('水','氯化锌'),
    ('水','硫酸'), ('水','盐酸'), ('水','硝酸'), ('水','氢氧化钾'),
    ('甲醇','氯化锂'), ('甲醇','碘化钠'), ('乙醇','氯化铜'),
    ('乙醇','氯化锌'), ('乙酸','醋酸钠'), ('乙二醇','氯化钠'),
]

CATEGORIES = [
    ('00_第一批优先体系_9种', BATCH1),
    ('01_第二批体系_8种', BATCH2),
    ('1_脂肪烃_脂肪烃_芳香烃', C1_HYDROCARBONS),
    ('2_醚酯胺_醇_芳香烃', C2_ETHER_ESTER_AMINE),
    ('3_酯_酮_烷烃_醇', C3_ESTER),
    ('4_羧酸_酯_醇基组合', C4_ACID),
    ('5_卤代烃_极性分子_烃', C5_HALO),
    ('6_含硫体系', C6_SULFUR),
    ('8_电解质VLE', C8_ELECTROLYTE),
]

# ========== 7. 导出 ==========
OUT_DIR = Path('VLE_按体系分类整理')
OUT_DIR.mkdir(exist_ok=True)

# 保存一份完整数据
full_path = OUT_DIR / 'A_完整数据汇总.xlsx'
df.to_excel(full_path, index=False, engine='openpyxl')
print(f'\n完整数据: {full_path.name} ({len(df)} 行, {df["DOI"].nunique()} DOI)')

# 逐类导出 + 总览
summary_rows = []
total_in_cats = 0

for cat_name, target_list in CATEGORIES:
    mask = df.apply(lambda r: match_system(r, target_list), axis=1)
    sub_df = df[mask].copy()
    # 按体系分组统计
    sys_df = pd.DataFrame(columns=['体系','数据点数','文献数','Fredenslund一致性检验(G)','Herington一致性检验(H)'])
    if len(sub_df) > 0:
        sys_groups = sub_df.groupby(['名称1','名称2'])
        sys_stats = []
        for (n1, n2), g in sys_groups:
            sys_stats.append({
                '体系': f'{n1} + {n2}',
                '数据点数': len(g),
                '文献数': g['DOI'].nunique(),
                'Fredenslund一致性检验(G)': g['一致性检验方法一'].iloc[0],
                'Herington一致性检验(H)': g['一致性检验方法二'].iloc[0],
            })
        sys_df = pd.DataFrame(sys_stats).sort_values('数据点数', ascending=False)
    
    # 导出明细
    detail_path = OUT_DIR / f'{cat_name}_数据明细.xlsx'
    with pd.ExcelWriter(detail_path, engine='openpyxl') as writer:
        sub_df.to_excel(writer, sheet_name='数据明细', index=False)
        sys_df.to_excel(writer, sheet_name='体系统计', index=False)
    
    total_points = len(sub_df)
    total_in_cats += total_points
    n_systems = len(sys_df)
    n_papers = sub_df['DOI'].nunique()
    
    summary_rows.append({
        '类别': cat_name,
        '体系数': n_systems,
        '数据点数': total_points,
        '文献数(Distinct DOI)': n_papers,
        '包含体系': '；'.join(sys_df['体系'].tolist()[:10]),
        '文件名': detail_path.name,
    })
    print(f'  {cat_name}: {n_systems} 体系, {total_points} 行, {n_papers} DOI')

# 总览 sheet
summary_df = pd.DataFrame(summary_rows)
summary_path = OUT_DIR / 'Z_分类总览.xlsx'
with pd.ExcelWriter(summary_path, engine='openpyxl') as writer:
    summary_df.to_excel(writer, sheet_name='分类总览', index=False)
    # 加一张总表的概览
    overview = pd.DataFrame([
        {'项目': '总行数', '数值': len(df)},
        {'项目': '总DOI数', '数值': df['DOI'].nunique()},
        {'项目': '总体系数', '数值': df.groupby(['名称1','名称2']).ngroups},
        {'项目': '已分类数据行数', '数值': total_in_cats},
    ])
    overview.to_excel(writer, sheet_name='数据概览', index=False)

print(f'\n总览: {summary_path.name}')
print(f'\n全部文件在: {OUT_DIR.resolve()}')
