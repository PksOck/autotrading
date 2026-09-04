import type { PricePoint } from "@/domain/price-history";

export interface WalkForwardFold {
  train: PricePoint[];
  test: PricePoint[];
}

/** Strictly time-ordered split; no shuffling, no leakage. */
export function inSampleOutOfSample(
  history: PricePoint[],
  trainRatio = 0.7,
): { inSample: PricePoint[]; outOfSample: PricePoint[] } {
  const cut = Math.floor(history.length * trainRatio);
  return { inSample: history.slice(0, cut), outOfSample: history.slice(cut) };
}

/** Rolling walk-forward folds with fixed train/test windows. */
export function walkForward(
  history: PricePoint[],
  options: { trainSize: number; testSize: number; step?: number },
): WalkForwardFold[] {
  const { trainSize, testSize, step = testSize } = options;
  const folds: WalkForwardFold[] = [];
  for (let start = 0; start + trainSize + testSize <= history.length; start += step) {
    folds.push({
      train: history.slice(start, start + trainSize),
      test: history.slice(start + trainSize, start + trainSize + testSize),
    });
  }
  return folds;
}

/** Pearson correlation over a rolling window; null during warmup. */
export function rollingCorrelation(a: number[], b: number[], window: number): (number | null)[] {
  const out: (number | null)[] = new Array(a.length).fill(null);
  for (let i = window - 1; i < a.length; i += 1) {
    const wa = a.slice(i - window + 1, i + 1);
    const wb = b.slice(i - window + 1, i + 1);
    const meanA = wa.reduce((x, y) => x + y, 0) / window;
    const meanB = wb.reduce((x, y) => x + y, 0) / window;
    const cov = wa.reduce((acc, _, k) => acc + (wa[k] - meanA) * (wb[k] - meanB), 0);
    const varA = wa.reduce((acc, v) => acc + (v - meanA) ** 2, 0);
    const varB = wb.reduce((acc, v) => acc + (v - meanB) ** 2, 0);
    out[i] = varA > 0 && varB > 0 ? cov / Math.sqrt(varA * varB) : null;
  }
  return out;
}

/**
 * Deflated Sharpe guard: penalizes the observed Sharpe by the number of
 * trials (strategies/parameter sets tested). Returns the haircut Sharpe
 * that must stay positive for the result to count.
 */
export function deflatedSharpe(observedSharpe: number, trials: number, observations = 252): number {
  if (trials <= 1) return observedSharpe;
  const expectedMax = Math.sqrt(2 * Math.log(trials)) - (Math.log(Math.log(trials)) + Math.log(4 * Math.PI)) / (2 * Math.sqrt(2 * Math.log(trials)));
  const variance = 1 / (observations - 1);
  return observedSharpe - expectedMax * Math.sqrt(variance);
}
