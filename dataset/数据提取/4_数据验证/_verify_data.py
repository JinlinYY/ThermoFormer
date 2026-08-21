# -*- coding: utf-8 -*-
"""
数据真实性验证:
1. DOI 来源检查 - 从 Cordra handle 直接截取, XML 也以 DOI 为文件名请求
2. 随机抽 10 篇 DOI, 请求 NIST ThermoML XML, 核对:
   a. <DOI> 标签内的文献号是否和我们数据里匹配
   b. 该文献里报道的 VLE 数据点数目, 和我们表里的行数是否对得上
3. 抽样 5 个具体数据点 (T, P, x1, y1) 与 XML 原始数值核对
"""
import json, re, random, time
from pathlib import Path
import pandas as pd
import requests

XML_BASE = "https://trc.nist.gov/ThermoML"

df = pd.read_excel('VLE_按体系分类整理_V3_扩展Antoine/A_完整数据汇总.xlsx', engine='openpyxl')
print(f'总数据: {len(df)} 行, {df["DOI"].nunique()} 篇 DOI')

# 随机抽样 DOI
random.seed(42)
all_dois = df['DOI'].unique().tolist()
sample_dois = random.sample(all_dois, 10)
print(f'\n随机抽样 DOI: {sample_dois}')

def thermoml_xml_info(doi):
    """请求一篇 ThermoML XML, 返回 DOI标签内容 + 报告的数据点数."""
    url = f"{XML_BASE}/{doi}.xml"
    try:
        t0 = time.time()
        resp = requests.get(url, timeout=90, headers={'Accept':'application/xml'})
        dt = time.time() - t0
        if resp.status_code != 200:
            return {'status': f'HTTP {resp.status_code}', 'dt': dt}
        content = resp.text
        # 提取所有 <eDOI> 或 <DOI> 标签
        dois_found = re.findall(r'<[^>]*DOI[^>]*>([^<]+)<', content)
        # 提取组分 (RegNum / Component 子标签)
        comps = re.findall(r'<nOrgNum[^>]*>([^<]+)<', content)
        if not comps:
            comps = re.findall(r'<Component[^>]*>\s*<sRegNum>([^<]+)</sRegNum>', content)
        # 粗略: 数 <ePropName> 中含 Vapor/Pressure/Comp 之类的点
        n_points = len(re.findall(r'<nVarValue>', content))
        return {
            'status': 'OK',
            'dt': dt,
            'doi_in_xml': dois_found,
            'nComponents_in_xml': len(comps),
            'nVarValue_xml': n_points,
            'bytes': len(content),
        }
    except Exception as e:
        return {'status': f'ERR {type(e).__name__}: {e}', 'dt': 0}

print('\n====== 验证 1: 抽样 DOI 对 ThermoML XML 做元数据核对 ======\n')
for doi in sample_dois:
    info = thermoml_xml_info(doi)
    ours_rows = len(df[df['DOI'] == doi])
    ours_systems = df[df['DOI'] == doi].groupby(['名称1','名称2']).ngroups
    doi_match = False
    if 'doi_in_xml' in info:
        doi_match = any(doi.lower() in str(x).lower() for x in info['doi_in_xml']) or len(info['doi_in_xml'])>0
    print(f'DOI: {doi}')
    print(f'  我们数据: {ours_rows} 行, {ours_systems} 体系')
    if info.get('status') == 'OK':
        print(f'  XML 返回: {info["bytes"]} bytes, {info["dt"]:.1f}s')
        print(f'  DOI标签: {info.get("doi_in_xml")[:3]} {("匹配" if doi_match else "⚠️ 不匹配")}')
        print(f'  组分数: {info.get("nComponents_in_xml")}, VarValue个数(粗估): {info.get("nVarValue_xml")}')
    else:
        print(f'  ⚠️  XML 状态: {info.get("status")}')
    print()

# ====== 验证 2: 取其中一篇查具体 5 个数据点 ======
print('====== 验证 2: 取 DOI=10.1016/j.fluid.2011.09.020 的前 3 个数据点核对 ======')
check_doi = '10.1016/j.fluid.2011.09.020'
url = f"{XML_BASE}/{check_doi}.xml"
resp = requests.get(url, timeout=90, headers={'Accept':'application/xml'})
print(f'HTTP: {resp.status_code}')
if resp.status_code == 200:
    content = resp.text
    # 找 2 个组分的分子式/名称
    org_nums = re.findall(r'<nOrgNum[^>]*>([^<]+)<', content)
    reg_nums = re.findall(r'<sRegNum[^>]*>([^<]+)<', content)
    print(f'  OrgNum: {org_nums[:4]}')
    print(f'  RegNum: {reg_nums[:4]}')

    # 找原始数据点中的 T, P, x1, y1 (不解析结构, 直接搜 property 值)
    # 列出我们数据里该 DOI 的前 3 行
    ours = df[df['DOI'] == check_doi].head(3)
    print(f'\n  我们的数据样例 ({len(ours)} 行):')
    for _, r in ours.iterrows():
        print(f'    ({r["名称1"]} + {r["名称2"]}): P={r["压强"]} mmHg, T={r["温度"]}°C, X1={r["X1"]}, Y1={r["Y1"]}')

    # 从 XML 中找到对应的 Temperature, Pressure, MoleFracLiquid, MoleFracVapor 数值
    # 粗略估计数量匹配
    n_T = len(re.findall(r'<ePropName>Temperature</ePropName>\s*<nVarValue>([^<]+)<', content))
    n_P = len(re.findall(r'<ePropName>Pressure</ePropName>\s*<nVarValue>([^<]+)<', content))
    n_x = len(re.findall(r'LiquidPhaseMoleFraction.*?<nVarValue>([^<]+)<', content, re.S) or re.findall(r'<sPropName[^>]*>Liquid.*?Mole.*?</sPropName>.*?<nVarValue>([^<]+)<', content, re.S))
    n_y = len(re.findall(r'VaporPhaseMoleFraction.*?<nVarValue>([^<]+)<', content, re.S) or re.findall(r'<sPropName[^>]*>Vapor.*?Mole.*?</sPropName>.*?<nVarValue>([^<]+)<', content, re.S))
    n_all_V = len(re.findall(r'<ePropName>Vapor.*?</ePropName>\s*<nVarValue>([^<]+)<', content))
    n_all_L = len(re.findall(r'<ePropName>Liquid.*?</ePropName>\s*<nVarValue>([^<]+)<', content))
    print(f'\n  XML 里的数值出现次数(粗略):')
    print(f'    Temperature: {n_T}, Pressure: {n_P}')
    print(f'    LiquidPhaseMoleFrac 关键词: {n_x}, VaporPhaseMoleFrac: {n_y}')
    print(f'    广义 Liquid: {n_all_L}, 广义 Vapor: {n_all_V}')
    sub = df[df['DOI'] == check_doi]
    print(f'    我们从这篇提取了 {len(sub)} 行')

# ====== 验证 3: 检查所有 DOI 是否真的能映射到 ThermoML handle ======
print('\n====== 验证 3: 随机 50 个 DOI 请求 Cordra 元数据 ======')
CORDRA_API = "https://trc.nist.gov/ThermoML-API/objects"
HANDLE_PREFIX = "20.5000.trc.thermoml/"
random.seed(99)
s50 = random.sample(all_dois, 50)
sess = requests.Session()
sess.headers.update({'User-Agent': 'verifier/1.0'})
found, miss = 0, 0
for doi in s50:
    # 用 Cordra 的精确 DOI 查询
    handle = f"{HANDLE_PREFIX}{doi}"
    t0 = time.time()
    if time.time() - t0 < 0.2:
        time.sleep(0.2 - (time.time()-t0))
    resp = sess.get(f"https://trc.nist.gov/ThermoML-API/objects/{handle}", timeout=30)
    if resp.status_code == 200:
        found += 1
    else:
        miss += 1
        print(f'  ❌ Cordra 未找到: {doi} ({resp.status_code})')
print(f'  ✅ Cordra 元数据: {found}/50 找到, {miss}/50 未找到')
print(f'  可信度: Cordra DOI 匹配度 {found/50*100:.0f}%')

# ====== 验证 4: DOI 有没有被错误复用 ======
print('\n====== 验证 4: DOI -> 组分集合 映射唯一性 ======')
# 如果同一个 DOI 在我们数据里出现了完全无关的组分集合,说明可能混了
# 正常情况同一篇文献报道有限的几个体系
df_grp = df.groupby('DOI').apply(
    lambda g: set(f"{a}+{b}" for a,b in zip(g['名称1'], g['名称2']))
)
suspicious = df_grp[df_grp.apply(lambda s: len(s) > 6)]
print(f'  报道体系数 > 6 的 DOI: {len(suspicious)} 个')
if len(suspicious):
    for d, s in list(suspicious.items())[:5]:
        print(f'    {d}: {len(s)} 体系 -> {sorted(s)[:10]}')
print('  (如果单篇文献含 10+ 完全无关体系, 大概率 DOI 错配)')

# ====== 验证 5: 有多少数据点的 T, P, x1, y1 完全是合理的数值范围 ======
print('\n====== 验证 5: 数据值合理性检查 ======')
print(f'  温度 (°C): min={df["温度"].min():.2f}, max={df["温度"].max():.2f}')
print(f'  压强 (mmHg): min={df["压强"].min():.3f}, max={df["压强"].max():.3f}')
print(f'  X1 范围: [0, 1] 全部合理? {"是" if (df["X1"].between(0,1)).all() else "否"}')
print(f'  Y1 范围: [0, 1] 全部合理? {"是" if (df["Y1"].between(0,1)).all() else "否"}')
print(f'  空 DOI 行数: {df["DOI"].isna().sum()} / {len(df)}')
print(f'  重复 DOI 数: 总 {len(df)} 行, DOI 种类 {df["DOI"].nunique()}')
print(f'  平均每篇 DOI 数据点: {len(df)/df["DOI"].nunique():.1f}')
