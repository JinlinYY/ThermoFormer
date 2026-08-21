# -*- coding: utf-8 -*-
"""
修正 XML_BASE 后重新做严谨的验证.
"""
import json, re, random, time
import pandas as pd
import requests

XML_BASE = "https://trc.nist.gov/ThermoML"

df = pd.read_excel('VLE_按体系分类整理_V3_扩展Antoine/A_完整数据汇总.xlsx', engine='openpyxl')
print(f'总数据: {len(df)} 行, {df["DOI"].nunique()} DOI')

random.seed(42)
all_dois = df['DOI'].unique().tolist()
sample = random.sample(all_dois, 5)
print(f'抽样 5 篇 DOI: {sample}\n')

sess = requests.Session()
sess.headers.update({'User-Agent': 'verify/1.0'})

for doi in sample:
    url = f"{XML_BASE}/{doi}.xml"
    t0 = time.time()
    resp = sess.get(url, timeout=120)
    dt = time.time() - t0
    time.sleep(max(0, 0.5 - dt))

    our_rows = df[df['DOI'] == doi]
    print(f'==== DOI: {doi} ====')
    print(f'  HTTP {resp.status_code}, 字节数: {len(resp.content)}, 用时: {dt:.1f}s')
    print(f'  我们提取: {len(our_rows)} 行, {our_rows.groupby(["名称1","名称2"]).ngroups} 体系')

    if resp.status_code != 200:
        print('  ❌ 无法获取 XML')
        continue

    content = resp.text[:200000]  # 防止过大

    # ---- 1) DOI / 标题 / 期刊 关键词 ----
    # ThermoML 标准标签
    m_doi = re.findall(r'<DOI>([^<]+)</DOI>|<sDOI>([^<]+)</sDOI>', content)
    m_title = re.findall(r'<sTitle>([^<]+)</sTitle>|<nTitle[^>]*>([^<]+)</nTitle>', content)
    m_journal = re.findall(r'<sJournal>([^<]+)</sJournal>|<nJournal>([^<]+)</nJournal>', content)
    m_year = re.findall(r'<nYearPub[^>]*>([^<]+)</nYearPub>', content)
    m_author = re.findall(r'<sAuthor[^>]*>([^<]+)</sAuthor>', content)

    doi_matches = []
    for a, b in m_doi:
        if a: doi_matches.append(a.strip())
        if b: doi_matches.append(b.strip())
    title_matches = []
    for a, b in m_title:
        if a: title_matches.append(a.strip())
        if b: title_matches.append(b.strip())
    journal_matches = []
    for a, b in m_journal:
        if a: journal_matches.append(a.strip())
        if b: journal_matches.append(b.strip())

    doi_hit = any(doi.lower() in d.lower() for d in doi_matches) or len(doi_matches) > 0
    print(f'  DOI 标签: {doi_matches[:4]} {("✅匹配" if doi_hit else "⚠️")}')
    if title_matches:
        print(f'  文献标题: {title_matches[0][:120]}')
    if journal_matches:
        print(f'  期刊: {journal_matches[0]} {m_year[:2]}')
    if m_author:
        print(f'  作者: {m_author[:3]}')

    # ---- 2) 组分 核对 ----
    reg_nums = re.findall(r'<sRegNum>([^<]+)</sRegNum>', content)
    org_nums = re.findall(r'<nOrgNum[^>]*>([^<]+)</nOrgNum>', content)
    cas_nums = re.findall(r'<sCASRN[^>]*>([^<]+)</sCASRN>', content)
    names = re.findall(r'<sName[^>]*>([^<]+)</sName>', content)
    print(f'  组分RegNum: {reg_nums[:4]}')
    print(f'  组分OrgNum: {org_nums[:4]}')
    print(f'  组分CAS: {cas_nums[:4]}')
    print(f'  组分名称: {names[:4]}')
    # 列出我们的体系
    for (n1, n2), g in our_rows.groupby(['名称1', '名称2']):
        print(f'    我们的体系: {n1} + {n2} = {len(g)} 点')

    # ---- 3) 数据点数量对比 ----
    n_T = len(re.findall(r'(<ePropName>Temperature</ePropName>|<sPropName[^>]*Temperature[^>]*</sPropName>)\s*<nVarValue>([^<]+)<', content))
    n_P = len(re.findall(r'(<ePropName>Pressure</ePropName>|<sPropName[^>]*Pressure[^>]*</sPropName>)\s*<nVarValue>([^<]+)<', content))
    n_x = len(re.findall(r'MoleFraction.*?Liquid.*?<nVarValue>([^<]+)<', content, re.S)) or len(re.findall(r'Liquid.*?MoleFraction.*?<nVarValue>([^<]+)<', content, re.S))
    n_y = len(re.findall(r'MoleFraction.*?Vapor.*?<nVarValue>([^<]+)<', content, re.S)) or len(re.findall(r'Vapor.*?MoleFraction.*?<nVarValue>([^<]+)<', content, re.S))

    # 更精确的: 所有 VLE property 出现
    n_VLE_datasets = len(re.findall(r'<ePropName>.*?VaporLiqEquil.*?</ePropName>', content))
    n_propval = len(re.findall(r'<nVarValue>', content))

    print(f'  XML 里 nVarValue 总数: {n_propval}')
    print(f'  Temperature 值数: {n_T}, Pressure 值数: {n_P}')
    print(f'  LiquidMoleFrac (模糊): {n_x}, VaporMoleFrac (模糊): {n_y}')
    print(f'  VaporLiqEquil 数据集标识: {n_VLE_datasets}')
    print()

# ====== 补充: 随机 5 篇 DOI, 检查 Cordra 精确匹配 ======
HANDLE_PREFIX = "20.5000.trc.thermoml/"
s2 = random.sample(all_dois, 10)
print('\n====== Cordra 元数据精确匹配 (10/387) ======')
ok, bad = 0, 0
for doi in s2:
    handle = HANDLE_PREFIX + doi
    resp = sess.get(f"https://trc.nist.gov/ThermoML-API/objects/{handle}", timeout=30)
    time.sleep(0.3)
    if resp.status_code == 200:
        payload = resp.json()
        content = str(payload)[:1500].lower()
        # 有没有 DOI 回显
        echo = doi.split('/')[0] in content or doi.split('/')[1] in content
        ok += 1
        print(f'  ✅ {doi}  Cordra 找到, DOI回显={"是" if echo else "无回显(句柄已含DOI)"}')
    else:
        bad += 1
        print(f'  ❌ {doi}  Cordra HTTP {resp.status_code}')
print(f'  Cordra 匹配: {ok}/10, 缺失: {bad}/10')

print('\n========== 合理性范围检查 ==========')
print(f'  温度(°C): min={df["温度"].min():.2f}, max={df["温度"].max():.2f}')
print(f'  压强(mmHg): min={df["压强"].min():.3f}, max={df["压强"].max():.3f}')
print(f'  压强(kPa换算): min={df["压强"].min()*0.133322:.2f} kPa, max={df["压强"].max()*0.133322:.0f} kPa')
print(f'  X1 有效率: {(df["X1"].between(0,1)).mean()*100:.1f}%')
print(f'  Y1 有效率: {(df["Y1"].between(0,1)).mean()*100:.1f}%')
print(f'  空 SMILES 比例: smiles1={((df["smiles1"].fillna("")=="").mean()*100):.1f}%, smiles2={((df["smiles2"].fillna("")=="").mean()*100):.1f}%')
print(f'  DOI 字符串中 "10." 比例: {(df["DOI"].str.startswith("10.", na=False)).mean()*100:.1f}%')
print(f'  分子式1 非空: {df["分子式1"].notna().mean()*100:.1f}%, 分子式2 非空: {df["分子式2"].notna().mean()*100:.1f}%')
