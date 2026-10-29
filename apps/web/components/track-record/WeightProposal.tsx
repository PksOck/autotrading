"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useState } from "react";
import { ApiError } from "@/lib/api/client";
import { useCalibration, useConfirmWeights, useProposeWeights, useRejectWeights } from "@/lib/api/hooks";
import type { GroupProposal, WeightSetOut } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatNumber, formatShare } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

const KNOWN_ERRORS = new Set(["stale_proposal", "not_pending", "no_changes"]);

const reasonClass: Record<GroupProposal["reason"], string> = {
  better: "text-pos",
  worse: "text-neg",
  low_sample: "text-warn",
  not_significant: "text-text-3",
  no_baseline: "text-text-3",
};

function useGroupLabel() {
  const t = useTranslations();
  return (kind: string, source: string) => {
    const k = t.has(`signal.kind.${kind}`) ? t(`signal.kind.${kind}`) : kind;
    const s = t.has(`signalsPage.source.${source}`) ? t(`signalsPage.source.${source}`) : source;
    return `${k} · ${s}`;
  };
}

function ProposalTable({ set }: { set: WeightSetOut }) {
  const t = useTranslations("trackRecord.weights");
  const locale = useAppLocale();
  const label = useGroupLabel();
  const share = (v: string | null | undefined) => (v == null ? "—" : formatShare(locale, Number(v)));
  const weight = (v: string) => formatNumber(locale, Number(v), 2);
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead className="text-left text-xs text-text-3">
          <tr className="border-b border-border">
            <th className="px-4 py-2 font-medium">{t("group")}</th>
            <th className="px-4 py-2 text-right font-medium">{t("count")}</th>
            <th className="px-4 py-2 text-right font-medium">{t("hitRate")}</th>
            <th className="px-4 py-2 text-right font-medium">{t("interval")}</th>
            <th className="px-4 py-2 text-right font-medium">{t("weight")}</th>
            <th className="px-4 py-2 font-medium">{t("reasonTitle")}</th>
          </tr>
        </thead>
        <tbody>
          {set.proposal?.groups.map((g) => {
            const moved = Number(g.proposed_weight) !== Number(g.current_weight);
            return (
              <tr key={`${g.kind}:${g.source}`} data-testid={`weight-${g.kind}-${g.source}`} className="border-b border-border last:border-0">
                <td className="px-4 py-2">{label(g.kind, g.source)}</td>
                <td className="num px-4 py-2 text-right">{g.count}</td>
                <td className="num px-4 py-2 text-right">{share(g.hit_rate)}</td>
                <td className="num px-4 py-2 text-right text-text-2">
                  {g.interval ? t("intervalValue", { low: share(g.interval.low), high: share(g.interval.high) }) : "—"}
                </td>
                <td className="num px-4 py-2 text-right whitespace-nowrap">
                  {moved ? (
                    <>
                      <span className="text-text-3">{weight(g.current_weight)}</span>
                      {" → "}
                      <span className="font-semibold">{weight(g.proposed_weight)}</span>
                    </>
                  ) : (
                    weight(g.current_weight)
                  )}
                </td>
                <td className={cn("px-4 py-2", reasonClass[g.reason])}>{t(`reason.${g.reason}`, { min: set.proposal?.min_sample ?? 0 })}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** BL-103: proposed strength weights per group; nothing changes until you confirm (ADR-0015). */
export function WeightProposal({ horizonDays }: { horizonDays: number }) {
  const t = useTranslations("trackRecord.weights");
  const ux = useTranslations("researchUx");
  const format = useFormatter();
  const locale = useAppLocale();
  const calibration = useCalibration();
  const { data } = calibration;
  const propose = useProposeWeights();
  const confirm = useConfirmWeights();
  const reject = useRejectWeights();
  const [confirming, setConfirming] = useState(false);
  const busy = propose.isPending || confirm.isPending || reject.isPending;
  const failure = propose.error ?? confirm.error ?? reject.error;
  const failureKey = failure instanceof ApiError && KNOWN_ERRORS.has(failure.detail) ? failure.detail : "generic";
  const pending = data?.proposal;
  const basis = pending?.proposal;
  const date = (iso: string) => format.dateTime(new Date(iso), { dateStyle: "medium", timeStyle: "short" });
  const reset = () => {
    setConfirming(false);
    propose.reset();
    confirm.reset();
    reject.reset();
  };

  if (calibration.isLoading) return <div className="card h-24 animate-pulse" aria-busy="true"/>;
  if (calibration.error) return <div className="card p-4" role="alert"><p>{ux("calibrationUnavailable")}</p><button className="min-h-10 text-accent" onClick={() => void calibration.refetch()}>{ux("retry")}</button></div>;

  return (
    <section className="flex flex-col gap-3" aria-labelledby="weights-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-2xl">
          <h2 id="weights-title" className="font-semibold">
            {t("title")}
          </h2>
          <p className="text-[13px] text-text-3">{t("hint")}</p>
          <p className="mt-1 text-xs text-text-3">
            {data?.active?.decided_at ? t("activeSince", { date: date(data.active.decided_at) }) : t("defaults")}
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            reset();
            propose.mutate(horizonDays);
          }}
          className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2 disabled:opacity-50"
        >
          {t("propose", { days: horizonDays })}
        </button>
      </div>
      {failure && (
        <p role="alert" className="rounded-md bg-warn-soft px-4 py-3 text-[13px] text-warn">
          {t(`error.${failureKey}`)}
        </p>
      )}
      {pending && basis && (
        <>
          <p className="text-xs text-text-3">
            {t("basis", {
              days: basis.horizon_days,
              count: basis.baseline_count,
              rate: basis.baseline_hit_rate == null ? "—" : formatShare(locale, Number(basis.baseline_hit_rate)),
              date: date(pending.created_at),
            })}
          </p>
          <ProposalTable set={pending} />
          {!basis.changed && <p className="text-[13px] text-text-3">{t("unchanged")}</p>}
          {confirming ? (
            <div className="card flex flex-col gap-3 border-accent p-4">
              <p className="text-[13px]">{t("confirmText")}</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => confirm.mutate(pending.id, { onSuccess: () => setConfirming(false) })}
                  className="h-9 rounded-md bg-accent px-3 font-medium text-on-accent disabled:opacity-50"
                >
                  {t("confirm")}
                </button>
                <button type="button" onClick={() => setConfirming(false)} className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2">
                  {t("cancel")}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy || !basis.changed}
                onClick={() => setConfirming(true)}
                className="h-9 rounded-md bg-accent px-3 font-medium text-on-accent disabled:opacity-50"
              >
                {t("apply")}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  reset();
                  reject.mutate(pending.id);
                }}
                className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2 disabled:opacity-50"
              >
                {t("reject")}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
