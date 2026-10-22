"use client";

import { useFormatter, useTranslations } from "next-intl";
import type { Provenance } from "@/lib/api/types";
import { cn } from "@/lib/cn";

/** CMP-08: where a number comes from and how fresh it is (AGENTS.md §3.5). */
export function ProvenanceTag({ provenance, className }: { provenance?: Provenance | null; className?: string }) {
  const t = useTranslations("provenance");
  const format = useFormatter();
  if (!provenance) return null;
  const known = ["ibkr", "ibkr_flex", "yahoo", "stooq", "demo", "fake", "universe"].includes(provenance.source);
  const source = known ? t(`sources.${provenance.source}`) : provenance.source;
  return (
    <span className={cn("inline-flex flex-wrap items-center gap-1.5 text-xs text-text-3", className)}>
      <span>{source}</span>
      <span aria-hidden>·</span>
      <time dateTime={provenance.as_of}>{format.relativeTime(new Date(provenance.as_of), new Date())}</time>
      {provenance.stale && (
        <span className="rounded-full bg-warn-soft px-1.5 leading-5 font-medium text-warn">{t("stale")}</span>
      )}
      {provenance.source === "demo" && (
        <span className="rounded-full bg-warn-soft px-1.5 leading-5 font-medium text-warn">{t("demo")}</span>
      )}
    </span>
  );
}
