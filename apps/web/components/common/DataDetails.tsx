"use client";

import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { Icon } from "./Icon";

/** Native disclosure works on touch and keyboard; critical warnings stay outside. */
export function DataDetails({ children, label }: { children: ReactNode; label?: string }) {
  const t = useTranslations("pageHelp");
  const name = label ?? t("details");
  return (
    <details className="group min-w-0 max-w-full text-sm">
      <summary
        aria-label={name}
        title={name}
        className="flex min-h-12 min-w-12 cursor-pointer list-none items-center justify-center rounded-full text-text-3 hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-accent [&::-webkit-details-marker]:hidden"
      >
        <Icon name="info" size={18} />
        <span className="sr-only">{name}</span>
      </summary>
      <div className="max-w-xl space-y-2 rounded-md border border-border bg-surface p-3 text-xs leading-relaxed text-text-2">
        {children}
      </div>
    </details>
  );
}
