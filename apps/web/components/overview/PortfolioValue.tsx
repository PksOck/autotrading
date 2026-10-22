"use client";

import { useTranslations } from "next-intl";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { formatChange, formatMoney } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

export function PortfolioValue({ value, change }: { value: number; change: number }) {
  const t = useTranslations("overview");
  const locale = useAppLocale();
  return (
    <div className="card flex flex-col gap-1 px-5 py-4">
      <span className="label">{t("portfolioValue")}</span>
      <AnimatedNumber value={value} format={(v) => formatMoney(locale, v, "USD", 0)} className="text-2xl leading-8 font-medium" />
      <span className={`num text-[13px] ${change >= 0 ? "text-pos" : "text-neg"}`}>
        {formatChange(locale, change)} <span className="text-text-3">{t("today")}</span>
      </span>
    </div>
  );
}
