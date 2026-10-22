"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";

export type Cause = "market" | "sector" | "transient" | "fundamental" | "unknown";

export const CAUSE_COLOR: Record<Cause, string> = {
  market: "var(--accent)",
  sector: "var(--warn)",
  transient: "var(--pos)",
  fundamental: "var(--neg)",
  unknown: "var(--text-3)",
};

const STYLE: Record<Cause, string> = {
  market: "bg-accent-soft text-accent",
  sector: "bg-warn-soft text-warn",
  transient: "bg-pos-soft text-pos",
  fundamental: "bg-neg-soft text-neg",
  unknown: "bg-surface-2 text-text-3",
};

/** CMP-10: why the price fell, as judged by dip_analyst (interpretation, not a number). */
export function CauseBadge({
  cause,
  className,
}: {
  cause: string | null | undefined;
  className?: string;
}) {
  const t = useTranslations("entry.cause");
  const key = (cause ?? "unknown") as Cause;
  if (!cause) return <span className={cn("text-xs text-text-3", className)}>{t("pending")}</span>;
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 text-xs leading-5 font-medium",
        STYLE[key],
        className,
      )}
    >
      {t(key)}
    </span>
  );
}
