"use client";

import { motion, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { CauseBadge } from "@/components/entries/CauseBadge";
import { EntryMap } from "@/components/entries/EntryMap";
import { EntryZoneBar } from "@/components/entries/EntryZoneBar";
import { useEntries } from "@/lib/api/hooks";
import { formatNumber } from "@/lib/format";
import { spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";

const n = (v: number | string | null | undefined) => (v == null ? null : Number(v));

/** BL-070: entry candidates in or below their zone, with the compact OV-05 map. */
export function InZoneCard() {
  const t = useTranslations("overview.inZone");
  const locale = useAppLocale();
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const { data, isPending } = useEntries("all");
  const hits = (data ?? [])
    .filter((e) => e.state === "in_zone" || e.state === "below")
    .sort((a, b) => b.rules.length - a.rules.length);
  const go = (symbol: string) => router.push(`/entries?symbol=${encodeURIComponent(symbol)}`);

  return (
    <section className="card p-5" aria-label={t("title")}>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-base font-semibold">
          <Link href="/entries" className="hover:underline">
            {t("title")}
          </Link>
        </h2>
        <Link href="/entries" className="text-xs text-accent hover:underline">
          {t("all")}
        </Link>
      </div>
      {isPending ? (
        <div className="h-40 animate-pulse rounded-lg bg-surface-2" aria-hidden />
      ) : hits.length === 0 ? (
        <div className="flex flex-col items-start gap-2 py-4">
          <p className="text-sm text-text-2">{t("empty")}</p>
          <Link href="/entries" className="text-sm font-medium text-accent hover:underline">
            {t("emptyAction")}
          </Link>
        </div>
      ) : (
        <>
          <EntryMap compact entries={hits} onSelect={go} />
          <ul className="mt-3 flex flex-col divide-y divide-border">
            {hits.slice(0, 4).map((e, i) => (
              <motion.li
                key={e.symbol}
                initial={reduceMotion ? false : { opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...spring.soft, delay: reduceMotion ? 0 : i * 0.03 }}
              >
                <Link
                  href={`/entries?symbol=${encodeURIComponent(e.symbol)}`}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded py-2 hover:bg-surface-2"
                >
                  <span className="num w-14 font-medium">{e.symbol}</span>
                  <CauseBadge cause={e.cause} />
                  <span className="min-w-20 flex-1">
                    <EntryZoneBar
                      compact
                      price={Number(e.price)}
                      zoneLow={n(e.zone_low)}
                      zoneHigh={n(e.zone_high)}
                      stop={n(e.stop)}
                    />
                  </span>
                  <span className="num w-16 text-right text-xs whitespace-nowrap text-text-3">
                    {e.distance_atr == null ? "—" : `${formatNumber(locale, Number(e.distance_atr), 1)} ATR`}
                  </span>
                </Link>
              </motion.li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
