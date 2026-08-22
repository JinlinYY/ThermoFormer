# -*- coding: utf-8 -*-
"""
用已保存的 _all_handles.json (11922 条) 跑剩余 ThermoML 文献的二元 VLE 数据。
复用 fetch_vle_expand.py 的逻辑, 但跳过已处理的文献。
输出格式严格对齐: 名称1, 分子式1, smiles1, 名称2, 分子式2, smiles2,
                    一致性检验方法一, 一致性检验方法二, 压强, 温度, X1, Y1, DOI
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
from thermoml_io.classification import classify_property, normalize_term

# 复用 fetch_vle_expand.py 的函数
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_vle_expand as fve

# 加载已保存的句柄
with open("_all_handles.json", "r") as f:
    ALL_HANDLES = json.load(f)
print(f"加载 {len(ALL_HANDLES)} 条句柄")

# 加载缓存
CACHE_FILE = Path("vle_progress_cache.json")
if CACHE_FILE.exists():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

# 找出剩余的句柄
remaining = []
for h in ALL_HANDLES:
    if h not in cache or not isinstance(cache[h], dict) or cache[h].get("status") not in ("ok","empty","error"):
        remaining.append(h)
print(f"已处理: {len(ALL_HANDLES) - len(remaining)}, 剩余: {len(remaining)}")

# 构建会话
sess = fve.build_session(rate_limit=0.4)

# 处理剩余文献
OUT_CSV = Path("vle_binary_expand.csv")
rows_total = 0
new_rows = []
processed = 0
ok_count = 0
empty_count = 0
error_count = 0

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
            cache[handle] = {"status": "ok", "n_rows": len(rows)}
        else:
            empty_count += 1
            cache[handle] = {"status": "empty"}
    except Exception as exc:
        cache[handle] = {"status": "error", "msg": str(exc)[:200]}
        error_count += 1
        # 写错误日志
        with open("download_parse_error.log", "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {doi} | {exc!r}\n")
    
    processed += 1
    
    # 每 50 篇保存一次
    if processed % 50 == 0:
        rows_total = len(new_rows)
        print(f"  进度 {processed}/{len(remaining)} | ok={ok_count} empty={empty_count} err={error_count} | 本次新增 {rows_total} 行")
        # 保存缓存
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

# 最终保存缓存
with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False)

print(f"\n处理完成: ok={ok_count}, empty={empty_count}, err={error_count}")
print(f"本次新增 {len(new_rows)} 行 VLE 数据")

# 合并到 CSV
if new_rows:
    new_df = pd.DataFrame(new_rows)
    # 清洗
    new_df = new_df.dropna(subset=["压强","温度","X1","Y1"]).copy()
    new_df = new_df[(new_df["X1"]>=0)&(new_df["X1"]<=1)&(new_df["Y1"]>=0)&(new_df["Y1"]<=1)].copy()
    
    if OUT_CSV.exists():
        existing = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["名称1","名称2","压强","温度","X1","Y1","DOI"])
    else:
        combined = new_df
    
    combined.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"合并后 CSV: {len(combined)} 行, {combined['DOI'].nunique()} 篇文献")
else:
    print("无新增数据")
