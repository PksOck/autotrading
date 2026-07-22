import {
  ColorType,
  createChart,
  HistogramSeries,
  LineSeries,
  type Time,
} from "lightweight-charts";

import type { ChartPoint } from "@/lib/price-history";

export interface PriceVolumeChartOptions {
  showVolume: boolean;
  isDark?: boolean;
}

function themeOptions(isDark: boolean) {
  const textColor = isDark ? "#dbe7ff" : "#14213d";
  const gridColor = isDark ? "#263653" : "#dbe3ef";

  return {
    layout: {
      background: { type: ColorType.Solid, color: isDark ? "#0d1527" : "#ffffff" },
      textColor,
    },
    grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } },
  };
}

export function mountPriceVolumeChart(
  element: HTMLElement,
  data: ChartPoint[],
  { showVolume, isDark = false }: PriceVolumeChartOptions,
) {
  const chart = createChart(element, {
    ...themeOptions(isDark),
    width: element.clientWidth,
    height: element.clientHeight,
    crosshair: { mode: 0 },
    rightPriceScale: { borderColor: isDark ? "#4d6388" : "#b9c6d8" },
    timeScale: { borderColor: isDark ? "#4d6388" : "#b9c6d8" },
  });
  const priceSeries = chart.addSeries(LineSeries, {
    color: "#3562d8",
    lineWidth: 2,
    priceScaleId: "right",
  });
  chart.priceScale("right").applyOptions({
    scaleMargins: { top: 0.08, bottom: showVolume ? 0.3 : 0.08 },
  });

  priceSeries.setData(data.map(({ time, value }) => ({ time: time as Time, value })));

  if (showVolume) {
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#7d9ef2",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.76, bottom: 0 } });
    volumeSeries.setData(
      data
        .filter((point): point is ChartPoint & { volume: number } => point.volume !== null)
        .map(({ time, volume }) => ({ time: time as Time, value: volume })),
    );
  }

  chart.timeScale().fitContent();

  return {
    updateTheme(nextIsDark: boolean) {
      chart.applyOptions(themeOptions(nextIsDark));
    },
    resize(width: number, height: number) {
      chart.resize(width, height);
    },
    destroy() {
      chart.remove();
    },
  };
}
