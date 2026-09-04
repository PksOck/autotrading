import { describe, expect, it } from "vitest";

import { bollingerBands, ema, macd, rsi, sma } from "./indicators";

const closes = [10, 11, 12, 13, 14, 15, 16];

describe("quant indicators", () => {
  it("computes SMA with null warmup", () => {
    expect(sma(closes, 3)).toEqual([null, null, 11, 12, 13, 14, 15]);
  });

  it("computes EMA seeded from SMA", () => {
    const result = ema(closes, 3);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(11, 8);
    expect(result[3]).toBeCloseTo(12, 8);
  });

  it("computes RSI in 0..100 with null warmup", () => {
    const up = [10, 11, 12, 13, 14, 15, 16, 17];
    const result = rsi(up, 3);
    expect(result.slice(0, 3)).toEqual([null, null, null]);
    expect(result[3]).toBeCloseTo(100, 5);
  });

  it("computes MACD line as fast minus slow EMA", () => {
    const series = Array.from({ length: 40 }, (_, i) => 100 + i);
    const result = macd(series, 12, 26, 9);
    expect(result.macdLine[25]).not.toBeNull();
    expect(result.signalLine[33]).not.toBeNull();
    expect(result.histogram[33]).toBeCloseTo(
      (result.macdLine[33] as number) - (result.signalLine[33] as number),
      8,
    );
  });

  it("computes Bollinger bands symmetric around SMA", () => {
    const result = bollingerBands(closes, 3, 2);
    const middle = result[2]?.middle;
    expect(middle).toBeCloseTo(11, 8);
    expect(result[2]?.upper).toBeGreaterThan(middle as number);
    expect(result[2]?.lower).toBeLessThan(middle as number);
  });
});
