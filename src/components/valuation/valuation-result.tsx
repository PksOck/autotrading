import type { ValuationBreakdown } from "@/domain/valuation";
import { MetricCard } from "@/components/stock/metric-card";

export function ValuationResult({
  breakdown,
  currency,
  unit,
}: {
  breakdown: ValuationBreakdown;
  currency: string;
  unit: string;
}) {
  return (
    <div role="region" aria-label="Valuation result">
      <p className="valuation-provenance">
        Two-stage discounted cash flow in {currency} {unit}.
      </p>
      <dl className="metric-grid">
        <MetricCard label="Explicit period value" value={breakdown.explicitPeriodValue} unit="currency" currency={currency} />
        <MetricCard label="Terminal value (present)" value={breakdown.terminalValuePresentValue} unit="currency" currency={currency} />
        <MetricCard label="Enterprise value" value={breakdown.enterpriseValue} unit="currency" currency={currency} />
        <MetricCard label="Equity value" value={breakdown.equityValue} unit="currency" currency={currency} />
        <MetricCard label="Per-share estimate" value={breakdown.perShareValue} unit="currency" currency={currency} />
      </dl>
      <p className="estimate-note">
        <strong>Estimate — not a recommendation or target price.</strong> A mechanical
        scenario output for research only.
      </p>
    </div>
  );
}
