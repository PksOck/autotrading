"use client";

import { motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import type { EntryOut } from "@/lib/api/types";
import { useFocusStore } from "@/stores/focus";
import { CAUSE_COLOR, type Cause } from "./CauseBadge";

const H_FULL = 260;
const H_COMPACT = 170;
const PAD = { l: 56, r: 16, t: 24, b: 28 };

/** Pushes overlapping points apart vertically so every symbol stays readable. */
function dodge<T extends { cx: number; cy: number; r: number }>(points: T[], H: number): T[] {
  const placed: T[] = [];
  for (const p of [...points].sort((a, b) => a.cx - b.cx)) {
    let cy = p.cy;
    for (let i = 0; i < 12; i++) {
      const hit = placed.find((q) => Math.hypot(q.cx - p.cx, q.cy - cy) < q.r + p.r + 14);
      if (!hit) break;
      cy = cy + (cy < H / 2 ? 1 : -1) * (hit.r + p.r + 16);
    }
    placed.push({ ...p, cy: Math.min(Math.max(cy, PAD.t + p.r), H - PAD.b - p.r) });
  }
  return placed;
}

/** OV-05: distance to the zone (x) against valuation (y); size = rules hit, colour = cause. */
export function EntryMap({
  entries,
  selected,
  onSelect,
  compact = false,
}: {
  entries: EntryOut[];
  selected?: string;
  onSelect: (symbol: string) => void;
  /** Overview variant: lower plot, no caption. */
  compact?: boolean;
}) {
  const H = compact ? H_COMPACT : H_FULL;
  const t = useTranslations("entriesPage.map");
  const reduceMotion = useReducedMotion();
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);
  const ref = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(640);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, Math.round(e!.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const withDistance = entries.filter((e) => e.distance_atr != null);
  const ds = withDistance.map((e) => Number(e.distance_atr));
  const X_MIN = Math.floor(Math.min(-1, ...ds));
  const X_MAX = Math.min(8, Math.ceil(Math.max(3, ...ds)));
  const x = (d: number) =>
    PAD.l + ((Math.min(Math.max(d, X_MIN), X_MAX) - X_MIN) / (X_MAX - X_MIN)) * (W - PAD.l - PAD.r);
  const y = (v: number) => PAD.t + (1 - v) * (H - PAD.t - PAD.b);
  const ticks = Array.from({ length: X_MAX - X_MIN + 1 }, (_, i) => X_MIN + i).filter(
    (d) => X_MAX - X_MIN <= 6 || d % 2 === 0,
  );
  const points = dodge(
    withDistance.map((e) => {
      const val = typeof e.valuation?.summary === "number" ? (e.valuation.summary as number) : null;
      return {
        e,
        val,
        cx: x(Number(e.distance_atr)),
        cy: y(val ?? 0.5),
        r: 6 + 3 * e.rules.length,
      };
    }),
    H,
  );
  return (
    <figure className="flex flex-col gap-2" ref={ref}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        className="max-w-full"
        role="img"
        aria-label={t("label")}
      >
        <rect
          x={x(X_MIN)}
          y={y(1)}
          width={x(0.5) - x(X_MIN)}
          height={y(0.5) - y(1)}
          fill="var(--pos-soft)"
          rx={6}
        />
        <text x={x(X_MIN) + 6} y={y(0.5) - 6} className="fill-[var(--pos)] text-[11px]">
          {t("target")}
        </text>
        {ticks.map((d) => (
          <g key={d}>
            <line
              x1={x(d)}
              x2={x(d)}
              y1={PAD.t}
              y2={H - PAD.b}
              stroke="var(--border)"
              strokeDasharray={d === 0 ? undefined : "2 4"}
            />
            <text
              x={x(d)}
              y={H - 10}
              textAnchor="middle"
              className="num fill-[var(--text-3)] text-[11px]"
            >
              {d}
            </text>
          </g>
        ))}
        <text
          x={W - PAD.r}
          y={PAD.t - 8}
          textAnchor="end"
          className="fill-[var(--text-3)] text-[11px]"
        >
          {t("x")}
        </text>
        <text x={4} y={y(1)} dominantBaseline="middle" className="fill-[var(--text-3)] text-[11px]">
          {t("cheap")}
        </text>
        <text x={4} y={y(0)} dominantBaseline="middle" className="fill-[var(--text-3)] text-[11px]">
          {t("rich")}
        </text>
        {points.map(({ e, val, cx, cy, r }, i) => {
          const color = CAUSE_COLOR[(e.cause ?? "unknown") as Cause];
          const focus = hovered === `instrument:${e.symbol}` || selected === e.symbol;
          return (
            <motion.g
              key={e.symbol}
              initial={reduceMotion ? false : { opacity: 0, scale: 0.4 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                delay: reduceMotion ? 0 : i * 0.03,
                type: "spring",
                stiffness: 260,
                damping: 22,
              }}
              style={{ transformOrigin: `${cx}px ${cy}px`, cursor: "pointer" }}
              onClick={() => onSelect(e.symbol)}
              onMouseEnter={() => setHovered(`instrument:${e.symbol}`)}
              onMouseLeave={() => setHovered(null)}
            >
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill={val == null ? "var(--surface)" : color}
                fillOpacity={val == null ? 1 : 0.25}
                stroke={color}
                strokeWidth={focus ? 3 : 1.5}
                strokeDasharray={val == null ? "3 2" : undefined}
              />
              <text
                x={cx + r + 4}
                y={cy}
                dominantBaseline="middle"
                className="num fill-[var(--text)] text-[11px] font-medium"
              >
                {e.symbol}
              </text>
            </motion.g>
          );
        })}
      </svg>
      {!compact && <figcaption className="text-xs text-text-3">{t("caption")}</figcaption>}
    </figure>
  );
}
