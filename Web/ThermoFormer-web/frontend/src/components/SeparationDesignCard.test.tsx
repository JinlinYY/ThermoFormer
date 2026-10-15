import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SeparationReport } from "@/lib/types";
import { SeparationDesignCard } from "./SeparationDesignCard";

describe("SeparationDesignCard", () => {
  it("keeps preliminary selection distinct from rigorous validation", () => {
    const report: SeparationReport = {
      status: "preliminary", stop_reason: "first_candidate_meets_preliminary_checks", selected_attempt_id: "a",
      missing_inputs: [], input_snapshot: {}, calculation_snapshots: [], warnings: [],
      capabilities: [{ method: "distillation", label: "普通精馏", availability: "design_loop", limitation: "快捷设计" }],
      decisions: [{ action: "revise_reflux", reason: "塔板数超限，调整回流比", attempt_id: "a" }],
      attempts: [{ attempt_id: "a", method: "distillation", status: "preliminary", reason: "初步通过",
        failure_type: null, recovery_action: null, metrics: { theoretical_stages: 14 }, evidence_run_ids: ["run-1"],
        checks: [{ name: "rigorous_product_targets", status: "unverified", message: "尚未完成严格塔模拟" }] }],
    };
    render(<SeparationDesignCard report={report} />);
    expect(screen.getByText("初步设计 · 待严格验证")).toBeInTheDocument();
    expect(screen.getByText("未验证：尚未完成严格塔模拟")).toBeInTheDocument();
    expect(screen.getByText("塔板数超限，调整回流比")).toBeInTheDocument();
    expect(screen.getByText("理论塔板数")).toBeInTheDocument();
  });
});
