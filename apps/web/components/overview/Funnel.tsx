"use client";

import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { formatNumber } from "@/lib/format";
import { ease } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";

type Stage = { key: string; value: number };

/** CMP-27 / OV-03: how much noise the system filters. Bars use a log scale. */
export function Funnel({ stages }: { stages: readonly Stage[] }) {
  const t = useTranslations("funnel");
  const locale = useAppLocale();
  const max = Math.log10(Math.max(...stages.map((s) => s.value), 10));

  return (
    <ol className="flex flex-col gap-2.5">
      {stages.map((stage, index) => (
        <li key={stage.key} className="grid grid-cols-[110px_1fr_64px] items-center gap-3 text-[13px]">
          <span className="text-text-2">{t(stage.key)}</span>
          <span className="h-2 overflow-hidden rounded-full bg-surface-2">
            <motion.span
              className="block h-2 origin-left rounded-full bg-accent"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: Math.log10(Math.max(stage.value, 1)) / max }}
              transition={{ duration: 0.7, delay: index * 0.08, ease: ease.standard }}
            />
          </span>
          <AnimatedNumber value={stage.value} format={(v) => formatNumber(locale, Math.round(v))} className="text-right" />
        </li>
      ))}
    </ol>
  );
}
