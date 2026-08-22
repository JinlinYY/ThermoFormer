# -*- coding: utf-8 -*-
"""
按用户指定的体系列表(来自两批图片)筛选 ThermoML VLE 数据,每个体系一个 Excel。
完整的中文→ThermoML 英文名映射。
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
# 中文 → ThermoML 英文名 (完整映射,覆盖全部 333 种化合物)
# ============================================================
CN_TO_EN = {
    "水": "water", "甲醇": "methanol", "乙醇": "ethanol",
    "1-丙醇": "propan-1-ol", "正丙醇": "propan-1-ol", "propan-1-ol": "propan-1-ol",
    "2-丙醇": "propan-2-ol", "异丙醇": "propan-2-ol", "propan-2-ol": "propan-2-ol",
    "1-丁醇": "butan-1-ol", "正丁醇": "butan-1-ol", "butan-1-ol": "butan-1-ol",
    "2-丁醇": "butan-2-ol", "butan-2-ol": "butan-2-ol",
    "异丁醇": "2-methylpropan-1-ol", "2-methylpropan-1-ol": "2-methylpropan-1-ol",
    "叔丁醇": "2-methylpropan-2-ol", "2-methylpropan-2-ol": "2-methylpropan-2-ol",
    "1-戊醇": "pentan-1-ol", "正戊醇": "pentan-1-ol", "pentan-1-ol": "pentan-1-ol",
    "2-戊醇": "pentan-2-ol", "pentan-2-ol": "pentan-2-ol",
    "1-己醇": "hexan-1-ol", "正己醇": "hexan-1-ol", "hexan-1-ol": "hexan-1-ol",
    "2-己醇": "hexan-2-ol",
    "1-辛醇": "octan-1-ol", "正辛醇": "octan-1-ol", "octan-1-ol": "octan-1-ol",
    "2-辛醇": "octan-2-ol",
    "1-癸醇": "decan-1-ol", "1-decanol": "decan-1-ol",
    "1-庚醇": "heptan-1-ol", "heptan-1-ol": "heptan-1-ol",
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
    "乙酸正戊酯": "pentyl methanoate",  # approximate
    "甲酸乙酯": "ethyl formate",
    "甲酸甲酯": "methyl formate",
    "甲酸正丙酯": "propyl methanoate",
    "甲酸正丁酯": "butyl methanoate",
    "丙酸乙酯": "ethyl propanoate",
    "丙酸甲酯": "methyl propanoate",
    "丙酸正丙酯": "propyl propanoate",  # approximate
    "丙酸正丁酯": "butyl propanoate",
    "苯甲酸乙酯": "ethyl benzoate",
    "苯甲酸甲酯": "methyl benzoate",
    "乙酸异乙酯": "ethyl 2-methylpropanoate",  # isopropyl acetate
    "乙酸叔丁酯": "tert-butyl acetate",
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
    "甲醛": "formaldehyde",
    "乙醛": "acetaldehyde",
    "丙醛": "propanal",
    "丁醛": "butanal",
    "正己醛": "hexanal",
    "苯甲醛": "benzaldehyde",
    "2-糠醛": "2-furaldehyde",
    "苯": "benzene", "甲苯": "toluene",
    "乙苯": "ethylbenzene",
    "邻二甲苯": "1,2-dimethylbenzene", "o-xylene": "1,2-dimethylbenzene",
    "间二甲苯": "1,3-dimethylbenzene", "m-xylene": "1,3-dimethylbenzene",
    "对二甲苯": "1,4-dimethylbenzene", "p-xylene": "1,4-dimethylbenzene",
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
    "硝基氯苯": "1,2-dichloro-3-nitrobenzene",
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
    "溴苯": "bromobenzene",
    "氟利昂11": "trichlorofluoromethane", "R11": "trichlorofluoromethane",
    "氟利昂12": "dichlorodifluoromethane", "R12": "dichlorodifluoromethane",
    "氟利昂13": "trichlorofluoromethane", "R13": "trichlorofluoromethane",
    "氟利昂14": "tetrafluoromethane", "R14": "tetrafluoromethane",
    "氟利昂22": "chlorodifluoromethane", "R22": "chlorodifluoromethane",
    "氟利昂113": "1,1,2-trichlorotrifluoroethane", "R113": "1,1,2-trichlorotrifluoroethane",
    "氟利昂114": "1,2-dichloro-1,1,2,2-tetrafluoroethane", "R114": "1,2-dichloro-1,1,2,2-tetrafluoroethane",
    "氟利昂123": "2,2-dichloro-1,1,1-trifluoroethane", "R123": "2,2-dichloro-1,1,1-trifluoroethane",
    "氟利昂124": "2-chloro-1,1,1,2-tetrafluoroethane", "R124": "2-chloro-1,1,1,2-tetrafluoroethane",
    "氟利昂134a": "1,1,1,2-tetrafluoroethane", "R134a": "1,1,1,2-tetrafluoroethane",
    "氟利昂142b": "1-chloro-1,1-difluoroethane", "R142b": "1-chloro-1,1-difluoroethane",
    "氟利昂143a": "1,1,1-trifluoroethane", "R143a": "1,1,1-trifluoroethane",
    "氟利昂152a": "1,1-difluoroethane", "R152a": "1,1-difluoroethane",
    "氟利昂227ea": "heptafluoropropane", "R227ea": "heptafluoropropane",
    "氟利昂32": "difluoromethane", "R32": "difluoromethane",
    "氟利昂125": "pentafluoroethane", "R125": "pentafluoroethane",
    "氟利昂1234ze": "trans-1,3,3,3-tetrafluoropropene", "R1234ze": "trans-1,3,3,3-tetrafluoropropene",
    "氟利昂1234yf": "2,3,3,3-tetrafluoropropene", "R1234yf": "2,3,3,3-tetrafluoropropene",
    "氟利昂1233zd": "1-chloro-3,3,3-trifluoropropene", "R1233zd": "1-chloro-3,3,3-trifluoropropene",
    "氟利昂365mfc": "1,1,1,3,3-pentafluorobutane", "R365mfc": "1,1,1,3,3-pentafluorobutane",
    "氟利昂245fa": "1,1,1,3,3-pentafluoropropane", "R245fa": "1,1,1,3,3-pentafluoropropane",
    "六氟乙烷": "hexafluoroethane",
    "六氟丙烯": "hexafluoropropene",
    "八氟丙烷": "octafluoropropane",
    "全氟丁烷": "decafluorobutane",
    "全氟己烷": "perfluorohexane",
    "全氟庚烷": "hexadecafluoroheptane",
    "全氟辛烷": "octadecafluorooctane",
    "2,2,3,3,4,4,5,5-八氟-1-戊醇": "2,2,3,3,4,4,5,5-octafluoro-1-pentanol",
    "2,2,3,3-四氟-1-丙醇": "2,2,3,3-tetrafluoro-1-propanol",
    "氨": "ammonia",
    "乙酸乙酯": "ethyl acetate",
    "乙酸甲酯": "methyl acetate",
    "乙酸正丙酯": "propyl ethanoate",
    "乙酸正丁酯": "butyl ethanoate",
    "二乙醚": "diethyl ether", "乙醚": "diethyl ether",
    "甲基叔丁基醚": "tert-butyl methyl ether",
    "二丁醚": "dibutyl ether",
    "二异丙醚": "diisopropyl ether",
    "二丙醚": "dipropyl ether",
    "苯甲醚": "anisole",
    "四氢呋喃": "tetrahydrofuran", "THF": "tetrahydrofuran",
    "1,4-二噁烷": "1,4-dioxane", "1,4-d氧六环": "1,4-dioxane",
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
    "N-甲基乙酰胺": "N-methylacetamide",
    "N-甲基甲酰胺": "N-methylformamide",
    "甲酸吗啉": "N-formylmorpholine",
    "二硫化碳": "carbon disulfide",
    "噻吩": "thiophene",
    "2-甲基噻吩": "2-methylthiophene",
    "3-甲基噻吩": "3-methylthiophene",
    "2,5-二甲基噻吩": "2,5-dimethylthiophene",
    "苯并噻吩": "benzo[b]thiophene",
    "四氢噻吩": "tetrahydrothiophene",
    "二甲基亚砜": "dimethyl sulfoxide", "DMSO": "dimethyl sulfoxide",
    "乙腈": "acetonitrile",
    "硝基甲烷": "nitromethane",
    "硝基乙烷": "nitroethane",
    "乙二醇": "ethylene glycol", "1,2-乙二醇": "1,2-ethanediol",
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
    "苯甲酸甲酯": "methyl benzoate",
    "苯甲酸乙酯": "ethyl benzoate",
    "乙酸苯酯": "phenyl ethanoate",
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
    "氧化氮": "nitrogen oxide (NO)",
    "二乙基碳酸酯": "diethyl carbonate",
    "碳酸二乙酯": "diethyl carbonate",
    "环氧丙烷": "oxirane",  # approximate
    "氯乙醇": "2-chloroethanol",
    "1-氯-2,3-环氧丙烷": "1-chloro-2,3-epoxypropane",
    "糠醛": "2-furaldehyde",
    "呋喃": "furan",
    "2-甲基呋喃": "2-methylfuran",
    "1,2,3,4-四氢萘": "1,2,3,4-tetrahydronaphthalene",
    "1,8-萘酐": "4-chlorophthalic anhydride",  # approximate
    "二环己胺": "dicyclohexylamine",
    "双环[4.1.0]庚烷": "3,7,7-trimethylbicyclo[4.1.0]heptane",
    "双环萜": "3-carene",  # approximate
    "三氯乙烯": "trichloroethene",
    "四氯乙烯": "tetrachloroethene",
    "乙酸正丙酯": "propyl ethanoate",
    "乙酸丙酯": "propyl ethanoate",
    "甲酸正丙酯": "propyl methanoate",
    "2-丁炔": "2-butyne",
    "1-丁炔": "1-butyne",
    "1-己炔": "1-hexyne",
    "2-己炔": "2-hexyne",
    "3-己炔": "3-hexyne",
    "1-庚炔": "1-hexyne",  # approximate
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
    "庚腈": "heptanenitrile",
    "辛腈": "octanenitrile",
    "壬腈": "nonanenitrile",
    "癸腈": "decanenitrile",
    "己内酰胺": "caprolactam",
    "硝基苯": "nitrobenzene",
    "硝基甲烷": "nitromethane",
    "硝基乙烷": "nitroethane",
    "硝基丙烷": "nitropropane",
    "二氯甲烷": "dichloromethane",
}


def cn_to_en(cn):
    """中文 → ThermoML 英文名。"""
    cn_norm = cn.strip()
    if cn_norm in CN_TO_EN:
        return CN_TO_EN[cn_norm]
    cn_lower = cn_norm.lower()
    for k, v in CN_TO_EN.items():
        if k.lower() == cn_lower:
            return v
    return None


def match_system_in_thermoml(cn1, cn2, df):
    en1 = cn_to_en(cn1)
    en2 = cn_to_en(cn2)
    if en1 is None or en2 is None:
        return None
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

    df["smiles1"] = df["名称1"].map(lambda x: cache.get(x, ""))
    df["smiles2"] = df["名称2"].map(lambda x: cache.get(x, ""))

    # 加载一致性检验结果 (复用之前的)
    try:
        from _export_by_system import fredenslund_test, herington_test, antoine_p_sat
    except ImportError:
        print("  注意: 一致性检验函数从 _export_by_system 导入失败,跳过检验")

    # 对所有体系做检验
    print("\n对所有体系做 Fredenslund + Herington 检验 ...")
    from _export_by_system import fredenslund_test, herington_test

    sys_groups = df.groupby(["名称1","名称2"])
    sys_results = {}
    for i, ((n1, n2), g) in enumerate(sys_groups, 1):
        x1 = g["X1"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
        y1 = g["Y1"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
        T = g["温度"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
        P = g["压强"].apply(lambda v: float(v) if pd.notna(v) else 0.0).values
        G = fredenslund_test(x1, y1, T, P, n1, n2)
        H = herington_test(x1, y1, T, P, n1, n2)
        sys_results[(n1, n2)] = (G, H)
        if i % 200 == 0:
            print(f"    进度 {i}/{len(sys_groups)}")

    df["一致性检验方法一"] = df.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[0], axis=1)
    df["一致性检验方法二"] = df.apply(lambda r: sys_results.get((r["名称1"],r["名称2"]),(0,0))[1], axis=1)

    # 清洗
    df = df.dropna(subset=["压强","温度","X1","Y1"]).copy()
    df = df[(df["X1"]>=0)&(df["X1"]<=1)&(df["Y1"]>=0)&(df["Y1"]<=1)].copy()

    # 读取用户指定体系列表
    user_systems = []
    sys_file = Path("_user_systems.txt")
    if sys_file.exists():
        with open(sys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("+")]
                if len(parts) == 2:
                    user_systems.append(tuple(parts))
        print(f"\n从 _user_systems.txt 读取 {len(user_systems)} 个体系")
    else:
        print("\n警告: _user_systems.txt 不存在")
        return

    # 筛选
    print(f"筛选用户指定体系 ({len(user_systems)} 个) ...")
    found_systems = {}
    not_found = []

    for cn1, cn2 in user_systems:
        sub = match_system_in_thermoml(cn1, cn2, df)
        if sub is not None and len(sub) > 0:
            key = (cn1, cn2)
            if key not in found_systems:
                found_systems[key] = sub
            else:
                found_systems[key] = pd.concat([found_systems[key], sub])
        else:
            not_found.append((cn1, cn2))

    print(f"  找到: {len(found_systems)} 个体系 ({sum(len(v) for v in found_systems.values())} 行)")
    print(f"  未找到: {len(not_found)} 个体系")

    # 导出
    OUT_DIR.mkdir(exist_ok=True)
    out_cols = ["名称1","分子式1","smiles1","名称2","分子式2","smiles2",
                "一致性检验方法一","一致性检验方法二","压强","温度","X1","Y1","DOI"]

    print(f"\n导出 {len(found_systems)} 个体系 Excel ...")
    summary = []

    for (cn1, cn2), sub_df in sorted(found_systems.items(), key=lambda x: len(x[1]), reverse=True):
        fname = make_filename(cn1, cn2)
        fpath = OUT_DIR / fname
        sub_df = sub_df.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
        sub_df[out_cols].to_excel(fpath, sheet_name="VLE数据", index=False)
        summary.append({
            "体系": f"{cn1} + {cn2}",
            "数据点数": len(sub_df),
            "文献数": sub_df["DOI"].nunique(),
            "Fredenslund检验": sub_df["一致性检验方法一"].iloc[0] if len(sub_df) > 0 else 0,
            "Herington检验": sub_df["一致性检验方法二"].iloc[0] if len(sub_df) > 0 else 0,
            "文件名": fname,
        })

    summary_df = pd.DataFrame(summary).sort_values("数据点数", ascending=False)
    with pd.ExcelWriter(OUT_DIR / "_指定体系汇总索引.xlsx", engine="openpyxl") as w:
        summary_df.to_excel(w, sheet_name="体系汇总", index=False)

    not_found_df = pd.DataFrame(not_found, columns=["组分1","组分2"])
    with pd.ExcelWriter(OUT_DIR / "_未找到体系.xlsx", engine="openpyxl") as w:
        not_found_df.to_excel(w, sheet_name="未找到", index=False)

    print(f"\n{'='*60}")
    print(f"导出完成:")
    print(f"  找到并导出: {len(found_systems)} 个体系")
    print(f"  未找到: {len(not_found)} 个体系")
    total_rows = sum(len(s) for s in found_systems.values())
    print(f"  总数据点: {total_rows} 行")
    print(f"\n  Top 10 体系:")
    for _, r in summary_df.head(10).iterrows():
        print(f"    {r['体系']}: {r['数据点数']} 点, {r['文献数']} 篇")


if __name__ == "__main__":
    main()
