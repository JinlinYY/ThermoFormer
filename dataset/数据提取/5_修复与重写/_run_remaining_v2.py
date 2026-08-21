# -*- coding: utf-8 -*-
"""
跑剩余 ThermoML 文献, 每 50 篇把新数据写入 CSV, 断点续跑。
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

# 加载全部句柄
with open("_all_handles.json", "r") as f:
    ALL_HANDLES = json.load(f)

# 加载缓存
CACHE_FILE = Path("vle_progress_cache.json")
if CACHE_FILE.exists():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

# 找出剩余的
remaining = []
for h in ALL_HANDLES:
    v = cache.get(h)
    if not isinstance(v, dict) or v.get("status") not in ("ok","empty","error"):
        remaining.append(h)
    elif isinstance(v, dict) and v.get("status") == "ok" and "doi" not in v:
        remaining.append(h)  # 需要重新解析
print(f"总: {len(ALL_HANDLES)}, 剩余: {len(remaining)}")

sess = fve.build_session(rate_limit=0.4)

OUT_CSV = Path("vle_binary_expand.csv")
new_rows = []
ok_count = 0
empty_count = 0
error_count = 0
processed = 0

for i, handle in enumerate(remaining, 1):
    doi = fve.handle_to_doi(handle)
    if not doi:
        cache[handle] = {"status": "error", "msg": "no doi"}
        error_count += 1
        processed += 1
        continue

    try:
        xml_bytes = fve.fetch_xml_bytes(sess, doi)
        doc = tml.parse_thermoml(xml_bytes)
        xml_url = f"{fve.XML_BASE}/{doi}.xml"
        rows = fve.extract_binary_vle_rows(doc, doi, xml_url)
        
        if rows:
            new_rows.extend(rows)
            ok_count += 1
            cache[handle] = {"status": "ok", "n_rows": len(rows), "doi": doi}
        else:
            empty_count += 1
            cache[handle] = {"status": "empty", "doi": doi}
    except Exception as exc:
        cache[handle] = {"status": "error", "msg": str(exc)[:200], "doi": doi}
        error_count += 1
        with open("download_parse_error.log", "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {doi} | {exc!r}\n")
    
    processed += 1
    
    # 每 50 篇保存一次
    if processed % 50 == 0:
        # 写入 CSV
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
            new_rows = []  # 清空已保存的数据
        
        # 保存缓存
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        
        rows_saved = len(combined) if new_rows else (len(pd.read_csv(OUT_CSV, encoding="utf-8-sig")) if OUT_CSV.exists() else 0)
        print(f"  {processed}/{len(remaining)} | ok={ok_count} empty={empty_count} err={error_count} | CSV={rows_saved} rows")

# 最终保存剩余数据
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

with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False)

final_df = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
print(f"\n完成: ok={ok_count}, empty={empty_count}, err={error_count}")
print(f"最终 CSV: {len(final_df)} 行, {final_df['DOI'].nunique()} 篇")
