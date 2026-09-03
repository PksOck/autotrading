import { describe, expect, it } from "vitest";

import {
  VALUATION_SCENARIOS,
  calculateDcfValue,
  validateValuationAssumptions,
  type ValuationAssumptions,
} from "./valuation";

const base: ValuationAssumptions = {
  normalizedFcf: 100,
  growthRate: 0.1,
  explicitYears: 3,
  terminalGrowthRate: 0.02,
  discountRate: 0.1,
  netDebt: 50,
  dilutedShares: 10,
};

describe("DCF valuation", () => {
  it("values the hand-verified example: explicit PV 300, terminal PV 1275", () => {
    // FCF: 110, 121, 133.1. Each discounts to exactly 100 at a 10% rate.
    // Terminal: 133.1 * 1.02 / 0.08 = 1697.025, discounted at 1.1^3 = 1275.
    const breakdown = calculateDcfValue(base);

    expect(breakdown.explicitPeriodValue).toBeCloseTo(300, 8);
    expect(breakdown.terminalValuePresentValue).toBeCloseTo(1275, 8);
    expect(breakdown.enterpriseValue).toBeCloseTo(1575, 8);
    expect(breakdown.equityValue).toBeCloseTo(1525, 8);
    expect(breakdown.perShareValue).toBeCloseTo(152.5, 8);
  });

  it("accepts valid assumptions without errors or warnings", () => {
    expect(validateValuationAssumptions(base)).toEqual({ errors: [], warnings: [] });
  });

  it("refuses terminal growth at or above the discount rate", () => {
    expect(
      validateValuationAssumptions({ ...base, terminalGrowthRate: 0.1 }).errors,
    ).not.toHaveLength(0);
    expect(
      validateValuationAssumptions({ ...base, terminalGrowthRate: 0.12 }).errors,
    ).not.toHaveLength(0);
  });

  it("refuses non-positive discount rates and share counts", () => {
    expect(validateValuationAssumptions({ ...base, discountRate: 0 }).errors).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, discountRate: -0.05 }).errors).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, dilutedShares: 0 }).errors).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, dilutedShares: -3 }).errors).not.toHaveLength(0);
  });

  it("refuses non-integer or out-of-range explicit horizons", () => {
    expect(validateValuationAssumptions({ ...base, explicitYears: 0 }).errors).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, explicitYears: 2.5 }).errors).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, explicitYears: 21 }).errors).not.toHaveLength(0);
  });

  it("refuses non-finite inputs", () => {
    expect(validateValuationAssumptions({ ...base, normalizedFcf: NaN }).errors).not.toHaveLength(0);
    expect(
      validateValuationAssumptions({ ...base, growthRate: Number.POSITIVE_INFINITY }).errors,
    ).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, netDebt: NaN }).errors).not.toHaveLength(0);
  });

  it("warns on extreme but computable assumptions", () => {
    expect(validateValuationAssumptions({ ...base, growthRate: 0.2 }).warnings).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, discountRate: 0.03 }).warnings).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, discountRate: 0.25 }).warnings).not.toHaveLength(0);
    expect(
      validateValuationAssumptions({ ...base, terminalGrowthRate: 0.05, discountRate: 0.1 }).warnings,
    ).not.toHaveLength(0);
    expect(validateValuationAssumptions({ ...base, explicitYears: 15 }).warnings).not.toHaveLength(0);
  });

  it("keeps every scenario preset internally consistent", () => {
    expect(VALUATION_SCENARIOS.map((scenario) => scenario.id)).toEqual([
      "conservative",
      "base",
      "optimistic",
    ]);
    for (const scenario of VALUATION_SCENARIOS) {
      const check = validateValuationAssumptions({
        ...scenario.assumptions,
        normalizedFcf: 100,
        netDebt: 0,
        dilutedShares: 10,
      });
      expect(check.errors).toEqual([]);
    }
    const [conservative, baseScenario, optimistic] = VALUATION_SCENARIOS.map((scenario) =>
      calculateDcfValue({ ...scenario.assumptions, normalizedFcf: 100, netDebt: 0, dilutedShares: 10 }),
    );
    expect(conservative.perShareValue).toBeLessThan(baseScenario.perShareValue);
    expect(baseScenario.perShareValue).toBeLessThan(optimistic.perShareValue);
  });
});
