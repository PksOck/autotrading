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
        <InZoneCard />
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">{t("table.allSignals")}</h2>
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
        </section>
      </div>
      {data && (
        <section className="card flex flex-wrap gap-6 p-4 text-sm text-text-3">
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
