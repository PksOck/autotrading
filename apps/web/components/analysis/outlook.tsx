"use client";

import { useFormatter, useTranslations } from "next-intl";
import type { HorizonOutlook, OutlookEvidence } from "@/lib/api/types";
import { cn } from "@/lib/cn";

export type Horizon = HorizonOutlook["horizon"];
export type Verdict = HorizonOutlook["verdict"];
export const HORIZONS: Horizon[] = ["short", "medium", "long"];

const VERDICT_TONE: Record<Verdict, string> = {
  supports: "bg-pos-soft text-pos",
  mixed: "bg-surface-2 text-text-2",
  against: "bg-neg-soft text-neg",
  insufficient: "bg-warn-soft text-warn",
};
const VERDICT_MARK: Record<Verdict, string> = {
  supports: "▲",
  mixed: "◆",
  against: "▼",
  insufficient: "?",
};

/** Verdict of one horizon (ADR-0014); the mark keeps it readable without colour. */
export function VerdictChip({ verdict, size = "sm" }: { verdict: Verdict; size?: "sm" | "lg" }) {
  const t = useTranslations("analysisPage.verdict");
  return (
    <span
      data-testid="verdict-chip"
      data-verdict={verdict}
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium whitespace-nowrap",
        size === "lg" ? "h-7 px-3 text-[13px]" : "px-2 text-xs leading-5",
        VERDICT_TONE[verdict],
      )}
    >
      <span aria-hidden>{VERDICT_MARK[verdict]}</span>
      {t(verdict)}
    </span>
  );
}

const ACTION_TONE: Record<string, string> = {
  Buy: "bg-pos-soft text-pos",
  Overweight: "bg-pos-soft text-pos",
  Hold: "bg-surface-2 text-text",
  Underweight: "bg-neg-soft text-neg",
  Sell: "bg-neg-soft text-neg",
  REVIEW: "bg-warn-soft text-warn",
};

/** The agents' rating in plain words ("Zmanjšaj delež" instead of "Underweight"). */
export function ActionPill({
  rating,
  size = "sm",
}: {
  rating: string | null | undefined;
  size?: "sm" | "lg";
}) {
  const t = useTranslations("analysisPage.action");
  if (!rating) return null;
  const known = rating in ACTION_TONE;
  return (
    <span
      data-testid="action-pill"
      data-rating={rating}
      className={cn(
        "inline-flex items-center rounded-full font-semibold whitespace-nowrap",
        size === "lg" ? "h-9 px-4 text-[17px]" : "px-2 text-xs leading-5 font-medium",
        known ? ACTION_TONE[rating] : "bg-surface-2 text-text-2",
      )}
    >
      {known ? t(rating as "Buy") : rating}
    </span>
  );
}

const UNSIGNED = new Set(["quality.roe_pct", "quality.net_margin_pct", "volatility_atr"]);

/** Label and sentence for one piece of evidence. Values come from the API, only formatted here. */
export function useEvidenceText() {
  const t = useTranslations("analysisPage.evidence.keys");
  const format = useFormatter();
  const number = (key: string, unit: OutlookEvidence["unit"], v: number, signed: boolean) => {
    if (unit === "pct")
      return format.number(v / 100, {
        style: "percent",
        maximumFractionDigits: 1,
        signDisplay: signed ? "exceptZero" : "auto",
      });
    if (key === "rsi14") return format.number(v, { maximumFractionDigits: 0 });
    return format.number(v, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      signDisplay: signed ? "exceptZero" : "auto",
    });
  };
  const label = (key: string) => (t.has(`${key}.label`) ? t(`${key}.label` as "rsi14.label") : key);
  const text = (e: OutlookEvidence) => {
    const value =
      e.value == null
        ? "–"
        : number(
            e.key,
            e.unit,
            e.value,
            !UNSIGNED.has(e.key) && e.key !== "quality.debt_to_equity",
          );
    const reference = e.reference == null ? "" : number(e.key, e.unit, e.reference, false);
    return t.has(`${e.key}.text`)
      ? t(`${e.key}.text` as "rsi14.text", { value, reference, stance: e.stance })
      : value;
  };
  return { label, text };
}

export function useHorizonTitle() {
  const t = useTranslations("analysisPage.horizon");
  return (h: Horizon) => ({ title: t(h), span: t(`${h}Span`), column: t(`${h}Col`) });
}

/** Stacked bar of pro / neutral / contra counts; the counts are in the label for screen readers. */
export function StanceBar({
  outlook,
  label,
}: {
  outlook: Pick<HorizonOutlook, "pro" | "contra" | "neutral">;
  label: string;
}) {
  const total = outlook.pro + outlook.neutral + outlook.contra;
  const pct = (n: number) => `${total ? (n / total) * 100 : 0}%`;
  return (
    <div
      role="img"
      aria-label={label}
      className="flex h-2.5 overflow-hidden rounded-full bg-surface-2"
    >
      <span className="bg-pos" style={{ width: pct(outlook.pro) }} />
      <span className="bg-text-3/40" style={{ width: pct(outlook.neutral) }} />
      <span className="bg-neg" style={{ width: pct(outlook.contra) }} />
    </div>
  );
}
