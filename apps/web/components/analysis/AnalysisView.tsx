"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { AgentTimeline } from "@/components/analysis/AgentTimeline";
import { AnalysisStatusPill } from "@/components/analysis/AnalysisStatusPill";
import { DecisionCardPanel } from "@/components/analysis/DecisionCardPanel";
import { RatingPill } from "@/components/analysis/RatingPill";
import { Markdown } from "@/components/common/Markdown";
import { CreateThesisButton } from "@/components/theses/CreateThesisButton";
import { ApiError } from "@/lib/api/client";
import { useAnalysis, useAnalysisStream } from "@/lib/api/hooks";
import type { AnalysisOut } from "@/lib/api/types";

function Provenance({ run }: { run: AnalysisOut }) {
  const t = useTranslations("analysisPage.provenance");
  const format = useFormatter();
  const d = run.data_sources;
  const day = (v: string | null | undefined) =>
    v ? format.dateTime(new Date(v), { dateStyle: "medium" }) : t("unknown");
  return (
    <p className="text-xs leading-5 text-text-3" data-testid="analysis-provenance">
      {t("line", { bars: d.bars ?? t("unknown"), asOf: day(d.as_of) })}
      {" · "}
      {d.fundamentals
        ? t("fundamentals", { source: d.fundamentals, asOf: day(d.fundamentals_as_of) })
        : t("noFundamentals")}
      {" · "}
      {t("models", { quick: run.models.quick ?? t("unknown"), deep: run.models.deep ?? t("unknown") })}
    </p>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-5" aria-busy="true">
      <div className="card h-40 animate-pulse" />
      <div className="card h-64 animate-pulse" />
    </div>
  );
}

/** SCR-06 Analiza: header with rating and provenance, final decision, live agent timeline. */
export function AnalysisView({ runId }: { runId: string }) {
  const t = useTranslations("analysisPage");
  const format = useFormatter();
  const { data: run, isLoading, error } = useAnalysis(runId);
  const { steps, connected } = useAnalysisStream(runId, run?.steps ?? [], run?.status);

  if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
    return <p className="card p-6 text-text-2">{t("notFound")}</p>;
  }
  if (error) return <p className="card p-6 text-warn">{t("loadFailed")}</p>;
  if (isLoading || !run) return <Skeleton />;

  const hypothesisCheck =
    steps.find((s) => s.agent === "hypothesis" && s.title === "hypothesis_check")?.content ||
    run.reports.hypothesis_check ||
    null;

  return (
    <div className="flex flex-col gap-5">
      <Link href="/analysis" className="w-fit text-[13px] text-text-2 no-underline hover:text-accent">
        ← {t("back")}
      </Link>

      <header className="card flex flex-col gap-3 p-4 sm:p-5" aria-label={t("runTitle")}>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <Link href={`/i/${encodeURIComponent(run.symbol)}`} className="num text-[28px] leading-[34px] font-medium text-text no-underline hover:text-accent">
            {run.symbol}
          </Link>
          {run.name && <span className="text-text-2">{run.name}</span>}
          <AnalysisStatusPill status={run.status} />
          <span data-testid="analysis-engine" className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">
            {t.has(`engines.${run.engine}`) ? t(`engines.${run.engine}` as "engines.etf") : run.engine}
          </span>
          {run.rating && (
            <span className="sm:ml-auto" aria-label={t("ratingLabel", { rating: run.rating })}>
              <RatingPill rating={run.rating} size="lg" />
            </span>
          )}
        </div>
        <p className="text-[13px] text-text-2">
          {t("tradeDate")}: <span className="num">{format.dateTime(new Date(run.trade_date), { dateStyle: "medium" })}</span>
          {" · "}
          {t("stepCount", { count: steps.length })}
        </p>
        {run.caveats.length > 0 && (
          <ul className="flex flex-wrap gap-2" aria-label={t("caveatHint")}>
            {run.caveats.map((c) => (
              <li key={c} className="rounded-full bg-warn-soft px-2.5 text-xs leading-6 font-medium text-warn">
                {t.has(`caveats.${c}`) ? t(`caveats.${c}` as "caveats.rumor_only") : c}
              </li>
            ))}
          </ul>
        )}
        <Provenance run={run} />
        <p className="rounded-md bg-surface-2 px-3 py-2 text-[13px] text-text-2">{t("opinion")}</p>
      </header>

      {hypothesisCheck && (
        <section className="card flex flex-col gap-3 border-accent p-4 sm:p-5" aria-label={t("hypothesis.title")} data-testid="hypothesis-panel">
          <h2 className="text-base font-semibold">{t("hypothesis.title")}</h2>
          {run.hypothesis && <p className="text-[13px] text-text-2 italic">“{run.hypothesis}”</p>}
          <Markdown source={hypothesisCheck.replace(/^\s*#{1,6}[^\n]*\n+/, "")} className="text-[15px] text-text" />
          <p className="text-xs text-text-3">{t("hypothesis.note")}</p>
        </section>
      )}

      <section
        className="card flex flex-col gap-3 p-4 sm:p-5"
        aria-label={run.status === "failed" ? t("decision.failedTitle") : t("decision.title")}
        data-testid="decision-panel"
      >
        {run.status === "failed" ? (
          <>
            <h2 className="text-base font-semibold text-neg">{t("decision.failedTitle")}</h2>
            <p className="rounded-md bg-neg-soft px-3 py-2 text-[13px] text-neg [overflow-wrap:anywhere]">{run.error ?? t("decision.noError")}</p>
            <p className="text-[13px] text-text-3">{t("decision.failedHint")}</p>
          </>
        ) : (
          <>
            <h2 className="text-base font-semibold">{t("decision.title")}</h2>
            {run.decision ? (
              <Markdown source={run.decision.replace(/^\s*#{1,6}[^\n]*\n+/, "")} className="text-[15px] text-text" />
            ) : (
              <p className="text-text-3">{run.status === "queued" ? t("decision.queued") : t("decision.pending")}</p>
            )}
          </>
        )}
      </section>

      {run.card && <DecisionCardPanel card={run.card} />}
      {run.status === "done" && run.card && ((run.card.upgrade_if?.length ?? 0) > 0 || (run.card.downgrade_if?.length ?? 0) > 0) && <CreateThesisButton runId={runId} />}

      <AgentTimeline steps={steps} status={run.status} connected={connected} />
    </div>
  );
}
