export const HELP_PAGES = [
  "overview",
  "radar",
  "entries",
  "signals",
  "proposals",
  "analysis",
  "analysisDetail",
  "portfolio",
  "instrument",
  "theses",
  "thesisDetail",
  "trackRecord",
  "settings",
  "options",
  "ux",
] as const;

export type PageHelpKey = (typeof HELP_PAGES)[number];

/** Explicit destinations, not actions that start analysis or change a decision. */
export const HELP_LINKS: Partial<Record<PageHelpKey, { href: string; label: string }[]>> = {
  overview: [
    { href: "/portfolio", label: "portfolio" },
    { href: "/signals", label: "signals" },
  ],
  radar: [{ href: "/signals", label: "signals" }],
  entries: [{ href: "/portfolio", label: "portfolio" }],
  signals: [{ href: "/track-record", label: "trackRecord" }],
  proposals: [{ href: "/analysis", label: "analyses" }],
  analysis: [{ href: "/theses", label: "theses" }],
  analysisDetail: [{ href: "/theses", label: "theses" }],
  portfolio: [{ href: "/settings", label: "settings" }],
  instrument: [
    { href: "/portfolio", label: "portfolio" },
    { href: "/analysis", label: "analyses" },
  ],
  theses: [{ href: "/analysis", label: "analyses" }],
  thesisDetail: [{ href: "/theses", label: "theses" }],
  trackRecord: [
    { href: "/signals", label: "signals" },
    { href: "/analysis", label: "analyses" },
  ],
  settings: [{ href: "/portfolio", label: "portfolio" }],
};
