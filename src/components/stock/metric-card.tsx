import { formatCompactNumber, formatMultiple, formatPercent } from "@/lib/format";

type MetricUnit = "currency" | "multiple" | "percent";

export function MetricCard({ label, value, unit, currency }: { label: string; value: number | null; unit: MetricUnit; currency: string }) {
  const formatted = unit === "currency" ? formatCompactNumber(value) : unit === "multiple" ? formatMultiple(value) : formatPercent(value);
  return (
    <div className="metric-card">
      <dt>{label}</dt>
      <dd>{formatted}</dd>
      <span>{unit === "currency" ? currency : unit}</span>
    </div>
  );
}
