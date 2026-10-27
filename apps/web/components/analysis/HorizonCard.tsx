"use client";

import { useTranslations } from "next-intl";
import {
  StanceBar,
  VerdictChip,
  useEvidenceText,
  useHorizonTitle,
} from "@/components/analysis/outlook";
import type { HorizonOutlook } from "@/lib/api/types";
import { cn } from "@/lib/cn";

/** CMP-31: one horizon of the outlook (ADR-0014). Clicking it selects that horizon's evidence. */
export function HorizonCard({
  outlook,
  selected,
  onSelect,
}: {
  outlook: HorizonOutlook;
  selected?: boolean;
  onSelect?: () => void;
}) {
  const t = useTranslations("analysisPage");
  const { label, text } = useEvidenceText();
  const { title, span } = useHorizonTitle()(outlook.horizon);
  const pro = outlook.evidence.filter((e) => e.stance === "pro").slice(0, 2);
  const contra = outlook.evidence.filter((e) => e.stance === "contra").slice(0, 2);

  return (
    <button
      type="button"
      data-testid={`horizon-${outlook.horizon}`}
      aria-pressed={selected}
      aria-label={t("outlook.show", { title })}
      onClick={onSelect}
      className={cn(
        "touch-target flex min-w-0 flex-col gap-2.5 rounded-lg border bg-surface p-3.5 text-left transition-colors duration-[var(--dur-fast)] hover:border-text-3",
        selected ? "border-accent" : "border-border",
      )}
    >
      <span className="flex flex-wrap items-baseline justify-between gap-x-2">
        <span className="text-[15px] font-semibold text-text">{title}</span>
        <span className="text-xs text-text-3">{span}</span>
      </span>
      <VerdictChip verdict={outlook.verdict} size="lg" />
      <StanceBar
        outlook={outlook}
        label={t("outlook.barLabel", {
          title,
          pro: outlook.pro,
          neutral: outlook.neutral,
          contra: outlook.contra,
        })}
      />
      <span className="num flex gap-3 text-xs text-text-2" aria-hidden>
        <span className="text-pos">▲ {outlook.pro}</span>
        <span>◆ {outlook.neutral}</span>
        <span className="text-neg">▼ {outlook.contra}</span>
      </span>
      {(pro.length > 0 || contra.length > 0) && (
        <ul className="flex flex-col gap-1 text-[13px] leading-5">
          {pro.map((e) => (
            <li key={e.key} className="flex gap-1.5 text-text-2">
              <span aria-hidden className="text-pos">
                ▲
              </span>
              <span className="min-w-0">
                <span className="text-text">{label(e.key)}</span> · {text(e)}
              </span>
            </li>
          ))}
          {contra.map((e) => (
            <li key={e.key} className="flex gap-1.5 text-text-2">
              <span aria-hidden className="text-neg">
                ▼
              </span>
              <span className="min-w-0">
                <span className="text-text">{label(e.key)}</span> · {text(e)}
              </span>
            </li>
          ))}
        </ul>
      )}
      {outlook.missing.length > 0 && (
        <span className="text-xs text-text-3">
          {t("outlook.missing", { items: outlook.missing.map(label).join(", ") })}
        </span>
      )}
    </button>
  );
}
