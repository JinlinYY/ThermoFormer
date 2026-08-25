import pandas as pd, json

df = pd.read_csv('vle_binary_expand.csv', encoding='utf-8-sig')
print(f'CSV: {len(df)} rows, {df["DOI"].nunique()} DOIs')
print(f'Cols: {list(df.columns)}')

with open('vle_progress_cache.json','r',encoding='utf-8') as f:
    cache = json.load(f)
ok = sum(1 for v in cache.values() if isinstance(v,dict) and v.get('status')=='ok')
empty = sum(1 for v in cache.values() if isinstance(v,dict) and v.get('status')=='empty')
error = sum(1 for v in cache.values() if isinstance(v,dict) and v.get('status')=='error')
print(f'Cache: ok={ok}, empty={empty}, error={error}, total={len(cache)}')
