"use client";

import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { OhlcBar } from "@/lib/indicators";
import { THEME_EVENT } from "@/lib/theme";

type Props = {
  locale: "sl" | "en";
  bars: OhlcBar[];
  sma50: (number | null)[];
  sma200: (number | null)[];
  summary: string;
  height?: number;
};

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const time = (day: string) => (Date.parse(`${day}T00:00:00Z`) / 1000) as UTCTimestamp;

function localization(locale: "sl" | "en") {
  const intl = locale === "sl" ? "sl-SI" : "en-US";
  const price = new Intl.NumberFormat(intl, { minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: "always" });
  return { locale: intl, priceFormatter: (value: number) => price.format(value) };
}

function themeOptions() {
  return {
    layout: {
      background: { type: ColorType.Solid, color: "transparent" },
      textColor: css("--text-3"),
      fontFamily: "IBM Plex Mono, ui-monospace, monospace",
    },
    grid: { vertLines: { color: css("--border") }, horzLines: { color: css("--border") } },
    rightPriceScale: { borderColor: css("--border") },
    timeScale: { borderColor: css("--border") },
  };
}

/** CMP-13: candles + SMA50/SMA200 + volume. The canvas is decorative; `summary` is the accessible text. */
export function PriceChart({ locale, bars, sma50, sma200, summary, height = 360 }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<{
    candles: ISeriesApi<"Candlestick">;
    volume: ISeriesApi<"Histogram">;
    sma50: ISeriesApi<"Line">;
    sma200: ISeriesApi<"Line">;
  } | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const instance = createChart(container.current, {
      ...themeOptions(),
      localization: localization(locale),
      autoSize: true,
      height,
    });
    const paint = () => ({
      up: css("--pos"),
      down: css("--neg"),
    });
    const colors = paint();
    series.current = {
      candles: instance.addSeries(CandlestickSeries, {
        upColor: colors.up,
        downColor: colors.down,
        wickUpColor: colors.up,
        wickDownColor: colors.down,
        borderVisible: false,
      }),
      volume: instance.addSeries(HistogramSeries, { priceScaleId: "volume", priceFormat: { type: "volume" } }),
      sma50: instance.addSeries(LineSeries, { color: css("--accent"), lineWidth: 2, priceLineVisible: false }),
      sma200: instance.addSeries(LineSeries, { color: css("--warn"), lineWidth: 2, priceLineVisible: false }),
    };
    instance.priceScale("volume").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    chart.current = instance;

    const onTheme = () =>
      requestAnimationFrame(() => {
        instance.applyOptions(themeOptions());
        const c = paint();
        series.current?.candles.applyOptions({ upColor: c.up, downColor: c.down, wickUpColor: c.up, wickDownColor: c.down });
        series.current?.sma50.applyOptions({ color: css("--accent") });
        series.current?.sma200.applyOptions({ color: css("--warn") });
      });
    window.addEventListener(THEME_EVENT, onTheme);
    return () => {
      window.removeEventListener(THEME_EVENT, onTheme);
      instance.remove();
      chart.current = null;
      series.current = null;
    };
  }, [height, locale]);

  useEffect(() => {
    const s = series.current;
    if (!s) return;
    const volumeColor = css("--surface-2") || "#ccc";
    s.candles.setData(bars.map((b) => ({ time: time(b.day), open: b.open, high: b.high, low: b.low, close: b.close })));
    s.volume.setData(bars.map((b) => ({ time: time(b.day), value: b.volume ?? 0, color: volumeColor })));
    const line = (values: (number | null)[]) =>
      bars.flatMap((b, i) => (values[i] == null ? [] : [{ time: time(b.day), value: values[i] as number }]));
    s.sma50.setData(line(sma50));
    s.sma200.setData(line(sma200));
    chart.current?.timeScale().fitContent();
  }, [bars, sma50, sma200]);

  return (
    <figure className="m-0">
      <div ref={container} aria-hidden style={{ height }} className="w-full" />
      <figcaption className="sr-only">{summary}</figcaption>
    </figure>
  );
}
