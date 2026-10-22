"use client";

import { useTranslations } from "next-intl";
import { Treemap, type TreemapItem } from "@/components/overview/Treemap";
import { usePortfolio } from "@/lib/api/hooks";
import { INSTRUMENTS } from "@/lib/sample-data";

/** OV-01 on Overview: live portfolio when available, sample data (labelled) otherwise. */
export function PortfolioTreemapCard() {
  const t = useTranslations();
  const { data } = usePortfolio();
  const live = data?.positions.length ? data : null;
  const items: TreemapItem[] = live
    ? live.positions.map((p) => ({ symbol: p.symbol, weight: Number(p.weight_pct ?? 0), change: Number(p.change_pct ?? 0), thesis: "none" }))
    : INSTRUMENTS;

  return (
    <section className="card p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-semibold">
          {t("overview.treemap")}
          {(!live || live.source === "demo") && (
            <span className="rounded-full bg-warn-soft px-2 text-xs leading-5 font-medium text-warn">
              {live ? t("provenance.demo") : t("header.sample")}
            </span>
          )}
        </h2>
        <p className="text-xs text-text-3">{t("overview.treemapHint")}</p>
      </div>
      <Treemap items={items} />
    </section>
  );
}
