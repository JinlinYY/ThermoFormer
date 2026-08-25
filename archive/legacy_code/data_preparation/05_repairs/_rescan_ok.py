# -*- coding: utf-8 -*-
"""
把缓存中已处理的文献重新解析一遍,把 VLE 数据写入 CSV。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import thermoml_io as tml
import fetch_vle_expand as fve

with open("_all_handles.json", "r") as f:
    ALL_HANDLES = json.load(f)

with open("vle_progress_cache.json", "r", encoding="utf-8") as f:
    cache = json.load(f)

# 找出已处理但 CSV 中没有的文献
existing_dois = set()
if Path("vle_binary_expand.csv").exists():
    existing_df = pd.read_csv("vle_binary_expand.csv", encoding="utf-8-sig")
    existing_dois = set(existing_df["DOI"].dropna().unique())

print(f"CSV 中已有 {len(existing_dois)} 篇 DOI")

# 需要重新解析的: ok 状态但 CSV 中没有的
needs_parsing = []
for handle, info in cache.items():
    if isinstance(info, dict) and info.get("status") == "ok":
        doi = info.get("doi", "") or fve.handle_to_doi(handle)
        if doi and doi not in existing_dois:
            needs_parsing.append(handle)

print(f"需要重新解析: {len(needs_parsing)} 篇")

# 重新解析
sess = fve.build_session(rate_limit=0.4)
OUT_CSV = Path("vle_binary_expand.csv")
new_rows = []

for i, handle in enumerate(needs_parsing, 1):
    doi = fve.handle_to_doi(handle)
    if not doi:
        continue
    
    try:
        xml_bytes = fve.fetch_xml_bytes(sess, doi)
        doc = tml.parse_thermoml(xml_bytes)
        xml_url = f"{fve.XML_BASE}/{doi}.xml"
        rows = fve.extract_binary_vle_rows(doc, doi, xml_url)
        new_rows.extend(rows)
    except Exception as exc:
        print(f"  错误 {doi}: {exc}")
    
    if i % 50 == 0:
        print(f"  进度 {i}/{len(needs_parsing)}, 新增 {len(new_rows)} 行")

# 合并到 CSV
if new_rows:
    new_df = pd.DataFrame(new_rows)
    new_df = new_df.dropna(subset=["压强","温度","X1","Y1"]).copy()
    new_df = new_df[(new_df["X1"]>=0)&(new_df["X1"]<=1)&(new_df["Y1"]>=0)&(new_df["Y1"]<=1)].copy()
    
    if OUT_CSV.exists():
        existing = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
    else:
        combined = new_df
    
    combined.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n合并完成: {len(combined)} 行, {combined['DOI'].nunique()} 篇 DOI")
    print(f"新增: {len(new_df)} 行")
else:
    print("\n无新增数据")
