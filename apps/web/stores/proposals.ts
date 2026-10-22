/** Helpers for manual proposals (DESIGN §11). Proposals themselves live in the API (BL-053). */

/** Parses "msft, asml  $nvda" into ["MSFT", "ASML", "NVDA"]. */
export function parseSymbols(input: string): string[] {
  const symbols = input
    .toUpperCase()
    .split(/[\s,;]+/)
    .map((s) => s.replace(/^\$/, ""))
    .filter((s) => /^[A-Z][A-Z0-9.]{0,9}$/.test(s));
  return [...new Set(symbols)];
}

/** Window event used by the header button, ⌘K, peek panels and Radar to open the composer. */
export const PROPOSE_EVENT = "preza:propose";
export type ProposeDetail = { symbols?: string[]; hypothesis?: string };

export function openProposalComposer(detail: ProposeDetail = {}) {
  window.dispatchEvent(new CustomEvent<ProposeDetail>(PROPOSE_EVENT, { detail }));
}
