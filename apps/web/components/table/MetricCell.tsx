"use client";
import { useFormatter, useTranslations } from "next-intl";
import { useAppLocale } from "@/lib/use-app-locale";
import { formatNumber } from "@/lib/format";
import type { components } from "@/lib/api/schema";
type Metric = components["schemas"]["MetricValue"];

export function MetricCell({ metric }: { metric?: Metric }) {
  const t = useTranslations("table");
  const locale = useAppLocale();
  if (!metric) return <span title={t("missing")}>—</span>;
  const meta = metric.meta;
  const hint = [
    meta?.source,
    meta?.basis,
    meta?.source_field,
    meta?.market_date ?? meta?.fetched_at,
    meta?.reason_code
      ? t.has(`reason.${meta.reason_code}`)
        ? t(`reason.${meta.reason_code}`)
        : t("missing")
      : null,
  ]
    .filter(Boolean)
    .join(" · ");
  if (metric.value === null || metric.value === undefined)
    return (
      <span tabIndex={0} title={hint || t("missing")} className="text-text-3">
        —
      </span>
    );
  const numeric = Number(metric.value);
  const display =
    metric.unit === "text" || !Number.isFinite(numeric)
      ? metric.value
      : metric.unit === "fraction"
        ? new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 2 }).format(
            numeric,
          )
        : `${formatNumber(locale, numeric, 2)}${metric.unit === "percent" ? " %" : ""}`;
  return (
    <span tabIndex={0} title={hint} className={meta?.stale ? "text-warn" : ""}>
      {display}
      {meta?.availability === "partial" ? " *" : ""}
    </span>
  );
}

export function DataQualityBadges({
  identity,
  price,
  metrics,
}: {
  identity?: string;
  price?: components["schemas"]["DataMeta"];
  metrics?: Record<string, Metric>;
}) {
  const t = useTranslations("table");
  const format = useFormatter();
  const stamp = (meta?: components["schemas"]["DataMeta"]) => {
    const fetched = meta?.fetched_at ?? meta?.as_of;
    return (
      <span className="block">
        {meta?.market_date && (
          <span className="block">
            {t("qualityPeriod")}: {meta.market_date}
          </span>
        )}
        {fetched ? (
          <span>
            {t("qualityFetched")}:{" "}
            <time dateTime={fetched}>
              {format.dateTime(new Date(fetched), { dateStyle: "medium", timeStyle: "short" })}
            </time>
          </span>
        ) : (
          <span>
            {t("qualityFetched")}: {t("missing")}
          </span>
        )}
      </span>
    );
  };
  const staleMetrics = Object.entries(metrics ?? {}).filter(([, metric]) => metric.meta?.stale);
  const stale = price?.stale || staleMetrics.length > 0;
  const partial = Object.values(metrics ?? {}).some(
    (metric) => metric.meta?.availability === "partial",
  );
  return (
    <div className="flex flex-wrap gap-1 text-[11px] font-normal">
      {identity === "unresolved" && (
        <span className="rounded bg-warn-soft px-1 text-warn">{t("identityUnresolved")}</span>
      )}
      {stale && (
        <details className="max-w-full">
          <summary className="min-h-8 cursor-pointer content-center rounded bg-warn-soft px-1 text-warn">
            {t("stale")}
          </summary>
          <ul className="mt-1 space-y-1 break-words rounded border border-border bg-surface p-2 text-xs">
            {price?.stale && (
              <li>
                {t("close")} · {price.source ?? t("missing")} · {stamp(price)}
              </li>
            )}
            {staleMetrics.map(([key, metric]) => (
              <li key={key}>
                {t.has(`metric.${key}`) ? t(`metric.${key}`) : t("otherMetric")} ·{" "}
                {metric.meta?.source ?? t("missing")} · {stamp(metric.meta)}
              </li>
            ))}
          </ul>
        </details>
      )}
      {partial && <span className="rounded bg-warn-soft px-1 text-warn">{t("partial")}</span>}
    </div>
  );
}
