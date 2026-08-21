# -*- coding: utf-8 -*-
"""
按 water.xlsx / alcohol.xlsx 标准筛选 VLE 数据：
- water 体系：必须包含"水"（water）
- alcohol 体系：必须包含醇类（methanol/ethanol/propanol/butanol 等），且不含水
严格按 12 列核心定义输出：名称1, 分子式1, smiles1, 名称2, 分子式2, smiles2,
                          一致性检验方法一, 一致性检验方法二, 压强, 温度, X1, Y1
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

CSV_PATH = "vle_binary_expand.csv"
SMILES_CACHE = Path("_smiles_cache.json")
OUT_DIR = Path("vle_water_alcohol_systems")
OUT_WATER = OUT_DIR / "water_systems.xlsx"
OUT_ALCOHOL = OUT_DIR / "alcohol_systems.xlsx"
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/JSON"

# 醇类英文名模式
ALCOHOL_PATTERNS = [
    "methanol", "ethanol", "propanol", "butanol", "pentanol", "hexanol",
    "heptanol", "octanol", "nonanol", "decanol", "undecanol", "dodecanol",
    "tetradecanol", "hexadecanol", "octadecanol",
    "glycol", "glycerol", "phenol", "benzyl alcohol", "cyclohexanol",
    "cyclopentanol", "allyl alcohol", "propargyl alcohol",
    "tert-butanol", "tert-amyl alcohol", "isobutanol", "isopropanol",
    "isopentanol", "2-methylpropan-2-ol", "2-methylpropan-1-ol",
    "2-methylbutan-1-ol", "3-methylbutan-1-ol", "2,2-dimethyl-1-propanol",
    "2-amino-2-methylpropan-1-ol", "2-butyne-1,4-diol",
    "2,3-dimethylbutane-2,3-diol", "2-methylpentane-2,4-diol",
    "ethane-1,2-diol", "propane-1,2-diol", "propane-1,3-diol",
    "propane-1,2,3-triol", "tetrahydrofurfuryl alcohol", "furfuryl alcohol",
    "furfurylalcohol", "2-methoxyethanol", "2-ethoxyethanol",
    "2-butoxyethanol", "2-isopropoxyethanol", "benzyl alcohol",
    "phenethyl alcohol", "cinnamyl alcohol", "salicyl alcohol",
    "2,2,3,3-tetrafluoro-1-propanol",
]

# 中文名映射（参考现有 water.xlsx/alcohol.xlsx）
CN_NAME_MAP = {
    "water": "水", "methanol": "甲醇", "ethanol": "乙醇",
    "propan-2-ol": "2-丙醇", "isopropanol": "异丙醇", "2-propanol": "异丙醇",
    "propan-1-ol": "1-丙醇", "1-propanol": "1-丙醇", "n-propanol": "1-丙醇",
    "butan-1-ol": "1-丁醇", "1-butanol": "1-丁醇", "n-butanol": "正丁醇",
    "butan-2-ol": "2-丁醇", "2-butanol": "2-丁醇",
    "2-methylpropan-2-ol": "叔丁醇", "tert-butanol": "叔丁醇", "tert-butyl alcohol": "叔丁醇",
    "2-methylpropan-1-ol": "异丁醇", "isobutanol": "异丁醇", "2-methyl-1-propanol": "异丁醇",
    "pentan-1-ol": "1-戊醇", "1-pentanol": "1-戊醇", "n-pentanol": "正戊醇",
    "pentan-2-ol": "2-戊醇", "2-pentanol": "2-戊醇",
    "3-methylbutan-1-ol": "3-甲基丁醇", "isopentanol": "异戊醇",
    "2-methylbutan-1-ol": "2-甲基-1-丁醇",
    "2,2-dimethyl-1-propanol": "2,2-二甲基-1-丙醇", "neopentyl alcohol": "2,2-二甲基-1-丙醇",
    "hexan-1-ol": "1-己醇", "1-hexanol": "1-己醇", "n-hexanol": "己醇",
    "heptan-1-ol": "1-庚醇", "1-heptanol": "1-庚醇",
    "octan-1-ol": "1-辛醇", "1-octanol": "1-辛醇",
    "decan-1-ol": "1-癸醇", "1-decanol": "1-癸醇",
    "undecan-1-ol": "1-十一醇", "1-undecanol": "1-十一醇",
    "dodecan-1-ol": "1-十二醇", "1-dodecanol": "1-十二醇",
    "ethane-1,2-diol": "乙二醇", "ethylene glycol": "乙二醇", "1,2-ethanediol": "乙二醇",
    "propane-1,2-diol": "1,2-丙二醇", "propylene glycol": "1,2-丙二醇", "1,2-propanediol": "1,2-丙二醇",
    "propane-1,3-diol": "1,3-丙二醇", "1,3-propanediol": "1,3-丙二醇", "propan-1,3-diol": "1,3-丙二醇",
    "propane-1,2,3-triol": "丙三醇", "glycerol": "丙三醇", "1,2,3-propanetriol": "丙三醇",
    "phenol": "苯酚", "benzyl alcohol": "苯甲醇", "phenylmethanol": "苯甲醇",
    "cyclohexanol": "环己醇", "cyclopentanol": "环戊醇",
    "allyl alcohol": "烯丙醇", "prop-2-en-1-ol": "烯丙醇", "2-propenol": "烯丙醇", "2-propen-1-ol": "烯丙醇",
    "propargyl alcohol": "炔丙醇", "prop-2-yn-1-ol": "炔丙醇",
    "2-butyne-1,4-diol": "2-丁炔-1,4-二醇",
    "2-methoxyethanol": "2-甲氧基乙醇", "2-methoxyethan-1-ol": "2-甲氧基乙醇",
    "2-ethoxyethanol": "2-乙氧基乙醇", "2-ethoxyethan-1-ol": "2-乙氧基乙醇",
    "2-butoxyethanol": "2-丁氧基乙醇", "2-butoxyethan-1-ol": "2-丁氧基乙醇",
    "2-isopropoxyethanol": "2-异丙氧基乙醇",
    "2-amino-2-methylpropan-1-ol": "2-氨基-2-甲基-1-丙醇",
    "2,2,3,3-tetrafluoro-1-propanol": "2,2,3,3-四氟-1-丙醇",
    "furfuryl alcohol": "糠醇", "furfurylalcohol": "糠醇", "tetrahydrofurfuryl alcohol": "四氢糠醇",
    "acetone": "丙酮", "propanone": "丙酮",
    "acetic acid": "乙酸", "ethanoic acid": "乙酸",
    "formic acid": "甲酸", "methanoic acid": "甲酸",
    "propionic acid": "丙酸", "propanoic acid": "丙酸",
    "butyric acid": "丁酸", "butanoic acid": "丁酸",
    "acetaldehyde": "乙醛", "ethanal": "乙醛",
    "formaldehyde": "甲醛", "methanal": "甲醛",
    "benzene": "苯", "toluene": "甲苯",
    "ethylbenzene": "乙苯", "styrene": "苯乙烯",
    "1,2-dimethylbenzene": "邻二甲苯", "o-xylene": "邻二甲苯",
    "1,3-dimethylbenzene": "间二甲苯", "m-xylene": "间二甲苯",
    "1,4-dimethylbenzene": "对二甲苯", "p-xylene": "对二甲苯",
    "1,2,4-trimethylbenzene": "1,2,4-三甲苯",
    "isopropylbenzene": "异丙苯", "cumene": "异丙苯",
    "chlorobenzene": "氯苯", "fluorobenzene": "氟苯",
    "aniline": "苯胺", "pyridine": "吡啶",
    "morpholine": "吗啉", "piperidine": "哌啶",
    "tetrahydrofuran": "四氢呋喃", "thiophene": "噻吩",
    "1,4-dioxane": "1,4-二噁烷", "1,3-dioxolane": "1,3-二噁唑烷",
    "dimethyl sulfoxide": "二甲基亚砜", "dmso": "二甲基亚砜",
    "dimethylformamide": "二甲基甲酰胺", "dmf": "二甲基甲酰胺",
    "dimethylacetamide": "二甲基乙酰胺", "n,n-dimethylethanamide": "n,n-二甲基乙酰胺",
    "n-methylpyrrolidone": "n-甲基吡咯烷酮",
    "acetonitrile": "乙腈", "methyl cyanide": "乙腈",
    "acetamide": "乙酰胺", "propionamide": "丙酰胺",
    "urea": "尿素",
    "dimethyl carbonate": "碳酸二甲酯", "diethyl carbonate": "碳酸二乙酯",
    "ethylene carbonate": "碳酸乙烯酯", "propylene carbonate": "碳酸丙烯酯",
    "methyl formate": "甲酸甲酯", "ethyl formate": "甲酸乙酯",
    "propyl formate": "甲酸丙酯", "butyl formate": "甲酸丁酯",
    "methyl acetate": "乙酸甲酯", "ethyl acetate": "乙酸乙酯",
    "propyl acetate": "乙酸丙酯", "butyl acetate": "乙酸丁酯",
    "isopropyl acetate": "乙酸异丙酯", "tert-butyl acetate": "乙酸叔丁酯",
    "methyl propionate": "丙酸甲酯", "ethyl propionate": "丙酸乙酯",
    "methyl butyrate": "丁酸甲酯", "ethyl butyrate": "丁酸乙酯",
    "dichloromethane": "二氯甲烷", "methylene chloride": "二氯甲烷",
    "chloroform": "三氯甲烷", "trichloromethane": "三氯甲烷",
    "carbon tetrachloride": "四氯化碳", "tetrachloromethane": "四氯化碳",
    "1,2-dichloroethane": "1,2-二氯乙烷",
    "trichloroethylene": "三氯乙烯", "tetrachloroethylene": "四氯乙烯",
    "chloromethane": "氯甲烷", "bromoethane": "溴乙烷",
    "diethyl ether": "乙醚", "dimethyl ether": "二甲醚",
    "dipropyl ether": "二丙醚", "dibutyl ether": "二丁醚",
    "methyl tert-butyl ether": "甲基叔丁基醚", "mtbe": "甲基叔丁基醚",
    "diisopropyl ether": "二异丙醚",
    "butyl ethyl ether": "丁基乙醚", "2-ethoxy-2-methylpropane": "乙基叔丁基醚",
    "hexane": "己烷", "n-hexane": "己烷",
    "heptane": "庚烷", "n-heptane": "庚烷",
    "octane": "辛烷", "n-octane": "辛烷",
    "nonane": "壬烷", "decane": "癸烷", "undecane": "十一烷",
    "2-methylbutane": "异戊烷", "isopentane": "异戊烷",
    "2-methylpentane": "异己烷", "3-methylpentane": "3-甲基戊烷",
    "2,2,4-trimethylpentane": "异辛烷", "isooctane": "异辛烷",
    "cyclohexane": "环己烷", "cyclopentane": "环戊烷",
    "methylcyclohexane": "甲基环己烷",
    "methane": "甲烷", "ethane": "乙烷", "propane": "丙烷", "butane": "丁烷",
    "isobutane": "异丁烷", "2-methylpropane": "异丁烷",
    "pentane": "戊烷",
    "ethene": "乙烯", "ethylene": "乙烯",
    "propene": "丙烯", "propylene": "丙烯",
    "1-hexene": "1-己烯", "hex-1-ene": "1-己烯",
    "2-hexene": "2-己烯",
    "2-methylpropene": "异丁烯", "isobutylene": "异丁烯",
    "acetylene": "乙炔", "ethyne": "乙炔",
    "propyne": "丙炔",
    "1-hexyne": "1-己炔", "2-hexyne": "2-己炔", "3-hexyne": "3-己炔",
    "carbon dioxide": "二氧化碳", "co2": "二氧化碳",
    "nitrogen": "氮气", "oxygen": "氧气", "hydrogen": "氢气",
    "ammonia": "氨", "nh3": "氨",
    "sulfur dioxide": "二氧化硫", "hydrogen sulfide": "硫化氢",
    "dimethyl sulfide": "二甲硫醚", "2-thiapropane": "2-硫杂丙烷",
    "carbon disulfide": "二硫化碳",
    "2-ethylthiophene": "2-乙基噻吩",
    "acetophenone": "苯乙酮",
    "cyclohexanone": "环己酮", "cyclopentanone": "环戊酮",
    "butanone": "2-丁酮", "methyl ethyl ketone": "2-丁酮",
    "3-methyl-2-butanone": "3-甲基-2-丁酮",
    "4-methylpentan-2-one": "4-甲基-2-戊酮", "methyl isobutyl ketone": "4-甲基-2-戊酮",
    "3,3-dimethyl-2-butanone": "3,3-二甲基-2-丁酮",
    "2,4-dimethyl-3-pentanone": "2,4-二甲基-3-戊酮",
    "trifluoromethane": "三氟甲烷", "fluoroform": "三氟甲烷",
    "difluoromethane": "二氟甲烷",
    "pentafluoroethane": "五氟乙烷",
    "hexafluoroethane": "六氟乙烷",
    "1,1,1,2-tetrafluoroethane": "1,1,1,2-四氟乙烷",
    "1,1-difluoroethane": "1,1-二氟乙烷",
    "perfluorohexane": "全氟己烷",
    "octadecafluorooctane": "全氟辛烷",
    "2,2,3,3-tetrafluoro-1-propanol": "2,2,3,3-四氟-1-丙醇",
    "trifluoroiodomethane": "三氟碘甲烷",
    "chlorodifluoromethane": "氯二氟甲烷",
    "dichlorofluoromethane": "二氯氟甲烷",
    "trichlorofluoromethane": "三氯氟甲烷",
    "1,1,1-trifluoroethane": "1,1,1-三氟乙烷",
    "1,1,1,3,3-pentafluoropropane": "1,1,1,3,3-五氟丙烷",
    "(z)-1,3,3,3-tetrafluoro-1-propene": "1,3,3,3-四氟丙烯",
    "trans-1,3,3,3-tetrafluoropropene": "反式-1,3,3,3-四氟丙烯",
    "2,3,3,3-tetrafluoro-1-propene": "2,3,3,3-四氟丙烯",
    "hexafluoropropene": "六氟丙烯",
    "2,5-dimethylfuran": "2,5-二甲基呋喃",
    "tetrahydropyran": "四氢吡喃",
    "methyl octanoate": "辛酸甲酯",
    "methyl decanoate": "癸酸甲酯",
    "methyl dodecanoate": "月桂酸甲酯",
    "methyl cis-9-octadecenoate": "油酸甲酯",
    "ethyl dodecanoate": "月桂酸乙酯",
    "ethyl tetradecanoate": "肉豆蔻酸乙酯",
    "ethyl 2-methylpropanoate": "甲基丙烯酸乙酯",
    "phenyl ethanoate": "乙酸苯酯",
    "3-methylbutyl propanoate": "丙酸异戊酯",
    "3-pentenenitrile": "3-戊烯腈",
    "4-chlorophthalic anhydride": "4-氯代苯酐",
    "5-fluoro-1,3-isobenzofurandione": "5-氟代苯酐",
    "(trifluoromethyl)benzene": "三氟甲基苯",
    "1-(1-methylethyl)-4-methylbenzene": "对撒丁异丙苯",
    "iodoethane": "碘乙烷",
    "butane, 1-(1,1-dimethylethoxy)-": "叔丁氧基丁烷",
    "2-chlorobutane": "2-氯丁烷",
    "2-chloro-2-methylpropane": "2-氯-2-甲基丙烷",
    "1-chloro-2-methylpropane": "1-氯-2-甲基丙烷",
    "1-chloropentane": "1-氯戊烷",
    "2-methylpropyl ethanoate": "乙酸异丁酯",
    "1-methylpropyl ethanoate": "乙酸仲丁酯",
    "1-methylethyl ethanoate": "乙酸异丙酯",
    "2-methylpropyl methanoate": "甲酸异丁酯",
    "pentyl methanoate": "甲酸戊酯",
    "dodecafluoro-2-methylpentan-3-one": "十二氟-2-甲基戊-3-酮",
    "2,2,3-trifluoro-3-(trifluoromethyl)oxirane": "2,2,3-三氟-3-(三氟甲基)环氧乙烷",
    "2-pinene": "β-蒎烯",
    "(+)-3-carene": "(+)-3-蒈烯",
    "(R)-1-methyl-4-(1-methylethenyl)cyclohexene": "(R)-1-甲基-4-(1-甲基乙烯基)环己烯",
    "4-ethenylcyclohexene": "4-乙烯基环己烯",
    "2,2-dimethyl-3-methylenebicyclo[2.2.1]heptane": "2,2-二甲基-3-亚甲基二环[2.2.1]庚烷",
    "3,7-dimethyl-1,6-octadiene": "3,7-二甲基-1,6-辛二烯",
    "2,6-dimethyl-7-octen-2-ol": "2,6-二甲基-7-辛烯-2-醇",
    "2,4,4-trimethyl-1-pentene": "2,4,4-三甲基-1-戊烯",
    "2-methyl-6-methylene-2,7-octadiene": "2-甲基-6-亚甲基-2,7-辛二烯",
    "1,2-dibromoethane": "1,2-二溴乙烷",
    "1,1,2,2-tetrachloroethane": "1,1,2,2-四氯乙烷",
    "2,2-dichloroacetic acid": "二氯乙酸",
    "chloroacetic acid": "氯乙酸", "chloroethanoic acid": "氯乙酸",
    "nitromethane": "硝基甲烷",
    "nitroethane": "硝基乙烷",
    "dimethylamine": "二甲胺", "trimethylamine": "三甲胺",
    "diethylamine": "二乙胺", "triethylamine": "三乙胺",
    "methylamine": "甲胺", "ethylamine": "乙胺",
    "propylamine": "丙胺", "butylamine": "丁胺",
}


def _normalize(s: str) -> str:
    return " ".join(s.lower().strip().split())


def lookup_cn(en: str) -> str:
    key = _normalize(en)
    if key in CN_NAME_MAP:
        return CN_NAME_MAP[key]
    # 尝试去掉前缀
    import re
    stripped = re.sub(r'^\d+-', '', key)
    if stripped in CN_NAME_MAP:
        return CN_NAME_MAP[stripped]
    return en  # 找不到就保留英文


def is_water(name: str) -> bool:
    n = _normalize(name)
    return n == "water" or "水" in str(name)


def is_alcohol(name: str) -> bool:
    n = _normalize(name)
    # 中文"醇"字
    if "醇" in str(name):
        return True
    # 英文匹配
    for pat in ALCOHOL_PATTERNS:
        if pat in n:
            return True
    # 通用：以 -ol 结尾且不是其他东西
    if n.endswith("ol") and not any(x in n for x in ["phenol", "thiol", "sterol"]):
        # 但要排除 "benzene", "propane" 等
        if not any(x in n for x in ["benzene", "propane", "butane", "pentane",
                                     "hexane", "heptane", "octane", "nonane",
                                     "decane", "undecane", "dodecane"]):
            return True
    return False


def fetch_smiles(name: str, sess: requests.Session, cache: dict) -> str:
    if name in cache:
        return cache[name]
    url = PUBCHEM_URL.format(name=name)
    try:
        r = sess.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()["PropertyTable"]["Properties"][0]
            smi = data.get("SMILES", data.get("ConnectivitySMILES", ""))
            cache[name] = smi
            return smi
    except Exception:
        pass
    cache[name] = ""
    return ""


def main() -> None:
    print("读取 vle_binary_expand.csv ...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"  共 {len(df)} 行, {df['DOI'].nunique()} 篇文献")

    # 加载 SMILES 缓存
    cache = {}
    if SMILES_CACHE.exists():
        cache = json.loads(SMILES_CACHE.read_text(encoding="utf-8"))
        print(f"  已加载 SMILES 缓存: {len(cache)} 条")

    sess = requests.Session()
    sess.headers.update({"User-Agent": "thermoml-water-alcohol/1.0"})

    # 收集所有唯一化合物名，查找 SMILES
    all_names = set(df["名称1"]) | set(df["名称2"])
    missing = [n for n in all_names if n not in cache]
    print(f"  待查找 SMILES: {len(missing)} 个")
    for i, name in enumerate(missing, 1):
        fetch_smiles(name, sess, cache)
        time.sleep(0.15)
        if i % 20 == 0:
            print(f"    进度 {i}/{len(missing)}")
    SMILES_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  SMILES 缓存已更新: {len(cache)} 条")

    # 构建新列
    rows = []
    for _, r in df.iterrows():
        n1, n2 = r["名称1"], r["名称2"]
        cn1 = lookup_cn(n1)
        cn2 = lookup_cn(n2)
        smi1 = cache.get(n1, "")
        smi2 = cache.get(n2, "")
        rows.append({
            "名称1": cn1, "分子式1": r["分子式1"], "smiles1": smi1,
            "名称2": cn2, "分子式2": r["分子式2"], "smiles2": smi2,
            "一致性检验方法一": 0, "一致性检验方法二": 0,
            "压强": r["压强"], "温度": r["温度"],
            "X1": r["X1"], "Y1": r["Y1"],
            # 元数据列（不输出到 Excel，仅用于筛选）
            "_DOI": r["DOI"], "_文献来源": r["文献来源"], "_NIST链接": r["NIST资源链接"],
        })
    full = pd.DataFrame(rows)

    # 清洗
    before = len(full)
    full = full.drop_duplicates(subset=["名称1", "分子式1", "smiles1",
                                          "名称2", "分子式2", "smiles2",
                                          "压强", "温度", "X1", "Y1"]).copy()
    full = full.dropna(subset=["压强", "温度", "X1", "Y1"]).copy()
    full = full[(full["X1"] >= 0) & (full["X1"] <= 1)
                & (full["Y1"] >= 0) & (full["Y1"] <= 1)].copy()
    print(f"  清洗: {before} -> {len(full)} 行")

    # —— 筛选水体系 ——
    # water.xlsx 中水的位置不固定（有时名称1=水，有时名称2=水），
    # X1 始终是名称1 的摩尔分数，与 ThermoML 输出一致，无需交换。
    water_mask = full["名称1"].apply(is_water) | full["名称2"].apply(is_water)
    water_df = full[water_mask].copy()
    print(f"\n水体系: {len(water_df)} 行, {water_df.groupby(['名称1','名称2']).ngroups} 个体系")
    print("  体系列表:")
    for (n1, n2), cnt in water_df.groupby(["名称1","名称2"]).size().sort_values(ascending=False).items():
        print(f"    {n1} + {n2}: {cnt}")

    # —— 筛选醇体系（不含水）——
    alcohol_mask = (full["名称1"].apply(is_alcohol) | full["名称2"].apply(is_alcohol))
    alcohol_mask &= ~(full["名称1"].apply(is_water) | full["名称2"].apply(is_water))
    alcohol_df = full[alcohol_mask].copy()
    print(f"\n醇体系: {len(alcohol_df)} 行, {alcohol_df.groupby(['名称1','名称2']).ngroups} 个体系")
    print("  Top 20 体系:")
    for (n1, n2), cnt in alcohol_df.groupby(["名称1","名称2"]).size().sort_values(ascending=False).head(20).items():
        print(f"    {n1} + {n2}: {cnt}")

    # —— 导出 Excel ——
    OUT_DIR.mkdir(exist_ok=True)
    out_cols = ["名称1", "分子式1", "smiles1", "名称2", "分子式2", "smiles2",
                "一致性检验方法一", "一致性检验方法二", "压强", "温度", "X1", "Y1"]

    with pd.ExcelWriter(OUT_WATER, engine="openpyxl") as w:
        water_df[out_cols].to_excel(w, sheet_name="水体系VLE数据", index=False)
    with pd.ExcelWriter(OUT_ALCOHOL, engine="openpyxl") as w:
        alcohol_df[out_cols].to_excel(w, sheet_name="醇体系VLE数据", index=False)

    # 也导出 CSV 副本
    water_df[out_cols].to_csv(OUT_DIR / "water_systems.csv", index=False, encoding="utf-8-sig")
    alcohol_df[out_cols].to_csv(OUT_DIR / "alcohol_systems.csv", index=False, encoding="utf-8-sig")

    print(f"\n已导出:")
    print(f"  水体系 Excel: {OUT_WATER}")
    print(f"    行数: {len(water_df)} × {len(out_cols)} 列")
    print(f"  醇体系 Excel: {OUT_ALCOHOL}")
    print(f"    行数: {len(alcohol_df)} × {len(out_cols)} 列")


if __name__ == "__main__":
    main()
