"use client";

import { scaleLinear } from "d3-scale";
import { line } from "d3-shape";
import { motion } from "motion/react";
import { duration, ease } from "@/lib/motion";

type Props = {
  values: number[];
  width?: number;
  height?: number;
  color?: string;
};

/** CMP-29 / OV-07: 30-day trend, drawn once on mount. Decorative: data is shown as text nearby. */
export function Sparkline({ values, width = 80, height = 24, color }: Props) {
  if (values.length < 2) return null;
  const x = scaleLinear()
    .domain([0, values.length - 1])
    .range([1, width - 1]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const y = scaleLinear()
    .domain([min, max === min ? min + 1 : max])
    .range([height - 2, 2]);
  const path = line()(values.map((v, i) => [x(i), y(v)] as [number, number])) ?? "";
  const rising = values[values.length - 1]! >= values[0]!;
  const stroke = color ?? (rising ? "var(--pos)" : "var(--neg)");

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden>
      <motion.path
        d={path}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: duration.slow * 2, ease: ease.standard }}
      />
    </svg>
  );
}
