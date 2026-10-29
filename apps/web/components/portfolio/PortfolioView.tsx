"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { PositionsPanel } from "@/components/portfolio/PositionsPanel";
import { PortfolioDividends } from "@/components/portfolio/PortfolioDividends";
import { AutomationBatchPanel } from "@/components/settings/AutomationBatchPanel";
import { WatchlistPanel } from "@/components/watchlist/WatchlistPanel";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";

const TABS = ["positions", "watchlist", "analyses", "dividends"] as const;
type Tab = (typeof TABS)[number];

/** SCR-08 Portfelj with the watchlist as a second tab (BL-028, BL-030). Tab lives in the URL (LX-08). */
export function PortfolioView() {
  const t = useTranslations("portfolio");
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const tab: Tab = TABS.includes(params.get("tab") as Tab)
    ? (params.get("tab") as Tab)
    : "positions";

  const select = (next: Tab) => {
    const query = new URLSearchParams(params.toString());
    if (next === "positions") query.delete("tab");
    else query.set("tab", next);
    router.replace(query.size ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  return (
    <div className="flex flex-col gap-5">
      <div role="tablist" className="flex flex-wrap border-b border-border">
        {TABS.map((key) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => select(key)}
            className={cn(
              "relative h-11 px-4 font-medium text-text-2",
              tab === key && "text-accent",
            )}
          >
            {t(
              key === "positions"
                ? "tabPositions"
                : key === "watchlist"
                  ? "tabWatchlist"
                  : key === "analyses"
                    ? "tabAnalyses"
                    : "tabDividends",
            )}
            {tab === key && (
              <motion.span
                layoutId="portfolio-tab"
                transition={spring.snappy}
                className="absolute inset-x-0 -bottom-px h-0.5 bg-accent"
              />
            )}
          </button>
        ))}
      </div>
      {tab === "positions" ? (
        <PositionsPanel />
      ) : tab === "watchlist" ? (
        <WatchlistPanel />
      ) : tab === "dividends" ? (
        <PortfolioDividends />
      ) : (
        <AutomationBatchPanel accountId={params.get("account_id") ?? undefined} />
      )}
    </div>
  );
}
