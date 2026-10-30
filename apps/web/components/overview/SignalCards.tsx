"use client";

import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { EntityLink } from "@/components/common/EntityLink";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";
import { spring } from "@/lib/motion";
import type { SampleSignal } from "@/lib/sample-data";
import { useAppLocale } from "@/lib/use-app-locale";
import { openProposalComposer } from "@/stores/proposals";
import { toast } from "sonner";

const KIND = {
  entry: "bg-accent-soft text-accent",
  catalyst: "bg-pos-soft text-pos",
  rumor: "bg-rumor-soft text-rumor",
} as const;

/** CMP-03 on Overview. Cards expand in place (MO-01) and dismiss with undo (MO-10). */
export function SignalCards({ signals }: { signals: SampleSignal[] }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const [expanded, setExpanded] = useState<string | null>(null);
  const [hidden, setHidden] = useState<string[]>([]);

  const dismiss = (signal: SampleSignal) => {
    setHidden((h) => [...h, signal.id]);
    toast(t("ux.dismissed"), {
      action: {
        label: t("proposal.undo"),
        onClick: () => setHidden((h) => h.filter((id) => id !== signal.id)),
      },
    });
  };

  return (
    <LayoutGroup>
      <ul className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {signals
            .filter((s) => !hidden.includes(s.id))
            .map((signal) => {
              const open = expanded === signal.id;
              const kindLabel =
                signal.kind === "rumor" ? t("radar.rumor") : t(`signal.kind.${signal.kind}`);
              return (
                <motion.li
                  key={signal.id}
                  layout
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0, marginBottom: -12 }}
                  transition={spring.soft}
                  className={cn(
                    "card overflow-hidden p-4",
                    signal.kind === "rumor" && "border-dashed border-rumor",
                  )}
                >
                  <motion.div layout="position" className="flex flex-wrap items-center gap-2">
                    <span
                      className={cn(
                        "rounded-full px-2 text-xs leading-5 font-medium",
                        KIND[signal.kind],
                      )}
                    >
                      {kindLabel}
                    </span>
                    <EntityLink
                      entity={{ kind: "instrument", id: signal.symbol }}
                      className="text-base"
                    />
                    <span className="ml-auto flex items-center gap-2 text-xs text-text-3">
                      {t("signal.strength")}
                      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2">
                        <motion.span
                          className="block h-1.5 origin-left rounded-full bg-accent"
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: signal.strength }}
                          transition={spring.soft}
                        />
                      </span>
                      <span className="num text-text">
                        {formatNumber(locale, signal.strength, 2)}
                      </span>
                    </span>
                  </motion.div>
                  <motion.p layout="position" className="mt-2 text-text-2">
                    {signal.why[locale]}
                  </motion.p>
                  <AnimatePresence initial={false}>
                    {open && (
                      <motion.p
                        key="detail"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={spring.soft}
                        className="overflow-hidden text-[13px] text-text-2"
                      >
                        <span className="mt-2 block rounded-md bg-surface-2 p-3">
                          {signal.detail[locale]}
                        </span>
                      </motion.p>
                    )}
                  </AnimatePresence>
                  <motion.div
                    layout="position"
                    className="mt-3 flex flex-wrap items-center gap-2 text-[13px]"
                  >
                    <span className="text-text-3">{signal.source[locale]}</span>
                    <span className="ml-auto flex flex-wrap gap-2">
                      <button
                        type="button"
                        aria-expanded={open}
                        onClick={() => setExpanded(open ? null : signal.id)}
                        className="h-9 rounded-md px-3 text-text-2 hover:bg-surface-2"
                      >
                        {open ? t("ux.collapse") : t("ux.expand")}
                      </button>
                      <button
                        type="button"
                        onClick={() => openProposalComposer({ symbols: [signal.symbol] })}
                        className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2"
                      >
                        {t("action.analyze")}
                      </button>
                      <button
                        type="button"
                        onClick={() => dismiss(signal)}
                        className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2"
                      >
                        {t("action.dismiss")}
                      </button>
                    </span>
                  </motion.div>
                </motion.li>
              );
            })}
        </AnimatePresence>
      </ul>
    </LayoutGroup>
  );
}
