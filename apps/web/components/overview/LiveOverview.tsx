"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations, useFormatter } from "next-intl";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { usePortfolio } from "@/lib/api/hooks";
import { useAppLocale } from "@/lib/use-app-locale";
import { formatMoney } from "@/lib/format";
import { EntityLink } from "@/components/common/EntityLink";
import { TranslatedText } from "@/components/common/TranslatedText";
import { InZoneCard } from "./InZoneCard";
import { PortfolioTreemapCard } from "./PortfolioTreemapCard";
import { PulseTimeline } from "./PulseTimeline";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";

export function LiveOverview() {
  const t = useTranslations();
  const locale = useAppLocale();
  const format = useFormatter();
  const portfolio = usePortfolio();
  const overview = useQuery({
    queryKey: ["overview"],
    queryFn: () => api.get<components["schemas"]["OverviewOut"]>("/overview"),
    refetchInterval: 60_000,
  });
  const data = overview.data;
  return (
    <div className="space-y-5">
      {data && (
        <p className="text-xs text-text-3">
          {t("table.liveOverview")} · {data.source} ·{" "}
          {format.dateTime(new Date(data.as_of), { dateStyle: "medium", timeStyle: "short" })}
        </p>
      )}
      <section aria-label={t("overviewFeedback.market")} className="space-y-2">
        <h2 className="label">{t("overviewFeedback.market")}</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {(["spy", "vix", "us10y", "dxy"] as const).map((key) => {
            const indicator = data?.market_strip.find((row) => row.key === key);
            return (
              <div key={key} className="card space-y-1 px-4 py-3">
                <h3 className="label">{t(`overviewFeedback.${key}`)}</h3>
                <p className="num text-xl">
                  {indicator?.value != null
                    ? `${formatNumber(locale, Number(indicator.value), 2)}${key === "spy" || key === "us10y" ? " %" : ""}`
                    : "—"}
                </p>
                <p className="text-xs text-text-3">
                  {indicator?.value != null
                    ? `${indicator.source} · ${indicator.as_of}`
                    : t("overviewFeedback.macroMissing")}
                </p>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-text-3">{t("overviewFeedback.macroHint")}</p>
      </section>
      <div className="grid gap-4 md:grid-cols-3">
        <section className="card space-y-2 p-5">
          <h2 className="label">{t("overview.portfolioValue")}</h2>
          <p className="num text-2xl">
            {portfolio.data?.total_value != null
              ? formatMoney(
                  locale,
                  Number(portfolio.data.total_value),
                  portfolio.data.base_currency,
                )
              : "—"}
          </p>
          <p className="text-xs text-text-3">
            {portfolio.error
              ? t("table.loadFailed")
              : (portfolio.data?.as_of ?? t("table.missing"))}
          </p>
          <Link href="/portfolio" className="text-sm text-accent">
            {t("nav.portfolio")} →
          </Link>
        </section>
        {(["new", "watching"] as const).map((status) => (
          <Link key={status} href={`/signals?status=${status}`} className="card space-y-2 p-5">
            <h2 className="label">{t(`signal.status.${status}`)}</h2>
            <p className="num text-2xl">{data ? (data.signal_counts[status] ?? 0) : "—"}</p>
            <p className="text-xs text-text-3">{t("table.allSignals")} →</p>
          </Link>
        ))}
      </div>
      {overview.isLoading && <div className="card h-32 animate-pulse" aria-busy="true" />}
      {overview.error && (
        <div role="alert" className="card p-4 text-warn">
          {t("table.loadFailed")}{" "}
          <button type="button" onClick={() => void overview.refetch()}>
            {t("table.retry")}
          </button>
        </div>
      )}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="min-w-0 space-y-5">
          <PortfolioTreemapCard />
          <InZoneCard />
          <section className="card space-y-3 p-5">
            <h2 className="text-base font-semibold">{t("overview.pulse")}</h2>
            <p className="text-xs text-text-3">{t("overviewFeedback.pulseHint")}</p>
            <p className="text-xs text-text-2">{t("overviewFeedback.pulseLegend")}</p>
            {data?.timeline7d.events.length ? (
              <PulseTimeline
                events={data.timeline7d.events.flatMap((event) =>
                  (event.symbols.length ? event.symbols : [t("overviewFeedback.noSymbol")]).map(
                    (symbol) => ({
                      id: String(event.id),
                      symbol,
                      hoursAgo: Math.max(
                        0,
                        Math.min(
                          168,
                          (Date.parse(data.as_of) - Date.parse(event.first_seen_at)) / 3_600_000,
                        ),
                      ),
                      score: event.score == null ? null : Number(event.score),
                      type: event.is_rumor ? "rumor" : (event.event_type ?? "other"),
                      title: event.title,
                    }),
                  ),
                )}
              />
            ) : (
              <p className="text-sm text-text-3">
                {t(
                  overview.error
                    ? "table.loadFailed"
                    : overview.isLoading
                      ? "state.loading"
                      : "table.empty",
                )}
              </p>
            )}
            {data && (
              <p className="text-xs text-text-3">
                {t("overviewFeedback.pulseScope", {
                  shown: data.timeline7d.events.length,
                  total: data.timeline7d.total,
                })}{" "}
                · {data.source}
              </p>
            )}
          </section>
        </div>
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">{t("table.allSignals")}</h2>
          <p className="text-xs text-text-3">{t("overviewFeedback.active")}</p>
          {data?.signals.map((signal) => (
            <article key={signal.id} className="card space-y-2 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <EntityLink entity={{ kind: "signal", id: signal.id }}>{signal.symbol}</EntityLink>
                <span className="text-xs text-text-3">
                  {t(`signal.kind.${signal.kind}`)} · {t(`signal.status.${signal.status}`)}
                </span>
                {signal.is_rumor && (
                  <span className="rounded bg-rumor-soft px-1 text-xs text-rumor">
                    {t("radar.rumor")}
                  </span>
                )}
              </div>
              <div
                className="flex items-center gap-2 text-xs"
                title={t("overviewFeedback.strengthHint")}
              >
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5",
                    signal.is_rumor
                      ? "bg-rumor-soft text-rumor"
                      : signal.direction === "down"
                        ? "bg-neg-soft text-neg"
                        : signal.direction === "up"
                          ? "bg-pos-soft text-pos"
                          : "bg-accent-soft text-accent",
                  )}
                >
                  {t(`signal.kind.${signal.kind}`)}
                </span>
                <span className="ml-auto text-text-3">{t("signal.strength")}</span>
                <meter
                  min={0}
                  max={1}
                  value={Number(signal.strength)}
                  aria-label={`${signal.symbol} ${t("signal.strength")}`}
                  className="h-2 w-20"
                />
                <span className="num">{formatNumber(locale, Number(signal.strength), 2)}</span>
              </div>
              <p className="line-clamp-3 text-sm text-text-2">
                <TranslatedText
                  original={signal.rationale}
                  translations={signal.rationale_translations}
                />
              </p>
              <p className="text-xs text-text-3">
                {t(`signal.source.${signal.source}`)} ·{" "}
                {format.dateTime(new Date(signal.created_at), { dateStyle: "short" })}
              </p>
            </article>
          ))}
          {data && !data.signals.length && (
            <p className="card p-4 text-text-3">{t("table.empty")}</p>
          )}
          {data && (
            <section className="card space-y-3 p-4">
              <h2 className="font-semibold">{t("overviewFeedback.funnel")}</h2>
              <p className="text-xs text-text-3">{t("overviewFeedback.funnelHint")}</p>
              <ol className="space-y-3">
                {(["news", "events", "triaged", "signalled"] as const).map((stage, index) => {
                  const colors = ["bg-surface-2", "bg-accent", "bg-warn", "bg-pos"];
                  const value = data.funnel30d[stage];
                  return (
                    <li key={stage} className="space-y-1 text-xs">
                      <div className="flex justify-between gap-2">
                        <span>{t(`overviewFeedback.${stage}`)}</span>
                        <strong className="num">{formatNumber(locale, value)}</strong>
                      </div>
                      <div className="h-2 rounded-full bg-surface-2">
                        <div
                          className={cn("h-2 rounded-full", colors[index])}
                          style={{
                            width: `${data.funnel30d.news ? (value / data.funnel30d.news) * 100 : 0}%`,
                          }}
                        />
                      </div>
                    </li>
                  );
                })}
              </ol>
              <p className="text-xs text-text-3">
                {format.dateTime(new Date(data.funnel30d.since), { dateStyle: "short" })} –{" "}
                {format.dateTime(new Date(data.as_of), { dateStyle: "short" })} · {data.source}
              </p>
            </section>
          )}
        </section>
      </div>
      {data && (
        <section className="card flex flex-wrap gap-6 p-4 text-sm text-text-3">
          <span>{t("overviewFeedback.lifetime")}</span>
          <span>
            {t("nav.radar")}: <strong className="num text-text">{data.event_count}</strong>
          </span>
          <span>
            {t("table.source")}: <strong className="num text-text">{data.news_count}</strong> ·{" "}
            {data.source}
          </span>
        </section>
      )}
    </div>
  );
}
