import type { PricePoint, PriceRange } from "@/domain/price-history";

export interface ChartPoint {
  time: string;
  value: number;
  volume: number | null;
}

export interface PriceHistorySummary {
  startPrice: number;
  endPrice: number;
  absoluteChange: number;
  percentChange: number;
  currency: string;
  observationCount: number;
}

const rangeMonths: Record<Exclude<PriceRange, "MAX">, number> = {
  "1M": 1,
  "6M": 6,
  "1Y": 12,
  "5Y": 60,
};

function sortAndDeduplicate(points: PricePoint[]): PricePoint[] {
  const finalByTimestamp = new Map<string, PricePoint>();
  for (const point of points) {
    finalByTimestamp.set(point.timestamp, point);
  }

  return [...finalByTimestamp.values()].sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp),
  );
}

function subtractMonths(timestamp: string, months: number): Date {
  const latest = new Date(timestamp);
  const cutoff = new Date(
    Date.UTC(
      latest.getUTCFullYear(),
      latest.getUTCMonth() - months,
      1,
      latest.getUTCHours(),
      latest.getUTCMinutes(),
      latest.getUTCSeconds(),
      latest.getUTCMilliseconds(),
    ),
  );
  const lastDayOfMonth = new Date(
    Date.UTC(cutoff.getUTCFullYear(), cutoff.getUTCMonth() + 1, 0),
  ).getUTCDate();
  cutoff.setUTCDate(Math.min(latest.getUTCDate(), lastDayOfMonth));

  return cutoff;
}

export function filterPriceHistory(
  points: PricePoint[],
  range: PriceRange,
): PricePoint[] {
  const sortedPoints = sortAndDeduplicate(points);
  if (range === "MAX" || sortedPoints.length === 0) return sortedPoints;

  const cutoff = subtractMonths(
    sortedPoints[sortedPoints.length - 1].timestamp,
    rangeMonths[range],
  ).getTime();

  return sortedPoints.filter(({ timestamp }) => new Date(timestamp).getTime() >= cutoff);
}

export function summarizePriceHistory(
  points: PricePoint[],
  currency: string,
): PriceHistorySummary | null {
  if (points.length === 0) return null;

  const first = points[0];
  const last = points[points.length - 1];
  const absoluteChange = last.close - first.close;

  return {
    startPrice: first.close,
    endPrice: last.close,
    absoluteChange,
    percentChange: absoluteChange / first.close,
    currency,
    observationCount: points.length,
  };
}

export function toChartPoints(points: PricePoint[]): ChartPoint[] {
  return points.map(({ timestamp, close, volume }) => ({
    time: timestamp.slice(0, 10),
    value: close,
    volume,
  }));
}
