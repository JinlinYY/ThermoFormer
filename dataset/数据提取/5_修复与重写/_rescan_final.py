# -*- coding: utf-8 -*-
"""
直接从 _all_handles.json 跑剩余文献, 每篇都立即写入 CSV。
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

with open("_all_handles.json", "r") as f:
    ALL_HANDLES = json.load(f)

with open("vle_progress_cache.json", "r", encoding="utf-8") as f:
    cache = json.load(f)

# CSV 中已有的 DOI
existing_dois = set()
if Path("vle_binary_expand.csv").exists():
    existing_df = pd.read_csv("vle_binary_expand.csv", encoding="utf-8-sig")
    existing_dois = set(existing_df["DOI"].dropna().unique())

# 需要解析的: ok 但 CSV 没有
needs = []
for handle, info in cache.items():
    if isinstance(info, dict) and info.get("status") == "ok":
        doi = handle_to_doi(handle)
        if doi and doi not in existing_dois:
            needs.append((handle, doi))

print(f"需要解析: {len(needs)} 篇 (CSV已有 {len(existing_dois)} DOI)")

# 构建会话
sess = requests.Session()
sess.headers.update({"User-Agent": "thermoml-vle-expand/2.0", "Accept": "application/xml"})
retry = Retry(total=3, backoff_factor=2.0, status_forcelist=(429,500,502,503,504))
sess.mount("https://", HTTPAdapter(max_retries=retry))

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_vle_expand import extract_binary_vle_rows

OUT_CSV = Path("vle_binary_expand.csv")

# 增量读取/写入 CSV
if OUT_CSV.exists():
    all_df = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
else:
    all_df = pd.DataFrame()

ok_count = 0
empty_count = 0
error_count = 0

for i, (handle, doi) in enumerate(needs, 1):
    url = f"{XML_BASE}/{doi}.xml"
    try:
        time.sleep(0.3)
        resp = sess.get(url, timeout=60)
        resp.raise_for_status()
        xml_bytes = resp.content
        doc = tml.parse_thermoml(xml_bytes)
        rows = extract_binary_vle_rows(doc, doi, url)
        
        if rows:
            new_df = pd.DataFrame(rows)
            new_df = new_df.dropna(subset=["压强","温度","X1","Y1"]).copy()
            new_df = new_df[(new_df["X1"]>=0)&(new_df["X1"]<=1)&(new_df["Y1"]>=0)&(new_df["Y1"]<=1)].copy()
            
            # 直接追加到 CSV
            if len(new_df) > 0:
                new_df.to_csv(OUT_CSV, mode="a", header=not OUT_CSV.exists(), index=False, encoding="utf-8-sig")
                all_df = pd.concat([all_df, new_df], ignore_index=True)
                all_df = all_df.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
                all_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
                ok_count += 1
            else:
                empty_count += 1
        else:
            empty_count += 1
    except Exception as exc:
        error_count += 1
        with open("download_parse_error.log", "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {doi} | {exc!r}\n")
    
    if i % 50 == 0:
        cur = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
        print(f"  {i}/{len(needs)} | ok={ok_count} empty={empty_count} err={error_count} | CSV={len(cur)} rows, {cur['DOI'].nunique()} DOIs")

# 最终去重
final = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
final = final.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
final.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n完成: {len(final)} 行, {final['DOI'].nunique()} DOI")
print(f"新增: ok={ok_count}, empty={empty_count}, err={error_count}")
