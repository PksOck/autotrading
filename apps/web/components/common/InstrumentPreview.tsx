"use client";

import { useTranslations } from "next-intl";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { ProvenanceTag } from "@/components/common/ProvenanceTag";
import { Sparkline } from "@/components/overview/Sparkline";
import { ApiError } from "@/lib/api/client";
import { useBars, useInstrument, usePortfolio, useWatchlist } from "@/lib/api/hooks";
import { cn } from "@/lib/cn";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

/** Shared body of CMP-20 HoverPreview and CMP-21 PeekPanel for an instrument (live API data). */
export function InstrumentPreview({ symbol, size = "sm" }: { symbol: string; size?: "sm" | "lg" }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const instrument = useInstrument(symbol);
  const bars = useBars(symbol, "3m", size === "lg");
  const portfolio = usePortfolio();
  const watchlist = useWatchlist();

  if (instrument.error instanceof ApiError && instrument.error.status === 404) {
    return <p className="text-text-3">{t("instrumentPage.notFound", { symbol })}</p>;
  }
  const detail = instrument.data;
  if (!detail) {
    return (
      <div className="flex flex-col gap-3" aria-busy>
        <div className="h-5 w-20 animate-pulse rounded bg-surface-2" />
        <div className="h-8 w-32 animate-pulse rounded bg-surface-2" />
      </div>
    );
  }

  const closes = (bars.data?.bars ?? []).map((b) => Number(b.close));
  const position = portfolio.data?.positions.find((p) => p.symbol === detail.symbol);
  const watched = watchlist.data?.find((w) => w.symbol === detail.symbol);
  const currency = detail.currency;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <div className="num text-base font-medium">{detail.symbol}</div>
          <div className="truncate text-[13px] text-text-3">{detail.name}</div>
        </div>
        <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 font-medium text-text-2">
          {detail.kind === "etf" ? (detail.ucits ? "UCITS ETF" : "ETF") : detail.kind === "stock" ? t("instrument.stock") : t("table.identityUnresolved")}
        </span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <div>
          {detail.last_close != null ? (
            <AnimatedNumber
              value={Number(detail.last_close)}
              format={(v) => currency ? formatMoney(locale, v, currency) : `${formatNumber(locale, v, 2)} (${t("table.unknownCurrency")})`}
              className={size === "lg" ? "text-2xl leading-8 font-medium" : "text-lg font-medium"}
            />
          ) : (
            <span className="text-text-3">—</span>
          )}
          {detail.change_pct != null && (
            <div className={cn("num text-[13px]", Number(detail.change_pct) >= 0 ? "text-pos" : "text-neg")}>
              {formatChange(locale, Number(detail.change_pct))}
            </div>
          )}
        </div>
        {closes.length > 1 && <Sparkline values={closes} width={size === "lg" ? 160 : 96} height={size === "lg" ? 40 : 28} />}
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
        <div>
          <dt className="label">{t("peek.weight")}</dt>
          <dd className="num">
            {position?.weight_pct != null ? `${formatNumber(locale, Number(position.weight_pct), 1)} %` : t("peek.notHeld")}
          </dd>
        </div>
        <div>
          <dt className="label">{t("portfolio.tabWatchlist")}</dt>
          <dd>{watched ? t(`watchlist.tiers.${watched.tier}`) : "—"}</dd>
        </div>
      </dl>
      <ProvenanceTag provenance={detail.provenance} />
    </div>
  );
}
