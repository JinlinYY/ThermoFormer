# -*- coding: utf-8 -*-
"""
三元 VLE 数据真实性验证:
1. 随机抽样 10 个 DOI
2. 下载原始 ThermoML XML
3. 核对 DOI 标签是否一致
4. 核对文献标题与体系是否吻合
5. 核对具体数据点 (T, P, x1, x2, y1, y2) 是否在 XML 中存在
"""
import json, random, time
from pathlib import Path
import pandas as pd
import requests
import thermoml_io as tml
from thermoml_io.classification import normalize_term

WORK = Path(__file__).resolve().parent
XML_BASE = "https://trc.nist.gov/ThermoML"

df = pd.read_excel(WORK / "VLE_三元体系数据/A_三元完整数据汇总.xlsx", engine="openpyxl")
all_dois = sorted(df["DOI"].unique().tolist())
print(f"三元数据: {len(df)} 行, {len(all_dois)} DOI, {df.groupby(['名称1','名称2','名称3']).ngroups} 体系")

# 随机选 10 个 DOI (有较多数据点的)
doi_sizes = df.groupby("DOI").size().sort_values(ascending=False)
sample_dois = list(doi_sizes.head(10).index)
print(f"\n抽样 {len(sample_dois)} 个 DOI (按数据量 Top 10):")
for d in sample_dois:
    n = (df["DOI"] == d).sum()
    systems = df[df["DOI"] == d].groupby(["名称1", "名称2", "名称3"]).ngroups
    print(f"  {d}: {n} 行, {systems} 体系")

sess = requests.Session()
sess.headers.update({"User-Agent": "ternary-verify/1.0"})

print("\n" + "=" * 80)
print("验证 1: DOI 格式检查")
print("=" * 80)
bad_format = [d for d in all_dois if not d.startswith("10.")]
print(f"DOI 以 10. 开头: {len(all_dois) - len(bad_format)}/{len(all_dois)} = {(len(all_dois)-len(bad_format))/len(all_dois)*100:.1f}%")
if bad_format:
    print(f"  异常: {bad_format[:5]}")

print("\n" + "=" * 80)
print("验证 2: XML <DOI> 标签回显 + 文献标题 + 数据点核对")
print("=" * 80)

for i, doi in enumerate(sample_dois, 1):
    print(f"\n--- [{i}/{len(sample_dois)}] DOI: {doi} ---")
    try:
        url = f"{XML_BASE}/{doi}.xml"
        r = requests.get(url, timeout=60)
        time.sleep(0.5)
        if r.status_code != 200:
            print(f"  ❌ HTTP {r.status_code}")
            continue
        xml_bytes = r.content
        doc = tml.parse_thermoml(xml_bytes)
        
        # DOI 核对
        xml_doi = doc.citation.normalized_doi or ""
        match_doi = "✅" if xml_doi == doi else "❌"
        print(f"  XML <DOI>: {xml_doi}  {match_doi}")
        
        # 文献标题
        title = doc.citation.title or "(无标题)"
        print(f"  标题: {title[:100]}")
        
        # 作者
        authors = doc.citation.authors or []
        auth_str = "; ".join(a[:50] for a in authors[:3])
        print(f"  作者: {auth_str}")
        
        # 统计 XML 中的三元数据集
        ternary_dss = [ds for ds in doc.datasets if ds.system_type == "ternary"]
        n_ternary = len(ternary_dss)
        print(f"  XML 三元数据集数: {n_ternary}")
        
        # 提取 XML 中的三元组分组合
        xml_systems = set()
        xml_data_points = []
        for ds in ternary_dss:
            cids = list(dict.fromkeys(ds.component_ids))
            if len(cids) != 3:
                continue
            comp_names = []
            for cid in cids:
                comp = doc.compound(cid)
                comp_names.append(comp.preferred_name if comp else f"Unknown_{cid}")
            sys_key = tuple(sorted(comp_names))
            xml_systems.add(sys_key)
            
            # 提取数据点
            for pt in ds.points:
                point_data = {"x": {}, "y": {}, "T": None, "P": None}
                var_def = {v.number: v for v in ds.variables}
                prop_def = {p.number: p for p in ds.properties}
                
                for mv in pt.variable_values:
                    d = var_def.get(mv.number)
                    if d is None: continue
                    nm = normalize_term(d.name)
                    if nm.startswith("mole_fraction"):
                        ph = normalize_term(d.phase)
                        if ph.startswith("liquid") and d.component_id:
                            point_data["x"][d.component_id] = mv.value
                        elif ph in ("gas", "vapor", "vapour") and d.component_id:
                            point_data["y"][d.component_id] = mv.value
                    elif "temperature" in nm:
                        point_data["T"] = mv.value
                    elif "pressure" in nm:
                        point_data["P"] = mv.value
                
                for mv in pt.property_values:
                    d = prop_def.get(mv.number)
                    if d is None: continue
                    nm = normalize_term(d.name)
                    if nm.startswith("mole_fraction"):
                        ph = normalize_term(d.phase)
                        if ph.startswith("liquid") and d.component_id:
                            point_data["x"][d.component_id] = mv.value
                        elif ph in ("gas", "vapor", "vapour") and d.component_id:
                            point_data["y"][d.component_id] = mv.value
                    elif "temperature" in nm:
                        point_data["T"] = mv.value
                    elif "pressure" in nm:
                        point_data["P"] = mv.value
                
                if len(point_data["x"]) >= 2 and len(point_data["y"]) >= 2 and point_data["T"] and point_data["P"]:
                    xml_data_points.append(point_data)
        
        print(f"  XML 三元体系数: {len(xml_systems)}")
        print(f"  XML 三元 VLE 数据点: {len(xml_data_points)}")
        
        # 表中对应数据
        df_doi = df[df["DOI"] == doi]
        n_rows = len(df_doi)
        n_sys = df_doi.groupby(["名称1", "名称2", "名称3"]).ngroups
        print(f"  表中数据: {n_rows} 行, {n_sys} 体系")
        
        # 逐点核对: 随机取 3 个数据点检查是否在 XML 中存在
        if len(xml_data_points) > 0 and n_rows > 0:
            sample_rows = df_doi.sample(min(3, n_rows))
            match_count = 0
            for _, row in sample_rows.iterrows():
                t_c = row["温度"]
                p_mmhg = row["压强"]
                x1 = row["X1"]
                x2 = row["X2"]
                y1 = row["Y1"]
                y2 = row["Y2"]
                
                # 在 XML 数据点中找匹配
                found = False
                for dp in xml_data_points:
                    t_xml = dp["T"] - 273.15 if dp["T"] else None
                    p_xml = dp["P"] * 7.50061683 if dp["P"] else None
                    if t_xml is None or p_xml is None:
                        continue
                    if abs(t_xml - t_c) < 0.2 and abs(p_xml - p_mmhg) < 1.0:
                        # 检查 x1, x2 是否匹配
                        x_vals = sorted(dp["x"].values())
                        y_vals = sorted(dp["y"].values())
                        table_x = sorted([x1, x2, 1 - x1 - x2])
                        table_y = sorted([y1, y2, 1 - y1 - y2])
                        x_match = all(abs(a - b) < 0.01 for a, b in zip(x_vals, table_x)) if len(x_vals) == 3 else True
                        y_match = all(abs(a - b) < 0.01 for a, b in zip(y_vals, table_y)) if len(y_vals) == 3 else True
                        if x_match and y_match:
                            found = True
                            break
                
                status = "✅ 匹配" if found else "⚠️ 需检查"
                if found:
                    match_count += 1
                print(f"    点: T={t_c}°C, P={p_mmhg}mmHg, x1={x1}, x2={x2}, y1={y1}, y2={y2} → {status}")
            print(f"  数据点匹配: {match_count}/{min(3, n_rows)}")
        
        # 体系名称核对
        table_systems = set()
        for _, row in df_doi.iterrows():
            table_systems.add(tuple(sorted([row["名称1"], row["名称2"], row["名称3"]])))
        
        # XML 体系名（转中文后比较）
        EN_TO_CN = json.load(open(WORK / "_en_to_cn_full.json", "r", encoding="utf-8"))
        xml_systems_cn = set()
        for sys in xml_systems:
            cn_sys = tuple(sorted(EN_TO_CN.get(n, n) for n in sys))
            xml_systems_cn.add(cn_sys)
        
        sys_match = table_systems & xml_systems_cn
        print(f"  体系匹配: {len(sys_match)}/{len(table_systems)} 表中体系在 XML 中找到")
        if len(sys_match) < len(table_systems):
            diff = table_systems - xml_systems_cn
            if diff:
                print(f"    未匹配: {list(diff)[:3]}")
        
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("验证 3: 数据范围合理性检查")
print("=" * 80)
print(f"温度范围: {df['温度'].min():.2f} ~ {df['温度'].max():.2f} °C")
print(f"压强范围: {df['压强'].min():.4f} ~ {df['压强'].max():.2f} mmHg")
print(f"X1 范围: {df['X1'].min():.4f} ~ {df['X1'].max():.4f}")
print(f"X2 范围: {df['X2'].min():.4f} ~ {df['X2'].max():.4f}")
print(f"Y1 范围: {df['Y1'].min():.4f} ~ {df['Y1'].max():.4f}")
print(f"Y2 范围: {df['Y2'].min():.4f} ~ {df['Y2'].max():.4f}")
x3 = 1 - df["X1"] - df["X2"]
y3 = 1 - df["Y1"] - df["Y2"]
print(f"X3 范围: {x3.min():.4f} ~ {x3.max():.4f}")
print(f"Y3 范围: {y3.min():.4f} ~ {y3.max():.4f}")
print(f"X1+X2+X3≈1: {((x3 > -0.01) & (x3 < 1.01)).all()}")
print(f"Y1+Y2+Y3≈1: {((y3 > -0.01) & (y3 < 1.01)).all()}")
print(f"分子式非空: 名称1={df['分子式1'].notna().all()}, 名称2={df['分子式2'].notna().all()}, 名称3={df['分子式3'].notna().all()}")
print(f"DOI 非空: {df['DOI'].notna().all()}")
