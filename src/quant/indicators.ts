/**
 * Deterministic technical indicators over close-price series.
 * Warmup values are null (never zero). Pure functions, no I/O.
 */

export function sma(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  if (period <= 0) return out;
  let sum = 0;
  for (let i = 0; i < values.length; i += 1) {
    sum += values[i];
    if (i >= period) sum -= values[i - period];
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

export function ema(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  if (period <= 0 || values.length < period) return out;
  const seed = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  const k = 2 / (period + 1);
  out[period - 1] = seed;
  for (let i = period; i < values.length; i += 1) {
    out[i] = values[i] * k + (out[i - 1] as number) * (1 - k);
  }
  return out;
}

function emaSeeded(values: (number | null)[], period: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  const firstValid = values.findIndex((v) => v !== null);
  if (firstValid === -1) return out;
  const k = 2 / (period + 1);
  let prev: number | null = null;
  let seedSum = 0;
  let seedCount = 0;
  for (let i = firstValid; i < values.length; i += 1) {
    const value = values[i] as number;
    if (seedCount < period) {
      seedSum += value;
      seedCount += 1;
      if (seedCount === period) {
        prev = seedSum / period;
        out[i] = prev;
      }
      continue;
    }
    prev = value * k + (prev as number) * (1 - k);
    out[i] = prev;
  }
  return out;
}

export function rsi(closes: number[], period = 14): (number | null)[] {
  const out: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length <= period) return out;
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = closes[i] - closes[i - 1];
    if (change > 0) gain += change;
    else loss -= change;
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  out[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = period + 1; i < closes.length; i += 1) {
    const change = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(change, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-change, 0)) / period;
    out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return out;
}

export interface MacdResult {
  macdLine: (number | null)[];
  signalLine: (number | null)[];
  histogram: (number | null)[];
}

export function macd(closes: number[], fast = 12, slow = 26, signal = 9): MacdResult {
  const fastEma = ema(closes, fast);
  const slowEma = ema(closes, slow);
  const macdLine: (number | null)[] = closes.map((_, i) =>
    fastEma[i] !== null && slowEma[i] !== null ? (fastEma[i] as number) - (slowEma[i] as number) : null,
  );
  const signalLine = emaSeeded(macdLine, signal);
  const histogram = macdLine.map((value, i) =>
    value !== null && signalLine[i] !== null ? value - (signalLine[i] as number) : null,
  );
  return { macdLine, signalLine, histogram };
}

export interface BollingerBand {
  middle: number;
  upper: number;
  lower: number;
}

export function bollingerBands(closes: number[], period = 20, mult = 2): (BollingerBand | null)[] {
  const middle = sma(closes, period);
  return closes.map((_, i) => {
    if (middle[i] === null) return null;
    const window = closes.slice(i - period + 1, i + 1);
    const mean = middle[i] as number;
    const variance = window.reduce((acc, value) => acc + (value - mean) ** 2, 0) / period;
    const sd = Math.sqrt(variance);
    return { middle: mean, upper: mean + mult * sd, lower: mean - mult * sd };
  });
}

export function atr(highs: number[], lows: number[], closes: number[], period = 14): (number | null)[] {
  const out: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length <= period) return out;
  const trs: number[] = [];
  for (let i = 1; i < closes.length; i += 1) {
    trs.push(Math.max(highs[i] - lows[i], Math.abs(highs[i] - closes[i - 1]), Math.abs(lows[i] - closes[i - 1])));
  }
  let avg = trs.slice(0, period).reduce((a, b) => a + b, 0) / period;
  out[period] = avg;
  for (let i = period + 1; i < closes.length; i += 1) {
    avg = (avg * (period - 1) + trs[i - 1]) / period;
    out[i] = avg;
  }
  return out;
}
