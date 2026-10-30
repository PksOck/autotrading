"use client";

import { useTranslations } from "next-intl";
import { Treemap, type TreemapItem } from "@/components/overview/Treemap";
import { usePortfolio } from "@/lib/api/hooks";

/** OV-01: API positions only; absence is never replaced with illustrative holdings. */
export function PortfolioTreemapCard() {
  const t = useTranslations();
  const { data, error, isLoading } = usePortfolio();
  const live = data?.positions.length ? data : null;
  const items: TreemapItem[] = live
    ? [...new Set(live.positions.map((p) => p.symbol))].map((symbol) => {
        const positions = live.positions.filter((p) => p.symbol === symbol);
        const changes = new Set(positions.map((p) => p.change_pct));
        const change = changes.size === 1 ? positions[0]!.change_pct : null;
        return {
          symbol,
          weight: positions.reduce((sum, p) => sum + Number(p.weight_pct ?? 0), 0),
          change: change == null ? null : Number(change),
          thesis: "none",
        };
      })
    : [];

  return (
    <section className="card p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-semibold">
          {t("overview.treemap")}
          {live?.source === "demo" && (
            <span className="rounded-full bg-warn-soft px-2 text-xs leading-5 font-medium text-warn">
              {t("provenance.demo")}
            </span>
          )}
        </h2>
        <p className="text-xs text-text-3">{t("overviewFeedback.portfolioHint")}</p>
      </div>
      {error ? (
        <p role="alert" className="text-warn">
          {t("table.loadFailed")}
        </p>
      ) : isLoading ? (
        <div className="h-48 animate-pulse" aria-busy="true" />
      ) : items.length ? (
        <Treemap items={items} />
      ) : (
        <p className="text-text-3">{t("table.empty")}</p>
      )}
      {data && (
        <p className="mt-3 text-xs text-text-3">
          {data.source ?? t("table.missing")} · {data.as_of ?? t("table.missing")}
        </p>
      )}
    </section>
  );
}
