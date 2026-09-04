import { describe, expect, it } from "vitest";

import type { PricePoint } from "@/domain/price-history";

import { buyAndHold, runBacktest } from "./backtest";
import { inSampleOutOfSample, rollingCorrelation, walkForward } from "./validation";

function points(closes: number[]): PricePoint[] {
  const base = Date.UTC(2025, 0, 1);
  return closes.map((close, i) => ({
    timestamp: new Date(base + i * 86_400_000).toISOString(),
    close,
    volume: null,
  }));
}

describe("validation", () => {
  it("splits history into time-ordered in/out samples", () => {
    const history = points([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    const { inSample, outOfSample } = inSampleOutOfSample(history, 0.7);

    expect(inSample).toHaveLength(7);
    expect(outOfSample).toHaveLength(3);
    expect(inSample.at(-1)!.timestamp < outOfSample[0].timestamp).toBe(true);
  });

  it("walk-forward evaluates each fold out-of-sample only", () => {
    const history = points(Array.from({ length: 20 }, (_, i) => 100 + i));
    const folds = walkForward(history, { trainSize: 10, testSize: 5 });

    expect(folds).toHaveLength(2);
    expect(folds[0].test[0].timestamp).toBe(history[10].timestamp);
    for (const fold of folds) {
      const result = runBacktest(fold.test, buyAndHold(), { commissionBps: 0, slippageBps: 0 });
      expect(result.totalReturn).toBeGreaterThan(0);
    }
  });

  it("rolling correlation stays in [-1, 1]", () => {
    const a = [1, 2, 3, 4, 5, 6];
    const b = [2, 4, 6, 8, 10, 12];
    const result = rollingCorrelation(a, b, 3);

    expect(result.slice(0, 2)).toEqual([null, null]);
    expect(result[2]).toBeCloseTo(1, 8);
  });
});
