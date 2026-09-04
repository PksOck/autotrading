import { describe, expect, it } from "vitest";

import {
  beatsNaive,
  evaluateForecast,
  linRegPredict,
  naiveLast,
  smaPredict,
  wrapChallenger,
} from "./forecast";

describe("forecast baselines", () => {
  it("naive predicts the last observed close", () => {
    expect(naiveLast([1, 2, 3], 2)).toBe(3);
    expect(naiveLast([1, 2, 3], -1)).toBeNull();
  });

  it("SMA predictor averages the trailing window", () => {
    expect(smaPredict(3)([10, 20, 30], 2)).toBeCloseTo(20, 8);
    expect(smaPredict(5)([10, 20], 1)).toBeNull();
  });

  it("linear regression extrapolates a linear series exactly", () => {
    expect(linRegPredict(3)([10, 20, 30], 2)).toBeCloseTo(40, 6);
    expect(linRegPredict(5)([10, 20], 1)).toBeNull();
  });

  it("evaluates MAE/RMSE/directional accuracy on known arrays", () => {
    const evaluation = evaluateForecast([100, 101, 102, 103], naiveLast);

    expect(evaluation?.predictions).toBe(3);
    expect(evaluation?.mae).toBeCloseTo(1, 8);
    expect(evaluation?.rmse).toBeCloseTo(1, 8);
    expect(evaluation?.directionalAccuracy).toBeCloseTo(0, 8);
  });

  it("challenger adapter preserves the wrapped function contract", () => {
    const challenger = wrapChallenger(() => 42);
    expect(challenger([1, 2, 3], 2)).toBe(42);
  });

  it("promotion requires lower MAE, DA above half, and 30 predictions", () => {
    const naive = { mae: 2, rmse: 2, directionalAccuracy: 0.5, predictions: 40 };
    expect(beatsNaive({ ...naive, mae: 1, directionalAccuracy: 0.6 }, naive)).toBe(true);
    expect(beatsNaive({ ...naive, mae: 3, directionalAccuracy: 0.9 }, naive)).toBe(false);
    expect(beatsNaive({ ...naive, mae: 1, directionalAccuracy: 0.5 }, naive)).toBe(false);
    expect(beatsNaive({ ...naive, mae: 1, directionalAccuracy: 0.9, predictions: 10 }, naive)).toBe(false);
    expect(beatsNaive(null, naive)).toBe(false);
  });
});
