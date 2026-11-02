"use client";

import { useState } from "react";
import { useFormatter, useTranslations } from "next-intl";
import type { PortfolioOut } from "@/lib/api/types";
import { DataDetails } from "@/components/common/DataDetails";
import { SignedChange } from "./MarketContext";

type Summary = Pick<
  PortfolioOut,
  "base_currency" | "daily_move" | "daily_native" | "ytd_move" | "ytd_native"
>;

export function PortfolioChangeSummary({ data }: { data: Summary }) {
  const t = useTranslations("portfolioChange");
  const format = useFormatter();
  const details = useTranslations("screenRefinement");
  const [period, setPeriod] = useState("day");
  const move = period === "day" ? data.daily_move : data.ytd_move;
  const native = (period === "day" ? data.daily_native : data.ytd_native) ?? [];
  const rows = move?.amount != null ? [{ ...move, currency: data.base_currency }] : native;
  return (
    <section aria-label={t("title")} className="min-w-0 space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-xs text-text-2">
          {t("period")}{" "}
          <select
            aria-label={t("period")}
            className="min-h-8 rounded-md border border-border bg-surface px-2"
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
          >
            <option value="day">{t("day")}</option>
            <option value="ytd">{t("ytd")}</option>
          </select>
        </label>
        <span className="text-xs text-text-3">{t("title")}</span>
        <DataDetails compact label={t("help")}>
          <p>{t(period === "day" ? "dayMethod" : "ytdMethod")}</p>
          {period === "day" && <p>{details("dailyMethod")}</p>}
          {(move?.amount != null ? [{ ...move, currency: data.base_currency }] : native).map(
            (row) => (
              <p key={row.currency}>
                {row.currency} · {row.previous_market_date ?? "—"} → {row.market_date ?? "—"} ·{" "}
                {row.sources?.join(", ") || "—"} · {row.holdings_dates?.join(", ") || "—"}
                {!!row.captured_at?.length && (
                  <span className="block">
                    {t("captured")}:{" "}
                    {row.captured_at
                      .map((value) =>
                        format.dateTime(new Date(value), {
                          dateStyle: "medium",
                          timeStyle: "short",
                        }),
                      )
                      .join(" · ")}
                  </span>
                )}
                {!!row.capture_ids?.length && (
                  <span className="block">
                    {t("captureId")}: {row.capture_ids.join(", ")}
                  </span>
                )}
              </p>
            ),
          )}
        </DataDetails>
      </div>
      {move?.amount == null && !!native.length && (
        <p className="text-[11px] text-text-3">{t("native")}</p>
      )}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        {rows.length ? (
          rows.map((row) => (
            <div key={row.currency} className="flex flex-wrap items-baseline gap-x-2">
              {move?.amount == null && <span className="text-xs text-text-3">{row.currency}</span>}
              {row.amount != null ? (
                <>
                  <SignedChange value={Number(row.amount)} currency={row.currency} />
                  <SignedChange value={row.percent == null ? null : Number(row.percent)} />
                </>
              ) : (
                <span className="text-xs text-warn">
                  {row.reason && details.has(`dailyReasons.${row.reason}`)
                    ? details(`dailyReasons.${row.reason}`)
                    : details("dailyMissing")}
                </span>
              )}
            </div>
          ))
        ) : (
          <p className="text-xs text-warn">{details("dailyMissing")}</p>
        )}
      </div>
    </section>
  );
}
