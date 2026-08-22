# -*- coding: utf-8 -*-
"""
重新解析缓存中 ok 文献,把 VLE 数据写入 CSV。
加限流和重试。
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

XML_BASE = "https://trc.nist.gov/ThermoML"
HANDLE_PREFIX = "20.5000.trc.thermoml/"

def handle_to_doi(handle):
    if HANDLE_PREFIX in handle:
        return handle.split(HANDLE_PREFIX, 1)[1]
    return handle

with open("vle_progress_cache.json", "r", encoding="utf-8") as f:
    cache = json.load(f)

existing_dois = set()
if Path("vle_binary_expand.csv").exists():
    existing_df = pd.read_csv("vle_binary_expand.csv", encoding="utf-8-sig")
    existing_dois = set(existing_df["DOI"].dropna().unique())

print(f"CSV 中已有 {len(existing_dois)} 篇 DOI")

# 需要解析的
needs = []
for handle, info in cache.items():
    if isinstance(info, dict) and info.get("status") == "ok":
        doi = handle_to_doi(handle)
        if doi and doi not in existing_dois:
            needs.append((handle, doi))

print(f"需要解析: {len(needs)} 篇")

# 构建会话
sess = requests.Session()
sess.headers.update({"User-Agent": "thermoml-vle-expand/2.0", "Accept": "application/xml"})
retry = Retry(total=3, backoff_factor=2.0, status_forcelist=(429,500,502,503,504))
sess.mount("https://", HTTPAdapter(max_retries=retry))

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_vle_expand import extract_binary_vle_rows

OUT_CSV = Path("vle_binary_expand.csv")
new_rows = []
errors = 0

for i, (handle, doi) in enumerate(needs, 1):
    url = f"{XML_BASE}/{doi}.xml"
    try:
        time.sleep(0.4)  # 限流
        resp = sess.get(url, timeout=60)
        resp.raise_for_status()
        xml_bytes = resp.content
        doc = tml.parse_thermoml(xml_bytes)
        rows = extract_binary_vle_rows(doc, doi, url)
        new_rows.extend(rows)
    except Exception as exc:
        errors += 1
        with open("download_parse_error.log", "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {doi} | {exc!r}\n")
    
    if i % 50 == 0:
        print(f"  {i}/{len(needs)} | new_rows={len(new_rows)} | errors={errors}")

# 合并
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
    print(f"\n完成: {len(combined)} 行, {combined['DOI'].nunique()} 篇 DOI")
    print(f"新增: {len(new_df)} 行, {errors} 错误")
else:
    print("\n无新增数据")
