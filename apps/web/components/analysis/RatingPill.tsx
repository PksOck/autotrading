import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";

const TONE: Record<string, string> = {
  Buy: "bg-pos-soft text-pos",
  Overweight: "bg-pos-soft text-pos",
  Hold: "bg-surface-2 text-text-2",
  Underweight: "bg-neg-soft text-neg",
  Sell: "bg-neg-soft text-neg",
  REVIEW: "bg-warn-soft text-warn",
};
const KNOWN = new Set(Object.keys(TONE));

/** CMP-06: the agents' rating on the five-step scale (VOICE.md §4), or "Potreben pregled". */
export function RatingPill({ rating, size = "sm", className }: { rating: string | null; size?: "sm" | "lg"; className?: string }) {
  const t = useTranslations("analysisPage.rating");
  if (!rating) return null;
  const known = KNOWN.has(rating);
  return (
    <span
      data-testid="rating-pill"
      className={cn(
        "inline-flex items-center rounded-full font-medium whitespace-nowrap",
        size === "lg" ? "h-8 px-3.5 text-[15px]" : "px-2 text-xs leading-5",
        known ? TONE[rating] : "bg-surface-2 text-text-2",
        className,
      )}
    >
      {known ? t(rating) : rating}
    </span>
  );
}
