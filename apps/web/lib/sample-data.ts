/**
 * Sample data for M0 (clearly labelled "Vzorčni podatki" in the UI).
 * Replaced by API data in M1/M2. Fictional values; KSTL is a fictional company.
 */
export type ThesisState = "holds" | "weakening" | "broken" | "none";

export type SampleInstrument = {
  symbol: string;
  name: string;
  kind: "stock" | "etf";
  currency: "USD" | "EUR" | "GBP";
  price: number;
  change: number; // % today
  weight: number; // % of portfolio, 0 if not held
  thesis: ThesisState;
  lastSignal?: { kind: "entry" | "catalyst" | "thesis_break" | "rumor"; ageHours: number };
};

export const INSTRUMENTS: SampleInstrument[] = [
  { symbol: "VWRA", name: "Vanguard FTSE All-World UCITS ETF", kind: "etf", currency: "USD", price: 137.9, change: 0.4, weight: 24.1, thesis: "holds" },
  { symbol: "MSFT", name: "Microsoft", kind: "stock", currency: "USD", price: 406.8, change: -0.6, weight: 9.8, thesis: "holds", lastSignal: { kind: "entry", ageHours: 2 } },
  { symbol: "ASML", name: "ASML Holding", kind: "stock", currency: "USD", price: 702.5, change: 2.3, weight: 7.2, thesis: "holds" },
  { symbol: "EQQQ", name: "Invesco Nasdaq-100 UCITS ETF", kind: "etf", currency: "USD", price: 498.3, change: 0.9, weight: 8.4, thesis: "holds" },
  { symbol: "AMZN", name: "Amazon", kind: "stock", currency: "USD", price: 221.4, change: 1.1, weight: 6.2, thesis: "weakening" },
  { symbol: "IUES", name: "iShares S&P 500 Energy Sector UCITS ETF", kind: "etf", currency: "USD", price: 8.92, change: -1.4, weight: 4.0, thesis: "broken", lastSignal: { kind: "thesis_break", ageHours: 5 } },
  { symbol: "V", name: "Visa", kind: "stock", currency: "USD", price: 271.4, change: -1.6, weight: 5.1, thesis: "holds" },
  { symbol: "NVDA", name: "NVIDIA", kind: "stock", currency: "USD", price: 182.6, change: 3.2, weight: 3.6, thesis: "holds" },
  { symbol: "COST", name: "Costco", kind: "stock", currency: "USD", price: 918.2, change: -0.3, weight: 2.9, thesis: "none" },
  { symbol: "ORCL", name: "Oracle", kind: "stock", currency: "USD", price: 151.6, change: -0.4, weight: 0, thesis: "none", lastSignal: { kind: "catalyst", ageHours: 11 } },
  { symbol: "SMH", name: "VanEck Semiconductor UCITS ETF", kind: "etf", currency: "USD", price: 41.2, change: 1.2, weight: 0, thesis: "none", lastSignal: { kind: "catalyst", ageHours: 1 } },
  { symbol: "CRWD", name: "CrowdStrike", kind: "stock", currency: "USD", price: 412.9, change: 6.2, weight: 0, thesis: "none", lastSignal: { kind: "catalyst", ageHours: 1 } },
  { symbol: "KSTL", name: "Kestrel Bio (fiktivno)", kind: "stock", currency: "USD", price: 18.4, change: 3.1, weight: 0, thesis: "none", lastSignal: { kind: "rumor", ageHours: 1 } },
];

export function findInstrument(symbol: string) {
  return INSTRUMENTS.find((i) => i.symbol === symbol.toUpperCase());
}

/** Deterministic 30-point series ending at `price`, for sparklines. */
export function sparkSeries(symbol: string, price: number, points = 30): number[] {
  let seed = [...symbol].reduce((a, c) => a + c.charCodeAt(0), 0);
  const rnd = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  const out = [price];
  for (let i = 1; i < points; i += 1) out.unshift(out[0]! * (1 + (rnd() - 0.5) * 0.03));
  return out;
}

export type PulseEvent = {
  id: string;
  symbol: string;
  hoursAgo: number;
  score: number;
  type: "earnings" | "filing" | "insider" | "analyst" | "macro" | "rumor";
};

export const PULSE_EVENTS: PulseEvent[] = [
  { id: "e1", symbol: "CRWD", hoursAgo: 1, score: 0.74, type: "earnings" },
  { id: "e2", symbol: "KSTL", hoursAgo: 1.5, score: 0.42, type: "rumor" },
  { id: "e3", symbol: "SMH", hoursAgo: 3, score: 0.71, type: "filing" },
  { id: "e4", symbol: "MSFT", hoursAgo: 2, score: 0.48, type: "macro" },
  { id: "e5", symbol: "ORCL", hoursAgo: 14, score: 0.61, type: "insider" },
  { id: "e6", symbol: "IUES", hoursAgo: 5, score: 0.66, type: "macro" },
  { id: "e7", symbol: "ASML", hoursAgo: 6, score: 0.58, type: "filing" },
  { id: "e8", symbol: "MSFT", hoursAgo: 40, score: 0.35, type: "analyst" },
  { id: "e9", symbol: "AMZN", hoursAgo: 52, score: 0.4, type: "earnings" },
  { id: "e10", symbol: "NVDA", hoursAgo: 75, score: 0.55, type: "analyst" },
  { id: "e11", symbol: "KSTL", hoursAgo: 96, score: 0.3, type: "rumor" },
  { id: "e12", symbol: "V", hoursAgo: 110, score: 0.52, type: "filing" },
  { id: "e13", symbol: "ASML", hoursAgo: 130, score: 0.44, type: "analyst" },
  { id: "e14", symbol: "IUES", hoursAgo: 150, score: 0.5, type: "macro" },
];

export const FUNNEL = [
  { key: "news", value: 38214 },
  { key: "events", value: 6120 },
  { key: "aboveThreshold", value: 214 },
  { key: "signals", value: 41 },
  { key: "accepted", value: 12 },
] as const;

export type RegimeIndicator = {
  key: string;
  label: string;
  value: number;
  unit: "pct" | "pts" | "idx";
  change: number;
  regime: "risk_on" | "neutral" | "risk_off";
};

export const REGIME: RegimeIndicator[] = [
  { key: "spy", label: "SPY / SMA200", value: 4.2, unit: "pct", change: -0.6, regime: "risk_on" },
  { key: "vix", label: "VIX", value: 19.4, unit: "pts", change: 1.8, regime: "neutral" },
  { key: "us10y", label: "US 10Y", value: 4.31, unit: "pct", change: 0.04, regime: "neutral" },
  { key: "dxy", label: "DXY", value: 102.7, unit: "idx", change: -0.2, regime: "risk_on" },
];

export type SampleSignal = {
  id: string;
  symbol: string;
  kind: "entry" | "catalyst" | "rumor";
  strength: number;
  why: { sl: string; en: string };
  detail: { sl: string; en: string };
  source: { sl: string; en: string };
};

export const SIGNALS: SampleSignal[] = [
  {
    id: "s1",
    symbol: "MSFT",
    kind: "entry",
    strength: 0.72,
    why: {
      sl: "Cena je v vstopni coni po padcu −9 % od vrha. Padec sledi sektorju, teza o rasti oblaka drži.",
      en: "Price is in the entry zone after a −9% drawdown. The drop follows the sector; the cloud growth thesis holds.",
    },
    detail: {
      sl: "Cona 402–410 $ · tezni stop 371 $ · lestvica 40 % @ 408, 30 % @ 401, 30 % @ 394. Ovrglo bi jo: rast Azure pod 25 %.",
      en: "Zone $402–410 · thesis stop $371 · ladder 40% @ 408, 30% @ 401, 30% @ 394. Refuted by: Azure growth below 25%.",
    },
    source: { sl: "Pravilo + dip analitik · pred 2 h", en: "Rule + dip analyst · 2h ago" },
  },
  {
    id: "s2",
    symbol: "SMH",
    kind: "catalyst",
    strength: 0.64,
    why: {
      sl: "Trije največji držatelji ETF-ja so zvišali napovedi. Odziv cene je še zmeren.",
      en: "The three largest ETF holdings raised guidance. The price reaction is still moderate.",
    },
    detail: {
      sl: "Skupna utež treh podjetij 31 %. Prekrivanje s portfeljem 4 %. Horizont: tedni.",
      en: "Combined weight of the three companies 31%. Portfolio overlap 4%. Horizon: weeks.",
    },
    source: { sl: "Radar · 3 viri · pred 40 min", en: "Radar · 3 sources · 40 min ago" },
  },
  {
    id: "s3",
    symbol: "KSTL",
    kind: "rumor",
    strength: 0.38,
    why: {
      sl: "Omembe prevzema so 8× nad povprečjem. Uradnega vira ni, signal se nadgradi ob 8-K.",
      en: "Takeover mentions are 8× the average. No official source; the signal upgrades on an 8-K.",
    },
    detail: {
      sl: "Govorica nikoli ne postane priporočilo za nakup brez uradne potrditve (AGENTS.md §3.4).",
      en: "A rumor never becomes a buy recommendation without official confirmation (AGENTS.md §3.4).",
    },
    source: { sl: "Radar · Reddit, StockTwits · pred 15 min", en: "Radar · Reddit, StockTwits · 15 min ago" },
  },
];
