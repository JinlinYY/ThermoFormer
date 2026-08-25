# -*- coding: utf-8 -*-
"""
按用户指定的体系列表（来自图片）筛选 ThermoML VLE 数据，每个体系一个 Excel。
映射中文体系名到 ThermoML 英文名。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

CSV_PATH = "vle_binary_expand.csv"
OUT_DIR = Path("vle_by_system_selected")
SMILES_CACHE = Path("_smiles_cache.json")

# ============================================================
# 中文 → ThermoML 英文名映射
# ============================================================
CN_TO_EN = {
    "水": "water", "甲醇": "methanol", "乙醇": "ethanol",
    "1-丙醇": "propan-1-ol", "1-propanol": "propan-1-ol", "正丙醇": "propan-1-ol",
    "2-丙醇": "propan-2-ol", "2-propanol": "propan-2-ol", "异丙醇": "propan-2-ol", "isopropanol": "propan-2-ol",
    "1-丁醇": "butan-1-ol", "1-butanol": "butan-1-ol", "正丁醇": "butan-1-ol", "n-butanol": "butan-1-ol",
    "2-丁醇": "butan-2-ol", "2-butanol": "butan-2-ol",
    "异丁醇": "2-methylpropan-1-ol", "isobutanol": "2-methylpropan-1-ol", "2-methyl-1-propanol": "2-methylpropan-1-ol",
    "叔丁醇": "2-methylpropan-2-ol", "tert-butanol": "2-methylpropan-2-ol",
    "1-戊醇": "pentan-1-ol", "1-pentanol": "pentan-1-ol", "正戊醇": "pentan-1-ol",
    "2-戊醇": "pentan-2-ol", "2-pentanol": "pentan-2-ol",
    "1-己醇": "hexan-1-ol", "1-hexanol": "hexan-1-ol", "正己醇": "hexan-1-ol",
    "2-己醇": "hexan-2-ol", "2-hexanol": "hexan-2-ol",
    "1-辛醇": "octan-1-ol", "1-octanol": "octan-1-ol",
    "2-辛醇": "octan-2-ol", "2-octanol": "octan-2-ol",
    "1-癸醇": "decan-1-ol", "1-decanol": "decan-1-ol",
    "甲酸": "formic acid", "乙酸": "acetic acid",
    "丙酸": "propanoic acid", "正丁酸": "butanoic acid", "丁酸": "butanoic acid",
    "异丁酸": "2-methylpropanoic acid",
    "正戊酸": "pentanoic acid", "戊酸": "pentanoic acid",
    "正己酸": "hexanoic acid", "己酸": "hexanoic acid",
    "丙烯酸": "acrylic acid",
    "苯甲酸": "benzoic acid",
    "丙酮": "acetone",
    "丁酮": "butanone", "2-丁酮": "butanone", "甲基乙基酮": "butanone",
    "2-戊酮": "pentan-2-one", "2-pentanone": "pentan-2-one",
    "3-戊酮": "pentan-3-one",
    "2-己酮": "hexan-2-one",
    "2-庚酮": "heptan-2-one",
    "环己酮": "cyclohexanone",
    "甲醛": "formaldehyde",
    "乙醛": "acetaldehyde",
    "丙醛": "propanal",
    "丁醛": "butanal",
    "苯": "benzene", "甲苯": "toluene",
    "邻二甲苯": "1,2-dimethylbenzene", "o-xylene": "1,2-dimethylbenzene",
    "间二甲苯": "1,3-dimethylbenzene", "m-xylene": "1,3-dimethylbenzene",
    "对二甲苯": "1,4-dimethylbenzene", "p-xylene": "1,4-dimethylbenzene",
    "乙苯": "ethylbenzene",
    "己烷": "hexane", "正己烷": "hexane", "n-hexane": "hexane",
    "庚烷": "heptane", "正庚烷": "heptane", "n-heptane": "heptane",
    "辛烷": "octane", "正辛烷": "octane", "n-octane": "octane",
    "癸烷": "decane",
    "环己烷": "cyclohexane",
    "异辛烷": "2,2,4-trimethylpentane", "isooctane": "2,2,4-trimethylpentane",
    "二氯甲烷": "dichloromethane",
    "氯仿": "chloroform", "三氯甲烷": "chloroform",
    "四氯化碳": "carbon tetrachloride",
    "1,2-二氯乙烷": "1,2-dichloroethane",
    "1,1,1-三氯乙烷": "1,1,1-trichloroethane",
    "1,1,2-三氯乙烷": "1,1,2-trichloroethane",
    "二溴甲烷": "dibromomethane",
    "三溴甲烷": "bromoform",
    "溴氯甲烷": "bromochloromethane",
    "二氯二氟甲烷": "dichlorodifluoromethane", "R12": "dichlorodifluoromethane",
    "三氯氟甲烷": "trichlorofluoromethane", "R11": "trichlorofluoromethane",
    "氯二氟甲烷": "chlorodifluoromethane", "R22": "chlorodifluoromethane",
    "三氯三氟乙烷": "1,1,2-trichlorotrifluoroethane", "R113": "1,1,2-trichlorotrifluoroethane",
    "1,1,2-三氟三氯乙烷": "1,1,2-trichlorotrifluoroethane",
    "R112": "1,2-dichlorotetrafluoroethane",
    "R143a": "1,1,1-trifluoroethane",
    "R124": "2-chloro-1,1,1,2-tetrafluoroethane",
    "R32": "difluoromethane",
    "R125": "pentafluoroethane",
    "R134a": "1,1,1,2-tetrafluoroethane",
    "R152a": "1,1-difluoroethane",
    "R227ea": "heptafluoropropane",
    "R1234ze": "trans-1,3,3,3-tetrafluoropropene",
    "R13": "trichlorofluoromethane",
    "R14": "tetrafluoromethane",
    "R114": "1,2-dichloro-1,1,2,2-tetrafluoroethane",
    "R142b": "1-chloro-1,1-difluoroethane",
    "R123": "2,2-dichloro-1,1,1-trifluoroethane",
    "R245fa": "1,1,1,3,3-pentafluoropropane",
    "R365mfc": "1,1,1,3,3-pentafluorobutane",
    "R1234yf": "2,3,3,3-tetrafluoropropene",
    "R1233zd": "1-chloro-3,3,3-trifluoropropene",
    "R1243zf": "3,3-difluoropropene",
    "R1244zy": "1,1,2,2-tetrafluorocyclobutane",
    "R502": "chlorodifluoromethane",
    "氨": "ammonia",
    "乙酸乙酯": "ethyl acetate",
    "乙酸甲酯": "methyl acetate",
    "甲酸乙酯": "ethyl formate",
    "甲酸甲酯": "methyl formate",
    "丙酸乙酯": "ethyl propionate",
    "丙酸甲酯": "methyl propionate",
    "苯甲酸乙酯": "ethyl benzoate",
    "苯甲酸甲酯": "methyl benzoate",
    "乙酸正丙酯": "propyl acetate",
    "乙酸正丁酯": "butyl acetate",
    "二乙醚": "diethyl ether",
    "乙醚": "diethyl ether",
    "甲基叔丁基醚": "tert-butyl methyl ether", "MTBE": "tert-butyl methyl ether",
    "苯甲醚": "anisole",
    "四氢呋喃": "tetrahydrofuran", "THF": "tetrahydrofuran",
    "1,4-二噁烷": "1,4-dioxane",
    "吡啶": "pyridine",
    "哌啶": "piperidine",
    "吡咯烷": "pyrrolidine",
    "吗啉": "morpholine",
    "苯胺": "aniline",
    "三乙胺": "triethylamine",
    "正丁胺": "butylamine",
    "N-甲基-2-吡咯烷酮": "1-methyl-2-pyrrolidone", "NMP": "1-methyl-2-pyrrolidone",
    "环己胺": "cyclohexylamine",
    "二硫化碳": "carbon disulfide",
    "碳酸二甲酯": "dimethyl carbonate",
    "碳酸二乙酯": "diethyl carbonate",
    "碳酸丙烯酯": "propylene carbonate",
    "乙二醇": "ethylene glycol",
    "1,2-丙二醇": "propylene glycol",
    "1,3-丙二醇": "1,3-propanediol",
    "丙三醇": "glycerol",
    "环己醇": "cyclohexanol",
    "环戊醇": "cyclopentanol",
    "2-甲氧基乙醇": "2-methoxyethanol",
    "二甲基亚砜": "dimethyl sulfoxide", "DMSO": "dimethyl sulfoxide",
    "N,N-二甲基甲酰胺": "dimethylformamide", "DMF": "dimethylformamide",
    "N,N-二甲基乙酰胺": "dimethylacetamide", "DMA": "dimethylacetamide",
    "乙腈": "acetonitrile",
    "硝基苯": "nitrobenzene",
    "氯苯": "chlorobenzene",
    "苯乙酮": "acetophenone",
}

# ============================================================
# 用户指定的体系列表 (来自图片)
# 格式: [(cn1, cn2), ...]
# ============================================================
USER_SYSTEMS = []

def add(syslist, cn1, cn2):
    syslist.append((cn1, cn2))

# 1. 羧酸-脂肪醇、羧酸-芳香烃、芳香羧酸-羧酸
add(USER_SYSTEMS, "甲酸", "水")
add(USER_SYSTEMS, "甲酸", "乙醇")
add(USER_SYSTEMS, "甲酸", "苯")
add(USER_SYSTEMS, "甲酸", "1-丁醇")
add(USER_SYSTEMS, "甲酸", "1-戊醇")
add(USER_SYSTEMS, "甲酸", "1-己醇")
add(USER_SYSTEMS, "甲酸", "1-庚醇")
add(USER_SYSTEMS, "甲酸", "1-辛醇")
add(USER_SYSTEMS, "乙酸", "水")
add(USER_SYSTEMS, "乙酸", "乙醇")
add(USER_SYSTEMS, "乙酸", "苯")
add(USER_SYSTEMS, "乙酸", "1-丁醇")
add(USER_SYSTEMS, "乙酸", "1-戊醇")
add(USER_SYSTEMS, "乙酸", "1-己醇")
add(USER_SYSTEMS, "丙酸", "水")
add(USER_SYSTEMS, "丙酸", "乙醇")
add(USER_SYSTEMS, "丙酸", "1-丁醇")
add(USER_SYSTEMS, "丙酸", "1-戊醇")
add(USER_SYSTEMS, "丙酸", "1-己醇")
add(USER_SYSTEMS, "正丁酸", "水")
add(USER_SYSTEMS, "正丁酸", "乙醇")
add(USER_SYSTEMS, "正丁酸", "苯")
add(USER_SYSTEMS, "正丁酸", "1-丁醇")
add(USER_SYSTEMS, "正丁酸", "1-戊醇")
add(USER_SYSTEMS, "正丁酸", "1-己醇")
add(USER_SYSTEMS, "异丁酸", "水")
add(USER_SYSTEMS, "异丁酸", "苯")
add(USER_SYSTEMS, "正戊酸", "水")
add(USER_SYSTEMS, "正戊酸", "正己烷")
add(USER_SYSTEMS, "正戊酸", "乙醇")
add(USER_SYSTEMS, "正戊酸", "1-丁醇")
add(USER_SYSTEMS, "正戊酸", "1-戊醇")
add(USER_SYSTEMS, "正己酸", "乙醇")
add(USER_SYSTEMS, "正己酸", "对二甲苯")
add(USER_SYSTEMS, "正己酸", "水")
add(USER_SYSTEMS, "正己酸", "1-丁醇")
add(USER_SYSTEMS, "正己酸", "1-戊醇")
add(USER_SYSTEMS, "正己酸", "1-己醇")
add(USER_SYSTEMS, "丙烯酸", "水")
add(USER_SYSTEMS, "丙烯酸", "异辛烷")
add(USER_SYSTEMS, "丙烯酸", "1-丁醇")
add(USER_SYSTEMS, "丙烯酸", "1-戊醇")
add(USER_SYSTEMS, "丙烯酸", "1-己醇")
add(USER_SYSTEMS, "苯甲酸", "苯")
add(USER_SYSTEMS, "苯甲酸", "乙醇")
add(USER_SYSTEMS, "苯甲酸", "水")
add(USER_SYSTEMS, "苯甲酸", "1-丁醇")
add(USER_SYSTEMS, "苯甲酸", "1-戊醇")
add(USER_SYSTEMS, "苯甲酸", "1-己醇")

# 2. 酸、酮、酯与芳香烃
add(USER_SYSTEMS, "丙酮", "环己烷")
add(USER_SYSTEMS, "丙酮", "己烷")
add(USER_SYSTEMS, "丙酮", "庚烷")
add(USER_SYSTEMS, "丙酮", "苯")
add(USER_SYSTEMS, "丙酮", "甲苯")
add(USER_SYSTEMS, "丙酮", "氯苯")
add(USER_SYSTEMS, "乙酸乙酯", "环己烷")
add(USER_SYSTEMS, "乙酸乙酯", "己烷")
add(USER_SYSTEMS, "乙酸乙酯", "庚烷")
add(USER_SYSTEMS, "乙酸乙酯", "苯")
add(USER_SYSTEMS, "乙酸乙酯", "甲苯")
add(USER_SYSTEMS, "乙酸乙酯", "二甲苯")
add(USER_SYSTEMS, "乙酸乙酯", "氯苯")
add(USER_SYSTEMS, "甲酸甲酯", "苯")
add(USER_SYSTEMS, "甲酸乙酯", "苯")
add(USER_SYSTEMS, "丙酸乙酯", "苯")
add(USER_SYSTEMS, "苯甲酸甲酯", "苯")
add(USER_SYSTEMS, "苯甲酸乙酯", "苯")
add(USER_SYSTEMS, "二乙醚", "苯")
add(USER_SYSTEMS, "二乙醚", "环己烷")
add(USER_SYSTEMS, "二乙醚", "庚烷")
add(USER_SYSTEMS, "二乙醚", "氯苯")
add(USER_SYSTEMS, "二乙醚", "乙酸乙酯")
add(USER_SYSTEMS, "氯仿", "苯")
add(USER_SYSTEMS, "氯仿", "甲苯")
add(USER_SYSTEMS, "氯仿", "氯苯")
add(USER_SYSTEMS, "四氯化碳", "苯")
add(USER_SYSTEMS, "四氯化碳", "环己烷")
add(USER_SYSTEMS, "四氯化碳", "庚烷")
add(USER_SYSTEMS, "1,2-二氯乙烷", "苯")
add(USER_SYSTEMS, "1,2-二氯乙烷", "环己烷")
add(USER_SYSTEMS, "1,2-二氯乙烷", "庚烷")
add(USER_SYSTEMS, "1,2-二氯乙烷", "氯苯")
add(USER_SYSTEMS, "1,2-二氯乙烷", "甲苯")
add(USER_SYSTEMS, "二硫化碳", "苯")
add(USER_SYSTEMS, "二硫化碳", "环己烷")
add(USER_SYSTEMS, "二硫化碳", "庚烷")
add(USER_SYSTEMS, "二硫化碳", "氯仿")
add(USER_SYSTEMS, "二硫化碳", "乙醚")
add(USER_SYSTEMS, "苯", "环己烷")
add(USER_SYSTEMS, "苯", "庚烷")
add(USER_SYSTEMS, "苯", "甲苯")
add(USER_SYSTEMS, "苯", "氯苯")
add(USER_SYSTEMS, "环己烷", "庚烷")
add(USER_SYSTEMS, "环己烷", "甲苯")
add(USER_SYSTEMS, "环己烷", "氯苯")
add(USER_SYSTEMS, "庚烷", "甲苯")
add(USER_SYSTEMS, "庚烷", "氯苯")
add(USER_SYSTEMS, "四氢呋喃", "水")
add(USER_SYSTEMS, "四氢呋喃", "乙醇")
add(USER_SYSTEMS, "四氢呋喃", "苯")

# 3. 酯与醇、醚类及芳香烃
add(USER_SYSTEMS, "乙酸乙酯", "1-丁醇")
add(USER_SYSTEMS, "乙酸乙酯", "1-戊醇")
add(USER_SYSTEMS, "乙酸乙酯", "1-己醇")
add(USER_SYSTEMS, "乙酸乙酯", "1-庚醇")
add(USER_SYSTEMS, "乙酸乙酯", "1-辛醇")
add(USER_SYSTEMS, "乙酸乙酯", "水")
add(USER_SYSTEMS, "乙酸乙酯", "乙醇")
add(USER_SYSTEMS, "乙酸甲酯", "1-丁醇")
add(USER_SYSTEMS, "乙酸甲酯", "乙醇")
add(USER_SYSTEMS, "甲酸乙酯", "乙醇")
add(USER_SYSTEMS, "甲酸乙酯", "1-丁醇")
add(USER_SYSTEMS, "丙酸乙酯", "1-丁醇")
add(USER_SYSTEMS, "丙酸乙酯", "1-戊醇")
add(USER_SYSTEMS, "丙酸甲酯", "1-丁醇")
add(USER_SYSTEMS, "苯甲酸乙酯", "乙醇")
add(USER_SYSTEMS, "苯甲酸乙酯", "1-丁醇")
add(USER_SYSTEMS, "苯甲酸甲酯", "乙醇")
add(USER_SYSTEMS, "苯甲酸甲酯", "1-丁醇")
add(USER_SYSTEMS, "二乙醚", "1-丁醇")
add(USER_SYSTEMS, "二乙醚", "1-戊醇")
add(USER_SYSTEMS, "二乙醚", "1-己醇")
add(USER_SYSTEMS, "二乙醚", "水")
add(USER_SYSTEMS, "二乙醚", "乙醇")
add(USER_SYSTEMS, "甲基叔丁基醚", "1-丁醇")
add(USER_SYSTEMS, "甲基叔丁基醚", "水")
add(USER_SYSTEMS, "甲基叔丁基醚", "环己烷")
add(USER_SYSTEMS, "甲基叔丁基醚", "苯")
add(USER_SYSTEMS, "苯甲醚", "环己烷")
add(USER_SYSTEMS, "苯甲醚", "苯")
add(USER_SYSTEMS, "四氢呋喃", "1-丁醇")
add(USER_SYSTEMS, "四氢呋喃", "1-戊醇")
add(USER_SYSTEMS, "四氢呋喃", "乙醇")
add(USER_SYSTEMS, "四氢呋喃", "苯")
add(USER_SYSTEMS, "四氢呋喃", "环己烷")
add(USER_SYSTEMS, "1,4-二噁烷", "水")
add(USER_SYSTEMS, "1,4-二噁烷", "乙醇")
add(USER_SYSTEMS, "1,4-二噁烷", "苯")
add(USER_SYSTEMS, "1,4-二噁烷", "环己烷")

# 4. 酮、醛、胺等杂环体系
add(USER_SYSTEMS, "丙酮", "水")
add(USER_SYSTEMS, "丙酮", "乙醇")
add(USER_SYSTEMS, "丙酮", "1-丁醇")
add(USER_SYSTEMS, "丙酮", "氯苯")
add(USER_SYSTEMS, "丙酮", "庚烷")
add(USER_SYSTEMS, "丁酮", "水")
add(USER_SYSTEMS, "丁酮", "乙醇")
add(USER_SYSTEMS, "丁酮", "1-丁醇")
add(USER_SYSTEMS, "丁酮", "苯")
add(USER_SYSTEMS, "丁酮", "甲苯")
add(USER_SYSTEMS, "丁酮", "氯苯")
add(USER_SYSTEMS, "丁酮", "环己烷")
add(USER_SYSTEMS, "丁酮", "庚烷")
add(USER_SYSTEMS, "环己酮", "水")
add(USER_SYSTEMS, "环己酮", "乙醇")
add(USER_SYSTEMS, "环己酮", "1-丁醇")
add(USER_SYSTEMS, "环己酮", "苯")
add(USER_SYSTEMS, "环己酮", "环己烷")
add(USER_SYSTEMS, "环己酮", "庚烷")
add(USER_SYSTEMS, "甲醛", "水")
add(USER_SYSTEMS, "甲醛", "乙醇")
add(USER_SYSTEMS, "乙醛", "水")
add(USER_SYSTEMS, "乙醛", "乙醇")
add(USER_SYSTEMS, "丙醛", "水")
add(USER_SYSTEMS, "丙醛", "乙醇")
add(USER_SYSTEMS, "吡啶", "水")
add(USER_SYSTEMS, "吡啶", "乙醇")
add(USER_SYSTEMS, "吡啶", "1-丁醇")
add(USER_SYSTEMS, "吡啶", "苯")
add(USER_SYSTEMS, "吡啶", "环己烷")
add(USER_SYSTEMS, "吡啶", "庚烷")
add(USER_SYSTEMS, "吡啶", "氯苯")
add(USER_SYSTEMS, "哌啶", "水")
add(USER_SYSTEMS, "哌啶", "乙醇")
add(USER_SYSTEMS, "哌啶", "苯")
add(USER_SYSTEMS, "吡咯烷", "水")
add(USER_SYSTEMS, "吡咯烷", "乙醇")
add(USER_SYSTEMS, "吗啉", "水")
add(USER_SYSTEMS, "吗啉", "乙醇")
add(USER_SYSTEMS, "吗啉", "苯")
add(USER_SYSTEMS, "苯胺", "水")
add(USER_SYSTEMS, "苯胺", "乙醇")
add(USER_SYSTEMS, "苯胺", "1-丁醇")
add(USER_SYSTEMS, "苯胺", "苯")
add(USER_SYSTEMS, "苯胺", "环己烷")
add(USER_SYSTEMS, "苯胺", "氯苯")
add(USER_SYSTEMS, "三乙胺", "水")
add(USER_SYSTEMS, "三乙胺", "乙醇")
add(USER_SYSTEMS, "三乙胺", "苯")
add(USER_SYSTEMS, "三乙胺", "环己烷")
add(USER_SYSTEMS, "正丁胺", "水")
add(USER_SYSTEMS, "正丁胺", "乙醇")
add(USER_SYSTEMS, "正丁胺", "苯")

# 碳酸盐体系
add(USER_SYSTEMS, "碳酸二甲酯", "水")
add(USER_SYSTEMS, "碳酸二甲酯", "乙醇")
add(USER_SYSTEMS, "碳酸二甲酯", "1-丁醇")
add(USER_SYSTEMS, "碳酸二甲酯", "苯")
add(USER_SYSTEMS, "碳酸二乙酯", "水")
add(USER_SYSTEMS, "碳酸二乙酯", "乙醇")
add(USER_SYSTEMS, "碳酸二乙酯", "1-丁醇")
add(USER_SYSTEMS, "碳酸二乙酯", "苯")
add(USER_SYSTEMS, "碳酸丙烯酯", "水")
add(USER_SYSTEMS, "碳酸丙烯酯", "乙醇")
add(USER_SYSTEMS, "碳酸丙烯酯", "1-丁醇")

# 5. 卤代烃体系
add(USER_SYSTEMS, "二氯甲烷", "水")
add(USER_SYSTEMS, "二氯甲烷", "乙醇")
add(USER_SYSTEMS, "二氯甲烷", "1-丁醇")
add(USER_SYSTEMS, "二氯甲烷", "苯")
add(USER_SYSTEMS, "二氯甲烷", "环己烷")
add(USER_SYSTEMS, "二氯甲烷", "庚烷")
add(USER_SYSTEMS, "二氯甲烷", "甲苯")
add(USER_SYSTEMS, "二氯甲烷", "氯苯")
add(USER_SYSTEMS, "二氯甲烷", "乙酸乙酯")
add(USER_SYSTEMS, "氯仿", "水")
add(USER_SYSTEMS, "氯仿", "乙醇")
add(USER_SYSTEMS, "氯仿", "1-丁醇")
add(USER_SYSTEMS, "氯仿", "苯")
add(USER_SYSTEMS, "氯仿", "环己烷")
add(USER_SYSTEMS, "氯仿", "庚烷")
add(USER_SYSTEMS, "氯仿", "甲苯")
add(USER_SYSTEMS, "氯仿", "氯苯")
add(USER_SYSTEMS, "氯仿", "乙酸乙酯")
add(USER_SYSTEMS, "四氯化碳", "水")
add(USER_SYSTEMS, "四氯化碳", "乙醇")
add(USER_SYSTEMS, "四氯化碳", "1-丁醇")
add(USER_SYSTEMS, "四氯化碳", "苯")
add(USER_SYSTEMS, "四氯化碳", "甲苯")
add(USER_SYSTEMS, "四氯化碳", "氯苯")
add(USER_SYSTEMS, "1,2-二氯乙烷", "水")
add(USER_SYSTEMS, "1,2-二氯乙烷", "乙醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "1-丁醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "乙酸乙酯")
add(USER_SYSTEMS, "二溴甲烷", "水")
add(USER_SYSTEMS, "二溴甲烷", "乙醇")
add(USER_SYSTEMS, "三溴甲烷", "水")
add(USER_SYSTEMS, "三溴甲烷", "乙醇")
add(USER_SYSTEMS, "三溴甲烷", "苯")
add(USER_SYSTEMS, "溴氯甲烷", "水")
add(USER_SYSTEMS, "溴氯甲烷", "乙醇")

# 6. 含氟体系
add(USER_SYSTEMS, "R22", "R13")
add(USER_SYSTEMS, "R22", "R143a")
add(USER_SYSTEMS, "R32", "R125")
add(USER_SYSTEMS, "R32", "R134a")
add(USER_SYSTEMS, "R125", "R134a")
add(USER_SYSTEMS, "R125", "R143a")
add(USER_SYSTEMS, "R143a", "R134a")
add(USER_SYSTEMS, "R143a", "R227ea")
add(USER_SYSTEMS, "R134a", "R227ea")
add(USER_SYSTEMS, "R1234ze", "R32")
add(USER_SYSTEMS, "R1234ze", "R125")
add(USER_SYSTEMS, "R1234ze", "R134a")
add(USER_SYSTEMS, "R12", "R13")
add(USER_SYSTEMS, "R12", "R22")
add(USER_SYSTEMS, "R12", "R114")
add(USER_SYSTEMS, "R13", "R143a")
add(USER_SYSTEMS, "R22", "R114")

# 烷烃+氟利昂
add(USER_SYSTEMS, "甲烷", "R22")
add(USER_SYSTEMS, "乙烷", "R22")
add(USER_SYSTEMS, "丙烷", "R13")
add(USER_SYSTEMS, "丙烷", "R22")
add(USER_SYSTEMS, "丙烷", "R143a")
add(USER_SYSTEMS, "丁烷", "R13")
add(USER_SYSTEMS, "丁烷", "R22")
add(USER_SYSTEMS, "丁烷", "R143a")
add(USER_SYSTEMS, "戊烷", "R143a")
add(USER_SYSTEMS, "己烷", "R13")
add(USER_SYSTEMS, "辛烷", "R13")
add(USER_SYSTEMS, "辛烷", "R22")
add(USER_SYSTEMS, "辛烷", "R143a")
add(USER_SYSTEMS, "环己烷", "R13")
add(USER_SYSTEMS, "环己烷", "R22")
add(USER_SYSTEMS, "苯", "R13")
add(USER_SYSTEMS, "苯", "R22")
add(USER_SYSTEMS, "苯", "R143a")
add(USER_SYSTEMS, "甲苯", "R13")
add(USER_SYSTEMS, "甲苯", "R22")
add(USER_SYSTEMS, "甲苯", "R143a")
add(USER_SYSTEMS, "氯仿", "R13")
add(USER_SYSTEMS, "氯仿", "R22")
add(USER_SYSTEMS, "氯仿", "R143a")
add(USER_SYSTEMS, "四氯化碳", "R13")
add(USER_SYSTEMS, "四氯化碳", "R22")
add(USER_SYSTEMS, "四氯化碳", "R143a")
add(USER_SYSTEMS, "乙醇", "R13")
add(USER_SYSTEMS, "乙醇", "R22")
add(USER_SYSTEMS, "乙醇", "R143a")
add(USER_SYSTEMS, "正丙醇", "R13")
add(USER_SYSTEMS, "正丙醇", "R22")
add(USER_SYSTEMS, "正丙醇", "R143a")
add(USER_SYSTEMS, "正丁醇", "R13")
add(USER_SYSTEMS, "正丁醇", "R22")
add(USER_SYSTEMS, "正丁醇", "R143a")
add(USER_SYSTEMS, "丙酮", "R13")
add(USER_SYSTEMS, "丙酮", "R22")
add(USER_SYSTEMS, "丙酮", "R143a")

# 7. 低凝固点 VLE
add(USER_SYSTEMS, "水", "R13")
add(USER_SYSTEMS, "水", "R22")
add(USER_SYSTEMS, "甲醇", "R13")
add(USER_SYSTEMS, "甲醇", "R22")
add(USER_SYSTEMS, "正戊醇", "R13")
add(USER_SYSTEMS, "正戊醇", "R22")
add(USER_SYSTEMS, "正己烷", "R13")
add(USER_SYSTEMS, "正己烷", "R22")
add(USER_SYSTEMS, "正己烷", "苯")
add(USER_SYSTEMS, "正己烷", "甲苯")
add(USER_SYSTEMS, "正己烷", "氯仿")
add(USER_SYSTEMS, "正己烷", "四氯化碳")
add(USER_SYSTEMS, "正己烷", "二氯甲烷")
add(USER_SYSTEMS, "正己烷", "乙酸乙酯")
add(USER_SYSTEMS, "正己烷", "丙酮")
add(USER_SYSTEMS, "正庚烷", "苯")
add(USER_SYSTEMS, "正庚烷", "甲苯")
add(USER_SYSTEMS, "正庚烷", "氯仿")
add(USER_SYSTEMS, "正庚烷", "四氯化碳")
add(USER_SYSTEMS, "正庚烷", "二氯甲烷")
add(USER_SYSTEMS, "正庚烷", "乙酸乙酯")
add(USER_SYSTEMS, "正庚烷", "丙酮")
add(USER_SYSTEMS, "正辛烷", "苯")
add(USER_SYSTEMS, "正辛烷", "甲苯")
add(USER_SYSTEMS, "正辛烷", "氯仿")
add(USER_SYSTEMS, "正辛烷", "四氯化碳")
add(USER_SYSTEMS, "正辛烷", "二氯甲烷")
add(USER_SYSTEMS, "正辛烷", "乙酸乙酯")
add(USER_SYSTEMS, "正辛烷", "丙酮")
add(USER_SYSTEMS, "环己烷", "氯仿")
add(USER_SYSTEMS, "环己烷", "四氯化碳")
add(USER_SYSTEMS, "环己烷", "二氯甲烷")
add(USER_SYSTEMS, "环己烷", "乙酸乙酯")
add(USER_SYSTEMS, "环己烷", "丙酮")

# 8. DECHEMA 核心体系
add(USER_SYSTEMS, "水", "乙醇")
add(USER_SYSTEMS, "水", "1-丙醇")
add(USER_SYSTEMS, "水", "2-丙醇")
add(USER_SYSTEMS, "水", "1-丁醇")
add(USER_SYSTEMS, "水", "2-丁醇")
add(USER_SYSTEMS, "水", "1-戊醇")
add(USER_SYSTEMS, "水", "2-戊醇")
add(USER_SYSTEMS, "水", "1-己醇")
add(USER_SYSTEMS, "水", "2-己醇")
add(USER_SYSTEMS, "水", "正己烷")
add(USER_SYSTEMS, "水", "正庚烷")
add(USER_SYSTEMS, "水", "正辛烷")
add(USER_SYSTEMS, "水", "环己烷")
add(USER_SYSTEMS, "水", "苯")
add(USER_SYSTEMS, "水", "甲苯")
add(USER_SYSTEMS, "水", "二甲苯")
add(USER_SYSTEMS, "水", "氯仿")
add(USER_SYSTEMS, "水", "四氯化碳")
add(USER_SYSTEMS, "水", "1,2-二氯乙烷")
add(USER_SYSTEMS, "水", "乙酸乙酯")
add(USER_SYSTEMS, "水", "丙酮")
add(USER_SYSTEMS, "水", "乙醚")
add(USER_SYSTEMS, "水", "四氢呋喃")
add(USER_SYSTEMS, "水", "吡啶")
add(USER_SYSTEMS, "水", "苯胺")
add(USER_SYSTEMS, "水", "甲酸")
add(USER_SYSTEMS, "水", "乙酸")
add(USER_SYSTEMS, "水", "丙酸")
add(USER_SYSTEMS, "水", "正丁酸")
add(USER_SYSTEMS, "水", "丙烯酸")
add(USER_SYSTEMS, "水", "苯甲酸")
add(USER_SYSTEMS, "水", "碳酸二乙酯")

# 乙醇体系
add(USER_SYSTEMS, "乙醇", "1-丙醇")
add(USER_SYSTEMS, "乙醇", "2-丙醇")
add(USER_SYSTEMS, "乙醇", "1-丁醇")
add(USER_SYSTEMS, "乙醇", "2-丁醇")
add(USER_SYSTEMS, "乙醇", "1-戊醇")
add(USER_SYSTEMS, "乙醇", "2-戊醇")
add(USER_SYSTEMS, "乙醇", "1-己醇")
add(USER_SYSTEMS, "乙醇", "正己烷")
add(USER_SYSTEMS, "乙醇", "正庚烷")
add(USER_SYSTEMS, "乙醇", "正辛烷")
add(USER_SYSTEMS, "乙醇", "环己烷")
add(USER_SYSTEMS, "乙醇", "苯")
add(USER_SYSTEMS, "乙醇", "甲苯")
add(USER_SYSTEMS, "乙醇", "二甲苯")
add(USER_SYSTEMS, "乙醇", "乙酸乙酯")
add(USER_SYSTEMS, "乙醇", "丙酮")
add(USER_SYSTEMS, "乙醇", "乙醚")
add(USER_SYSTEMS, "乙醇", "四氢呋喃")
add(USER_SYSTEMS, "乙醇", "吡啶")
add(USER_SYSTEMS, "乙醇", "苯胺")
add(USER_SYSTEMS, "乙醇", "碳酸二甲酯")
add(USER_SYSTEMS, "乙醇", "甲基叔丁基醚")

# 乙酸乙酯体系
add(USER_SYSTEMS, "乙酸乙酯", "甲酸")
add(USER_SYSTEMS, "乙酸乙酯", "丙酸")
add(USER_SYSTEMS, "乙酸乙酯", "正丁酸")
add(USER_SYSTEMS, "乙酸乙酯", "正戊酸")
add(USER_SYSTEMS, "乙酸乙酯", "苯甲酸")
add(USER_SYSTEMS, "乙酸乙酯", "丙烯酸")
add(USER_SYSTEMS, "乙酸乙酯", "2-丁酮")
add(USER_SYSTEMS, "乙酸乙酯", "苯乙酮")
add(USER_SYSTEMS, "乙酸乙酯", "1-丙醇")
add(USER_SYSTEMS, "乙酸乙酯", "2-丙醇")
add(USER_SYSTEMS, "乙酸乙酯", "2-丁醇")
add(USER_SYSTEMS, "乙酸乙酯", "正己烷")
add(USER_SYSTEMS, "乙酸乙酯", "正庚烷")
add(USER_SYSTEMS, "乙酸乙酯", "正辛烷")
add(USER_SYSTEMS, "乙酸乙酯", "二氯甲烷")
add(USER_SYSTEMS, "乙酸乙酯", "1,2-二氯乙烷")
add(USER_SYSTEMS, "乙酸乙酯", "乙醚")
add(USER_SYSTEMS, "乙酸乙酯", "四氢呋喃")
add(USER_SYSTEMS, "乙酸乙酯", "吡啶")
add(USER_SYSTEMS, "乙酸乙酯", "氯苯")

# 补充
add(USER_SYSTEMS, "甲醇", "R143a")
add(USER_SYSTEMS, "甲醇", "碳酸二甲酯")
add(USER_SYSTEMS, "甲醇", "R22")
add(USER_SYSTEMS, "丁烷", "乙醇")
add(USER_SYSTEMS, "二氧化碳", "丙烷")
add(USER_SYSTEMS, "二氧化碳", "1-辛醇")
add(USER_SYSTEMS, "氮气", "庚烷")
add(USER_SYSTEMS, "氩气", "二氧化碳")
add(USER_SYSTEMS, "一氧化碳", "二氧化碳")
add(USER_SYSTEMS, "1-己烯", "R13")
add(USER_SYSTEMS, "1-己烯", "R22")
add(USER_SYSTEMS, "1-己烯", "苯")
add(USER_SYSTEMS, "1-己烯", "甲苯")
add(USER_SYSTEMS, "1-己烯", "氯仿")
add(USER_SYSTEMS, "1-己烯", "乙酸乙酯")
add(USER_SYSTEMS, "1-己烯", "丙酮")
add(USER_SYSTEMS, "1-己烯", "己烷")
add(USER_SYSTEMS, "1-己烯", "庚烷")
add(USER_SYSTEMS, "1-己烯", "辛烷")

# 正丁醇体系
add(USER_SYSTEMS, "1-丁醇", "苯")
add(USER_SYSTEMS, "1-丁醇", "甲苯")
add(USER_SYSTEMS, "1-丁醇", "二甲苯")
add(USER_SYSTEMS, "1-丁醇", "环己烷")
add(USER_SYSTEMS, "1-丁醇", "正己烷")
add(USER_SYSTEMS, "1-丁醇", "正庚烷")
add(USER_SYSTEMS, "1-丁醇", "氯仿")
add(USER_SYSTEMS, "1-丁醇", "二氯甲烷")
add(USER_SYSTEMS, "1-丁醇", "四氯化碳")
add(USER_SYSTEMS, "1-丁醇", "1,2-二氯乙烷")
add(USER_SYSTEMS, "1-丁醇", "丙酮")
add(USER_SYSTEMS, "1-丁醇", "乙酸甲酯")
add(USER_SYSTEMS, "1-丁醇", "甲酸乙酯")
add(USER_SYSTEMS, "1-丁醇", "丙酸乙酯")
add(USER_SYSTEMS, "1-丁醇", "甲酸")
add(USER_SYSTEMS, "1-丁醇", "乙酸")
add(USER_SYSTEMS, "1-丁醇", "丙酸")
add(USER_SYSTEMS, "1-丁醇", "正丁酸")
add(USER_SYSTEMS, "1-丁醇", "正戊酸")
add(USER_SYSTEMS, "1-丁醇", "正己酸")
add(USER_SYSTEMS, "1-丁醇", "苯甲酸")
add(USER_SYSTEMS, "1-丁醇", "丙烯酸")

# 正戊醇体系
add(USER_SYSTEMS, "1-戊醇", "苯")
add(USER_SYSTEMS, "1-戊醇", "环己烷")
add(USER_SYSTEMS, "1-戊醇", "正己烷")
add(USER_SYSTEMS, "1-戊醇", "氯仿")
add(USER_SYSTEMS, "1-戊醇", "二氯甲烷")
add(USER_SYSTEMS, "1-戊醇", "四氯化碳")
add(USER_SYSTEMS, "1-戊醇", "丙酮")
add(USER_SYSTEMS, "1-戊醇", "甲酸乙酯")
add(USER_SYSTEMS, "1-戊醇", "乙酸乙酯")
add(USER_SYSTEMS, "1-戊醇", "甲酸")
add(USER_SYSTEMS, "1-戊醇", "乙酸")
add(USER_SYSTEMS, "1-戊醇", "丙酸")
add(USER_SYSTEMS, "1-戊醇", "苯甲酸")
add(USER_SYSTEMS, "1-戊醇", "丙烯酸")

# 1-己醇体系
add(USER_SYSTEMS, "1-己醇", "苯")
add(USER_SYSTEMS, "1-己醇", "环己烷")
add(USER_SYSTEMS, "1-己醇", "正己烷")
add(USER_SYSTEMS, "1-己醇", "氯仿")
add(USER_SYSTEMS, "1-己醇", "二氯甲烷")
add(USER_SYSTEMS, "1-己醇", "丙酮")
add(USER_SYSTEMS, "1-己醇", "乙酸乙酯")
add(USER_SYSTEMS, "1-己醇", "乙酸")

# 补充 DECHEMA
add(USER_SYSTEMS, "水", "甲酸乙酯")
add(USER_SYSTEMS, "水", "丙酸乙酯")
add(USER_SYSTEMS, "水", "苯甲酸甲酯")
add(USER_SYSTEMS, "水", "苯甲酸乙酯")
add(USER_SYSTEMS, "水", "苯甲醚")
add(USER_SYSTEMS, "乙醇", "2-戊醇")
add(USER_SYSTEMS, "乙醇", "1-己醇")
add(USER_SYSTEMS, "乙醇", "2-己醇")
add(USER_SYSTEMS, "乙醇", "1-辛醇")
add(USER_SYSTEMS, "乙醇", "2-辛醇")
add(USER_SYSTEMS, "乙醇", "正己烷")
add(USER_SYSTEMS, "乙醇", "1-辛烷")
add(USER_SYSTEMS, "乙醇", "二甲苯")
add(USER_SYSTEMS, "乙醇", "1,2-二氯乙烷")
add(USER_SYSTEMS, "乙醇", "甲酸乙酯")
add(USER_SYSTEMS, "乙醇", "丙酸乙酯")
add(USER_SYSTEMS, "乙醇", "苯甲酸甲酯")
add(USER_SYSTEMS, "乙醇", "苯甲酸乙酯")
add(USER_SYSTEMS, "乙醇", "环己醇")
add(USER_SYSTEMS, "乙醇", "环戊醇")
add(USER_SYSTEMS, "乙醇", "2-丁酮")
add(USER_SYSTEMS, "乙醇", "2-戊酮")
add(USER_SYSTEMS, "乙醇", "2-己酮")
add(USER_SYSTEMS, "乙醇", "2-庚酮")
add(USER_SYSTEMS, "乙醇", "3-戊酮")
add(USER_SYSTEMS, "乙醇", "1,2-丙二醇")

# 二氯甲烷体系
add(USER_SYSTEMS, "二氯甲烷", "1-丙醇")
add(USER_SYSTEMS, "二氯甲烷", "2-丙醇")
add(USER_SYSTEMS, "二氯甲烷", "2-丁醇")
add(USER_SYSTEMS, "二氯甲烷", "1-戊醇")
add(USER_SYSTEMS, "二氯甲烷", "1-己醇")
add(USER_SYSTEMS, "二氯甲烷", "正己烷")
add(USER_SYSTEMS, "二氯甲烷", "正庚烷")
add(USER_SYSTEMS, "二氯甲烷", "正辛烷")
add(USER_SYSTEMS, "二氯甲烷", "丙酮")
add(USER_SYSTEMS, "二氯甲烷", "乙醚")
add(USER_SYSTEMS, "二氯甲烷", "甲酸乙酯")
add(USER_SYSTEMS, "二氯甲烷", "乙酸乙酯")

# 氯仿体系补充
add(USER_SYSTEMS, "氯仿", "1-丙醇")
add(USER_SYSTEMS, "氯仿", "2-丙醇")
add(USER_SYSTEMS, "氯仿", "1-戊醇")
add(USER_SYSTEMS, "氯仿", "正己烷")
add(USER_SYSTEMS, "氯仿", "正庚烷")
add(USER_SYSTEMS, "氯仿", "正辛烷")
add(USER_SYSTEMS, "氯仿", "丙酮")
add(USER_SYSTEMS, "氯仿", "乙醚")
add(USER_SYSTEMS, "氯仿", "四氢呋喃")

# 四氯化碳补充
add(USER_SYSTEMS, "四氯化碳", "1-戊醇")

# 正己烷体系
add(USER_SYSTEMS, "正己烷", "1-丁醇")
add(USER_SYSTEMS, "正己烷", "2-丁醇")
add(USER_SYSTEMS, "正己烷", "1-戊醇")
add(USER_SYSTEMS, "正己烷", "环己醇")
add(USER_SYSTEMS, "正己烷", "四氢呋喃")
add(USER_SYSTEMS, "正己烷", "1,2-二氯乙烷")
add(USER_SYSTEMS, "正己烷", "甲酸乙酯")
add(USER_SYSTEMS, "正己烷", "苯甲酸甲酯")

# 1,2-二氯乙烷补充
add(USER_SYSTEMS, "1,2-二氯乙烷", "1-丙醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "2-丙醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "2-丁醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "1-戊醇")
add(USER_SYSTEMS, "1,2-二氯乙烷", "正辛烷")

# 补充其他
add(USER_SYSTEMS, "甲酸", "乙酸乙酯")
add(USER_SYSTEMS, "乙酸", "乙酸乙酯")
add(USER_SYSTEMS, "丙酸", "乙酸乙酯")
add(USER_SYSTEMS, "正丁酸", "乙酸乙酯")
add(USER_SYSTEMS, "苯甲酸", "乙酸乙酯")
add(USER_SYSTEMS, "丙烯酸", "乙酸乙酯")
add(USER_SYSTEMS, "乙酸乙酯", "1-庚醇")
add(USER_SYSTEMS, "乙酸乙酯", "1-辛醇")
add(USER_SYSTEMS, "乙酸乙酯", "2-丁酮")
add(USER_SYSTEMS, "乙酸乙酯", "3-戊酮")

# 硝基苯
add(USER_SYSTEMS, "硝基苯", "水")
add(USER_SYSTEMS, "硝基苯", "乙醇")
add(USER_SYSTEMS, "硝基苯", "苯")

# 乙腈
add(USER_SYSTEMS, "乙腈", "水")
add(USER_SYSTEMS, "乙腈", "乙醇")
add(USER_SYSTEMS, "乙腈", "苯")
add(USER_SYSTEMS, "乙腈", "甲苯")

# 甘油
add(USER_SYSTEMS, "甘油", "水")
add(USER_SYSTEMS, "甘油", "乙醇")

# 乙二醇
add(USER_SYSTEMS, "乙二醇", "水")
add(USER_SYSTEMS, "乙二醇", "乙醇")

# 1,2-丙二醇
add(USER_SYSTEMS, "1,2-丙二醇", "水")
add(USER_SYSTEMS, "1,2-丙二醇", "乙醇")

# 苯乙酮
add(USER_SYSTEMS, "苯乙酮", "水")
add(USER_SYSTEMS, "苯乙酮", "乙醇")
add(USER_SYSTEMS, "苯乙酮", "苯")
add(USER_SYSTEMS, "苯乙酮", "环己烷")

# 其他补充
add(USER_SYSTEMS, "水", "N-甲基-2-吡咯烷酮")
add(USER_SYSTEMS, "乙醇", "N-甲基-2-吡咯烷酮")
add(USER_SYSTEMS, "水", "二甲基亚砜")
add(USER_SYSTEMS, "乙醇", "二甲基亚砜")
add(USER_SYSTEMS, "水", "二硫化碳")
add(USER_SYSTEMS, "乙醇", "二硫化碳")

# 异辛烷
add(USER_SYSTEMS, "异辛烷", "水")
add(USER_SYSTEMS, "异辛烷", "乙醇")
add(USER_SYSTEMS, "异辛烷", "苯")

# 双环萜
add(USER_SYSTEMS, "双环萜", "水")
add(USER_SYSTEMS, "双环萜", "乙醇")


# ============================================================
# 工具函数
# ============================================================

def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        try:
            return float(str(v).split("..")[0].strip())
        except Exception:
            return default


def cn_to_en(cn):
    """中文 → ThermoML 英文名。"""
    cn_norm = cn.strip()
    if cn_norm in CN_TO_EN:
        return CN_TO_EN[cn_norm]
    # 尝试小写
    cn_lower = cn_norm.lower()
    for k, v in CN_TO_EN.items():
        if k.lower() == cn_lower:
            return v
    return None


def match_system_in_thermoml(cn1, cn2, df):
    """在 ThermoML 数据中查找指定体系。"""
    en1 = cn_to_en(cn1)
    en2 = cn_to_en(cn2)
    if en1 is None or en2 is None:
        return None

    # 查找 (en1, en2) 或 (en2, en1)
    mask1 = (df["名称1"] == en1) & (df["名称2"] == en2)
    mask2 = (df["名称1"] == en2) & (df["名称2"] == en1)
    sub = df[mask1 | mask2].copy()
    if len(sub) == 0:
        return None
    return sub


def make_filename(cn1, cn2):
    safe = f"{cn1}_{cn2}".replace("/", "-").replace(" ", "_").replace("+", "_plus_")
    safe = re.sub(r'[\\/:*?"<>|]', '_', safe)
    if len(safe) > 190:
        safe = safe[:190]
    return safe + ".xlsx"


def main():
    print("读取 ThermoML VLE 数据 ...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"  共 {len(df)} 行, {df['DOI'].nunique()} 篇文献")

    # 加载 SMILES 缓存
    cache = {}
    if SMILES_CACHE.exists():
        cache = json.loads(SMILES_CACHE.read_text(encoding="utf-8"))

    # 预处理: 补充 smiles
    df["smiles1"] = df["名称1"].map(lambda x: cache.get(x, ""))
    df["smiles2"] = df["名称2"].map(lambda x: cache.get(x, ""))

    # 加载 Antoine 参数和做一致性检验
    from _export_by_system import antoine_p_sat, fredenslund_test, herington_test, legendre_poly, legendre_deriv

    # 按体系做一致性检验 (对所有体系)
    print("\n对所有体系做 Fredenslund + Herington 检验 ...")
    sys_groups = df.groupby(["名称1","名称2"])
    sys_results = {}
    for i, ((n1, n2), g) in enumerate(sys_groups, 1):
        x1 = g["X1"].apply(_safe_float).values
        y1 = g["Y1"].apply(_safe_float).values
        T = g["温度"].apply(_safe_float).values
        P = g["压强"].apply(_safe_float).values
        G = fredenslund_test(x1, y1, T, P, n1, n2)
        H = herington_test(x1, y1, T, P, n1, n2)
        sys_results[(n1, n2)] = (G, H)
        if i % 200 == 0:
            print(f"    进度 {i}/{len(sys_groups)}")

    df["一致性检验方法一"] = df.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[0], axis=1)
    df["一致性检验方法二"] = df.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[1], axis=1)
    print(f"  检验完成")

    # 清洗
    df = df.dropna(subset=["压强","温度","X1","Y1"]).copy()
    df = df[(df["X1"]>=0)&(df["X1"]<=1)&(df["Y1"]>=0)&(df["Y1"]<=1)].copy()

    # 按用户指定体系筛选
    print(f"\n筛选用户指定体系 ({len(USER_SYSTEMS)} 个) ...")
    found_systems = {}
    not_found = []

    for cn1, cn2 in USER_SYSTEMS:
        sub = match_system_in_thermoml(cn1, cn2, df)
        if sub is not None and len(sub) > 0:
            key = (cn1, cn2)
            if key not in found_systems:
                found_systems[key] = sub
            else:
                found_systems[key] = pd.concat([found_systems[key], sub])
        else:
            not_found.append((cn1, cn2))

    print(f"  找到: {len(found_systems)} 个体系")
    print(f"  未找到: {len(not_found)} 个体系")

    # 导出 Excel
    OUT_DIR.mkdir(exist_ok=True)
    out_cols = ["名称1","分子式1","smiles1","名称2","分子式2","smiles2",
                "一致性检验方法一","一致性检验方法二","压强","温度","X1","Y1","DOI"]

    print(f"\n导出 {len(found_systems)} 个体系 Excel ...")
    exported = 0
    summary = []

    for (cn1, cn2), sub_df in sorted(found_systems.items(), key=lambda x: len(x[1]), reverse=True):
        fname = make_filename(cn1, cn2)
        fpath = OUT_DIR / fname
        # 去重
        sub_df = sub_df.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
        sub_df[out_cols].to_excel(fpath, sheet_name="VLE数据", index=False)
        exported += 1
        summary.append({
            "体系": f"{cn1} + {cn2}",
            "数据点数": len(sub_df),
            "文献数": sub_df["DOI"].nunique(),
            "Fredenslund检验": sub_df["一致性检验方法一"].iloc[0] if len(sub_df) > 0 else 0,
            "Herington检验": sub_df["一致性检验方法二"].iloc[0] if len(sub_df) > 0 else 0,
            "文件名": fname,
        })

    # 生成汇总索引
    summary_df = pd.DataFrame(summary).sort_values("数据点数", ascending=False)
    with pd.ExcelWriter(OUT_DIR / "_指定体系汇总索引.xlsx", engine="openpyxl") as w:
        summary_df.to_excel(w, sheet_name="体系汇总", index=False)

    # 未找到的体系
    not_found_df = pd.DataFrame(not_found, columns=["组分1","组分2"])
    with pd.ExcelWriter(OUT_DIR / "_未找到体系.xlsx", engine="openpyxl") as w:
        not_found_df.to_excel(w, sheet_name="未找到", index=False)

    print(f"\n{'='*60}")
    print(f"导出完成:")
    print(f"  找到并导出: {exported} 个体系")
    print(f"  未找到: {len(not_found)} 个体系")
    print(f"  汇总索引: _指定体系汇总索引.xlsx")
    print(f"  未找到列表: _未找到体系.xlsx")
    total_rows = sum(len(s) for s in found_systems.values())
    print(f"  总数据点: {total_rows} 行")


if __name__ == "__main__":
    main()
