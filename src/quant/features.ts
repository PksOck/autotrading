import { rsi, sma } from "./indicators";

export interface FeatureRow {
  r1: number | null;
  r5: number | null;
  distSma20: number | null;
  distSma50: number | null;
  rsi14: number | null;
  vol20: number | null;
}

/**
 * Point-in-time feature row built from closes[0..index] only.
 * Returns null when index < 1 (no prior bar exists).
 * Individual fields stay null until their own warmup completes.
 */
export function buildFeatures(closes: number[], index: number): FeatureRow | null {
  if (index < 1 || index >= closes.length) return null;
  const price = closes[index];

  const r1 = price / closes[index - 1] - 1;
  const r5 = index >= 5 ? price / closes[index - 5] - 1 : null;

  const sma20 = sma(closes.slice(0, index + 1), 20).at(-1) ?? null;
  const sma50 = sma(closes.slice(0, index + 1), 50).at(-1) ?? null;

  const rsi14 = rsi(closes.slice(0, index + 1), 14).at(-1) ?? null;

  let vol20: number | null = null;
  if (index >= 20) {
    const returns: number[] = [];
    for (let k = index - 19; k <= index; k += 1) returns.push(closes[k] / closes[k - 1] - 1);
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    vol20 = Math.sqrt(returns.reduce((acc, r) => acc + (r - mean) ** 2, 0) / returns.length);
  }

  return {
    r1,
    r5,
    distSma20: sma20 === null ? null : price / sma20 - 1,
    distSma50: sma50 === null ? null : price / sma50 - 1,
    rsi14,
    vol20,
  };
}
