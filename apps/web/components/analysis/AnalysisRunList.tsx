"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { AnalysisStatusPill } from "@/components/analysis/AnalysisStatusPill";
import { RatingPill } from "@/components/analysis/RatingPill";
import { useAnalyses } from "@/lib/api/hooks";
import type { AnalysisSummary } from "@/lib/api/types";

function Row({ run, compact }: { run: AnalysisSummary; compact?: boolean }) {
  const format = useFormatter();
  return (
    <li className="border-t border-border first:border-t-0">
      <Link
        href={`/analysis/${run.id}`}
        className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-4 py-3 text-text no-underline hover:bg-surface-2"
      >
        {!compact && <span className="num w-20 font-medium">{run.symbol}</span>}
        {!compact && <span className="min-w-0 flex-1 truncate text-text-2">{run.name}</span>}
        {compact && (
          <span className="text-[13px] text-text-2">
            {format.dateTime(new Date(run.trade_date), { dateStyle: "medium" })}
          </span>
        )}
        <span className={compact ? "ml-auto" : ""}>
          <AnalysisStatusPill status={run.status} />
        </span>
        <RatingPill rating={run.rating} />
        {!compact && (
          <time dateTime={run.created_at} className="ml-auto text-xs whitespace-nowrap text-text-3">
            {format.relativeTime(new Date(run.created_at), new Date())}
          </time>
        )}
      </Link>
    </li>
  );
}

/** Recent deep-analysis runs; `limit` and `symbol` narrow it for the instrument page. */
export function AnalysisRunList({ symbol, limit, compact, emptyKey }: { symbol?: string; limit?: number; compact?: boolean; emptyKey?: "latest.empty" | "empty" }) {
  const t = useTranslations("analysisPage");
  const { data, isLoading, error } = useAnalyses(symbol);
  const runs = (data ?? []).slice(0, limit);

  if (isLoading) return <div className="h-24 animate-pulse rounded-md bg-surface-2" />;
  if (error) return <p className="p-4 text-warn">{t("loadFailed")}</p>;
  if (!runs.length) return <p className="p-4 text-[13px] text-text-3">{t(emptyKey ?? "empty")}</p>;
  return (
    <ul>
      {runs.map((run) => (
        <Row key={run.id} run={run} compact={compact} />
      ))}
    </ul>
  );
}
