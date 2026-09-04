import type { PricePoint } from "@/domain/price-history";

import { buyAndHold, runBacktest, smaCrossSignals } from "@/quant/backtest";
import { ema, rsi, sma } from "@/quant/indicators";
import { inSampleOutOfSample, walkForward } from "@/quant/validation";

export interface TechnicalSummary {
  sma50: number | null;
  sma200: number | null;
  rsi14: number | null;
  ema12: number | null;
  ema26: number | null;
}

export function summarizeTechnicals(history: PricePoint[]): TechnicalSummary {
  const closes = history.map((p) => p.close);
  const last = <T>(series: (T | null)[]): T | null => (series.length === 0 ? null : series.at(-1) ?? null);
  return {
    sma50: last(sma(closes, 50)),
    sma200: last(sma(closes, 200)),
    rsi14: last(rsi(closes, 14)),
    ema12: last(ema(closes, 12)),
    ema26: last(ema(closes, 26)),
  };
}

export interface StrategyComparison {
  buyHold: { totalReturn: number; maxDrawdown: number; sharpe: number };
  smaCross: { totalReturn: number; maxDrawdown: number; sharpe: number; trades: number };
  outOfSample: { totalReturn: number; sharpe: number };
  walkForwardFolds: number;
  walkForwardMedianReturn: number;
}

export function compareStrategies(history: PricePoint[]): StrategyComparison | null {
  if (history.length < 60) return null;
  const noCost = { commissionBps: 0, slippageBps: 0 };
  const buyHold = runBacktest(history, buyAndHold(), { initialCapital: 10_000, ...noCost });
  const smaResult = runBacktest(
    history,
    (i, h) => smaCrossSignals(h, 50, 200)[i] as 0 | 1,
    { initialCapital: 10_000, commissionBps: 5, slippageBps: 5 },
  );
  const { outOfSample } = inSampleOutOfSample(history, 0.7);
  const oos = runBacktest(outOfSample, buyAndHold(), { initialCapital: 10_000, ...noCost });
  const folds = walkForward(history, { trainSize: Math.floor(history.length * 0.5), testSize: Math.floor(history.length * 0.15) });
  const foldReturns = folds.map(
    (fold) => runBacktest(fold.test, buyAndHold(), { initialCapital: 10_000, ...noCost }).totalReturn,
  );
  const sorted = [...foldReturns].sort((a, b) => a - b);

  return {
    buyHold: { totalReturn: buyHold.totalReturn, maxDrawdown: buyHold.maxDrawdown, sharpe: buyHold.sharpe },
    smaCross: { totalReturn: smaResult.totalReturn, maxDrawdown: smaResult.maxDrawdown, sharpe: smaResult.sharpe, trades: smaResult.trades },
    outOfSample: { totalReturn: oos.totalReturn, sharpe: oos.sharpe },
    walkForwardFolds: folds.length,
    walkForwardMedianReturn: sorted.length > 0 ? sorted[Math.floor(sorted.length / 2)] : 0,
  };
}
