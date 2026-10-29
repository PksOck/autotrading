import type { AnalysisFilters } from "./api/research";

export function selectedEntry<T extends {symbol: string}>(items: T[], symbol: string | null): T | null {
  return symbol === null ? items[0] ?? null : items.find((e) => e.symbol.toUpperCase() === symbol.toUpperCase()) ?? null;
}

export function analysisFilters(params: Pick<URLSearchParams, "get">): AnalysisFilters {
  const status = params.get("status");
  const sort = params.get("sort");
  return {
    status: status === "all" ? undefined : status === "queued" || status === "running" || status === "failed" ? status : "done",
    latest_per_instrument: params.get("latest") !== "false",
    limit: 100,
    sort: sort === "symbol" || sort === "trade_date" ? sort : "created_at",
    direction: params.get("direction") === "asc" ? "asc" : "desc",
  };
}

export function eventConfirmation(event: {is_rumor: boolean; sources?: {kind?: string | null}[]}) {
  if (event.is_rumor) return "rumor";
  return event.sources?.some((s) => s.kind === "press_release" || s.kind === "filing") ? "verified" : "unverified";
}
