import { describe, expect, it } from "vitest";

import { buildFeatures } from "./features";

describe("feature builder", () => {
  it("returns null during warmup", () => {
    expect(buildFeatures([100], 0)).toBeNull();
    expect(buildFeatures([100, 101], 1)?.r5).toBeNull();
    expect(buildFeatures([100, 101], 1)?.vol20).toBeNull();
  });

  it("computes hand-verified lagged returns", () => {
    const closes = [100, 101, 102, 103, 104, 105];
    const features = buildFeatures(closes, 1);

    expect(features?.r1).toBeCloseTo(0.01, 8);
    expect(buildFeatures(closes, 5)?.r5).toBeCloseTo(5 / 100, 8);
  });

  it("computes SMA distances and RSI without future reads", () => {
    const closes = Array.from({ length: 60 }, (_, i) => 100 + i);
    const features = buildFeatures(closes, 59);

    expect(features?.distSma20).toBeGreaterThan(0);
    expect(features?.distSma50).toBeGreaterThan(0);
    expect(features?.rsi14).toBeCloseTo(100, 3);
  });
});
