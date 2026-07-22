import { describe, expect, it } from "vitest";

import type { PricePoint } from "@/domain/price-history";

import {
  filterPriceHistory,
  summarizePriceHistory,
  toChartPoints,
} from "./price-history";

function monthlyPointsFrom(startDate: string, endDate: string): PricePoint[] {
  const [startYear, startMonth, startDay] = startDate.split("-").map(Number);
  const [endYear, endMonth] = endDate.split("-").map(Number);
  const points: PricePoint[] = [];

  for (
    let year = startYear, month = startMonth - 1;
    year < endYear || (year === endYear && month <= endMonth - 1);
    month += 1
  ) {
    if (month === 12) {
      year += 1;
      month = 0;
    }
    const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
    const day = Math.min(startDay, lastDay);
    points.push({
      timestamp: `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}T20:00:00Z`,
      close: points.length + 100,
      volume: null,
    });
  }

  return points;
}

describe("price history transformations", () => {
  it("anchors month ranges to the latest observation", () => {
    const points = monthlyPointsFrom("2021-07-31", "2026-07-31");

    expect(filterPriceHistory(points, "1M").at(0)?.timestamp).toBe(
      "2026-06-30T20:00:00Z",
    );
    expect(filterPriceHistory(points, "1Y").at(0)?.timestamp).toBe(
      "2025-07-31T20:00:00Z",
    );
    expect(filterPriceHistory(points, "MAX")).toHaveLength(points.length);
  });

  it("keeps the final duplicate observation and sorts timestamps ascending", () => {
    const points: PricePoint[] = [
      { timestamp: "2026-07-02T20:00:00Z", close: 102, volume: 12 },
      { timestamp: "2026-07-01T20:00:00Z", close: 100, volume: null },
      { timestamp: "2026-07-02T20:00:00Z", close: 103, volume: null },
    ];

    expect(filterPriceHistory(points, "MAX")).toEqual([
      { timestamp: "2026-07-01T20:00:00Z", close: 100, volume: null },
      { timestamp: "2026-07-02T20:00:00Z", close: 103, volume: null },
    ]);
  });

  it("summarizes range endpoints without changing null volume data", () => {
    const points: PricePoint[] = [
      { timestamp: "2026-01-01T20:00:00Z", close: 100, volume: null },
      { timestamp: "2026-02-01T20:00:00Z", close: 125, volume: 10 },
    ];

    expect(summarizePriceHistory(points, "USD")).toMatchObject({
      startPrice: 100,
      endPrice: 125,
      absoluteChange: 25,
      percentChange: 0.25,
      currency: "USD",
      observationCount: 2,
    });
    expect(toChartPoints(points)).toEqual([
      { time: "2026-01-01", value: 100, volume: null },
      { time: "2026-02-01", value: 125, volume: 10 },
    ]);
  });

  it("returns null for an empty summary", () => {
    expect(summarizePriceHistory([], "USD")).toBeNull();
  });
});
