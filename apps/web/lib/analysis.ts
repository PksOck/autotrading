import type { AnalysisStep } from "@/lib/api/types";

export const PHASES = ["analysts", "debate", "plan", "risk", "decision"] as const;
export type Phase = (typeof PHASES)[number];

const AGENT_PHASE: Record<string, Phase> = {
  market: "analysts",
  news: "analysts",
  fundamentals: "analysts",
  social: "analysts",
  bull: "debate",
  bear: "debate",
  research_manager: "plan",
  trader: "plan",
  aggressive: "risk",
  conservative: "risk",
  neutral: "risk",
  portfolio_manager: "decision",
};

/** Phase of a step; system/status steps belong to no phase. */
export function phaseOf(step: Pick<AnalysisStep, "agent">): Phase | null {
  return AGENT_PHASE[step.agent] ?? null;
}

export type PhaseGroup = { phase: Phase; steps: AnalysisStep[] };

/** Group steps by phase in pipeline order; empty phases are omitted. System steps are dropped. */
export function groupByPhase(steps: AnalysisStep[]): PhaseGroup[] {
  const buckets = new Map<Phase, AnalysisStep[]>();
  for (const step of [...steps].sort((a, b) => a.seq - b.seq)) {
    const phase = phaseOf(step);
    if (!phase) continue;
    buckets.set(phase, [...(buckets.get(phase) ?? []), step]);
  }
  return PHASES.filter((p) => buckets.has(p)).map((phase) => ({ phase, steps: buckets.get(phase)! }));
}

/** The phase currently running: the last one that has steps. */
export function currentPhase(steps: AnalysisStep[]): Phase | null {
  return groupByPhase(steps).at(-1)?.phase ?? null;
}

export const lastSeq = (steps: AnalysisStep[]) => steps.reduce((m, s) => Math.max(m, s.seq), 0);

/** Append incoming steps, ignoring seqs already present (SSE replays after reconnect). Keeps seq order. */
export function mergeSteps(current: AnalysisStep[], incoming: AnalysisStep[]): AnalysisStep[] {
  const seen = new Set(current.map((s) => s.seq));
  const fresh: AnalysisStep[] = [];
  for (const step of incoming) {
    if (seen.has(step.seq)) continue;
    seen.add(step.seq);
    fresh.push(step);
  }
  if (!fresh.length) return current;
  return [...current, ...fresh].sort((a, b) => a.seq - b.seq);
}

