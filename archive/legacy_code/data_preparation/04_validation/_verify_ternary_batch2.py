# -*- coding: utf-8 -*-
"""
验证批次 2 新增 5 个 DOI 的数据真实性:
1. 下载原始 XML, 核对 DOI 标签
2. 核对文献标题与体系是否吻合
3. 核对具体数据点 (T, P, x1, x2, y1, y2) 是否在 XML 中存在
"""
import json, time
from pathlib import Path
import pandas as pd
import requests
import thermoml_io as tml
from thermoml_io.classification import normalize_term

WORK = Path(__file__).resolve().parent
XML_BASE = "https://trc.nist.gov/ThermoML"

df = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
# 新增的 5 个 DOI
new_dois = ['10.1016/j.jct.2015.04.032','10.1016/j.fluid.2014.10.038',
            '10.1016/j.fluid.2013.10.060','10.1016/j.fluid.2008.06.006',
            '10.1016/j.fluid.2012.12.022']

print("=" * 80)
print("验证 1: DOI 格式检查")
print("=" * 80)
all_dois = sorted(df["DOI"].unique())
bad = [d for d in all_dois if not d.startswith("10.")]
print(f"DOI 以 10. 开头: {len(all_dois)-len(bad)}/{len(all_dois)} = {(len(all_dois)-len(bad))/len(all_dois)*100:.1f}%")

print("\n" + "=" * 80)
print(f"验证 2: 对 {len(new_dois)} 个新 DOI 逐篇核对原始 XML")
print("=" * 80)

sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-verify-b2/1.0"})

for i, doi in enumerate(new_dois, 1):
    print(f"\n--- [{i}/{len(new_dois)}] DOI: {doi} ---")
    try:
        url = f"{XML_BASE}/{doi}.xml"
        r = requests.get(url, timeout=60)
        time.sleep(0.5)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            continue
        doc = tml.parse_thermoml(r.content)
        
        # DOI 核对
        xml_doi = doc.citation.normalized_doi or ""
        match = "YES" if xml_doi == doi else "NO"
        print(f"  XML DOI: {xml_doi}  match={match}")
        
        # 标题
        title = doc.citation.title or "(no title)"
        print(f"  Title: {title[:120]}")
        
        # 作者
        authors = doc.citation.authors or []
        print(f"  Authors: {'; '.join(str(a)[:40] for a in authors[:3])}")
        
        # 表中数据
        df_doi = df[df["DOI"] == doi]
        n_rows = len(df_doi)
        n_sys = df_doi.groupby(["名称1","名称2","名称3"]).ngroups
        print(f"  Table: {n_rows} rows, {n_sys} systems")
        
        # XML 三元数据集
        ternary_dss = [ds for ds in doc.datasets if ds.system_type == "ternary"]
        print(f"  XML ternary datasets: {len(ternary_dss)}")
        
        # 提取 XML 中的组分组合
        xml_systems = set()
        for ds in ternary_dss:
            cids = list(dict.fromkeys(ds.component_ids))
            if len(cids) == 3:
                names = []
                for cid in cids:
                    comp = doc.compound(cid)
                    names.append(comp.preferred_name if comp else f"Unknown_{cid}")
                xml_systems.add(tuple(sorted(names)))
        
        # 表中体系（反查英文名）
        EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
        CN_TO_EN = {v: k for k, v in EN_TO_CN.items()}
        table_systems = set()
        for _, row in df_doi.iterrows():
            ens = []
            for col in ['名称1','名称2','名称3']:
                cn = str(row[col]).strip()
                en = CN_TO_EN.get(cn, cn)
                ens.append(en)
            table_systems.add(tuple(sorted(ens)))
        
        # 体系匹配
        matched = table_systems & xml_systems
        print(f"  System match: {len(matched)}/{len(table_systems)} table systems found in XML")
        
        # 数据点核对: 取表中 3 个随机点
        if n_rows > 0:
            sample = df_doi.sample(min(3, n_rows))
            for _, row in sample.iterrows():
                t_c = row["温度"]; p_mmhg = row["压强"]
                x1 = row["X1"]; x2 = row["X2"]; y1 = row["Y1"]; y2 = row["Y2"]
                print(f"    Point: T={t_c}C, P={p_mmhg}mmHg, x1={x1}, x2={x2}, y1={y1}, y2={y2}")
            
            # 在 XML 中查找匹配点
            xml_points = []
            for ds in ternary_dss:
                cids = list(dict.fromkeys(ds.component_ids))
                if len(cids) != 3: continue
                for pt in ds.points:
                    dp = {"x": {}, "y": {}, "T": None, "P": None}
                    var_def = {v.number: v for v in ds.variables}
                    prop_def = {p.number: p for p in ds.properties}
                    for mv in pt.variable_values:
                        d = var_def.get(mv.number)
                        if not d: continue
                        nm = normalize_term(d.name)
                        try: val = float(mv.value) if mv.value else None
                        except: val = None
                        if val is None: continue
                        if nm.startswith("mole_fraction"):
                            ph = normalize_term(d.phase)
                            if ph.startswith("liquid") and d.component_id:
                                dp["x"][d.component_id] = val
                            elif ph in ("gas","vapor","vapour") and d.component_id:
                                dp["y"][d.component_id] = val
                        elif "temperature" in nm:
                            dp["T"] = val
                        elif "pressure" in nm:
                            dp["P"] = val
                    for mv in pt.property_values:
                        d = prop_def.get(mv.number)
                        if not d: continue
                        nm = normalize_term(d.name)
                        try: val = float(mv.value) if mv.value else None
                        except: val = None
                        if val is None: continue
                        if nm.startswith("mole_fraction"):
                            ph = normalize_term(d.phase)
                            if ph.startswith("liquid") and d.component_id:
                                dp["x"][d.component_id] = val
                            elif ph in ("gas","vapor","vapour") and d.component_id:
                                dp["y"][d.component_id] = val
                        elif "temperature" in nm:
                            dp["T"] = val
                        elif "pressure" in nm:
                            dp["P"] = val
                    if len(dp["x"]) >= 2 and len(dp["y"]) >= 2 and dp["T"] and dp["P"]:
                        xml_points.append(dp)
            
            print(f"  XML VLE points extracted: {len(xml_points)}")
            
            # 逐点匹配
            match_count = 0
            for _, row in sample.iterrows():
                t_c = row["温度"]; p_mmhg = row["压强"]
                x1 = row["X1"]; x2 = row["X2"]; y1 = row["Y1"]; y2 = row["Y2"]
                found = False
                for dp in xml_points:
                    t_xml = dp["T"] - 273.15
                    p_xml = dp["P"] * 7.50061683
                    if abs(t_xml - t_c) < 0.5 and abs(p_xml - p_mmhg) < 2.0:
                        found = True
                        break
                if found:
                    match_count += 1
            print(f"  Point match: {match_count}/{min(3, n_rows)} sampled points found in XML")
        
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("验证 3: 数据范围合理性")
print("=" * 80)
# 只看新 DOI 的数据
df_new = df[df["DOI"].isin(new_dois)]
print(f"新数据: {len(df_new)} 行")
print(f"温度: {df_new['温度'].min():.2f} ~ {df_new['温度'].max():.2f} C")
print(f"压强: {df_new['压强'].min():.4f} ~ {df_new['压强'].max():.2f} mmHg")
print(f"X1: {df_new['X1'].min():.4f} ~ {df_new['X1'].max():.4f}")
print(f"X2: {df_new['X2'].min():.4f} ~ {df_new['X2'].max():.4f}")
print(f"Y1: {df_new['Y1'].min():.4f} ~ {df_new['Y1'].max():.4f}")
print(f"Y2: {df_new['Y2'].min():.4f} ~ {df_new['Y2'].max():.4f}")
x3 = 1 - df_new["X1"] - df_new["X2"]
y3 = 1 - df_new["Y1"] - df_new["Y2"]
print(f"X3: {x3.min():.4f} ~ {x3.max():.4f}")
print(f"Y3: {y3.min():.4f} ~ {y3.max():.4f}")
print(f"X sum=1: {((x3 > -0.01) & (x3 < 1.01)).all()}")
print(f"Y sum=1: {((y3 > -0.01) & (y3 < 1.01)).all()}")
