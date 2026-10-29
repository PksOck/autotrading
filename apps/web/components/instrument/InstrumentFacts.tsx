"use client";

import { useLocale, useTranslations } from "next-intl";
import { ApiError } from "@/lib/api/client";
import { useEnrichIdentity, useIdentityFacts } from "@/lib/api/identity";

const STOCK_METRICS = [
  "pe",
  "forward_pe",
  "ev_ebit",
  "fcf_yield",
  "roe_pct",
  "gross_margin_pct",
  "net_margin_pct",
  "revenue_growth_pct",
  "debt_to_equity",
  "dividend_yield_pct",
  "payout_ratio_pct",
];
const ETF_METRICS = ["ter", "index_name", "distribution"];
const SAFE_ERRORS = new Set([
  "identity_unconfigured",
  "identity_not_found",
  "identity_conflict",
  "identity_ambiguous",
  "identity_symbol_mismatch",
  "identity_exchange_mismatch",
  "identity_provider_unavailable",
  "identity_invalid_profile",
]);

export function InstrumentFacts({ symbol }: { symbol: string }) {
  const t = useTranslations("identityFacts");
  const locale = useLocale();
  const query = useIdentityFacts(symbol);
  const enrich = useEnrichIdentity(symbol);
  const detail = query.data;
  const date = (value: string | null | undefined) =>
    value
      ? new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(
          new Date(value),
        )
      : t("unknown");
  if (query.isLoading)
    return (
      <section className="card p-5" aria-busy="true">
        {t("loading")}
      </section>
    );
  if (!detail)
    return (
      <section className="card p-5" role="alert">
        {t("loadError")}
      </section>
    );
  const metrics = detail.kind === "etf" ? ETF_METRICS : STOCK_METRICS;
  const errorCode =
    enrich.error instanceof ApiError && SAFE_ERRORS.has(enrich.error.detail)
      ? enrich.error.detail
      : "identity_provider_unavailable";

  return (
    <section className="card space-y-4 p-5" aria-label={t("title")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-medium">{t("title")}</h2>
          <p className="text-sm text-text-3">{t("identityHelp")}</p>
        </div>
        <button
          type="button"
          className="min-h-12 rounded-md border border-border px-4 text-sm disabled:opacity-50"
          disabled={enrich.isPending}
          onClick={() =>
            enrich.mutate({
              instrument_id: detail.instrument_id,
              expected_updated_at: detail.identity_updated_at,
            })
          }
        >
          {t(enrich.isPending ? "enriching" : "enrich")}
        </button>
      </div>
      {query.error && (
        <p role="alert" className="text-warn">
          {t("loadError")}
        </p>
      )}
      {enrich.error && (
        <p role="alert" className="text-warn">
          {t(`errors.${errorCode}`)}
        </p>
      )}
      {enrich.data && (
        <p role="status" className="text-text-2">
          {t(enrich.data.changed_fields.length ? "enriched" : "unchanged")}
        </p>
      )}
      <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
        {(
          [
            ["name", detail.name],
            ["kind", detail.kind === "unknown" ? null : t(`kinds.${detail.kind}`)],
            ["exchange", detail.exchange],
            ["currency", detail.currency],
          ] as const
        ).map(([key, value]) => (
          <div key={key}>
            <dt className="text-text-3">{t(key)}</dt>
            <dd>{value || t("unknown")}</dd>
          </div>
        ))}
      </dl>
      <p className="text-xs text-text-3">
        {t("identitySource", {
          source: detail.identity_source,
          time: date(detail.identity_updated_at),
        })}
      </p>
      {detail.identity_status !== "resolved" && (
        <p className="rounded-md bg-warn-soft p-3 text-sm text-warn">{t("unresolved")}</p>
      )}
      <p className="text-xs text-text-3">{t("enrichmentLimit")}</p>
      <h3 className="font-medium">{t(detail.kind === "etf" ? "fundFacts" : "companyFacts")}</h3>
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((key) => {
          const metric = detail.metrics?.[key];
          const meta = metric?.meta;
          const value = metric?.value;
          const numeric = value != null && metric?.unit !== "text" ? Number(value) : null;
          const text =
            value == null
              ? t("unknown")
              : numeric !== null && Number.isFinite(numeric)
                ? `${new Intl.NumberFormat(locale, { maximumFractionDigits: 4 }).format(numeric)}${metric?.unit === "multiple" ? " ×" : metric?.unit === "percent" ? " %" : ""}`
                : value;
          return (
            <div key={key} className="rounded-md border border-border p-3">
              <dt className="text-sm text-text-3">
                {t(`metrics.${key}`)}
                {metric?.unit === "fraction" && <span> · {t("fraction")}</span>}
              </dt>
              <dd className="num mt-1 text-lg">{text}</dd>
              {meta?.stale && <span className="text-xs text-warn">{t("stale")}</span>}
              {meta?.availability !== "available" && (
                <p className="text-xs text-warn">
                  {t(
                    meta?.availability === "not_applicable"
                      ? "notApplicable"
                      : value == null
                        ? "missing"
                        : "partial",
                  )}
                </p>
              )}
              {meta?.source && (
                <p className="mt-2 break-words text-xs text-text-3">
                  {meta.source}
                  {meta.source_field ? ` · ${meta.source_field}` : ""}
                  {meta.basis ? ` · ${meta.basis}` : ""}
                </p>
              )}
              {meta?.fetched_at && (
                <p className="text-xs text-text-3">
                  {t("fetched", { time: date(meta.fetched_at) })}
                </p>
              )}
              {meta?.market_date && (
                <p className="text-xs text-text-3">{t("period", { time: meta.market_date })}</p>
              )}
            </div>
          );
        })}
      </dl>
    </section>
  );
}
