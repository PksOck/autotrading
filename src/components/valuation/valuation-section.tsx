"use client";

import { useMemo, useState } from "react";

import {
  VALUATION_SCENARIOS,
  calculateDcfValue,
  validateValuationAssumptions,
  type ValuationScenarioId,
} from "@/domain/valuation";
import { formatExactNumber } from "@/lib/format";

import { ValuationForm, type ValuationFormValues } from "./valuation-form";
import { ValuationResult } from "./valuation-result";

export interface ValuationSectionProps {
  currency: string;
  unit: string;
  latestFcf: { value: number; period: string } | null;
  dilutedShares: number | null;
}

function toNumber(raw: string): number {
  return raw.trim() === "" ? Number.NaN : Number(raw);
}

function scenarioDefaults(id: ValuationScenarioId): Pick<
  ValuationFormValues,
  "growthPercent" | "explicitYears" | "terminalPercent" | "discountPercent"
> {
  const scenario = VALUATION_SCENARIOS.find((entry) => entry.id === id) ?? VALUATION_SCENARIOS[1];
  return {
    growthPercent: String(scenario.assumptions.growthRate * 100),
    explicitYears: String(scenario.assumptions.explicitYears),
    terminalPercent: String(scenario.assumptions.terminalGrowthRate * 100),
    discountPercent: String(scenario.assumptions.discountRate * 100),
  };
}

export function ValuationSection({ currency, unit, latestFcf, dilutedShares }: ValuationSectionProps) {
  const [scenarioId, setScenarioId] = useState<ValuationScenarioId>("base");
  const [values, setValues] = useState<ValuationFormValues>(() => ({
    ...scenarioDefaults("base"),
    normalizedFcf: latestFcf ? String(latestFcf.value) : "",
    netDebt: "0",
    dilutedShares: dilutedShares === null ? "" : String(dilutedShares),
  }));

  const validation = useMemo(() => {
    if (!latestFcf || dilutedShares === null) return null;
    return validateValuationAssumptions({
      normalizedFcf: toNumber(values.normalizedFcf),
      growthRate: toNumber(values.growthPercent) / 100,
      explicitYears: toNumber(values.explicitYears),
      terminalGrowthRate: toNumber(values.terminalPercent) / 100,
      discountRate: toNumber(values.discountPercent) / 100,
      netDebt: toNumber(values.netDebt),
      dilutedShares: toNumber(values.dilutedShares),
    });
  }, [values, latestFcf, dilutedShares]);

  if (!latestFcf || dilutedShares === null || !validation) {
    return (
      <section className="data-section">
        <h2>Valuation scenarios</h2>
        <p>Valuation is not available for this instrument</p>
      </section>
    );
  }

  const breakdown =
    validation.errors.length === 0
      ? calculateDcfValue({
          normalizedFcf: toNumber(values.normalizedFcf),
          growthRate: toNumber(values.growthPercent) / 100,
          explicitYears: toNumber(values.explicitYears),
          terminalGrowthRate: toNumber(values.terminalPercent) / 100,
          discountRate: toNumber(values.discountPercent) / 100,
          netDebt: toNumber(values.netDebt),
          dilutedShares: toNumber(values.dilutedShares),
        })
      : null;

  return (
    <section className="data-section">
      <div className="section-heading">
        <h2>Valuation scenarios</h2>
        <p>
          {currency} {unit}
        </p>
      </div>
      <p className="valuation-provenance">
        Normalized FCF {formatExactNumber(latestFcf.value)} {currency} {unit} ·{" "}
        {latestFcf.period} annual · net debt assumed {formatExactNumber(toNumber(values.netDebt))} unless edited below.
      </p>
      <div className="chart-ranges" role="group" aria-label="Valuation scenario">
        {VALUATION_SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            aria-pressed={scenario.id === scenarioId}
            onClick={() => {
              setScenarioId(scenario.id);
              setValues((current) => ({ ...current, ...scenarioDefaults(scenario.id) }));
            }}
          >
            {scenario.label}
          </button>
        ))}
      </div>
      <ValuationForm
        values={values}
        currency={currency}
        unit={unit}
        onChange={(field, value) => setValues((current) => ({ ...current, [field]: value }))}
      />
      {validation.errors.length > 0 && (
        <div role="alert" className="valuation-errors">
          <p>Fix the following before estimating:</p>
          <ul>
            {validation.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      {validation.warnings.length > 0 && (
        <div className="valuation-warnings">
          <p>Assumption warnings:</p>
          <ul>
            {validation.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      {breakdown && <ValuationResult breakdown={breakdown} currency={currency} unit={unit} />}
    </section>
  );
}
