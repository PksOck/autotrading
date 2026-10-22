"use client";

import { motion } from "motion/react";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { setLocale } from "@/app/actions";
import { LOCALES } from "@/i18n/config";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";

export function LocaleSwitch() {
  const t = useTranslations("locale");
  const locale = useLocale();
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <div role="group" aria-label={t("label")} className="flex gap-0.5 rounded-md bg-surface-2 p-0.5">
      {LOCALES.map((option) => {
        const active = option === locale;
        return (
          <button
            key={option}
            type="button"
            aria-pressed={active}
            title={t(option)}
            disabled={pending}
            onClick={() =>
              startTransition(async () => {
                await setLocale(option);
                router.refresh();
              })
            }
            className={cn(
              "relative h-9 min-w-11 rounded-[5px] px-2 text-[13px] font-medium uppercase text-text-2",
              active && "text-text",
            )}
          >
            {active && (
              <motion.span
                layoutId="locale-pill"
                transition={spring.snappy}
                className="absolute inset-0 rounded-[5px] bg-surface shadow-[0_0_0_1px_var(--border)]"
              />
            )}
            <span className="relative">{option}</span>
          </button>
        );
      })}
    </div>
  );
}
