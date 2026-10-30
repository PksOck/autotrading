"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { computeTreemap } from "@/components/overview/treemap-layout";
import { cn } from "@/lib/cn";
import { formatChange } from "@/lib/format";
import { spring } from "@/lib/motion";
import type { ThesisState } from "@/lib/sample-data";
import { useAppLocale } from "@/lib/use-app-locale";
import { useElementSize } from "@/lib/use-element-size";
import { usePeek } from "@/lib/use-peek";
import { useFocusStore } from "@/stores/focus";

/** Intensity of the daily-change tint, capped so text keeps its contrast. */
const tint = (change: number) => Math.min(Math.abs(change) / 3, 1) * 32 + 6;

export type TreemapItem = {
  symbol: string;
  weight: number;
  change: number | null;
  thesis: ThesisState;
};

/** CMP-25 / OV-01: portfolio treemap. Area = weight, tint = daily change, border = thesis. */
export function Treemap({ items, height = 280 }: { items: TreemapItem[]; height?: number }) {
  const t = useTranslations();
  const locale = useAppLocale();
  const [ref, size] = useElementSize<HTMLDivElement>();
  const { open } = usePeek();
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);
  const tiles = computeTreemap(items, size.width, height);

  return (
    <div ref={ref} className="relative w-full" style={{ height }}>
      {tiles.map(({ item, x, y, width, height: h }) => {
        const key = `instrument:${item.symbol}`;
        const color =
          item.change === null || item.change === 0
            ? "var(--text-3)"
            : item.change > 0
              ? "var(--pos)"
              : "var(--neg)";
        const changeLabel =
          item.change === null
            ? t("overviewFeedback.notAvailable")
            : formatChange(locale, item.change);
        const small = width < 72 || h < 48;
        return (
          <motion.button
            key={item.symbol}
            layout
            transition={spring.soft}
            type="button"
            onClick={() => open({ kind: "instrument", id: item.symbol })}
            onMouseEnter={() => setHovered(key)}
            onMouseLeave={() => setHovered(null)}
            onFocus={() => setHovered(key)}
            onBlur={() => setHovered(null)}
            aria-label={`${item.symbol}, ${changeLabel}`}
            className={cn(
              "absolute flex flex-col items-start justify-between overflow-hidden rounded-md p-2 text-left transition-shadow duration-[var(--dur-fast)]",
              item.thesis === "broken" && "outline-2 -outline-offset-2 outline-neg outline-dashed",
              item.thesis === "weakening" && "outline-2 -outline-offset-2 outline-warn",
              hovered === key && "ring-2 ring-accent ring-offset-2 ring-offset-bg",
            )}
            style={{
              left: x,
              top: y,
              width,
              height: h,
              background: `color-mix(in oklab, ${color} ${tint(item.change ?? 0)}%, var(--surface))`,
            }}
          >
            <span className="num text-[13px] leading-4 font-medium">{item.symbol}</span>
            {!small && (
              <span className="num text-xs leading-4 text-text-2">
                {item.change === null ? "—" : changeLabel}
              </span>
            )}
          </motion.button>
        );
      })}
      {size.width > 0 && tiles.length === 0 && <p className="text-text-3">{t("state.empty")}</p>}
    </div>
  );
}
