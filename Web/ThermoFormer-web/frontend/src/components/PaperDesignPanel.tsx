"use client";

import { FormEvent, useState } from "react";
import { runPaperDesign } from "@/lib/api";
import type { PaperRequest, PaperRun, PaperTask } from "@/lib/types";

const presets: Record<PaperTask["case"], PaperTask> = {
  binary: { task_id: "interactive-binary", case: "binary", purity: .995, recovery: .98,
    retention: .8, feed_fraction: .466, temperature_K: 303.15, solvent_total: 1.5,
    max_stages: 12, max_calls: 6, max_reflux: 3, margin: .0005 },
  extractive: { task_id: "interactive-extractive", case: "extractive", purity: .995, recovery: .98,
    retention: .8, feed_fraction: .5, temperature_K: 303.15, solvent_total: 1.5,
    max_stages: 200, max_calls: 6, max_reflux: 56, margin: .0005 },
  extraction: { task_id: "interactive-extraction", case: "extraction", purity: .995, recovery: .70,
    retention: .80, feed_fraction: 4 / 15, temperature_K: 303.15, solvent_total: 1.5,
    max_stages: 4, max_calls: 6, max_reflux: 3, margin: .0005 },
};
const outcomes: Record<PaperRun["outcome"], string> = {
  accepted: "接受初步方案", deferred: "证据不足，暂缓接受", exhausted: "计算预算已用尽",
  stopped: "停止，未接受方案", provider_error: "LLM 接口失败，未替换为规则结果",
};

export function PaperDesignPanel() {
  const [task, setTask] = useState<PaperTask>(presets.binary);
  const [mode, setMode] = useState<PaperRequest["mode"]>("rule");
  const [result, setResult] = useState<PaperRun>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  function numeric(field: keyof PaperTask, value: string) {
    setTask((current) => ({ ...current, [field]: Number(value) }));
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(undefined); setResult(undefined);
    try { setResult(await runPaperDesign({ task, mode, repeat: 0 })); }
    catch (failure) { setError(failure instanceof Error ? failure.message : "计算失败"); }
    finally { setBusy(false); }
  }
  function download() {
    if (!result) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `paper-design-${result.run_id}.json`;
    link.click(); URL.revokeObjectURL(url);
  }
  return (
    <details className="result-panel" data-testid="paper-design-panel">
      <summary>论文案例：验证反馈驱动的分离设计</summary>
      <p>三个已登记体系的初步设计。每一步保留候选行动、工具反馈与证据缺口；数值复核不等于独立实验验证。</p>
      <form onSubmit={submit} style={{ display: "grid", gap: "0.75rem" }}>
        <fieldset disabled={busy} style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          <legend>设计条件</legend>
          <label>案例 <select value={task.case} onChange={(event) => { setTask(presets[event.target.value as PaperTask["case"]]); setResult(undefined); }}>
            <option value="binary">二元精馏</option><option value="extractive">萃取精馏</option><option value="extraction">错流萃取</option>
          </select></label>
          <label>策略 <select value={mode} onChange={(event) => setMode(event.target.value as PaperRequest["mode"])}>
            <option value="fixed">固定流程</option><option value="rule">规则反馈闭环</option>
            <option value="rule_guided">质量约束规则闭环</option>
            <option value="llm_guided">质量约束 LLM 闭环</option>
            <option value="llm">LLM 选择行动（需可用接口额度）</option>
          </select></label>
          {task.case !== "extraction" && <label>产品纯度 <input type="number" min="0.001" max="0.99999" step="any" value={task.purity} onChange={(e) => numeric("purity", e.target.value)} required /></label>}
          <label>回收率 <input type="number" min="0.001" max="0.99999" step="any" value={task.recovery} onChange={(e) => numeric("recovery", e.target.value)} required /></label>
          {task.case === "extraction" && <>
            <label>庚烷保留率 <input type="number" min="0.001" max="0.99999" step="any" value={task.retention} onChange={(e) => numeric("retention", e.target.value)} required /></label>
            <label>总溶剂量（mol/s） <input type="number" min="0.01" max="3" step="any" value={task.solvent_total} onChange={(e) => numeric("solvent_total", e.target.value)} required /></label>
          </>}
          <label>最大级数 <input type="number" min="1" max={task.case === "extraction" ? 4 : 220} value={task.max_stages} onChange={(e) => numeric("max_stages", e.target.value)} required /></label>
          {task.case !== "extraction" && <label>最大回流比 <input type="number" min="0.01" max="60" step="any" value={task.max_reflux} onChange={(e) => numeric("max_reflux", e.target.value)} required /></label>}
          <label>工具调用预算 <input type="number" min="1" max="12" value={task.max_calls} onChange={(e) => numeric("max_calls", e.target.value)} required /></label>
        </fieldset>
        <button type="submit" disabled={busy}>{busy ? "正在计算并记录轨迹…" : "运行论文案例"}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {result && <div aria-live="polite">
        <h3>{outcomes[result.outcome]}</h3>
        <p>策略：{result.mode} · 数值工具调用：{result.calls} · 用时：{result.elapsed_s.toFixed(1)} s</p>
        {result.policy_error && <p>{result.policy_error}</p>}
        {typeof result.assessment.stopping_certificate === "string" && <p>停止依据：{result.assessment.stopping_certificate}</p>}
        {result.final_observation && <div>
          <h4>最终保留方案</h4>
          <p>{Object.entries(result.final_observation.metrics).map(([key, value]) => `${key}: ${value.toPrecision(6)}`).join(" · ")}</p>
          <p>{result.final_observation.evidence_gaps.length ? `证据缺口：${result.final_observation.evidence_gaps.join("；")}` : "无已登记的未解决证据缺口；不代表全面物理认证。"}</p>
        </div>}
        {result.assessment.accepted_with_unresolved_evidence === true && <p>该初步方案被接受时仍存在未解决的证据缺口。</p>}
        <ol>{result.trace.map((entry) => <li key={entry.index}>
          <strong>{entry.choice.action_id}</strong> — {entry.choice.reason}
          {entry.observation && <div>
            <p>{entry.observation.status === "failed" ? `计算失败：${entry.observation.failure}` : entry.observation.meets_targets ? "名义指标达标" : "尚未达到目标"}</p>
            <p>{Object.entries(entry.observation.metrics).map(([key, value]) => `${key}: ${value.toPrecision(6)}`).join(" · ")}</p>
            {entry.observation.evidence_gaps.length > 0 && <p>待解决：{entry.observation.evidence_gaps.join("；")}</p>}
          </div>}
        </li>)}</ol>
        <button type="button" onClick={download}>下载完整运行轨迹 JSON</button>
      </div>}
    </details>
  );
}
