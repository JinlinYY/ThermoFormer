import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PaperDesignPanel } from "./PaperDesignPanel";
import { runPaperDesign } from "@/lib/api";

vi.mock("@/lib/api", () => ({ runPaperDesign: vi.fn() }));

describe("paper design", () => {
  beforeEach(() => vi.clearAllMocks());
  it("runs only on submission and preserves evidence deferral", async () => {
    vi.mocked(runPaperDesign).mockResolvedValue({ outcome: "deferred", mode: "rule", calls: 3,
      elapsed_s: 2, policy_error: null, assessment: {}, trace: [],
    } as Awaited<ReturnType<typeof runPaperDesign>>);
    render(<PaperDesignPanel />);
    expect(runPaperDesign).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("论文案例：验证反馈驱动的分离设计"));
    fireEvent.click(screen.getByText("运行论文案例"));
    await waitFor(() => expect(screen.getByText("证据不足，暂缓接受")).toBeInTheDocument());
    expect(runPaperDesign).toHaveBeenCalledWith(expect.objectContaining({ mode: "rule", task: expect.objectContaining({ case: "binary", max_calls: 6 }) }));
  });
  it("reports worker failure without showing an accepted design", async () => {
    vi.mocked(runPaperDesign).mockRejectedValue(new Error("worker unavailable"));
    render(<PaperDesignPanel />);
    fireEvent.click(screen.getByText("论文案例：验证反馈驱动的分离设计"));
    fireEvent.click(screen.getByText("运行论文案例"));
    expect(await screen.findByRole("alert")).toHaveTextContent("worker unavailable");
    expect(screen.queryByText("接受初步方案")).not.toBeInTheDocument();
  });
});
