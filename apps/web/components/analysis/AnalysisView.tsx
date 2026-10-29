"use client";

import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";
import { AgentTimeline } from "@/components/analysis/AgentTimeline";
import { DecisionCardPanel } from "@/components/analysis/DecisionCardPanel";
import { DecisionHeader } from "@/components/analysis/DecisionHeader";
import { EvidenceSplit } from "@/components/analysis/EvidenceSplit";
import { HORIZONS, useHorizonTitle, type Horizon } from "@/components/analysis/outlook";
import { Markdown } from "@/components/common/Markdown";
import { SegmentedButtons } from "@/components/common/SegmentedButtons";
import { ApiError } from "@/lib/api/client";
import { useAnalysis, useAnalysisStream } from "@/lib/api/hooks";
import type { AnalysisOut } from "@/lib/api/types";

function Provenance({ run }: { run: AnalysisOut }) {
  const t = useTranslations("analysisPage.provenance");
  const ux = useTranslations("researchUx");
  const format = useFormatter();
  const d = run.data_sources;
  const day = (v: string | null | undefined) =>
    v ? format.dateTime(new Date(v), { dateStyle: "medium" }) : t("unknown");
  return (
    <p className="text-xs leading-5 text-text-3" data-testid="analysis-provenance">
      <span className="block font-medium">{ux("snapshot")}</span>
      {t("line", { bars: d.bars ?? t("unknown"), asOf: day(d.as_of) })}
      {" · "}
      {d.fundamentals
        ? t("fundamentals", { source: d.fundamentals, asOf: day(d.fundamentals_as_of) })
        : t("noFundamentals")}
      {" · "}
      {t("models", {
        quick: modelName(run.models.quick) ?? t("unknown"),
        deep: modelName(run.models.deep) ?? t("unknown"),
      })}
    </p>
  );
}

// `models` also carries structured entries such as `usage`; only string values are model names.
function modelName(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-5" aria-busy="true">
      <div className="card h-40 animate-pulse" />
      <div className="card h-64 animate-pulse" />
    </div>
  );
}

/** Collapsible section below the decision header; the summary is the heading. */
function Fold({
  title,
  open,
  testId,
  children,
}: {
  title: string;
  open?: boolean;
  testId?: string;
  children: React.ReactNode;
}) {
  return (
    <details className="group card" open={open} data-testid={testId}>
      <summary className="touch-target flex cursor-pointer list-none items-center gap-2 p-4 text-base font-semibold sm:px-5 [&::-webkit-details-marker]:hidden">
        <span aria-hidden className="text-text-3 transition-transform group-open:rotate-90">
          ›
        </span>
        {title}
      </summary>
      <div className="flex flex-col gap-3 border-t border-border p-4 sm:p-5">{children}</div>
    </details>
  );
}

/**
 * SCR-06 Analiza (BL-165): decision first. The header holds the action, price, position and the
 * code-computed outlook; evidence, reasoning, control score and agent steps fold below.
 */
export function AnalysisView({ runId }: { runId: string }) {
  const t = useTranslations("analysisPage");
  const horizonTitle = useHorizonTitle();
  const [horizon, setHorizon] = useState<Horizon>("medium");
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
  const live = run.status === "running" || run.status === "queued";
  const selected = run.outlook?.horizons.find((h) => h.horizon === horizon);

  return (
    <div className="flex flex-col gap-5">
      <Link
        href="/analysis"
        className="w-fit text-[13px] text-text-2 no-underline hover:text-accent"
      >
        ← {t("back")}
      </Link>

      <DecisionHeader run={run} stepCount={steps.length} horizon={horizon} onHorizon={setHorizon}>
        <Provenance run={run} />
      </DecisionHeader>

      {run.status === "failed" && (
        <section
          className="card flex flex-col gap-3 p-4 sm:p-5"
          aria-label={t("decision.failedTitle")}
          data-testid="decision-panel"
        >
          <h2 className="text-base font-semibold text-neg">{t("decision.failedTitle")}</h2>
          <p className="rounded-md bg-neg-soft px-3 py-2 text-[13px] text-neg [overflow-wrap:anywhere]">
            {run.error ?? t("decision.noError")}
          </p>
          <p className="text-[13px] text-text-3">{t("decision.failedHint")}</p>
        </section>
      )}

      {hypothesisCheck && (
        <section
          className="card flex flex-col gap-3 border-accent p-4 sm:p-5"
          aria-label={t("hypothesis.title")}
          data-testid="hypothesis-panel"
        >
          <h2 className="text-base font-semibold">{t("hypothesis.title")}</h2>
          {run.hypothesis && <p className="text-[13px] text-text-2 italic">“{run.hypothesis}”</p>}
          <Markdown
            source={hypothesisCheck.replace(/^\s*#{1,6}[^\n]*\n+/, "")}
            className="text-[15px] text-text"
          />
          <p className="text-xs text-text-3">{t("hypothesis.note")}</p>
        </section>
      )}

      {run.outlook && selected && (
        <Fold title={t("evidence.title")} open testId="evidence-section">
          <SegmentedButtons
            semantics="pressed"
            label={t("evidence.pick")}
            value={horizon}
            onChange={setHorizon}
            options={HORIZONS.map((h) => ({
              value: h,
              label: horizonTitle(h).column,
              testId: `evidence-pick-${h}`,
            }))}
            className="w-full sm:w-fit"
          />
          <EvidenceSplit outlook={selected} />
        </Fold>
      )}

      {run.status !== "failed" && (
        <Fold title={t("details.reasoning")} testId="decision-panel">
          <h2 className="sr-only">{t("decision.title")}</h2>
          {run.decision ? (
            <Markdown
              source={run.decision.replace(/^\s*#{1,6}[^\n]*\n+/, "")}
              className="text-[15px] text-text"
            />
          ) : (
            <p className="text-text-3">
              {run.status === "queued" ? t("decision.queued") : t("decision.pending")}
            </p>
          )}
        </Fold>
      )}

      {run.card && (
        <Fold title={t("details.control")}>
          <DecisionCardPanel card={run.card} triggers={false} />
        </Fold>
      )}

      <Fold title={t("details.steps", { count: steps.length })} open={live} testId="steps-section">
        <AgentTimeline steps={steps} status={run.status} connected={connected} />
      </Fold>
    </div>
  );
}
