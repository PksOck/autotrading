"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { EntityLink } from "@/components/common/EntityLink";
import { useProposalList } from "@/lib/api/hooks";
import { useRetryProposal } from "@/lib/api/research";
import { cn } from "@/lib/cn";
import { listItem } from "@/lib/motion";
import { openProposalComposer } from "@/stores/proposals";

const STATUS_STYLE: Record<string, string> = {
  queued: "bg-surface-2 text-text-2",
  running: "bg-accent-soft text-accent animate-pulse",
  done: "bg-pos-soft text-pos",
  failed: "bg-neg-soft text-neg",
};

/** SCR-12 (BL-054): the user's proposals with live status and the model's verdict. */
export function ProposalList() {
  const t = useTranslations();
  const ux = useTranslations("researchUx");
  const retry = useRetryProposal();
  const format = useFormatter();
  const refined = useTranslations("screenRefinement");
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const states = ["all", "pending", "queued", "running", "done", "attention", "failed"] as const;
  const status = states.find((value) => value === params.get("status")) ?? "all";
  const q = (params.get("q") ?? "").slice(0, 100);
  const query = new URLSearchParams();
  if (status !== "all") query.set("status", status);
  if (q.trim()) query.set("q", q.trim());
  const { data, isLoading, error } = useProposalList(query.toString());
  const change = (key: string, value: string) => {
    const next = new URLSearchParams(params.toString());
    if (value && value !== "all") next.set(key, value);
    else next.delete(key);
    next.delete("page");
    router.replace(`${pathname}${next.size ? `?${next}` : ""}`, { scroll: false });
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("proposal.listTitle")}</h2>
        <button
          type="button"
          onClick={() => openProposalComposer()}
          className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90"
        >
          + {t("header.propose")}
        </button>
      </div>
      <div className="card flex flex-wrap items-end gap-3 p-3">
        <label className="space-y-1 text-xs text-text-2">
          <span className="block">{refined("proposalStatus")}</span>
          <select
            aria-label={refined("proposalStatus")}
            value={status}
            onChange={(e) => change("status", e.target.value)}
            className="min-h-12 rounded-md border border-border bg-surface px-3"
          >
            {states.map((state) => (
              <option key={state} value={state}>
                {refined(`proposalStates.${state}`)}
              </option>
            ))}
          </select>
        </label>
        <form
          className="flex min-w-0 flex-1 flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            change("q", String(new FormData(event.currentTarget).get("q") ?? "").trim());
          }}
        >
          <label className="min-w-40 flex-1 space-y-1 text-xs text-text-2">
            <span className="block">{refined("proposalSearch")}</span>
            <input
              key={q}
              name="q"
              maxLength={100}
              defaultValue={q}
              className="min-h-12 w-full rounded-md border border-border bg-surface px-3"
            />
          </label>
          <button type="submit" className="min-h-12 rounded-md border border-border px-3">
            {refined("search")}
          </button>
        </form>
        {data && (
          <span className="py-3 text-xs text-text-3">
            {refined("proposalCount", { count: data.length })}
          </span>
        )}
      </div>
      {isLoading && <div className="card h-32 animate-pulse" />}
      {error && <p className="card p-6 text-warn">{t("system.unreachable")}</p>}
      {data && data.length === 0 && (
        <p className="card p-6 text-text-3">
          {status !== "all" || q ? refined("noMatchingProposals") : t("proposal.listEmpty")}
        </p>
      )}
      <ul className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {data?.map((p) => (
            <motion.li key={p.id} layout {...listItem} className="card flex flex-col gap-2 p-4">
              <div className="flex flex-wrap items-center gap-2">
                {p.symbols.map((s) => (
                  <EntityLink key={s} entity={{ kind: "instrument", id: s }} />
                ))}
                <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">
                  {t(`proposal.depth.${p.depth ?? "quick"}`)}
                </span>
                <span
                  className={cn(
                    "rounded-full px-2 text-xs leading-5 font-medium",
                    STATUS_STYLE[p.error_code ? "failed" : p.status],
                  )}
                >
                  {p.error_code
                    ? refined("proposalStates.attention")
                    : p.status === "done"
                      ? t("proposal.status.done")
                      : p.status === "failed"
                        ? t("proposalsPage.failed")
                        : t(`proposalsPage.${p.status}`)}
                </span>
                <span className="ml-auto text-xs text-text-3">
                  {format.relativeTime(new Date(p.created_at), new Date())}
                </span>
              </div>
              {p.hypothesis && <p className="text-text-2">“{p.hypothesis}”</p>}
              {p.status === "done" && !p.error_code && p.verdict_result && (
                <section className="rounded-md bg-surface-2 p-3 text-[13px]">
                  <h3 className="font-medium">
                    {ux("quickVerdict")} · {ux(p.verdict_result.verdict)}
                  </h3>
                  <p className="mt-1 text-text-2">{p.verdict_result.summary}</p>
                  {(["key_points", "risks"] as const).map((key) =>
                    p.verdict_result?.[key]?.length ? (
                      <div key={key} className="mt-2">
                        <h4 className="text-xs text-text-3">
                          {ux(key === "risks" ? "risks" : "keyPoints")}
                        </h4>
                        <ul className="list-disc pl-4">
                          {p.verdict_result?.[key]?.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null,
                  )}
                </section>
              )}
              {(p.error_code || p.status === "failed") && (
                <div
                  role="alert"
                  className="flex flex-col items-start gap-2 rounded-md bg-warn-soft p-3 text-[13px] text-warn"
                >
                  <p>{ux(p.error_code ?? "analysis_failed")}</p>
                  {p.status === "failed" && (
                    <button
                      type="button"
                      disabled={retry.isPending && retry.variables === p.id}
                      onClick={() => retry.mutate(p.id)}
                      className="h-9 rounded-md border border-border px-3 disabled:opacity-50"
                    >
                      {ux(retry.isPending && retry.variables === p.id ? "retrying" : "retry")}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() =>
                      openProposalComposer({ symbols: p.symbols, hypothesis: p.hypothesis })
                    }
                    className="min-h-9 text-accent"
                  >
                    {ux("editProposal")}
                  </button>
                  {retry.error && retry.variables === p.id && <p>{ux("actionFailed")}</p>}
                </div>
              )}
              {!!p.analysis_links?.length && (
                <section className="flex flex-wrap gap-3 text-[13px]">
                  <h3 className="text-xs text-text-3">{ux("deepAnalyses")}</h3>
                  {p.analysis_links.map((run) => (
                    <Link key={run.id} href={`/analysis/${run.id}`} className="text-accent">
                      {run.symbol} ·{" "}
                      {ux(
                        ["done", "failed", "queued", "running"].includes(run.status)
                          ? run.status
                          : "queued",
                      )}
                    </Link>
                  ))}
                </section>
              )}
              {p.signal_id && (
                <Link
                  href={`/signals?peek=signal:${p.signal_id}`}
                  className="text-[13px] text-accent"
                >
                  {t("proposalsPage.openSignal")} →
                </Link>
              )}
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}
