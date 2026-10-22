import { useTranslations } from "next-intl";
import type { ThesisState } from "@/lib/sample-data";

const STYLE: Record<Exclude<ThesisState, "none">, { icon: string; className: string }> = {
  holds: { icon: "✓", className: "text-pos" },
  weakening: { icon: "!", className: "text-warn" },
  broken: { icon: "✕", className: "text-neg" },
};

/** CMP-11 compact form. */
export function ThesisBadge({ state }: { state: ThesisState }) {
  const t = useTranslations("thesis");
  if (state === "none") return <span className="text-text-3">—</span>;
  const { icon, className } = STYLE[state];
  return (
    <span className={className}>
      <span aria-hidden className="num mr-1 font-medium">
        {icon}
      </span>
      {t(state === "weakening" ? "weakening" : state)}
    </span>
  );
}
