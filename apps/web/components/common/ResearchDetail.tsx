"use client";

import { Dialog } from "radix-ui";
import { useTranslations } from "next-intl";
import { useRef, useSyncExternalStore, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";

const subscribe = (callback: () => void) => {
  const query = window.matchMedia("(max-width: 1279px)");
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
};
const mobileSnapshot = () => window.matchMedia("(max-width: 1279px)").matches;

/** Exact selected details open immediately on touch screens, with dialog focus and Escape. */
export function ResearchDetail({
  open,
  close,
  title,
  children,
}: {
  open: boolean;
  close: () => void;
  title: string;
  children: ReactNode;
}) {
  const mobile = useSyncExternalStore(subscribe, mobileSnapshot, () => false);
  const peek = useSearchParams().get("peek");
  const t = useTranslations("researchUx");
  const trigger = useRef<HTMLElement | null>(null);
  if (!mobile)
    return (
      <aside
        className="card flex flex-col gap-4 p-5 lg:sticky lg:top-24 lg:self-start"
        aria-label={title}
      >
        {children}
      </aside>
    );
  return (
    <Dialog.Root
      open={open && !peek}
      onOpenChange={(next) => {
        if (!next) close();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Content
          className="card fixed inset-x-2 top-[4vh] bottom-[4vh] z-50 flex flex-col gap-4 overflow-y-auto p-5 shadow-float"
          onOpenAutoFocus={() => {
            trigger.current =
              document.activeElement instanceof HTMLElement ? document.activeElement : null;
          }}
          onCloseAutoFocus={(event) => {
            event.preventDefault();
            trigger.current?.focus();
          }}
        >
          <div className="flex items-center justify-between gap-3">
            <Dialog.Title className="font-semibold">{title}</Dialog.Title>
            <Dialog.Close className="min-h-12 rounded-md border border-border px-3">
              {t("close")}
            </Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">{title}</Dialog.Description>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
