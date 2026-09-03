import { normalizeSymbol } from "./market-data";

export const WATCHLIST_STORAGE_KEY = "northstar-research:watchlist:v1";

function readStorage(): Storage | null {
  try {
    if (typeof window === "undefined" || !window.localStorage) return null;
    return window.localStorage;
  } catch {
    return null;
  }
}

export function parseWatchlist(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  for (const entry of value) {
    if (typeof entry !== "string") continue;
    const symbol = normalizeSymbol(entry);
    if (symbol) seen.add(symbol);
  }
  return [...seen];
}

export function toggleWatchlistSymbol(symbols: string[], symbol: string): string[] {
  const normalized = normalizeSymbol(symbol);
  const current = parseWatchlist(symbols);
  if (!normalized) return current;
  return current.includes(normalized)
    ? current.filter((entry) => entry !== normalized)
    : [...current, normalized];
}

export function isWatchlisted(symbols: string[], symbol: string): boolean {
  return parseWatchlist(symbols).includes(normalizeSymbol(symbol));
}

export function loadWatchlist(): string[] {
  const storage = readStorage();
  if (!storage) return [];
  try {
    const raw = storage.getItem(WATCHLIST_STORAGE_KEY);
    if (!raw) return [];
    return parseWatchlist(JSON.parse(raw));
  } catch {
    return [];
  }
}

export function saveWatchlist(symbols: string[]): void {
  const storage = readStorage();
  if (!storage) return;
  try {
    storage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(parseWatchlist(symbols)));
  } catch {
    // Private-mode or quota failures must never break research browsing.
  }
}
