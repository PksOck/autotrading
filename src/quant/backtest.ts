import type { PricePoint } from "@/domain/price-history";

import { sma } from "./indicators";

export type Signal = -1 | 0 | 1;
export type SignalFn = (index: number, history: PricePoint[]) => Signal;

export interface BacktestCosts {
  initialCapital?: number;
  commissionBps?: number;
  slippageBps?: number;
}

export interface BacktestResult {
  totalReturn: number;
  cagr: number;
  sharpe: number;
  maxDrawdown: number;
  trades: number;
  turnover: number;
  equityCurve: (number | null)[];
}

/**
 * Event-driven long/flat backtest. Signals use data up to index i and
 * trade at close[i]; costs apply per side. No shorting, no leverage.
 */
export function runBacktest(
  history: PricePoint[],
  signal: SignalFn,
  costs: BacktestCosts = {},
): BacktestResult {
  const initialCapital = costs.initialCapital ?? 10_000;
  const commission = (costs.commissionBps ?? 5) / 10_000;
  const slippage = (costs.slippageBps ?? 5) / 10_000;
  const equityCurve: (number | null)[] = new Array(history.length).fill(null);
  if (history.length < 2) return { totalReturn: 0, cagr: 0, sharpe: 0, maxDrawdown: 0, trades: 0, turnover: 0, equityCurve };

  let cash = initialCapital;
  let shares = 0;
  let position: Signal = 0;
  let trades = 0;
  let turnoverNotional = 0;
  let peak = initialCapital;

  const firstTime = new Date(history[0].timestamp).getTime();
  const lastTime = new Date(history.at(-1)!.timestamp).getTime();
  const years = Math.max((lastTime - firstTime) / (365.25 * 86_400_000), 1 / 365.25);

  const equity: number[] = [];
  for (let i = 0; i < history.length; i += 1) {
    const price = history[i].close;
    const target = signal(i, history);
    if (target !== position) {
      if (target === 1 && position === 0) {
        const execPrice = price * (1 + slippage);
        const fee = cash * commission;
        cash -= fee;
        shares = cash / execPrice;
        turnoverNotional += cash;
        cash = 0;
        trades += 1;
      } else if (target === 0 && position === 1) {
        const execPrice = price * (1 - slippage);
        cash = shares * execPrice * (1 - commission);
        turnoverNotional += shares * execPrice;
        shares = 0;
        trades += 1;
      }
      position = target === 1 ? 1 : 0;
    }
    const value = cash + shares * price;
    equity.push(value);
    equityCurve[i] = value;
    peak = Math.max(peak, value);
  }

  const finalValue = equity.at(-1) as number;
  const totalReturn = finalValue / initialCapital - 1;
  const cagr = (1 + totalReturn) ** (1 / years) - 1;

  let maxDrawdown = 0;
  let runningPeak = initialCapital;
  for (const value of equity) {
    runningPeak = Math.max(runningPeak, value);
    maxDrawdown = Math.max(maxDrawdown, (runningPeak - value) / runningPeak);
  }

  const returns: number[] = [];
  for (let i = 1; i < equity.length; i += 1) returns.push(equity[i] / equity[i - 1] - 1);
  const mean = returns.reduce((a, b) => a + b, 0) / Math.max(returns.length, 1);
  const variance = returns.reduce((acc, r) => acc + (r - mean) ** 2, 0) / Math.max(returns.length - 1, 1);
  const sharpe = variance > 0 ? (mean / Math.sqrt(variance)) * Math.sqrt(252) : 0;

  return {
    totalReturn,
    cagr,
    sharpe,
    maxDrawdown,
    trades,
    turnover: turnoverNotional / initialCapital,
    equityCurve,
  };
}

export function buyAndHold(): SignalFn {
  return (index) => (index === 0 ? 1 : 1);
}

/** Classic fast/slow SMA cross, long-only. Warmup emits 0. */
export function smaCrossSignals(history: PricePoint[], fast: number, slow: number): Signal[] {
  const closes = history.map((p) => p.close);
  const fastSma = sma(closes, fast);
  const slowSma = sma(closes, slow);
  return history.map((_, i) => {
    if (fastSma[i] === null || slowSma[i] === null) return 0;
    return (fastSma[i] as number) > (slowSma[i] as number) ? 1 : 0;
  });
}

/** RSI mean-reversion: long when RSI crosses below oversold, flat above overbought. */
export function rsiMeanReversionSignals(rsiValues: (number | null)[], oversold = 30, overbought = 70): Signal[] {
  let position: Signal = 0;
  return rsiValues.map((value) => {
    if (value === null) return 0;
    if (value < oversold) position = 1;
    else if (value > overbought) position = 0;
    return position;
  });
}
