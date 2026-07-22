import type { FinancialPeriod } from "@/domain/financials";
import { formatCompactNumber } from "@/lib/format";

type FinancialMetric = "revenue" | "operatingIncome" | "freeCashFlow";

interface FinancialTrendChartProps {
  periods: FinancialPeriod[];
  metric: FinancialMetric;
  label: string;
  currency: string;
  unit: string;
}

const chartWidth = 1000;
const chartHeight = 240;
const chartPadding = { top: 20, right: 24, bottom: 44, left: 24 };

export function FinancialTrendChart({ periods, metric, label, currency, unit }: FinancialTrendChartProps) {
  const values = periods.map((period) => period[metric]).filter((value): value is number => value !== null);
  const maximum = Math.max(0, ...values);
  const minimum = Math.min(0, ...values);
  const valueRange = maximum - minimum || 1;
  const plotHeight = chartHeight - chartPadding.top - chartPadding.bottom;
  const plotWidth = chartWidth - chartPadding.left - chartPadding.right;
  const zeroY = chartPadding.top + (maximum / valueRange) * plotHeight;
  const slotWidth = plotWidth / Math.max(periods.length, 1);
  const barWidth = Math.max(12, slotWidth * 0.56);

  return (
    <figure className="financial-trend-chart">
      <figcaption>{label}</figcaption>
      <svg
        role="img"
        aria-label={`${label} trend in ${currency} ${unit}`}
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        preserveAspectRatio="none"
      >
        <line className="financial-trend-baseline" x1={chartPadding.left} x2={chartWidth - chartPadding.right} y1={zeroY} y2={zeroY} />
        {periods.map((period, index) => {
          const value = period[metric];
          const x = chartPadding.left + index * slotWidth + (slotWidth - barWidth) / 2;
          const labelY = chartHeight - 12;

          if (value === null) {
            return (
              <g key={period.period} aria-label={`${period.period}: Not available (gap)`}>
                <rect className="financial-trend-gap" x={x} y={chartPadding.top} width={barWidth} height={plotHeight} />
                <text className="financial-trend-gap-label" x={x + barWidth / 2} y={chartPadding.top + plotHeight / 2}>Not available</text>
                <text className="financial-trend-period" x={x + barWidth / 2} y={labelY}>{period.period}</text>
              </g>
            );
          }

          const barHeight = Math.abs(value / valueRange) * plotHeight;
          const y = value >= 0 ? zeroY - barHeight : zeroY;
          return (
            <g key={period.period} aria-label={`${period.period}: ${formatCompactNumber(value)} ${currency} ${unit}`}>
              <rect className="financial-trend-bar" x={x} y={y} width={barWidth} height={barHeight} />
              <text className="financial-trend-period" x={x + barWidth / 2} y={labelY}>{period.period}</text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
