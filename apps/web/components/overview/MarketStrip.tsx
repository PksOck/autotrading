"use client";

import { useTranslations } from "next-intl";
import { DataDetails } from "@/components/common/DataDetails";
import { LocalTime } from "@/components/theses/LocalTime";
import { formatNumber } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

type Indicator = {
  key: string;
  value?: string | number | null;
  source?: string | null;
  as_of?: string | null;
};
const KEYS = ["spy", "vix", "us10y", "dxy"] as const;

export function MarketStrip({
  indicators,
  source,
  asOf,
  failed = false,
  loading = false,
}: {
  indicators: Indicator[];
  source?: string;
  asOf?: string;
  failed?: boolean;
  loading?: boolean;
}) {
  const t = useTranslations();
  const locale = useAppLocale();
  const hasValues = KEYS.some((key) => indicators.find((row) => row.key === key)?.value != null);
  return (
    <section aria-label={t("overviewFeedback.market")} className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-x-3">
        <h2 className="label">{t("overviewFeedback.market")}</h2>
        <DataDetails>
          <p>{t("overviewFeedback.macroHint")}</p>
          {source && (
            <p>
              {t("table.source")}: {source}
            </p>
          )}
          {asOf && <LocalTime value={asOf} />}
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-2">
            {KEYS.map((key) => {
              const row = indicators.find((item) => item.key === key);
              return (
                <div key={key} className="contents">
                  <dt>{t(`overviewFeedback.${key}`)}</dt>
                  <dd>
                    {row?.source ?? t("overviewFeedback.macroMissing")}
                    {row?.as_of && (
                      <>
                        {" "}
                        · <LocalTime value={row.as_of} />
                      </>
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>
        </DataDetails>
      </div>
      {failed && (
        <p role="alert" className="text-sm text-warn">
          {t("table.loadFailed")}
        </p>
      )}
      {loading && !hasValues ? (
        <p aria-busy="true" className="text-xs text-text-3">
          {t("state.loading")}
        </p>
      ) : !hasValues ? (
        !failed && <p className="text-xs text-warn">{t("pageHelp.marketUnavailable")}</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {KEYS.map((key) => {
            const row = indicators.find((item) => item.key === key);
            return (
              <div key={key} className="card px-3 py-2">
                <h3 className="label">{t(`overviewFeedback.${key}`)}</h3>
                <p className="num">
                  {row?.value != null
                    ? `${formatNumber(locale, Number(row.value), 2)}${key === "spy" || key === "us10y" ? " %" : ""}`
                    : "—"}
                </p>
                {row?.value == null && (
                  <p className="text-[11px] text-warn">{t("overviewFeedback.macroMissing")}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
