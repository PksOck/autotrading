import { describe, expect, it } from "vitest";

import type { PricePoint } from "@/domain/price-history";

import { runBacktest, smaCrossSignals } from "./backtest";

function points(closes: number[]): PricePoint[] {
  const base = Date.UTC(2025, 0, 1);
  return closes.map((close, i) => ({
    timestamp: new Date(base + i * 86_400_000).toISOString(),
    close,
    volume: null,
  }));
}

describe("backtester", () => {
  it("buy-and-hold tracks price change minus costs", () => {
    const history = points([100, 110, 121]);
    const result = runBacktest(history, () => 1, { initialCapital: 1000, commissionBps: 0, slippageBps: 0 });

    expect(result.trades).toBe(1);
    expect(result.totalReturn).toBeCloseTo(0.21, 8);
    expect(result.maxDrawdown).toBeCloseTo(0, 8);
  });

  it("stays in cash on all-zero signals", () => {
    const history = points([100, 90, 80]);
    const result = runBacktest(history, () => 0, { initialCapital: 1000 });

    expect(result.totalReturn).toBeCloseTo(0, 8);
    expect(result.trades).toBe(0);
  });

  it("charges commission and slippage per side", () => {
    const history = points([100, 100, 100]);
    const free = runBacktest(history, () => 1, { initialCapital: 1000, commissionBps: 0, slippageBps: 0 });
    const paid = runBacktest(history, () => 1, { initialCapital: 1000, commissionBps: 10, slippageBps: 10 });

    expect(paid.equityCurve.at(-1)).toBeLessThan(free.equityCurve.at(-1) as number);
    expect(paid.totalReturn).toBeLessThan(0);
  });

  it("SMA-cross uses only past data and emits -1/0/1", () => {
    const history = points([10, 11, 12, 11, 10, 9, 10, 11, 12, 13]);
    const signals = smaCrossSignals(history, 2, 4);

    expect(signals).toHaveLength(history.length);
    expect(signals.slice(0, 3).every((s) => s === 0)).toBe(true);
    expect(signals.every((s) => s === -1 || s === 0 || s === 1)).toBe(true);
  });

  it("computes max drawdown and Sharpe on a drawdown path", () => {
    const history = points([100, 120, 90, 110]);
    const result = runBacktest(history, () => 1, { initialCapital: 1000, commissionBps: 0, slippageBps: 0 });

    expect(result.maxDrawdown).toBeGreaterThan(0.2);
    expect(Number.isFinite(result.sharpe)).toBe(true);
  });
});
