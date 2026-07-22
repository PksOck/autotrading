"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { PricePoint, PriceRange } from "@/domain/price-history";
import { formatCurrency, formatPercent } from "@/lib/format";
import {
  filterPriceHistory,
  summarizePriceHistory,
  toChartPoints,
} from "@/lib/price-history";

import { mountPriceVolumeChart } from "./lightweight-chart-adapter";

const ranges: PriceRange[] = ["1M", "6M", "1Y", "5Y", "MAX"];

export interface PriceChartProps {
  points: PricePoint[];
  currency: string;
  source: string;
  asOf: string;
  initialRange: PriceRange;
}

function rootIsDark(): boolean {
  return document.documentElement.classList.contains("dark");
}

export function PriceChart({
  points,
  currency,
  source,
  asOf,
  initialRange,
}: PriceChartProps) {
  const [range, setRange] = useState<PriceRange>(initialRange);
  const frameRef = useRef<HTMLDivElement>(null);
  const filteredPoints = useMemo(() => filterPriceHistory(points, range), [points, range]);
  const chartData = useMemo(() => toChartPoints(filteredPoints), [filteredPoints]);
  const summary = useMemo(
    () => summarizePriceHistory(filteredPoints, currency),
    [filteredPoints, currency],
  );
  const showVolume = chartData.some((point) => point.volume !== null);
  const summaryText = summary
    ? `${range} · ${summary.observationCount} observations: ${formatCurrency(summary.startPrice, currency)} to ${formatCurrency(summary.endPrice, currency)}. Change: ${formatCurrency(summary.absoluteChange, currency)} (${formatPercent(summary.percentChange)}).`
    : null;

  useEffect(() => {
    const element = frameRef.current;
    if (!element || chartData.length === 0) return;

    const chart = mountPriceVolumeChart(element, chartData, {
      showVolume,
      isDark: rootIsDark(),
    });
    const resize = () => chart.resize(element.clientWidth, element.clientHeight);
    const resizeObserver = typeof ResizeObserver === "undefined"
      ? undefined
      : new ResizeObserver(resize);
    resizeObserver?.observe(element);
    const themeObserver = new MutationObserver(() => chart.updateTheme(rootIsDark()));
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    return () => {
      resizeObserver?.disconnect();
      themeObserver.disconnect();
      chart.destroy();
    };
  }, [chartData, showVolume]);

  return (
    <section className="data-section price-history" aria-labelledby="price-history-heading">
      <div className="section-heading">
        <h2 id="price-history-heading">Price history</h2>
        <div className="chart-ranges" aria-label="Price history range">
          {ranges.map((candidate) => (
            <button
              aria-pressed={range === candidate}
              key={candidate}
              onClick={() => setRange(candidate)}
              type="button"
            >
              {candidate}
            </button>
          ))}
        </div>
      </div>
      <p className="chart-provenance">
        Source: {source}. As of <time dateTime={asOf}>{asOf.slice(0, 10)}</time>.
      </p>
      {summary ? (
        <p className="chart-summary" aria-live="polite">
          {summaryText}
        </p>
      ) : null}
      <div
        aria-hidden={summary ? "true" : undefined}
        aria-label={summary ? undefined : "No price history available"}
        className={summary ? "chart-frame" : "chart-frame chart-empty"}
        data-range={range}
        data-testid="price-volume-chart-frame"
        data-volume={showVolume ? "shown" : "unavailable"}
        ref={summary ? frameRef : undefined}
        role={summary ? undefined : "status"}
      >
        {summary ? null : "No price history available"}
      </div>
      <p className="chart-volume">{showVolume ? "Volume shown below price" : "Volume not available"}</p>
    </section>
  );
}
