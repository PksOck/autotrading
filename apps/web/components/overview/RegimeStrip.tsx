"use client";

import { useTranslations } from "next-intl";
import { Sparkline } from "@/components/overview/Sparkline";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";
import { sparkSeries, type RegimeIndicator } from "@/lib/sample-data";
import { useAppLocale } from "@/lib/use-app-locale";

const TONE = {
  risk_on: "bg-pos-soft text-pos",
  neutral: "bg-surface-2 text-text-2",
  risk_off: "bg-neg-soft text-neg",
} as const;

/** CMP-28 / OV-04: four market regime indicators. */
export function RegimeStrip({ indicators }: { indicators: RegimeIndicator[] }) {
  const t = useTranslations("regime");
  const locale = useAppLocale();
  const unit = (i: RegimeIndicator) => (i.unit === "pct" ? (locale === "sl" ? " %" : "%") : "");

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {indicators.map((indicator) => (
        <div key={indicator.key} className="card flex items-center justify-between gap-3 px-4 py-3">
          <div className="min-w-0">
            <div className="label">{indicator.label}</div>
            <div className="num text-base font-medium">
              {indicator.key === "spy" && indicator.value > 0 ? "+" : ""}
              {formatNumber(locale, indicator.value, indicator.unit === "idx" ? 1 : 2)}
              {unit(indicator)}
            </div>
            <span
              className={cn(
                "mt-1 inline-block rounded-full px-2 text-xs leading-5 font-medium",
                TONE[indicator.regime],
              )}
            >
              {t(indicator.regime)}
            </span>
          </div>
          <Sparkline
            values={sparkSeries(indicator.key, indicator.value)}
            width={72}
            height={28}
            color="var(--text-3)"
          />
        </div>
      ))}
    </div>
  );
}
