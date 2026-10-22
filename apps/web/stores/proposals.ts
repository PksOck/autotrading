import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ProposalDepth = "quick" | "standard" | "deep";
export type ProposalDirection = "up" | "down" | "unsure";
export type ProposalSaveTo = "active" | "reserve" | "once";

export type Proposal = {
  id: string;
  symbols: string[];
  hypothesis: string;
  source: string;
  direction: ProposalDirection;
  horizon: "days" | "weeks" | "months" | "years";
  depth: ProposalDepth;
  saveTo: ProposalSaveTo;
  createdAt: string;
  status: "draft" | "queued" | "running" | "done";
};

type ProposalState = {
  items: Proposal[];
  add: (proposal: Proposal) => void;
  remove: (id: string) => void;
};

// Local until the proposals API exists (BL-053); then this store becomes a query cache.
export const useProposals = create<ProposalState>()(
  persist(
    (set) => ({
      items: [],
      add: (proposal) => set((s) => ({ items: [proposal, ...s.items] })),
      remove: (id) => set((s) => ({ items: s.items.filter((p) => p.id !== id) })),
    }),
    { name: "preza.proposals.v1" },
  ),
);

/** Parses "msft, asml  nvda" into ["MSFT", "ASML", "NVDA"]. */
export function parseSymbols(input: string): string[] {
  const symbols = input
    .toUpperCase()
    .split(/[\s,;]+/)
    .map((s) => s.replace(/^\$/, ""))
    .filter((s) => /^[A-Z][A-Z0-9.]{0,9}$/.test(s));
  return [...new Set(symbols)];
}

/** Window event used by the header button, ⌘K and peek panels to open the composer. */
export const PROPOSE_EVENT = "preza:propose";
export type ProposeDetail = { symbols?: string[]; hypothesis?: string };

export function openProposalComposer(detail: ProposeDetail = {}) {
  window.dispatchEvent(new CustomEvent<ProposeDetail>(PROPOSE_EVENT, { detail }));
}
