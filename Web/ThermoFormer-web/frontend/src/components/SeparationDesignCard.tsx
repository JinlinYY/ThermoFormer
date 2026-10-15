"use client";

import type { SeparationReport } from "@/lib/types";

const statusLabels = {
  preliminary: "初步设计 · 待严格验证", needs_input: "需要补充输入",
  blocked: "未获得可接受方案", budget_exhausted: "计算预算已耗尽",
};

const metricLabels: Record<string, string> = {
  product_purity: "产品摩尔纯度", recovery: "目标组分回收率", vapor_fraction: "汽相分率",
  specified_purity: "设定塔顶摩尔纯度", specified_recovery: "设定回收率",
  theoretical_stages: "理论塔板数", reflux_ratio: "回流比", reflux_factor: "最小回流比倍数",
  sampled_minimum_alpha: "采样区间最小相对挥发度", distillate_flow_mol_s: "塔顶流量（mol/s）",
  bottoms_flow_mol_s: "塔底流量（mol/s）", condenser_temperature_K: "塔顶泡点（K）",
  reboiler_temperature_K: "塔底泡点（K）",
};

export function SeparationDesignCard({ report }: { report: SeparationReport }) {
  const labels = new Map(report.capabilities.map((c) => [c.method, c.label]));
  return (
    <section className="result-panel" aria-label="分离设计决策">
      <h3>分离设计决策</h3>
      <p>{statusLabels[report.status]}</p>
      {report.missing_inputs.length > 0 && <p>请补充：{report.missing_inputs.join("、")}</p>}
      <ol>
        {report.decisions.map((decision, index) => (
          <li key={index}>{decision.reason}</li>
        ))}
      </ol>
      {report.attempts.map((attempt) => (
        <article key={attempt.attempt_id}>
          <h4>{labels.get(attempt.method)}{report.selected_attempt_id === attempt.attempt_id ? " · 候选初步方案" : ""}</h4>
          <p>{attempt.reason}</p>
          <dl>{Object.entries(attempt.metrics).map(([name, value]) => (
            <div key={name}><dt>{metricLabels[name] ?? name}</dt><dd>{value}</dd></div>
          ))}</dl>
          <ul>{attempt.checks.map((check) => <li key={check.name}>
            {check.status === "unverified" ? "未验证" : check.status === "passed" ? "通过" : "未通过"}：{check.message}
          </li>)}</ul>
        </article>
      ))}
      <details><summary>分离方法支持范围</summary>
        <ul>{report.capabilities.map((capability) => <li key={capability.method}>
          <strong>{capability.label}</strong>（{capability.availability === "design_loop" ? "已接入闭环" : capability.availability === "legacy_specialized" ? "已有专用入口" : "待实现"}）：{capability.limitation}
        </li>)}</ul>
      </details>
      {report.warnings.map((warning) => <p key={warning}>{warning}</p>)}
    </section>
  );
}
