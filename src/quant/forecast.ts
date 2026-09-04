/**
 * Deterministic next-close baselines. Every predictor reads closes[0..index]
 * only; out-of-range or under-warmed calls return null, never zero.
 */

export type PredictFn = (closes: number[], index: number) => number | null;

export interface ForecastEvaluation {
  mae: number | null;
  rmse: number | null;
  directionalAccuracy: number | null;
  predictions: number;
}

function valid(closes: number[], index: number): boolean {
  return Number.isInteger(index) && index >= 0 && index < closes.length;
}

export function naiveLast(closes: number[], index: number): number | null {
  if (!valid(closes, index)) return null;
  return closes[index];
}

export function smaPredict(window: number): PredictFn {
  return (closes, index) => {
    if (!valid(closes, index) || window <= 0 || index + 1 < window) return null;
    const slice = closes.slice(index - window + 1, index + 1);
    return slice.reduce((a, b) => a + b, 0) / window;
  };
}

export function linRegPredict(window: number): PredictFn {
  return (closes, index) => {
    if (!valid(closes, index) || window <= 1 || index + 1 < window) return null;
    const y = closes.slice(index - window + 1, index + 1);
    const n = y.length;
    const meanX = (n - 1) / 2;
    const meanY = y.reduce((a, b) => a + b, 0) / n;
    let num = 0;
    let den = 0;
    for (let x = 0; x < n; x += 1) {
      num += (x - meanX) * (y[x] - meanY);
      den += (x - meanX) ** 2;
    }
    if (den === 0) return meanY;
    const slope = num / den;
    return meanY + slope * (n - meanX);
  };
}

/**
 * Adapter for a future external challenger (LightGBM / TimesFM service).
 * Keeps the PredictFn contract so evaluation and promotion rules stay put.
 */
export function wrapChallenger(fn: PredictFn): PredictFn {
  return (closes, index) => fn(closes, index);
}

/** Walk-forward next-bar evaluation of a predictor over full history. */
export function evaluateForecast(closes: number[], fn: PredictFn): ForecastEvaluation | null {
  if (closes.length < 2) return null;
  let absSum = 0;
  let sqSum = 0;
  let correct = 0;
  let total = 0;

  for (let i = 0; i < closes.length - 1; i += 1) {
    const predicted = fn(closes, i);
    if (predicted === null) continue;
    const actual = closes[i + 1];
    absSum += Math.abs(predicted - actual);
    sqSum += (predicted - actual) ** 2;
    const predictedDir = Math.sign(predicted - closes[i]);
    const actualDir = Math.sign(actual - closes[i]);
    if (predictedDir === actualDir) correct += 1;
    total += 1;
  }

  if (total === 0) return { mae: null, rmse: null, directionalAccuracy: null, predictions: 0 };
  return {
    mae: absSum / total,
    rmse: Math.sqrt(sqSum / total),
    directionalAccuracy: correct / total,
    predictions: total,
  };
}

/** Promotion gate: beats persistence on error AND direction with enough samples. */
export function beatsNaive(
  candidate: ForecastEvaluation | null,
  naive: ForecastEvaluation | null,
): boolean {
  if (!candidate || !naive) return false;
  if (candidate.mae === null || naive.mae === null) return false;
  if (candidate.directionalAccuracy === null) return false;
  if (candidate.predictions < 30 || naive.predictions < 30) return false;
  return candidate.mae < (naive.mae as number) && candidate.directionalAccuracy > 0.5;
}
