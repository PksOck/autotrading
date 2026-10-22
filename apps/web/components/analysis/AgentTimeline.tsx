"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useNow, useFormatter, useTranslations } from "next-intl";
import { useState } from "react";
import { Markdown } from "@/components/common/Markdown";
import { currentPhase, groupByPhase, type Phase } from "@/lib/analysis";
import type { AnalysisStatus, AnalysisStep } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { stripMarkdown } from "@/lib/markdown";
import { spring } from "@/lib/motion";

const AGENT_TONE: Record<string, string> = {
  bull: "bg-pos-soft text-pos",
  bear: "bg-neg-soft text-neg",
  aggressive: "bg-warn-soft text-warn",
  conservative: "bg-accent-soft text-accent",
  neutral: "bg-surface-2 text-text-2",
};

function useStepTitle() {
  const t = useTranslations("analysisPage");
  return (step: AnalysisStep) => {
    if (step.kind === "report" && step.title && t.has(`reports.${step.title}`)) return t(`reports.${step.title}`);
    if (step.kind === "decision") return t("kinds.decision");
    return t(`kinds.${step.kind}` as "kinds.report");
  };
}

function AgentChip({ agent }: { agent: string }) {
  const t = useTranslations("agents");
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 text-xs leading-5 font-medium", AGENT_TONE[agent] ?? "bg-accent-soft text-accent")}>
      {t.has(agent) ? t(agent) : agent}
    </span>
  );
}

/** Collapsed: ~3 lines of plain text. Expanded: full safe markdown. */
function Expandable({ step, title }: { step: AnalysisStep; title: string }) {
  const t = useTranslations("analysisPage");
  const [open, setOpen] = useState(false);
  const long = step.content.length > 180 || step.content.includes("\n");
  return (
    <div className="flex flex-col gap-1.5">
      {open ? (
        <Markdown source={step.content} />
      ) : (
        <p className="line-clamp-3 whitespace-pre-line text-[14px] leading-6 text-text-2 [overflow-wrap:anywhere]">{stripMarkdown(step.content)}</p>
      )}
      {long && (
        <button
          type="button"
          aria-expanded={open}
          aria-label={t(open ? "collapseLabel" : "expandLabel", { title })}
          onClick={() => setOpen((v) => !v)}
          className="inline-flex h-8 w-fit items-center text-[13px] font-medium text-accent hover:underline"
        >
          {t(open ? "collapse" : "expand")}
        </button>
      )}
    </div>
  );
}

function StepRow({ step, hideAgent }: { step: AnalysisStep; hideAgent?: boolean }) {
  const t = useTranslations("analysisPage");
  const format = useFormatter();
  const now = useNow({ updateInterval: 15_000 });
  const stepTitle = useStepTitle();
  const title = stepTitle(step);
  const time = (
    <time dateTime={step.created_at} className="ml-auto text-xs whitespace-nowrap text-text-3">
      {format.relativeTime(new Date(step.created_at), now)}
    </time>
  );

  if (step.kind === "tool") {
    return (
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {!hideAgent && <AgentChip agent={step.agent} />}
        <code className="num order-last min-w-0 basis-full sm:order-none sm:basis-0 sm:flex-1 rounded bg-surface-2 px-1.5 py-0.5 text-xs text-text-2 [overflow-wrap:anywhere]">
          {step.title}
        </code>
        {time}
      </div>
    );
  }
  if (step.kind === "status") {
    const key = step.title ?? "";
    return (
      <div className="flex items-center gap-2 text-xs text-text-3">
        <span>{t.has(`statusSteps.${key}`) ? t(`statusSteps.${key}` as "statusSteps.done") : key}</span>
        {time}
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-2">
        {!hideAgent && <AgentChip agent={step.agent} />}
        {step.kind !== "debate" && <span className="text-[13px] font-medium text-text">{title}</span>}
        {time}
      </div>
      <Expandable step={step} title={title} />
    </div>
  );
}

function PhaseHeading({ phase, count, active }: { phase: Phase; count: number; active: boolean }) {
  const t = useTranslations("analysisPage");
  return (
    <div className="flex flex-wrap items-center gap-2">
      <h3 className="text-sm font-semibold text-text">{t(`phases.${phase}`)}</h3>
      <span className="text-xs text-text-3">{t("stepCount", { count })}</span>
      {active && (
        <span data-testid="phase-live" className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-2 text-xs leading-5 font-medium text-accent">
          <span className="size-1.5 rounded-full bg-accent motion-safe:animate-pulse" />
          {t("live")}
        </span>
      )}
    </div>
  );
}

/** Bull and bear turns side by side on desktop, stacked on phone. */
function DebateColumns({ steps, reduced }: { steps: AnalysisStep[]; reduced: boolean }) {
  const t = useTranslations("agents");
  const sides = ["bull", "bear"] as const;
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {sides.map((side) => (
        <section key={side} className="flex min-w-0 flex-col gap-3 rounded-md border border-border bg-surface-2/40 p-3">
          <h4 className={cn("text-xs font-semibold tracking-wide uppercase", side === "bull" ? "text-pos" : "text-neg")}>{t(side)}</h4>
          <AnimatePresence initial={false}>
            {steps
              .filter((s) => s.agent === side)
              .map((s) => (
                <motion.div key={s.seq} {...stepMotion(reduced)}>
                  <StepRow step={s} hideAgent />
                </motion.div>
              ))}
          </AnimatePresence>
        </section>
      ))}
    </div>
  );
}

const stepMotion = (reduced: boolean) =>
  reduced
    ? ({ initial: false } as const)
    : ({ initial: { opacity: 0, y: -8 }, animate: { opacity: 1, y: 0, transition: spring.soft } } as const);

/**
 * CMP-12: vertical timeline of agent steps grouped into phases (SCR-06). New steps slide in (MO-03),
 * the phase in progress pulses while the run is live.
 */
export function AgentTimeline({ steps, status, connected = false }: { steps: AnalysisStep[]; status: AnalysisStatus; connected?: boolean }) {
  const t = useTranslations("analysisPage");
  const reduced = useReducedMotion() ?? false;
  const groups = groupByPhase(steps);
  const live = status === "running" || status === "queued";
  const active = live ? currentPhase(steps) : null;

  if (!groups.length) {
    return (
      <section aria-label={t("timelineLabel")} className="card flex items-center gap-2 p-5 text-text-3">
        {live && <span className="size-2 rounded-full bg-accent motion-safe:animate-pulse" />}
        {live ? t("liveWorking") : t("timelineEmpty")}
      </section>
    );
  }

  return (
    <section aria-label={t("timelineLabel")} data-testid="agent-timeline" data-step-count={steps.length} className="card p-4 sm:p-5">
      <ol className="relative flex flex-col gap-6">
        {groups.map((g) => (
          <li key={g.phase} className="group relative pl-6 sm:pl-7">
            <span aria-hidden className="absolute top-1.5 bottom-[-1.5rem] left-[5px] w-px bg-border group-last:hidden" />
            <span
              aria-hidden
              className={cn("absolute top-1.5 left-0 size-[11px] rounded-full border-2 border-border bg-surface", active === g.phase && "border-accent bg-accent motion-safe:animate-pulse")}
            />
            <PhaseHeading phase={g.phase} count={g.steps.length} active={active === g.phase} />
            <div className="mt-3">
              {g.phase === "debate" ? (
                <DebateColumns steps={g.steps} reduced={reduced} />
              ) : (
                <ul className="flex flex-col gap-3">
                  <AnimatePresence initial={false}>
                    {g.steps.map((s) => (
                      <motion.li key={s.seq} data-seq={s.seq} layout={!reduced} {...stepMotion(reduced)}>
                        <StepRow step={s} />
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </ul>
              )}
            </div>
          </li>
        ))}
      </ol>
      {live && (
        <p className="mt-5 flex items-center gap-2 pl-6 text-[13px] text-text-3 sm:pl-7" aria-live="polite">
          <span className={cn("size-2 rounded-full motion-safe:animate-pulse", connected ? "bg-accent" : "bg-text-3")} />
          {t("liveWorking")}
        </p>
      )}
    </section>
  );
}
