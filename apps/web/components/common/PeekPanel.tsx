"use client";

import Link from "next/link";
import { useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { Dialog } from "radix-ui";
import { InstrumentPreview } from "@/components/common/InstrumentPreview";
import { WatchButton } from "@/components/watchlist/WatchButton";
import { SignalDetail } from "@/components/signals/SignalDetail";
import { spring } from "@/lib/motion";
import { usePeek } from "@/lib/use-peek";
import { openProposalComposer } from "@/stores/proposals";

/** CMP-21 / LX-02: side panel that keeps the current screen in place. */
export function PeekPanel() {
  const t = useTranslations();
  const { current, close } = usePeek();
  const open = current !== null;
  const returnFocus = useRef<HTMLElement | null>(null);

  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && close()} modal={false}>
      <AnimatePresence>
        {current && (
          <Dialog.Portal forceMount>
            <Dialog.Content
              forceMount
              asChild
              onInteractOutside={(event) => event.preventDefault()}
              onOpenAutoFocus={() => {
                const active = document.activeElement;
                if (active instanceof HTMLElement && !active.closest('[role="dialog"]')) {
                  returnFocus.current = active;
                }
              }}
              onCloseAutoFocus={(event) => {
                if (returnFocus.current?.isConnected) {
                  event.preventDefault();
                  returnFocus.current.focus({ preventScroll: true });
                }
              }}
              aria-describedby={undefined}
            >
              <motion.aside
                key={`${current.kind}:${current.id}`}
                initial={{ x: "100%", opacity: 0.6 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "100%", opacity: 0.6 }}
                transition={spring.soft}
                className="fixed top-0 right-0 z-40 flex h-dvh w-full flex-col gap-5 overflow-y-auto overscroll-contain border-l border-border bg-surface p-6 shadow-float sm:w-[420px]"
              >
                <div className="flex items-center justify-between gap-2">
                  <Dialog.Title className="label">{t("peek.label")}</Dialog.Title>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      onClick={close}
                      className="h-9 rounded-md px-3 text-[13px] text-text-2 hover:bg-surface-2"
                    >
                      ← {t("peek.back")}
                    </button>
                    <Dialog.Close
                      aria-label={t("peek.close")}
                      className="grid h-9 w-9 place-items-center rounded-md text-text-2 hover:bg-surface-2"
                    >
                      ✕
                    </Dialog.Close>
                  </div>
                </div>

                {current.kind === "instrument" ? (
                  <InstrumentPreview symbol={current.id} size="lg" />
                ) : current.kind === "signal" ? (
                  <SignalDetail signalId={current.id} />
                ) : (
                  <p className="text-text-3">{t("peek.notFound")}</p>
                )}

                {current.kind === "instrument" && (
                  <div className="mt-auto flex flex-wrap gap-2">
                    <WatchButton symbol={current.id} />
                    <button
                      type="button"
                      onClick={() => openProposalComposer({ symbols: [current.id] })}
                      className="inline-flex h-10 items-center rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90"
                    >
                      {t("action.analyze")}
                    </button>
                    <Link
                      href={`/i/${current.id}`}
                      className="inline-flex h-10 items-center rounded-md border border-border px-4 font-medium hover:bg-surface-2"
                    >
                      {t("peek.open")}
                    </Link>
                  </div>
                )}
              </motion.aside>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  );
}
