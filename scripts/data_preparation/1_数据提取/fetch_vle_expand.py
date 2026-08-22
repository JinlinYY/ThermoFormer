# -*- coding: utf-8 -*-
"""
NIST ThermoML 二元汽液相平衡 (VLE) 数据在线抽取流水线
========================================================
功能：
  1. 通过 NIST ThermoML Cordra REST API（Lucene 语法）检索全部 ThermoML 文献元数据，
     获取每篇文献的 Cordra 句柄（内含 DOI）；
  2. 由 DOI 构造经典 NIST ThermoML XML 下载 URL，用 requests 在线流式获取单份 XML 文本，
     直接交由 thermoml-io 在内存中解析（不落地保存大量 xml 文件到磁盘）；
  3. 仅保留【二元组分 + 汽液相平衡 VLE】实验点，剔除纯组分/三元及以上/VLLE/LLLE/焓密度等；
  4. 提取：组分1/2 名称、分子式、CAS、温度 T、压力 P、液相摩尔分数 x1、气相摩尔分数 y1，
     并保留 DOI、文献来源、原始 NIST 资源链接；
  5. 单位与现有 water/alcohol 数据集完全对齐：温度 °C、压强 mmHg、摩尔分数无量纲；
  6. 数据清洗、限流重试、断点续跑缓存、错误日志，整体流程不崩溃；
  7. 只导出原始实验测量点，不做任何热力学拟合。

依赖：pandas, requests, thermoml-io   (pip install pandas requests thermoml-io)

运行示例：
  # 全量扩充（断点续跑，可重复执行）
  python fetch_vle_expand.py
  # 先小批量试跑（只处理前 200 篇文献）
  python fetch_vle_expand.py --max-papers 200
  # 调整限流间隔（秒）
  python fetch_vle_expand.py --rate-limit 0.5
  # 从头开始（忽略缓存，重写输出 csv）
  python fetch_vle_expand.py --fresh
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import thermoml_io as tml
from thermoml_io.classification import classify_property, normalize_term

# ---------------------------------------------------------------------------
# 基本常量
# ---------------------------------------------------------------------------
CORDRA_API = "https://trc.nist.gov/ThermoML-API/objects"      # Cordra 检索端点
CORDRA_QUERY = "type:TRCTml4"                                  # Lucene：全部 ThermoML 文献
XML_BASE = "https://trc.nist.gov/ThermoML"                    # 经典 XML 文件服务器
HANDLE_PREFIX = "20.5000.trc.thermoml/"                       # Cordra 句柄前缀，其后即 DOI

# 输出文件（与现有 water.xlsx/alcohol.xlsx 列名严格对齐，末尾追加元数据列）
OUT_COLUMNS = [
    "名称1", "分子式1", "smiles1", "名称2", "分子式2", "smiles2",
    "一致性检验方法一", "一致性检验方法二", "压强", "温度", "X1", "Y1",
    # 元数据（保留以备溯源；pd.concat 时现有数据集这些列自动补 NaN）
    "CAS1", "CAS2", "DOI", "文献来源", "NIST资源链接",
]
OUT_CSV = Path(__file__).resolve().parent / "vle_binary_expand.csv"
ERR_LOG = Path(__file__).resolve().parent / "download_parse_error.log"
CACHE_FILE = Path(__file__).resolve().parent / "vle_progress_cache.json"

# 单位换算系数
KPA_TO_MMHG = 7.50061683      # 1 kPa = 7.50061683 mmHg （101.325 kPa = 760 mmHg）

# 相态归一判定
GAS_PHASES = {"gas", "vapor", "vapour"}


def _is_liquid(phase: str | None) -> bool:
    return bool(phase) and normalize_term(phase).startswith("liquid")


def _is_gas(phase: str | None) -> bool:
    return bool(phase) and normalize_term(phase) in GAS_PHASES


def _is_mole_fraction(definition) -> bool:
    """判定 quantity 是否为（液/气相）摩尔分数定义。

    用 startswith 而非 in，避免误匹配 'Henry's Law constant (mole fraction scale), kPa'
    这类其实是压力量、但名字里含 mole fraction 字样的属性。
    """
    return normalize_term(definition.name).startswith("mole_fraction")


# ---------------------------------------------------------------------------
# HTTP 会话：限流 + 重试
# ---------------------------------------------------------------------------
def build_session(rate_limit: float, retries: int = 3) -> requests.Session:
    """构造带自动重试的 requests 会话。"""
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "thermoml-vle-expand/1.0 (research; contact: local)",
        "Accept": "application/json",
    })
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=1.5,            # 指数退避：1.5, 3, 6 ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess._rate_limit = rate_limit       # 自定义属性，记录最近请求时间
    sess._last_request_ts = 0.0
    return sess


def polite_get(sess: requests.Session, url: str, *, timeout: float, **kwargs) -> requests.Response:
    """带限流的 GET：保证两次请求间隔不少于 rate_limit 秒。kwargs 透传给 sess.get。"""
    elapsed = time.monotonic() - sess._last_request_ts
    if elapsed < sess._rate_limit:
        time.sleep(sess._rate_limit - elapsed)
    resp = sess.get(url, timeout=timeout, **kwargs)
    sess._last_request_ts = time.monotonic()
    return resp


# ---------------------------------------------------------------------------
# Cordra：检索全部文献句柄（一次请求返回完整 ID 列表，本地分批迭代）
# ---------------------------------------------------------------------------
def fetch_all_handles(sess: requests.Session) -> list[str]:
    """用 Lucene 语法 type:TRCTml4 检索全部 ThermoML 文献的 Cordra 句柄。

    Cordra 的 ids 模式在单次响应中返回全部标识符（约 1.2 万条，仅字符串，体积小），
    故无需服务端分页；本地按返回列表顺序分批处理即可。若一次请求因网络超时，
    将自动重试（见 build_session 的 Retry）。
    """
    params = {"query": CORDRA_QUERY, "ids": ""}
    last_err: Exception | None = None
    for attempt in range(1, 4):  # 额外做 3 轮整体重试
        try:
            resp = polite_get(sess, CORDRA_API, timeout=240, params=params)
            resp.raise_for_status()
            payload = resp.json()
            results = payload.get("results", [])
            size = payload.get("size")
            if not isinstance(results, list) or len(results) == 0:
                raise RuntimeError(f"Cordra 返回空结果: {payload}")
            if isinstance(size, int) and size != len(results):
                print(f"[警告] Cordra size({size}) 与返回条数({len(results)})不一致，"
                      f"将使用返回的 {len(results)} 条。")
            return list(results)
        except Exception as exc:  # 网络层错误整体重试
            last_err = exc
            print(f"[重试 {attempt}/3] 检索 Cordra 句柄失败: {exc!r}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"无法从 Cordra 获取文献句柄列表: {last_err!r}")


def handle_to_doi(handle: str) -> str | None:
    """句柄形如 20.5000.trc.thermoml/<DOI>，截取其后的 DOI。"""
    if HANDLE_PREFIX in handle:
        return handle.split(HANDLE_PREFIX, 1)[1]
    if "/" in handle:
        return handle.split("/", 1)[1]
    return None


# ---------------------------------------------------------------------------
# 单篇文献：在线获取 XML + thermoml-io 内存解析 + 二元 VLE 抽取
# ---------------------------------------------------------------------------
def fetch_xml_bytes(sess: requests.Session, doi: str) -> bytes:
    """requests 流式 GET 单份 ThermoML XML 文本，返回内存字节（不落地保存）。"""
    url = f"{XML_BASE}/{doi}.xml"
    resp = polite_get(sess, url, timeout=60, headers={"Accept": "application/xml"}, stream=True)
    # 流式读取到内存上限 100 MiB，避免异常大文件
    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > 100 * 1024 * 1024:
            raise RuntimeError(f"XML 过大(>{100}MiB)，放弃: {doi}")
        chunks.append(chunk)
    if resp.status_code != 200:
        raise RuntimeError(f"XML HTTP {resp.status_code}: {url}")
    return b"".join(chunks)


def _build_source(citation) -> str:
    """拼接文献来源字符串：作者 年 期刊 卷(页)。"""
    parts = []
    authors = " ".join(citation.authors[:3]) if citation.authors else ""
    if authors:
        parts.append(authors + (" et al." if len(citation.authors) > 3 else ""))
    if citation.year:
        parts.append(str(citation.year))
    if citation.publication_name:
        parts.append(str(citation.publication_name))
    if citation.volume:
        vol = str(citation.volume)
        if citation.pages:
            vol += f"({citation.pages})"
        parts.append(vol)
    return " ".join(parts).strip() or citation.title or "unknown"


def extract_binary_vle_rows(doc, doi: str, xml_url: str) -> list[dict]:
    """从已解析的 ThermoMLDocument 中抽取所有【二元 + VLE】实验点。

    返回行字典列表，键与 OUT_COLUMNS 对齐。

    核心设计：ThermoML 常把同一二元 VLE 系统的测量拆成多个"兄弟"数据集
    （一个存 T(x) 沸点曲线，另一个存 y1(x) 气相组成曲线），它们共享同一个
    液相摩尔分数变量 x1，且数据点按序号一一对应。本函数按 (体系, x1 组分)
    对兄弟数据集分组后，按点序号合并变量/属性值，从而还原完整的 (x1, y1, T, P)
    四元组。整组无 VLE 性质（即不是汽液相平衡）则跳过。
    """
    rows: list[dict] = []
    citation = doc.citation
    source_str = _build_source(citation)
    doi_str = citation.normalized_doi or doi

    # —— 1) 收集候选二元数据集：必须含液相摩尔分数（作为 x1 锚点）——
    candidates: list[tuple] = []  # (ds, comp1_id, cids)
    for ds in doc.datasets:
        if ds.system_type != "binary":
            continue
        cids = list(dict.fromkeys(ds.component_ids))  # 去重保序
        if len(cids) != 2:
            continue
        # 在变量和属性中查找液相摩尔分数作为 x1 锚点（变量优先）
        x1_def = None
        for v in ds.variables:
            if _is_mole_fraction(v) and _is_liquid(v.phase):
                x1_def = v
                break
        if x1_def is None:
            for p in ds.properties:
                if _is_mole_fraction(p) and _is_liquid(p.phase):
                    x1_def = p
                    break
        if x1_def is None:
            continue  # 无液相摩尔分数变量/属性，非典型 VLE 数据集（如 Henry 常数）
        comp1_id = x1_def.component_id
        if comp1_id is None:
            comp1_id = cids[0]
        if comp1_id not in cids:
            continue
        candidates.append((ds, comp1_id, cids))

    # —— 2) 按 (体系, x1 组分) 分组：同组视为同一 VLE 系统的兄弟测量集 ——
    groups: dict[tuple, list] = {}
    for ds, comp1_id, cids in candidates:
        groups.setdefault((frozenset(cids), comp1_id), []).append((ds, comp1_id, cids))

    for (_, comp1_id), members in groups.items():
        cids = members[0][2]
        comp2_id = next(c for c in cids if c != comp1_id)
        comp1 = doc.compound(comp1_id)
        comp2 = doc.compound(comp2_id)

        # 整组必须含至少一个 VLE 性质（气相摩尔分数，CompositionAtPhaseEquilibrium + Liquid+Gas）
        has_vle = any(
            classify_property(p, ds) == "VLE"
            for ds, _, _ in members
            for p in ds.properties
        )
        if not has_vle:
            continue  # 该体系不涉及汽液相平衡，跳过

        # 按"点数"分桶：同点数的成员视为同一实验的兄弟测量集，按点序号合并；
        # 不同点数的成员（如共沸点 4 行 vs 全组成曲线 34 行）各自独立。
        # 同组内若仍可能存在异构数据集（如 azeotrope 与 VLE 同点数），下面的
        # x1 值一致性校验会兜底——x1 序列不一致则拆分。
        from collections import defaultdict
        by_len: dict[int, list] = defaultdict(list)
        for m in members:
            by_len[len(m[0].points)].append(m)
        subgroups: list[list] = []
        for bucket in by_len.values():
            if len(bucket) == 1:
                subgroups.append(bucket)
                continue
            # 多成员桶：按 x1 值序列一致性校验，不一致则拆为单成员
            def _x1_seq(member) -> list:
                ds_m, cid, _ = member
                seq: list = []
                for pt in ds_m.points:
                    xv = None
                    for mv in pt.variable_values:
                        d = next((v for v in ds_m.variables if v.number == mv.number), None)
                        if d and _is_mole_fraction(d) and _is_liquid(d.phase) and d.component_id == cid:
                            xv = mv.value
                            break
                    if xv is None:
                        for mv in pt.property_values:
                            d = next((p for p in ds_m.properties if p.number == mv.number), None)
                            if d and _is_mole_fraction(d) and _is_liquid(d.phase) and d.component_id == cid:
                                xv = mv.value
                                break
                    seq.append(xv)
                return seq
            seqs = [_x1_seq(m) for m in bucket]
            consistent = True
            for i in range(len(seqs[0])):
                vals = [s[i] for s in seqs if s[i] is not None]
                if len(vals) >= 2:
                    try:
                        fv = [float(v) for v in vals]
                        if max(fv) - min(fv) > 1e-6:
                            consistent = False
                            break
                    except (TypeError, ValueError):
                        consistent = False
                        break
            if consistent:
                subgroups.append(bucket)
            else:
                subgroups.extend([[m] for m in bucket])

        for grp in subgroups:
            n_pts = len(grp[0][0].points)
            for i in range(n_pts):
                x1 = y1 = t_k = p_kpa = None
                # 收集此点序号在所有成员中的全部测量值，按 quantity 定义归类
                for ds, _, _ in grp:
                    pt = ds.points[i]
                    # 变量编号与属性编号是两个独立空间，必须分别用各自的定义查找
                    var_def = {v.number: v for v in ds.variables}
                    prop_def = {p.number: p for p in ds.properties}
                    for mv in pt.variable_values:
                        d = var_def.get(mv.number)
                        if d is None:
                            continue
                        nm = normalize_term(d.name)
                        if nm.startswith("mole_fraction"):
                            if _is_liquid(d.phase) and d.component_id == comp1_id:
                                if x1 is None:
                                    x1 = mv.value
                            elif _is_gas(d.phase) and d.component_id == comp1_id:
                                if y1 is None:
                                    y1 = mv.value
                        elif "temperature" in nm:
                            if t_k is None:
                                t_k = mv.value
                        elif "pressure" in nm:
                            if p_kpa is None:
                                p_kpa = mv.value
                    for mv in pt.property_values:
                        d = prop_def.get(mv.number)
                        if d is None:
                            continue
                        nm = normalize_term(d.name)
                        if nm.startswith("mole_fraction"):
                            if _is_liquid(d.phase) and d.component_id == comp1_id:
                                if x1 is None:
                                    x1 = mv.value
                            elif _is_gas(d.phase) and d.component_id == comp1_id:
                                if y1 is None:
                                    y1 = mv.value
                        elif "temperature" in nm:
                            if t_k is None:
                                t_k = mv.value
                        elif "pressure" in nm:
                            if p_kpa is None:
                                p_kpa = mv.value

                # 温度/压力回退：约束（同组任一成员）
                if t_k is None or p_kpa is None:
                    for ds, _, _ in grp:
                        for c in ds.constraints:
                            cn = normalize_term(c.name)
                            if "temperature" in cn and t_k is None and c.value is not None:
                                t_k = c.value
                            elif "pressure" in cn and p_kpa is None and c.value is not None:
                                p_kpa = c.value

                # 必须四项齐全
                if x1 is None or y1 is None or t_k is None or p_kpa is None:
                    continue
                try:
                    x1f = float(x1)
                    y1f = float(y1)
                    t_k_f = float(t_k)
                    p_kpa_f = float(p_kpa)
                except (TypeError, ValueError):
                    continue

                # 摩尔分数范围 0-1
                if not (0.0 <= x1f <= 1.0 and 0.0 <= y1f <= 1.0):
                    continue

                # 单位换算：K -> °C；kPa -> mmHg
                t_c = t_k_f - 273.15
                p_mmhg = p_kpa_f * KPA_TO_MMHG

                rows.append({
                    "名称1": comp1.preferred_name,
                    "分子式1": comp1.formula or "",
                    "smiles1": "",   # ThermoML 不提供 SMILES，留空（可用 InChIKey 溯源）
                    "名称2": comp2.preferred_name,
                    "分子式2": comp2.formula or "",
                    "smiles2": "",
                    "一致性检验方法一": "",
                    "一致性检验方法二": "",
                    "压强": round(p_mmhg, 4),
                    "温度": round(t_c, 3),
                    "X1": x1f,
                    "Y1": y1f,
                    "CAS1": comp1.cas_registry_number or "",
                    "CAS2": comp2.cas_registry_number or "",
                    "DOI": doi_str,
                    "文献来源": source_str,
                    "NIST资源链接": xml_url,
                })
    return rows


def process_one_paper(sess: requests.Session, doi: str) -> tuple[list[dict], str | None]:
    """处理单篇文献：下载 XML -> thermoml-io 解析 -> 抽取二元 VLE 行。

    返回 (rows, error)。error 非 None 表示失败原因（已捕获，流程不崩溃）。
    """
    xml_url = f"{XML_BASE}/{doi}.xml"
    try:
        xml_bytes = fetch_xml_bytes(sess, doi)
        # thermoml-io 内存解析（禁止自写 XML 解析逻辑）
        doc = tml.parse_thermoml(xml_bytes, source_label=xml_url)
        rows = extract_binary_vle_rows(doc, doi, xml_url)
        return rows, None
    except Exception as exc:  # noqa: BLE001  网络或解析异常统一记录跳过
        return [], f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# 断点续跑缓存：仅记录已处理 DOI 与状态（不缓存 XML 字节，不落地大量 xml）
# ---------------------------------------------------------------------------
def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_FILE)


def append_rows_to_csv(rows: list[dict]) -> None:
    """增量追加行到输出 CSV（首次写表头，utf-8-sig 便于 Excel 识别中文）。"""
    if not rows:
        return
    write_header = (not OUT_CSV.exists()) or OUT_CSV.stat().st_size == 0
    with OUT_CSV.open("a", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=OUT_COLUMNS)
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in OUT_COLUMNS})


def log_error(doi: str, message: str) -> None:
    with ERR_LOG.open("a", encoding="utf-8") as fp:
        fp.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {doi}\t{message}\n")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="在线抽取 NIST ThermoML 二元 VLE 数据集")
    ap.add_argument("--max-papers", type=int, default=None,
                    help="最多处理文献篇数（默认全部，用于试跑可设小值如 200）")
    ap.add_argument("--rate-limit", type=float, default=0.6,
                    help="对 NIST 服务器的最小请求间隔（秒），默认 0.6")
    ap.add_argument("--fresh", action="store_true",
                    help="忽略断点缓存，从头开始并重写输出 csv")
    args = ap.parse_args()

    print("=" * 70)
    print("NIST ThermoML 二元 VLE 在线抽取流水线")
    print("=" * 70)

    sess = build_session(args.rate_limit)

    # 1) Cordra 检索全部句柄（Lucene）
    print("[1/4] Cordra 检索全部 ThermoML 文献句柄 ...")
    handles = fetch_all_handles(sess)
    print(f"      共获取 {len(handles)} 篇文献句柄。")

    dois: list[str] = []
    for h in handles:
        d = handle_to_doi(h)
        if d:
            dois.append(d)
    if args.max_papers is not None:
        dois = dois[: args.max_papers]
        print(f"      --max-papers={args.max_papers}，本次将处理前 {len(dois)} 篇。")

    # 2) 断点续跑缓存
    cache = {} if args.fresh else load_cache()
    if args.fresh and OUT_CSV.exists():
        OUT_CSV.unlink()
    if args.fresh and ERR_LOG.exists():
        ERR_LOG.unlink()

    print(f"[2/4] 断点缓存：已处理 {len(cache)} 篇。输出: {OUT_CSV.name}")

    # 3) 逐篇：在线取 XML -> thermoml-io 解析 -> 抽取二元 VLE -> 增量写 CSV
    total_rows = 0
    n_ok, n_empty, n_err = 0, 0, 0
    print("[3/4] 逐篇下载解析中 ...")
    for i, doi in enumerate(dois, 1):
        if doi in cache:
            continue  # 已处理，跳过避免重复下载同一篇文献
        rows, err = process_one_paper(sess, doi)
        if err is not None:
            n_err += 1
            log_error(doi, err)
            cache[doi] = {"status": "error", "msg": err[:200]}
        elif rows:
            n_ok += 1
            total_rows += len(rows)
            append_rows_to_csv(rows)
            cache[doi] = {"status": "ok", "rows": len(rows)}
        else:
            n_empty += 1
            cache[doi] = {"status": "empty"}

        # 每 20 篇落盘缓存 + 进度
        if i % 20 == 0:
            save_cache(cache)
            print(f"      进度 {i}/{len(dois)} | 成功 {n_ok} | 无二元VLE {n_empty} | "
                  f"错误 {n_err} | 累计行 {total_rows}")

    save_cache(cache)

    # 4) 终态清洗：去重、丢弃缺失/越界行，重写最终 csv
    print("[4/4] 终态清洗与去重 ...")
    if OUT_CSV.exists():
        df = pd.read_csv(OUT_CSV, encoding="utf-8-sig")
        before = len(df)
        # 丢弃核心数值缺失
        df = df.dropna(subset=["压强", "温度", "X1", "Y1"])
        # 摩尔分数范围
        df = df[(df["X1"].between(0, 1)) & (df["Y1"].between(0, 1))]
        # 去重（同一文献同一数据点可能被异常重跑）
        df = df.drop_duplicates()
        df = df[OUT_COLUMNS]
        df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f"      清洗: {before} -> {len(df)} 行（去重/去缺失/去越界）。")

    print("-" * 70)
    print(f"完成。成功含二元VLE文献 {n_ok} 篇，累计 {total_rows} 行；"
          f"非二元VLE {n_empty} 篇；错误 {n_err} 篇。")
    print(f"输出 CSV : {OUT_CSV}")
    print(f"错误日志 : {ERR_LOG}")
    print(f"断点缓存 : {CACHE_FILE}")
    print("提示：全量扩充可直接重复运行 python fetch_vle_expand.py（自动断点续跑）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
