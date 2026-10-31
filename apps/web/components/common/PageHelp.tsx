"use client";

import { Dialog } from "radix-ui";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Icon } from "./Icon";
import { HELP_LINKS, type PageHelpKey } from "@/lib/page-help";
import { useBackToClose } from "@/lib/useBackToClose";

/** Editorial instructions are local content; opening help performs no data request. */
export function PageHelp({ pageKey, title }: { pageKey: PageHelpKey; title: string }) {
  const t = useTranslations("pageHelp");
  const labels = useTranslations("nav");
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const close = useBackToClose(open, () => setOpen(false));
  return (
    <Dialog.Root open={open} onOpenChange={(next) => (next ? setOpen(true) : close())}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label={t("open", { page: title })}
          title={t("open", { page: title })}
          className="inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded-full text-text-3 hover:bg-surface-2 hover:text-accent focus-visible:outline-2 focus-visible:outline-accent"
        >
          <Icon name="help" size={20} />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="card fixed inset-x-3 top-[5vh] z-[61] mx-auto max-h-[90dvh] max-w-xl overflow-y-auto p-5 shadow-float sm:inset-x-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <Dialog.Title className="text-xl font-semibold">
              {t("title", { page: title })}
            </Dialog.Title>
            <Dialog.Close className="min-h-12 shrink-0 rounded-md border border-border px-3 text-sm">
              {t("close")}
            </Dialog.Close>
          </div>
          <Dialog.Description className="mb-5 text-text-2">
            {t(`pages.${pageKey}.purpose`)}
          </Dialog.Description>
          <div className="space-y-5">
            {(["actions", "data", "limits"] as const).map((section) => (
              <section key={section}>
                <h2 className="mb-1 font-medium">{t(section)}</h2>
                <p className="text-sm leading-relaxed text-text-2">
                  {t(`pages.${pageKey}.${section}`)}
                </p>
              </section>
            ))}
            {HELP_LINKS[pageKey]?.length ? (
              <nav
                aria-label={t("links")}
                className="flex flex-wrap gap-2 border-t border-border pt-3"
              >
                {HELP_LINKS[pageKey]!.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={(event) => {
                      event.preventDefault();
                      close(() => router.push(link.href));
                    }}
                    className="inline-flex min-h-12 items-center rounded-md border border-border px-3 text-sm text-accent"
                  >
                    {labels(link.label)}
                  </a>
                ))}
              </nav>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
