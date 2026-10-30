"use client";

import { useTranslations } from "next-intl";
import { Sparkline } from "@/components/overview/Sparkline";
import type { EntryOut } from "@/lib/api/types";
import { formatChange, formatMoney } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

export type StoredPriceTrend = {
  points: { close: string | number; market_date: string }[];
  source?: string | null;
  as_of?: string | null;
};

export function SignedChange({
  value,
  currency,
}: {
  value: number | null | undefined;
  currency?: string;
}) {
  const locale = useAppLocale();
  if (value == null || !Number.isFinite(value)) return <span>—</span>;
  return (
    <span className={value > 0 ? "text-pos" : value < 0 ? "text-neg" : "text-text-2"}>
      {currency
        ? `${value >= 0 ? "▲ +" : "▼ −"}${formatMoney(locale, Math.abs(value), currency)}`
        : formatChange(locale, value)}
    </span>
  );
}

export function PriceTrend({ trend }: { trend?: StoredPriceTrend | null }) {
  const t = useTranslations("table");
  const points =
    trend?.points.filter((point) => Number.isFinite(Number(point.close))).slice(-30) ?? [];
  if (points.length < 2)
    return <span className="text-[11px] text-text-3">{t("trendUnknown")}</span>;
  return (
    <div
      className="space-y-1 text-[10px] text-text-3"
      title={[trend?.source, trend?.as_of].filter(Boolean).join(" · ")}
    >
      <Sparkline values={points.map((point) => Number(point.close))} width={104} height={26} />
      <div>{t("trendPeriod")}</div>
      <div>{t("trendSamples", { count: points.length })}</div>
      <div>
        {points[0]!.market_date} – {points.at(-1)!.market_date}
      </div>
    </div>
  );
}

export function EntryZoneBadge({ entry }: { entry?: EntryOut }) {
  const t = useTranslations("table");
  const known =
    entry &&
    entry.zone_low != null &&
    entry.zone_high != null &&
    [entry.price, entry.zone_low, entry.zone_high].every(Number.isFinite) &&
    entry.zone_low <= entry.zone_high;
  const inZone = known && entry.price >= entry.zone_low! && entry.price <= entry.zone_high!;
  return (
    <span
      className={`inline-block rounded px-1 text-[11px] ${inZone ? "bg-pos-soft text-pos" : "text-text-3"}`}
      title={entry ? [entry.source, entry.as_of].join(" · ") : undefined}
    >
      {t(!known ? "zoneUnknown" : inZone ? "inZone" : "outsideZone")}
    </span>
  );
}
