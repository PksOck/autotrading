import type { SignalOut } from "@/lib/api/types";

export const signalId = "10000000-0000-4000-8000-000000000123";
export const signal: SignalOut = {
  id: signalId,
  symbol: "MSFT",
  kind: "catalyst",
  source: "radar",
  direction: "up",
  horizon: "months",
  strength: 0.6,
  confidence: null,
  entry_low: null,
  entry_high: null,
  stop: null,
  target: null,
  rationale: "Original evidence needs confirmation.",
  rationale_translations: {},
  evidence: [
    { kind: "news", label: "Original source", url: "https://example.test/news", ref_id: null },
  ],
  is_rumor: true,
  status: "watching",
  event_id: null,
  proposal_id: null,
  created_at: "2026-10-29T10:00:00Z",
  expires_at: "2026-11-29T10:00:00Z",
};
