/**
 * Chart indicators computed in the browser with trading-signals (DESIGN §6, research §3.4).
 * The backend computes the same figures with TA-Lib for signals; BL-060 adds the parity test.
 */
import { ATR, RSI, SMA } from "trading-signals";

export type OhlcBar = { day: string; open: number; high: number; low: number; close: number; volume?: number | null };

export type IndicatorSnapshot = {
  sma50: (number | null)[];
  sma200: (number | null)[];
  rsi14: number | null;
  atr14: number | null;
  high52: number | null;
  low52: number | null;
  drawdownPct: number | null;
  distanceToSma200Pct: number | null;
};

const series = (closes: number[], period: number) => {
  const sma = new SMA(period);
  return closes.map((c) => sma.add(c));
};

export function computeIndicators(bars: OhlcBar[]): IndicatorSnapshot {
  const closes = bars.map((b) => b.close);
  const rsi = new RSI(14);
  const atr = new ATR(14);
  let rsi14: number | null = null;
  let atr14: number | null = null;
  for (const bar of bars) {
    rsi14 = rsi.add(bar.close);
    atr14 = atr.add({ high: bar.high, low: bar.low, close: bar.close });
  }
  const sma200 = series(closes, 200);
  const year = bars.slice(-252);
  const high52 = year.length ? Math.max(...year.map((b) => b.high)) : null;
  const low52 = year.length ? Math.min(...year.map((b) => b.low)) : null;
  const last = closes.at(-1) ?? null;
  const lastSma200 = sma200.at(-1) ?? null;
  return {
    sma50: series(closes, 50),
    sma200,
    rsi14,
    atr14,
    high52,
    low52,
    drawdownPct: last !== null && high52 ? (last / high52 - 1) * 100 : null,
    distanceToSma200Pct: last !== null && lastSma200 ? (last / lastSma200 - 1) * 100 : null,
  };
}
