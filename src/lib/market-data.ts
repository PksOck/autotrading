export function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase();
}

export function isStale(asOf: string, now: Date, maxAgeHours: number): boolean {
  const elapsedHours = (now.getTime() - new Date(asOf).getTime()) / 3_600_000;
  return elapsedHours > maxAgeHours;
}
