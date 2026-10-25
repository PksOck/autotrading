"use client";

import { scaleLinear } from "d3-scale";
import { motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import type { PulseEvent } from "@/lib/sample-data";
import { spring } from "@/lib/motion";
import { useElementSize } from "@/lib/use-element-size";
import { usePeek } from "@/lib/use-peek";
import { useFocusStore } from "@/stores/focus";

const ROW = 28;
const LABEL = 64;
const HOURS = 168;

const fill = (type: PulseEvent["type"]) =>
  type === "rumor" ? "var(--rumor-soft)" : type === "macro" ? "var(--warn)" : "var(--accent)";
const stroke = (type: PulseEvent["type"]) => (type === "rumor" ? "var(--rumor)" : "transparent");

/** CMP-26 / OV-02: events of the last 7 days, one row per symbol. */
export function PulseTimeline({ events }: { events: PulseEvent[] }) {
  const t = useTranslations();
  const reduceMotion = useReducedMotion();
  const [ref, { width }] = useElementSize<HTMLDivElement>();
  const { open } = usePeek();
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);

  const symbols = [
    ...new Set([...events].sort((a, b) => a.hoursAgo - b.hoursAgo).map((e) => e.symbol)),
  ];
  const height = symbols.length * ROW + 24;
  const x = scaleLinear()
    .domain([HOURS, 0])
    .range([LABEL, Math.max(LABEL + 1, width - 12)]);
  const newest = events.reduce((a, b) => (b.hoursAgo < a.hoursAgo ? b : a), events[0]!);

  return (
    <div ref={ref} className="w-full">
      <svg width={width} height={height} role="group" aria-label={t("overview.pulse")}>
        {[0, 1, 2, 3, 4, 5, 6, 7].map((day) => (
          <g key={day}>
            <line
              x1={x(day * 24)}
              x2={x(day * 24)}
              y1={0}
              y2={height - 20}
              stroke="var(--border)"
            />
            <text
              x={x(day * 24)}
              y={height - 6}
              textAnchor="middle"
              fontSize={11}
              fill="var(--text-3)"
            >
              {day === 0 ? "0" : `−${day}d`}
            </text>
          </g>
        ))}
        {symbols.map((symbol, row) => {
          const y = row * ROW + ROW / 2;
          const active = hovered === `instrument:${symbol}`;
          return (
            <g key={symbol}>
              {active && (
                <rect
                  x={0}
                  y={y - ROW / 2}
                  width={width}
                  height={ROW}
                  fill="var(--accent-soft)"
                  rx={4}
                />
              )}
              <text x={4} y={y + 4} fontSize={12} fontFamily="var(--font-mono)" fill="var(--text)">
                {symbol}
              </text>
            </g>
          );
        })}
        {width > 0 &&
          events.map((event, index) => {
            const row = symbols.indexOf(event.symbol);
            const cx = x(event.hoursAgo);
            const cy = row * ROW + ROW / 2;
            const r = 4 + event.score * 7;
            return (
              <g key={event.id}>
                {event.id === newest.id && !reduceMotion && (
                  <motion.circle
                    cx={cx}
                    cy={cy}
                    fill="none"
                    stroke="var(--accent)"
                    initial={{ r, opacity: 0.7 }}
                    animate={{ r: r + 14, opacity: 0 }}
                    transition={{ duration: 1.2, ease: "easeOut", delay: 0.6 }}
                  />
                )}
                <motion.circle
                  cx={cx}
                  cy={cy}
                  fill={fill(event.type)}
                  stroke={stroke(event.type)}
                  strokeDasharray={event.type === "rumor" ? "3 2" : undefined}
                  strokeWidth={1.5}
                  initial={{ r: 0 }}
                  animate={{ r }}
                  transition={{ ...spring.snappy, delay: reduceMotion ? 0 : index * 0.03 }}
                  tabIndex={0}
                  role="button"
                  aria-label={`${event.symbol}, ${t(`radar.score`)} ${event.score}`}
                  className="cursor-pointer focus:outline-none focus-visible:stroke-accent"
                  onClick={() => open({ kind: "instrument", id: event.symbol })}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      open({ kind: "instrument", id: event.symbol });
                  }}
                  onMouseEnter={() => setHovered(`instrument:${event.symbol}`)}
                  onMouseLeave={() => setHovered(null)}
                />
              </g>
            );
          })}
      </svg>
    </div>
  );
}
