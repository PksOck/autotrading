"use client";

import { useTranslations } from "next-intl";
import type { ClaimStatus } from "@/lib/api/types";

const styles = {
  open: { icon: "○", tone: "text-text-2" },
  confirmed: { icon: "✓", tone: "text-pos" },
  weakening: { icon: "!", tone: "text-warn" },
  broken: { icon: "✕", tone: "text-neg" },
  expired: { icon: "◷", tone: "text-text-3" },
} satisfies Record<ClaimStatus, { icon: string; tone: string }>;

/** CMP-11: text and shape carry the status independently of colour. */
export function ThesisCheck({ status }: { status: ClaimStatus }) {
  const t = useTranslations("thesis");
  const { icon, tone } = styles[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[13px] font-medium ${tone}`}
      data-status={status}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{t(`status.${status}`)}</span>
    </span>
  );
}
