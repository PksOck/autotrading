import { z } from "zod";

export interface ValuationAssumptions {
  normalizedFcf: number;
  growthRate: number;
  explicitYears: number;
  terminalGrowthRate: number;
  discountRate: number;
  netDebt: number;
  dilutedShares: number;
}

export interface ValuationBreakdown {
  explicitPeriodValue: number;
  terminalValuePresentValue: number;
  enterpriseValue: number;
  equityValue: number;
  perShareValue: number;
}

export type ValuationScenarioId = "conservative" | "base" | "optimistic";

export interface ValuationScenario {
  id: ValuationScenarioId;
  label: string;
  assumptions: Pick<
    ValuationAssumptions,
    "growthRate" | "explicitYears" | "terminalGrowthRate" | "discountRate"
  >;
}

export const VALUATION_SCENARIOS: ValuationScenario[] = [
  {
    id: "conservative",
    label: "Conservative",
    assumptions: { growthRate: 0.04, explicitYears: 5, terminalGrowthRate: 0.015, discountRate: 0.12 },
  },
  {
    id: "base",
    label: "Base",
    assumptions: { growthRate: 0.08, explicitYears: 5, terminalGrowthRate: 0.02, discountRate: 0.1 },
  },
  {
    id: "optimistic",
    label: "Optimistic",
    assumptions: { growthRate: 0.12, explicitYears: 5, terminalGrowthRate: 0.025, discountRate: 0.09 },
  },
];

const assumptionsSchema = z
  .object({
    normalizedFcf: z.number().finite(),
    growthRate: z.number().finite(),
    explicitYears: z.number().int().min(1).max(20),
    terminalGrowthRate: z.number().finite(),
    discountRate: z.number().finite().positive(),
    netDebt: z.number().finite(),
    dilutedShares: z.number().finite().positive(),
  })
  .superRefine((assumptions, context) => {
    if (assumptions.terminalGrowthRate >= assumptions.discountRate) {
      context.addIssue({
        code: "custom",
        message: "Terminal growth must stay below the discount rate",
        path: ["terminalGrowthRate"],
      });
    }
  });

export function validateValuationAssumptions(assumptions: ValuationAssumptions): {
  errors: string[];
  warnings: string[];
} {
  const parsed = assumptionsSchema.safeParse(assumptions);
  const errors = parsed.success
    ? []
    : parsed.error.issues.map((issue) => {
        const field = issue.path.length > 0 ? `${String(issue.path[0])}: ` : "";
        return `${field}${issue.message}`;
      });

  const warnings: string[] = [];
  if (assumptions.growthRate > 0.15) {
    warnings.push("Growth above 15% is unusually aggressive for a mature business");
  }
  if (Number.isFinite(assumptions.discountRate) && (assumptions.discountRate < 0.06 || assumptions.discountRate > 0.2)) {
    warnings.push("Discount rate outside 6–20% deserves a second look");
  }
  if (assumptions.terminalGrowthRate > 0.04) {
    warnings.push("Terminal growth above 4% exceeds most long-run economic growth");
  }
  if (
    Number.isInteger(assumptions.explicitYears) &&
    assumptions.explicitYears >= 1 &&
    assumptions.explicitYears <= 20 &&
    assumptions.explicitYears > 10
  ) {
    warnings.push("Explicit horizons beyond 10 years carry high forecast uncertainty");
  }
  return { errors, warnings };
}

export function calculateDcfValue(assumptions: ValuationAssumptions): ValuationBreakdown {
  const validation = validateValuationAssumptions(assumptions);
  if (validation.errors.length > 0) {
    throw new Error(`Invalid valuation assumptions: ${validation.errors.join("; ")}`);
  }

  let explicitPeriodValue = 0;
  let yearFcf = assumptions.normalizedFcf;
  for (let year = 1; year <= assumptions.explicitYears; year += 1) {
    yearFcf *= 1 + assumptions.growthRate;
    explicitPeriodValue += yearFcf / (1 + assumptions.discountRate) ** year;
  }

  const terminalValue =
    (yearFcf * (1 + assumptions.terminalGrowthRate)) /
    (assumptions.discountRate - assumptions.terminalGrowthRate);
  const terminalValuePresentValue =
    terminalValue / (1 + assumptions.discountRate) ** assumptions.explicitYears;

  const enterpriseValue = explicitPeriodValue + terminalValuePresentValue;
  const equityValue = enterpriseValue - assumptions.netDebt;
  return {
    explicitPeriodValue,
    terminalValuePresentValue,
    enterpriseValue,
    equityValue,
    perShareValue: equityValue / assumptions.dilutedShares,
  };
}
