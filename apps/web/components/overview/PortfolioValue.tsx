"use client";

import { useTranslations } from "next-intl";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { usePortfolio } from "@/lib/api/hooks";
import { formatChange, formatMoney } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

/** Live total from /portfolio; the sample value is shown (and labelled) until IBKR data exists. */
export function PortfolioValue({ sampleValue, sampleChange }: { sampleValue: number; sampleChange: number }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const { data } = usePortfolio();
  const live = data?.total_value != null ? data : null;
  const value = live ? Number(live.total_value) : sampleValue;
  const currency = live?.base_currency ?? "USD";

  return (
    <div className="card flex flex-col gap-1 px-5 py-4">
      <span className="label flex items-center gap-2">
        {t("overview.portfolioValue")}
        {(!live || live.source === "demo") && (
          <span className="rounded-full bg-warn-soft px-1.5 leading-5 text-warn">{live ? t("provenance.demo") : t("header.sample")}</span>
        )}
      </span>
      <AnimatedNumber value={value} format={(v) => formatMoney(locale, v, currency, 0)} className="text-2xl leading-8 font-medium" />
      {!live && (
        <span className={`num text-[13px] ${sampleChange >= 0 ? "text-pos" : "text-neg"}`}>
          {formatChange(locale, sampleChange)} <span className="text-text-3">{t("overview.today")}</span>
        </span>
      )}
    </div>
  );
}
