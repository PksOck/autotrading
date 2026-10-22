import { computeIndicators, type OhlcBar } from "./indicators";

const bars = (n: number, f: (i: number) => number): OhlcBar[] =>
  Array.from({ length: n }, (_, i) => {
    const c = f(i);
    return { day: `d${i}`, open: c, high: c + 1, low: c - 1, close: c };
  });

describe("computeIndicators", () => {
  it("keeps warm-up values null and averages correctly", () => {
    const result = computeIndicators(bars(60, (i) => i + 1));
    expect(result.sma50[48]).toBeNull();
    expect(result.sma50[49]).toBeCloseTo(25.5);
    expect(result.sma200.every((v) => v === null)).toBe(true);
    expect(result.distanceToSma200Pct).toBeNull();
  });

  it("measures drawdown from the 52-week high", () => {
    const result = computeIndicators(bars(260, (i) => (i < 200 ? 100 + i : 299 - (i - 200))));
    expect(result.high52).toBe(300);
    expect(result.drawdownPct).toBeCloseTo((240 / 300 - 1) * 100, 5);
    expect(result.rsi14).not.toBeNull();
    expect(result.atr14).toBeCloseTo(2, 0);
  });
});
