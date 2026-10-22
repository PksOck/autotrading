"use client";

import { useTranslations } from "next-intl";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { ThesisBadge } from "@/components/common/ThesisBadge";
import { Sparkline } from "@/components/overview/Sparkline";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { findInstrument, sparkSeries } from "@/lib/sample-data";
import { useAppLocale } from "@/lib/use-app-locale";

/** Shared body of CMP-20 HoverPreview and CMP-21 PeekPanel for an instrument. */
export function InstrumentPreview({ symbol, size = "sm" }: { symbol: string; size?: "sm" | "lg" }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const instrument = findInstrument(symbol);
  if (!instrument) return <p className="text-text-3">{t("peek.notFound")}</p>;

  const series = sparkSeries(instrument.symbol, instrument.price);
  const signalKind = instrument.lastSignal?.kind;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-3">
        <div className="min-w-0">
          <div className="num text-base font-medium">{instrument.symbol}</div>
          <div className="truncate text-[13px] text-text-3">{instrument.name}</div>
        </div>
        <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 font-medium text-text-2">
          {instrument.kind === "etf" ? "ETF" : t("instrument.stock")}
        </span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <div>
          <AnimatedNumber
            value={instrument.price}
            format={(v) => formatMoney(locale, v, instrument.currency)}
            className={size === "lg" ? "text-2xl leading-8 font-medium" : "text-lg font-medium"}
          />
          <div className={`num text-[13px] ${instrument.change >= 0 ? "text-pos" : "text-neg"}`}>
            {formatChange(locale, instrument.change)}
          </div>
        </div>
        <Sparkline values={series} width={size === "lg" ? 160 : 96} height={size === "lg" ? 40 : 28} />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
        <div>
          <dt className="label">{t("peek.weight")}</dt>
          <dd className="num">
            {instrument.weight > 0 ? `${formatNumber(locale, instrument.weight, 1)} %` : t("peek.notHeld")}
          </dd>
        </div>
        <div>
          <dt className="label">{t("peek.thesis")}</dt>
          <dd>
            <ThesisBadge state={instrument.thesis} />
          </dd>
        </div>
        {signalKind && (
          <div className="col-span-2">
            <dt className="label">{t("peek.lastSignal")}</dt>
            <dd>{t(`signal.kind.${signalKind === "rumor" ? "catalyst" : signalKind}`)}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
