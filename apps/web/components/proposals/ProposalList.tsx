"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { EntityLink } from "@/components/common/EntityLink";
import { useProposalList } from "@/lib/api/hooks";
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
  const format = useFormatter();
  const { data, isLoading, error } = useProposalList();

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">{t("proposal.listTitle")}</h2>
        <button type="button" onClick={() => openProposalComposer()} className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90">
          + {t("header.propose")}
        </button>
      </div>
      {isLoading && <div className="card h-32 animate-pulse" />}
      {error && <p className="card p-6 text-warn">{t("system.unreachable")}</p>}
      {data && data.length === 0 && <p className="card p-6 text-text-3">{t("proposal.listEmpty")}</p>}
      <ul className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {data?.map((p) => (
            <motion.li key={p.id} layout {...listItem} className="card flex flex-col gap-2 p-4">
              <div className="flex flex-wrap items-center gap-2">
                {p.symbols.map((s) => (
                  <EntityLink key={s} entity={{ kind: "instrument", id: s }} />
                ))}
                <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">{t(`proposal.depth.${p.depth ?? "quick"}`)}</span>
                <span className={cn("rounded-full px-2 text-xs leading-5 font-medium", STATUS_STYLE[p.status])}>
                  {p.status === "done" ? t("proposal.status.done") : p.status === "failed" ? t("proposalsPage.failed") : t(`proposalsPage.${p.status}`)}
                </span>
                <span className="ml-auto text-xs text-text-3">{format.relativeTime(new Date(p.created_at), new Date())}</span>
              </div>
              {p.hypothesis && <p className="text-text-2">“{p.hypothesis}”</p>}
              {p.verdict && <p className="rounded-md bg-surface-2 p-3 text-[13px] text-text">{p.verdict}</p>}
              {p.analysis_id && (
                <Link href={`/analysis/${p.analysis_id}`} className="text-[13px] text-accent">
                  {t("analysisPage.openAnalysis")} →
                </Link>
              )}
              {p.signal_id && (
                <Link href="/signals" className="text-[13px] text-accent">
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
