"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { DataTable, type ColumnDefinition } from "@/components/table/DataTable";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AnalysisStatusPill } from "@/components/analysis/AnalysisStatusPill";
import { ActionPill, HORIZONS, VerdictChip, useHorizonTitle } from "@/components/analysis/outlook";
import { usePortfolio } from "@/lib/api/hooks";
import { useResearchAnalyses, type AnalysisFilters } from "@/lib/api/research";
import { analysisFilters } from "@/lib/research-state";
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
  const columns: ColumnDefinition<AnalysisSummary>[] = [
    {id:"symbol", label:t("columns.instrument"),required:true,sortable:true,width:200,render:run => <Link href={`/analysis/${run.id}`} className="flex flex-col text-text no-underline"><span className="num font-medium">{run.symbol}</span><span className="text-xs text-text-2">{run.name}</span></Link>},
    {id:"trade_date",label:t("columns.date"),sortable:true,render:run => format.dateTime(new Date(run.trade_date),{dateStyle:"medium"})},
    {id:"agents",label:t("columns.agents"),required:true,render:run => <><Agents run={run}/>{(run.caveats ?? []).map(c => <span className="block text-xs text-warn" key={c}>{t.has(`caveats.${c}`) ? t(`caveats.${c}`) : t("loadFailed")}</span>)}</>},
    ...HORIZONS.map(h => ({id:h,label:title(h).column,render:(run:AnalysisSummary) => run.outlook_brief ? <VerdictChip verdict={run.outlook_brief[h]}/> : "—"})),
    {id:"evidence",label:t("columns.proContra"),render:run => <ProContra run={run}/>},
    {id:"conviction",label:t("columns.conviction"),numeric:true,render:run => run.conviction != null ? t("card.convictionValue",{n:run.conviction}) : "—"},
    {id:"position",label:t("columns.held"),render:run => held(run.symbol) != null ? t("position.shares",{qty:held(run.symbol)!}) : "—"},
    {id:"created_at",label:t("columns.when"),sortable:true,render:run => <time dateTime={run.created_at}>{format.dateTime(new Date(run.created_at),{dateStyle:"medium",timeStyle:"short"})}</time>},
  ];
  return <div data-testid="analysis-table"><DataTable module="analyses" columns={columns} rows={runs} rowKey={run => run.id} label={t("indexLabel")}/></div>;
}

/** Recent deep-analysis runs; `limit` and `symbol` narrow it for the instrument page. */
export function AnalysisRunList({
  symbol,
  limit,
  compact,
  emptyKey,
  filters,
}: {
  symbol?: string;
  limit?: number;
  compact?: boolean;
  emptyKey?: "latest.empty" | "empty";
  filters?: AnalysisFilters;
}) {
  const t = useTranslations("analysisPage");
  const { data, isLoading, error } = useResearchAnalyses({ ...filters, symbol, limit: limit ?? 100 });
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

export function AnalysisIndex() {
  const t = useTranslations("researchUx");
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const filters = analysisFilters(params);
  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params.toString());
    next.set(key, value);
    next.delete("page");
    router.replace(`${pathname}?${next}`, {scroll: false});
  };
  return <>
    <div className="flex flex-wrap items-center gap-4 border-b border-border p-4">
      <select aria-label={t("allStatuses")} value={filters.status ?? "all"} onChange={(e) => set("status", e.target.value)} className="h-10 rounded-md border border-border bg-surface px-3">
        {["done", "all", "queued", "running", "failed"].map((s) => <option key={s} value={s}>{t(s === "all" ? "allStatuses" : s)}</option>)}
      </select>
      <label className="flex min-h-10 items-center gap-2 text-[13px]">
        <input type="checkbox" checked={filters.latest_per_instrument} onChange={(e) => set("latest", String(e.target.checked))}/>{t("latest")}
      </label>
    </div>
    <AnalysisRunList filters={filters}/>
  </>;
}
