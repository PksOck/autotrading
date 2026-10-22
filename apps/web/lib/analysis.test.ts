import { describe, expect, it } from "vitest";
import type { AnalysisStep } from "@/lib/api/types";
import { currentPhase, groupByPhase, lastSeq, mergeSteps, phaseOf } from "./analysis";
import { parseMarkdown } from "./markdown";

const step = (seq: number, agent: string, kind = "tool"): AnalysisStep => ({
  seq,
  agent,
  kind,
  title: null,
  content: "",
  created_at: "2026-10-22T10:00:00Z",
});

describe("phase grouping", () => {
  it("maps agents to phases", () => {
    expect(phaseOf({ agent: "news" })).toBe("analysts");
    expect(phaseOf({ agent: "bear" })).toBe("debate");
    expect(phaseOf({ agent: "trader" })).toBe("plan");
    expect(phaseOf({ agent: "neutral" })).toBe("risk");
    expect(phaseOf({ agent: "portfolio_manager" })).toBe("decision");
    expect(phaseOf({ agent: "system" })).toBeNull();
  });

  it("groups in pipeline order, drops system steps and empty phases", () => {
    const groups = groupByPhase([
      step(3, "bull", "debate"),
      step(1, "system", "status"),
      step(2, "market"),
      step(4, "trader", "report"),
    ]);
    expect(groups.map((g) => g.phase)).toEqual(["analysts", "debate", "plan"]);
    expect(groups[0]!.steps.map((s) => s.seq)).toEqual([2]);
  });

  it("current phase is the latest one with steps", () => {
    expect(currentPhase([])).toBeNull();
    expect(currentPhase([step(1, "market"), step(2, "bull")])).toBe("debate");
  });
});

describe("mergeSteps (SSE dedupe)", () => {
  it("ignores seqs already present and keeps order", () => {
    const base = [step(1, "market"), step(2, "news")];
    const merged = mergeSteps(base, [step(2, "news"), step(4, "bull"), step(3, "fundamentals")]);
    expect(merged.map((s) => s.seq)).toEqual([1, 2, 3, 4]);
    expect(lastSeq(merged)).toBe(4);
  });

  it("returns the same array when nothing is new", () => {
    const base = [step(1, "market")];
    expect(mergeSteps(base, [step(1, "market")])).toBe(base);
  });

  it("dedupes repeats within one batch", () => {
    expect(mergeSteps([], [step(1, "market"), step(1, "market")])).toHaveLength(1);
  });
});

describe("parseMarkdown", () => {
  it("parses headings, lists and bold without HTML", () => {
    const blocks = parseMarkdown("### Naslov\n**Rating**: Buy\n\n- a\n- b\n\n<script>x</script>");
    expect(blocks.map((b) => b.type)).toEqual(["heading", "paragraph", "list", "paragraph"]);
    const last = blocks[3]!;
    expect(last.type === "paragraph" && last.inline[0]!.text).toBe("<script>x</script>");
  });
});
