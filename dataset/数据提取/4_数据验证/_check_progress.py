# -*- coding: utf-8 -*-
"""统计 NIST ThermoML 已处理进度和剩余待跑量"""
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent

# 全量 handle
handles = json.loads((WORK / "_all_handles.json").read_text(encoding="utf-8"))
all_dois = []
for h in handles:
    if "/" in h:
        doi = h.split("/", 1)[1]
    else:
        doi = h
    all_dois.append(doi)
print(f"全量 DOI 总数: {len(all_dois)}")

# 已处理（四元 batch3）
done = set()
cache3 = WORK / "vle_quaternary_batch3_cache.json"
if cache3.exists():
    cache = json.loads(cache3.read_text(encoding="utf-8"))
    done |= set(cache.keys())
print(f"四元 batch3 已处理: {len(done)}")

# 其他缓存
for f in ["vle_quaternary_cache.json", "vle_progress_cache.json", "vle_ternary_batch2_cache.json"]:
    p = WORK / f
    if p.exists():
        c = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(c, dict):
            done |= set(c.keys())
print(f"合并所有缓存后已处理: {len(done)}")

# 剩余
todo = [d for d in all_dois if d not in done]
print(f"剩余未跑: {len(todo)}")
print(f"前 10 个剩余 DOI 示例: {todo[:10]}")
