"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type { PortfolioOut } from "@/lib/api/types";
import { useAppLocale } from "@/lib/use-app-locale";
import { formatMoney } from "@/lib/format";
import { DataDetails } from "@/components/common/DataDetails";
import { SignedChange } from "@/components/portfolio/MarketContext";

type Summary = Pick<
  PortfolioOut,
  "total_value" | "base_currency" | "as_of" | "daily_move" | "daily_native"
>;

export function PortfolioValueCard({ data, failed = false }: { data?: Summary; failed?: boolean }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const move = data?.daily_move;
  return (
    <section className="card space-y-1.5 p-4">
      <h2 className="label">{t("overview.portfolioValue")}</h2>
      <div className="flex items-start justify-between gap-2">
        <p className="num text-2xl">
          {data?.total_value != null
            ? formatMoney(locale, Number(data.total_value), data.base_currency)
            : "—"}
        </p>
        <DataDetails compact label={t("screenRefinement.dailyDetails")}>
          <p>{t("screenRefinement.dailyMethod")}</p>
          {move?.reason && t.has(`screenRefinement.dailyReasons.${move.reason}`) && (
            <p className="text-warn">{t(`screenRefinement.dailyReasons.${move.reason}`)}</p>
          )}
          <p>
            {t("table.source")}: {move?.sources?.join(", ") || t("table.missing")}
          </p>
          <p>
            {t("screenRefinement.dailyDates")}: {move?.previous_market_date ?? "—"} →{" "}
            {move?.market_date ?? "—"}
          </p>
          <p>
            {t("screenRefinement.holdingsDates")}: {move?.holdings_dates?.join(", ") || "—"}
          </p>
          {data?.daily_native?.map((native) => (
            <p key={native.currency}>
              {native.currency} · {native.previous_market_date ?? "—"} → {native.market_date ?? "—"}{" "}
              · {native.sources?.join(", ") || t("table.missing")}
              {native.reason && t.has(`screenRefinement.dailyReasons.${native.reason}`) && (
                <> · {t(`screenRefinement.dailyReasons.${native.reason}`)}</>
              )}
            </p>
          ))}
        </DataDetails>
      </div>
      {move?.amount != null ? (
        <div className="flex flex-wrap items-baseline gap-x-2 text-xs">
          <SignedChange value={Number(move.amount)} currency={data?.base_currency} />
          <SignedChange value={move.percent == null ? null : Number(move.percent)} />
          <span className="text-text-3">{t("screenRefinement.dailyEstimate")}</span>
        </div>
      ) : data?.daily_native?.length ? (
        <div className="space-y-1 text-xs">
          <p className="text-text-3">{t("screenRefinement.dailyNative")}</p>
          {data.daily_native.map((native) => (
            <p key={native.currency} className="flex flex-wrap items-baseline gap-x-2">
              <span>{native.currency}</span>
              {native.amount != null ? (
                <>
                  <SignedChange value={Number(native.amount)} currency={native.currency} />
                  <SignedChange value={native.percent == null ? null : Number(native.percent)} />
                </>
              ) : (
                <span className="text-warn">{t("screenRefinement.dailyMissing")}</span>
              )}
            </p>
          ))}
        </div>
      ) : (
        <p className="text-xs text-warn">{t("screenRefinement.dailyMissing")}</p>
      )}
      <footer className="flex flex-wrap items-center justify-between gap-x-3 text-xs text-text-3">
        {failed ? (
          <span>{t("table.loadFailed")}</span>
        ) : data?.as_of ? (
          <time dateTime={data.as_of}>
            {new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(
              new Date(data.as_of),
            )}
          </time>
        ) : (
          <span>{t("table.missing")}</span>
        )}
        <Link href="/portfolio" className="text-accent">
          {t("nav.portfolio")} →
        </Link>
      </footer>
    </section>
  );
}
