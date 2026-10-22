"use client";

import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Icon } from "@/components/common/Icon";
import { duration } from "@/lib/motion";
import {
  THEME_EVENT,
  nextThemePreference,
  setThemePreference,
  type ThemePreference,
} from "@/lib/theme";

/** Cycles system → light → dark. The icon morphs between states (MO pattern, 200 ms). */
export function ThemeToggle({ initial }: { initial: ThemePreference }) {
  const t = useTranslations("theme");
  const [preference, setPreference] = useState(initial);

  useEffect(() => {
    const onChange = (event: Event) => setPreference((event as CustomEvent<ThemePreference>).detail);
    window.addEventListener(THEME_EVENT, onChange);
    return () => window.removeEventListener(THEME_EVENT, onChange);
  }, []);

  const icon = preference === "dark" ? "moon" : preference === "light" ? "sun" : "system";

  return (
    <button
      type="button"
      onClick={() => setThemePreference(nextThemePreference(preference))}
      aria-label={`${t("toggle")}: ${t(preference)}`}
      title={`${t("label")}: ${t(preference)}`}
      className="grid h-11 w-11 place-items-center overflow-hidden rounded-md border border-border bg-surface text-text-2 hover:bg-surface-2"
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={icon}
          initial={{ opacity: 0, rotate: -60, scale: 0.7 }}
          animate={{ opacity: 1, rotate: 0, scale: 1 }}
          exit={{ opacity: 0, rotate: 60, scale: 0.7 }}
          transition={{ duration: duration.base }}
        >
          <Icon name={icon} />
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
