"use client";

import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

type Props = {
  value: number;
  format: (value: number) => string;
  className?: string;
};

/**
 * CMP-24 / MO-04: counts to the new value and flashes the background in the
 * direction of the change. Screen readers get only the final value.
 */
export function AnimatedNumber({ value, format, className }: Props) {
  const reduceMotion = useReducedMotion();
  const spring = useSpring(value, { stiffness: 140, damping: 22 });
  const display = useTransform(spring, (v) => format(v));
  const [last, setLast] = useState(value);
  const [flash, setFlash] = useState<{ up: boolean; key: number } | null>(null);

  if (value !== last) {
    setFlash({ up: value > last, key: (flash?.key ?? 0) + 1 });
    setLast(value);
  }

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  if (reduceMotion) return <span className={cn("num", className)}>{format(value)}</span>;

  return (
    <span className={cn("relative -mx-0.5 inline-block rounded-sm px-0.5", className)}>
      {flash && (
        <motion.span
          key={flash.key}
          aria-hidden
          className="absolute inset-0 rounded-sm"
          style={{ background: flash.up ? "var(--pos-soft)" : "var(--neg-soft)" }}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ duration: 0.6 }}
        />
      )}
      <motion.span aria-hidden className="num relative">
        {display}
      </motion.span>
      <span className="sr-only">{format(value)}</span>
    </span>
  );
}
