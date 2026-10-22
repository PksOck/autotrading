"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";
import { spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";

/** CMP-07: price against the entry zone and stop on one linear scale. */
export function EntryZoneBar({
  price,
  zoneLow,
  zoneHigh,
  stop,
  compact = false,
  className,
}: {
  price: number;
  zoneLow: number | null;
  zoneHigh: number | null;
  stop: number | null;
  compact?: boolean;
  className?: string;
}) {
  const t = useTranslations("signal");
  const locale = useAppLocale();
  if (zoneLow == null || zoneHigh == null) return <span className="text-xs text-text-3">—</span>;
  const lo = Math.min(stop ?? zoneLow, price, zoneLow);
  const hi = Math.max(price, zoneHigh);
  const pad = (hi - lo) * 0.08 || 1;
  const min = lo - pad;
  const span = hi + pad - min;
  const x = (v: number) => `${((v - min) / span) * 100}%`;
  const inZone = price >= zoneLow && price <= zoneHigh;
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div
        className={cn("relative w-full rounded-full bg-surface-2", compact ? "h-2" : "h-3")}
        role="img"
        aria-label={`${t("entryZone")} ${formatNumber(locale, zoneLow, 2)}–${formatNumber(locale, zoneHigh, 2)}`}
      >
        <span
          className="absolute inset-y-0 rounded-full bg-pos-soft ring-1 ring-pos"
          style={{ left: x(zoneLow), width: `calc(${x(zoneHigh)} - ${x(zoneLow)})` }}
        />
        {stop != null && (
          <span
            className="absolute -inset-y-1 w-0.5 rounded bg-neg"
            style={{ left: x(stop) }}
            title={`${t("stop")} ${formatNumber(locale, stop, 2)}`}
          />
        )}
        <motion.span
          className={cn(
            "absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface",
            compact ? "size-3" : "size-4",
            inZone ? "bg-pos" : "bg-text",
          )}
          initial={false}
          animate={{ left: x(price) }}
          transition={spring.soft}
        />
      </div>
      {!compact && (
        <div className="num flex justify-between text-[11px] text-text-3">
          <span>{stop != null ? `${t("stop")} ${formatNumber(locale, stop, 2)}` : ""}</span>
          <span>
            {formatNumber(locale, zoneLow, 2)}–{formatNumber(locale, zoneHigh, 2)}
          </span>
        </div>
      )}
    </div>
  );
}
