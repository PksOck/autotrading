"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { AnalysisStatusPill } from "@/components/analysis/AnalysisStatusPill";
import { ActionPill, HORIZONS, VerdictChip, useHorizonTitle } from "@/components/analysis/outlook";
import { useAnalyses, usePortfolio } from "@/lib/api/hooks";
import type { AnalysisSummary } from "@/lib/api/types";

/** Agents' action once the run is done, otherwise the run status. */
function Agents({ run }: { run: AnalysisSummary }) {
  return run.status === "done" && run.rating ? (
    <ActionPill rating={run.rating} />
  ) : (
    <AnalysisStatusPill status={run.status} />
  );
}

function Verdicts({ run }: { run: AnalysisSummary }) {
  const title = useHorizonTitle();
  const b = run.outlook_brief;
  if (!b) return <span className="text-xs text-text-3">–</span>;
  return (
    <span className="flex flex-wrap gap-1">
      {HORIZONS.map((h) => (
        <span key={h} title={title(h).title} className="inline-flex items-center gap-1">
          <span className="text-[11px] text-text-3">{title(h).column}</span>
          <VerdictChip verdict={b[h]} />
        </span>
      ))}
    </span>
  );
}

function ProContra({ run }: { run: AnalysisSummary }) {
  const t = useTranslations("analysisPage");
  const b = run.outlook_brief;
  if (!b) return <span className="text-text-3">–</span>;
  return (
    <span
      className="num whitespace-nowrap"
      aria-label={t("proContraLabel", { pro: b.pro, contra: b.contra })}
    >
      <span className="text-pos">{b.pro} ▲</span> · <span className="text-neg">{b.contra} ▼</span>
    </span>
  );
}

function useHeld() {
  const { data } = usePortfolio();
  return (symbol: string) =>
    data?.positions.find((p) => p.symbol.toUpperCase() === symbol.toUpperCase() && p.quantity !== 0)
      ?.quantity ?? null;
}

/** Instrument page: date, agents' action and the three horizon verdicts per run. */
function CompactRow({ run }: { run: AnalysisSummary }) {
  const format = useFormatter();
  return (
    <li className="border-t border-border first:border-t-0">
      <Link
        href={`/analysis/${run.id}`}
        className="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-4 py-3 text-text no-underline hover:bg-surface-2"
      >
        <span className="text-[13px] text-text-2">
          {format.dateTime(new Date(run.trade_date), { dateStyle: "medium" })}
        </span>
        <span className="ml-auto">
          <Agents run={run} />
        </span>
        <span className="basis-full">
          <Verdicts run={run} />
        </span>
      </Link>
    </li>
  );
}

/** Phone card for the /analysis index. */
function CardRow({ run, held }: { run: AnalysisSummary; held: number | null }) {
  const t = useTranslations("analysisPage");
  const format = useFormatter();
  return (
    <li className="border-t border-border first:border-t-0">
      <Link
        href={`/analysis/${run.id}`}
        className="flex flex-col gap-2 px-4 py-3 text-text no-underline hover:bg-surface-2"
      >
        <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="num font-medium">{run.symbol}</span>
          <span className="min-w-0 flex-1 truncate text-text-2">{run.name}</span>
          <Agents run={run} />
        </span>
        <Verdicts run={run} />
        <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-2">
          <ProContra run={run} />
          {run.conviction != null && (
            <span className="num">{t("card.convictionValue", { n: run.conviction })}</span>
          )}
          {held != null && <span className="num">{t("position.shares", { qty: held })}</span>}
          <time dateTime={run.created_at} className="ml-auto text-text-3">
            {format.relativeTime(new Date(run.created_at), new Date())}
          </time>
        </span>
      </Link>
    </li>
  );
}

function Table({ runs, held }: { runs: AnalysisSummary[]; held: (s: string) => number | null }) {
  const t = useTranslations("analysisPage");
  const format = useFormatter();
  const title = useHorizonTitle();
  const th = "px-3 py-2 text-left text-xs font-medium text-text-3 whitespace-nowrap";
  return (
    <table className="w-full text-[14px]" data-testid="analysis-table">
      <thead className="border-b border-border">
        <tr>
          <th className={th}>{t("columns.instrument")}</th>
          <th className={th}>{t("columns.date")}</th>
          <th className={th}>{t("columns.agents")}</th>
          {HORIZONS.map((h) => (
            <th key={h} className={th}>
              {title(h).column}
            </th>
          ))}
          <th className={th}>{t("columns.proContra")}</th>
          <th className={th}>{t("columns.conviction")}</th>
          <th className={th}>{t("columns.held")}</th>
          <th className={`${th} text-right`}>{t("columns.when")}</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => {
          const qty = held(run.symbol);
          const b = run.outlook_brief;
          return (
            <tr
              key={run.id}
              className="relative border-t border-border first:border-t-0 hover:bg-surface-2"
              data-testid="analysis-row"
            >
              <td className="px-3 py-2.5">
                <Link
                  href={`/analysis/${run.id}`}
                  className="flex flex-col text-text no-underline after:absolute after:inset-0"
                >
                  <span className="num font-medium">{run.symbol}</span>
                  {run.name && (
                    <span className="max-w-56 truncate text-xs text-text-2">{run.name}</span>
                  )}
                </Link>
              </td>
              <td className="num px-3 py-2.5 whitespace-nowrap text-text-2">
                {format.dateTime(new Date(run.trade_date), { dateStyle: "medium" })}
              </td>
              <td className="px-3 py-2.5">
                <Agents run={run} />
              </td>
              {HORIZONS.map((h) => (
                <td key={h} className="px-3 py-2.5">
                  {b ? <VerdictChip verdict={b[h]} /> : <span className="text-text-3">–</span>}
                </td>
              ))}
              <td className="px-3 py-2.5">
                <ProContra run={run} />
              </td>
              <td className="num px-3 py-2.5 text-text-2">
                {run.conviction != null ? t("card.convictionValue", { n: run.conviction }) : "–"}
              </td>
              <td className="num px-3 py-2.5 whitespace-nowrap text-text-2">
                {qty != null ? t("position.shares", { qty }) : "–"}
              </td>
              <td className="px-3 py-2.5 text-right text-xs whitespace-nowrap text-text-3">
                <time dateTime={run.created_at}>
                  {format.relativeTime(new Date(run.created_at), new Date())}
                </time>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/** Recent deep-analysis runs; `limit` and `symbol` narrow it for the instrument page. */
export function AnalysisRunList({
  symbol,
  limit,
  compact,
  emptyKey,
}: {
  symbol?: string;
  limit?: number;
  compact?: boolean;
  emptyKey?: "latest.empty" | "empty";
}) {
  const t = useTranslations("analysisPage");
  const { data, isLoading, error } = useAnalyses(symbol);
  const held = useHeld();
  const runs = (data ?? []).slice(0, limit);

  if (isLoading) return <div className="h-24 animate-pulse rounded-md bg-surface-2" />;
  if (error) return <p className="p-4 text-warn">{t("loadFailed")}</p>;
  if (!runs.length) return <p className="p-4 text-[13px] text-text-3">{t(emptyKey ?? "empty")}</p>;
  if (compact) {
    return (
      <ul>
        {runs.map((run) => (
          <CompactRow key={run.id} run={run} />
        ))}
      </ul>
    );
  }
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <Table runs={runs} held={held} />
      </div>
      <ul className="md:hidden">
        {runs.map((run) => (
          <CardRow key={run.id} run={run} held={held(run.symbol)} />
        ))}
      </ul>
    </>
  );
}
