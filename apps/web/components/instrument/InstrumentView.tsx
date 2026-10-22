"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import Link from "next/link";
import { AnalysisRunList } from "@/components/analysis/AnalysisRunList";
import { LaunchAnalysisButton } from "@/components/analysis/LaunchAnalysisButton";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { ProvenanceTag } from "@/components/common/ProvenanceTag";
import { CauseBadge } from "@/components/entries/CauseBadge";
import { EntryZoneBar } from "@/components/entries/EntryZoneBar";
import { PriceChart, type EntryLevels } from "@/components/instrument/PriceChart";
import { WatchButton } from "@/components/watchlist/WatchButton";
import { ApiError } from "@/lib/api/client";
import { useBars, useEntry, useInstrument } from "@/lib/api/hooks";
import type { BarsRange } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { computeIndicators } from "@/lib/indicators";
import { spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";
import { openProposalComposer } from "@/stores/proposals";

const STATE_STYLE: Record<string, string> = {
  in_zone: "bg-pos-soft text-pos",
  below: "bg-warn-soft text-warn",
  near: "bg-accent-soft text-accent",
  far: "bg-surface-2 text-text-3",
};

const RANGES: BarsRange[] = ["1m", "3m", "1y", "2y", "5y"];
// SMA200 needs history before the visible window: always load at least two years.
const LOAD: Record<BarsRange, BarsRange> = { "1m": "2y", "3m": "2y", "1y": "2y", "2y": "2y", "5y": "5y" };
const VISIBLE_DAYS: Record<BarsRange, number> = { "1m": 22, "3m": 64, "1y": 252, "2y": 504, "5y": 1260 };

/** SCR-05 Instrument (M1): price, chart with indicators, key data, watchlist and analysis actions. */
export function InstrumentView({ symbol }: { symbol: string }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const [range, setRange] = useState<BarsRange>("1y");
  const instrument = useInstrument(symbol);
  const bars = useBars(symbol, LOAD[range]);
  const entryQuery = useEntry(symbol);
  const entry = entryQuery.data ?? null;
  const [showZone, setShowZone] = useState(true);

  const all = useMemo(
    () => (bars.data?.bars ?? []).map((b) => ({ ...b, day: b.day })),
    [bars.data],
  );
  const indicators = useMemo(() => computeIndicators(all), [all]);
  const entryLevels = useMemo<EntryLevels | null>(() => {
    if (!entry || entry.zone_low == null || entry.zone_high == null) return null;
    return {
      zoneLow: Number(entry.zone_low),
      zoneHigh: Number(entry.zone_high),
      stop: entry.stop == null ? null : Number(entry.stop),
      ladder: (entry.ladder ?? []).map((l) => Number(l.price)),
      labels: {
        zone: t("instrumentPage.entryToggle"),
        stop: t("instrumentPage.entryStop"),
      },
    };
  }, [entry, t]);

  const from = Math.max(0, all.length - VISIBLE_DAYS[range]);
  const visible = all.slice(from);

  if (instrument.error instanceof ApiError && instrument.error.status === 404) {
    return (
      <section className="card mx-auto mt-10 flex max-w-xl flex-col gap-3 p-8">
        <h1 className="num text-2xl font-medium">{symbol}</h1>
        <p className="text-text-2">{t("instrumentPage.notFound", { symbol })}</p>
        <p className="text-text-3">{t("instrumentPage.notFoundHint")}</p>
        <div className="flex gap-2">
          <WatchButton symbol={symbol} />
          <button type="button" onClick={() => openProposalComposer({ symbols: [symbol] })} className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent">
            {t("action.analyze")}
          </button>
        </div>
      </section>
    );
  }

  const detail = instrument.data;
  const currency = detail?.currency ?? "USD";
  const last = visible.at(-1);
  const firstVisible = visible[0];
  const rangeChange = last && firstVisible ? (last.close / firstVisible.close - 1) * 100 : null;
  const pct = (v: number | null) => (v === null ? "—" : formatChange(locale, v));

  const stats = [
    { label: t("instrumentPage.high52"), value: indicators.high52 === null ? "—" : formatMoney(locale, indicators.high52, currency) },
    { label: t("instrumentPage.low52"), value: indicators.low52 === null ? "—" : formatMoney(locale, indicators.low52, currency) },
    { label: t("instrumentPage.drawdown"), value: pct(indicators.drawdownPct), tone: (indicators.drawdownPct ?? 0) < 0 ? "text-neg" : "" },
    { label: t("instrumentPage.sma200"), value: pct(indicators.distanceToSma200Pct), tone: (indicators.distanceToSma200Pct ?? 0) >= 0 ? "text-pos" : "text-neg" },
    { label: t("instrumentPage.rsi"), value: indicators.rsi14 === null ? "—" : formatNumber(locale, indicators.rsi14, 0) },
    { label: t("instrumentPage.atr"), value: indicators.atr14 === null ? "—" : formatMoney(locale, indicators.atr14, currency) },
  ];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <motion.h1 layoutId={`symbol-${symbol}`} className="num text-[28px] leading-[34px] font-medium">
              {symbol}
            </motion.h1>
            <span className="text-text-2">{detail?.name}</span>
            {detail && (
              <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 font-medium text-text-2">
                {detail.kind === "etf" ? "ETF" : t("instrument.stock")}
              </span>
            )}
            {detail?.ucits && (
              <span className="rounded-full bg-accent-soft px-2 text-xs leading-5 font-medium text-accent">UCITS</span>
            )}
          </div>
          <div className="mt-2 flex flex-wrap items-baseline gap-3">
            {detail?.last_close != null ? (
              <AnimatedNumber value={detail.last_close} format={(v) => formatMoney(locale, v, currency)} className="text-2xl leading-8 font-medium" />
            ) : (
              <span className="h-8 w-28 animate-pulse rounded-md bg-surface-2" />
            )}
            {detail?.change_pct != null && (
              <span className={cn("num", detail.change_pct >= 0 ? "text-pos" : "text-neg")}>{formatChange(locale, detail.change_pct)}</span>
            )}
            <ProvenanceTag provenance={bars.data?.provenance ?? detail?.provenance} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => openProposalComposer({ symbols: [symbol] })} className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90">
            {t("action.analyze")}
          </button>
          <LaunchAnalysisButton symbol={symbol} />
          <WatchButton symbol={symbol} />
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="card flex min-w-0 flex-col gap-3 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div role="group" aria-label={t("instrumentPage.range")} className="flex gap-0.5 rounded-md bg-surface-2 p-0.5">
              {RANGES.map((r) => (
                <button
                  key={r}
                  type="button"
                  aria-pressed={range === r}
                  onClick={() => setRange(r)}
                  className={cn("relative h-9 min-w-11 rounded-[5px] px-2 text-[13px] font-medium text-text-2", range === r && "text-text")}
                >
                  {range === r && (
                    <motion.span layoutId="range-pill" transition={spring.snappy} className="absolute inset-0 rounded-[5px] bg-surface shadow-[0_0_0_1px_var(--border)]" />
                  )}
                  <span className="relative">{t(`instrumentPage.ranges.${r}`)}</span>
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-text-2">
              <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-3.5 bg-accent" />SMA50</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-3.5 bg-warn" />SMA200</span>
              {entryLevels && (
                <button
                  type="button"
                  aria-pressed={showZone}
                  onClick={() => setShowZone((v) => !v)}
                  className={cn(
                    "inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium",
                    showZone ? "bg-pos-soft text-pos" : "bg-surface-2 text-text-2",
                  )}
                >
                  <span className={cn("h-0.5 w-3 border-t-2 border-dashed", showZone ? "border-pos" : "border-text-3")} />
                  {t("instrumentPage.entryToggle")}
                </button>
              )}
              {rangeChange !== null && <span className={cn("num", rangeChange >= 0 ? "text-pos" : "text-neg")}>{formatChange(locale, rangeChange)}</span>}
            </div>
          </div>
          {bars.isLoading ? (
            <div className="h-[360px] animate-pulse rounded-md bg-surface-2" />
          ) : visible.length ? (
            <PriceChart
              entry={showZone ? entryLevels : null}
              locale={locale}
              bars={visible}
              sma50={indicators.sma50.slice(from)}
              sma200={indicators.sma200.slice(from)}
              summary={t("instrumentPage.chartSummary", {
                symbol,
                range: t(`instrumentPage.ranges.${range}`),
                close: last ? formatMoney(locale, last.close, currency) : "—",
                change: pct(rangeChange),
              })}
            />
          ) : (
            <p className="py-16 text-center text-text-3">{t("instrumentPage.noBars")}</p>
          )}
        </section>

        <aside className="flex flex-col gap-6">
          {entry && entryLevels && (
            <section className="card flex flex-col gap-3 p-4" aria-label={t("instrumentPage.entryZone")}>
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-base font-semibold">{t("instrumentPage.entryZone")}</h2>
                {entry.state && (
                  <span className={cn("rounded-full px-2 text-xs leading-5 font-medium", STATE_STYLE[entry.state] ?? STATE_STYLE.far)}>
                    {t(`entriesPage.state.${entry.state}`, {
                      atr: formatNumber(locale, Math.abs(Number(entry.distance_atr ?? 0)), 1),
                    })}
                  </span>
                )}
              </div>
              <EntryZoneBar
                price={Number(entry.price)}
                zoneLow={entryLevels.zoneLow}
                zoneHigh={entryLevels.zoneHigh}
                stop={entryLevels.stop}
              />
              {entry.rules.length > 0 && (
                <div className="flex items-center gap-2 text-[13px] text-text-2">
                  <span>{t("instrumentPage.entryCauseLabel")}</span>
                  <CauseBadge cause={entry.cause} />
                </div>
              )}
              <Link href={`/entries?symbol=${encodeURIComponent(symbol)}`} className="text-[13px] font-medium text-accent hover:underline">
                {t("instrumentPage.entryOpen")} →
              </Link>
            </section>
          )}
          <section className="card overflow-hidden" aria-label={t("analysisPage.latest.title")}>
            <div className="flex items-center justify-between gap-2 px-4 pt-4 pb-2">
              <h2 className="text-base font-semibold">{t("analysisPage.latest.title")}</h2>
              <Link href="/analysis" className="text-[13px] font-medium text-accent hover:underline">
                {t("analysisPage.latest.all")} →
              </Link>
            </div>
            <AnalysisRunList symbol={symbol} limit={3} compact emptyKey="latest.empty" />
          </section>
          <section className="card p-4">
            <h2 className="mb-3 text-base font-semibold">{t("instrumentPage.stats")}</h2>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
              {stats.map((s) => (
                <div key={s.label}>
                  <dt className="label">{s.label}</dt>
                  <dd className={cn("num text-[15px]", s.tone)}>{s.value}</dd>
                </div>
              ))}
            </dl>
          </section>
          {detail && (
            <section className="card p-4">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-[13px]">
                <div><dt className="label">{t("instrumentPage.exchange")}</dt><dd className="num">{detail.exchange ?? "—"}</dd></div>
                <div><dt className="label">{t("instrumentPage.currency")}</dt><dd className="num">{detail.currency ?? "—"}</dd></div>
                <div className="col-span-2"><dt className="label">{t("instrumentPage.isin")}</dt><dd className="num">{detail.isin ?? "—"}</dd></div>
              </dl>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}
