"use client";

import {
  BaselineSeries,
  CandlestickSeries,
  LineStyle,
  ColorType,
  HistogramSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { OhlcBar } from "@/lib/indicators";
import { THEME_EVENT } from "@/lib/theme";

export type EntryLevels = {
  zoneLow: number;
  zoneHigh: number;
  stop: number | null;
  ladder: number[];
  labels: { zone: string; stop: string };
};

type Props = {
  entry?: EntryLevels | null;
  locale: "sl" | "en";
  bars: OhlcBar[];
  sma50: (number | null)[];
  sma200: (number | null)[];
  summary: string;
  height?: number;
};

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const time = (day: string) => (Date.parse(`${day}T00:00:00Z`) / 1000) as UTCTimestamp;

/** Adds alpha to a #rrggbb token so the zone fill stays see-through; other formats pass through. */
const withAlpha = (color: string, alpha: string) => (/^#[0-9a-f]{6}$/i.test(color) ? `${color}${alpha}` : color);

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
export function PriceChart({ entry = null, locale, bars, sma50, sma200, summary, height = 360 }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<{
    candles: ISeriesApi<"Candlestick">;
    volume: ISeriesApi<"Histogram">;
    sma50: ISeriesApi<"Line">;
    sma200: ISeriesApi<"Line">;
    zone: ISeriesApi<"Baseline">;
  } | null>(null);
  const lines = useRef<IPriceLine[]>([]);

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
      zone: instance.addSeries(BaselineSeries, {
        baseValue: { type: "price", price: 0 },
        lineVisible: false,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      }),
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
      lines.current = [];
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

  // Entry overlay: zone fill + zone edges, stop and ladder as price lines. Re-run on theme change too.
  useEffect(() => {
    const s = series.current;
    if (!s) return;
    const draw = () => {
      for (const line of lines.current) s.candles.removePriceLine(line);
      lines.current = [];
      if (!entry) {
        s.zone.applyOptions({ autoscaleInfoProvider: () => null });
        s.zone.setData([]);
        return;
      }
      const pos = css("--pos");
      const neg = css("--neg");
      const muted = css("--text-3");
      s.zone.applyOptions({
        baseValue: { type: "price", price: entry.zoneLow },
        topLineColor: "transparent",
        topFillColor1: withAlpha(pos, "38"),
        topFillColor2: withAlpha(pos, "38"),
        bottomFillColor1: "transparent",
        bottomFillColor2: "transparent",
        bottomLineColor: "transparent",
      });
      // Keep every level inside the visible price range, even when the zone is far below the price.
      const levels = [entry.zoneLow, entry.zoneHigh, ...entry.ladder, ...(entry.stop != null ? [entry.stop] : [])];
      const range = { priceRange: { minValue: Math.min(...levels), maxValue: Math.max(...levels) } };
      s.zone.applyOptions({ autoscaleInfoProvider: () => range });
      s.zone.setData(bars.map((b) => ({ time: time(b.day), value: entry.zoneHigh })));
      const add = (price: number, color: string, lineStyle: LineStyle, title: string, lineWidth: 1 | 2 = 1) =>
        lines.current.push(
          s.candles.createPriceLine({ price, color, lineWidth, lineStyle, axisLabelVisible: true, title }),
        );
      add(entry.zoneHigh, pos, LineStyle.Dashed, entry.labels.zone);
      add(entry.zoneLow, pos, LineStyle.Dashed, "");
      entry.ladder.forEach((price, i) => add(price, muted, LineStyle.Dotted, `L${i + 1}`));
      if (entry.stop != null) add(entry.stop, neg, LineStyle.Dashed, entry.labels.stop, 2);
    };
    draw();
    const onTheme = () => requestAnimationFrame(draw);
    window.addEventListener(THEME_EVENT, onTheme);
    return () => window.removeEventListener(THEME_EVENT, onTheme);
  }, [entry, bars, height, locale]);

  return (
    <figure className="m-0">
      <div ref={container} aria-hidden style={{ height }} className="w-full" />
      <figcaption className="sr-only">{summary}</figcaption>
    </figure>
  );
}
