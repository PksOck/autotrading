"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import { useSyncExternalStore } from "react";
import { EntityLink } from "@/components/common/EntityLink";
import { listItem } from "@/lib/motion";
import { openProposalComposer, useProposals } from "@/stores/proposals";

export function ProposalList() {
  const t = useTranslations();
  const format = useFormatter();
  const items = useProposals((s) => s.items);
  const remove = useProposals((s) => s.remove);
  // The store is restored from localStorage after hydration; render nothing on the server.
  const hydrated = useSyncExternalStore(
    (onChange) => useProposals.persist.onFinishHydration(onChange),
    () => useProposals.persist.hasHydrated(),
    () => false,
  );

  if (!hydrated) return null;

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
      {items.length === 0 && <p className="card p-6 text-text-3">{t("proposal.listEmpty")}</p>}
      <ul className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {items.map((p) => (
            <motion.li key={p.id} layout {...listItem} className="card flex flex-col gap-2 p-4">
              <div className="flex flex-wrap items-center gap-2">
                {p.symbols.map((s) => (
                  <EntityLink key={s} entity={{ kind: "instrument", id: s }} />
                ))}
                <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">
                  {t(`proposal.depth.${p.depth}`)}
                </span>
                <span className="rounded-full bg-warn-soft px-2 text-xs leading-5 text-warn">
                  {t(`proposal.status.${p.status}`)}
                </span>
                <span className="ml-auto text-xs text-text-3">
                  {format.relativeTime(new Date(p.createdAt), new Date())}
                </span>
              </div>
              {p.hypothesis && <p className="text-text-2">{p.hypothesis}</p>}
              <div>
                <button type="button" onClick={() => remove(p.id)} className="h-9 rounded-md px-3 text-[13px] text-text-2 hover:bg-surface-2">
                  {t("action.dismiss")}
                </button>
              </div>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </section>
  );
}
