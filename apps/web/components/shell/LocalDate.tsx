"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useAppLocale } from "@/lib/use-app-locale";

/** Hydrate without a server timezone, then refresh at the next local midnight. */
export function LocalDate() {
  const t = useTranslations("pageHelp");
  const locale = useAppLocale();
  const [date, setDate] = useState<Date | null>(null);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const update = () => {
      clearTimeout(timer);
      const now = new Date();
      setDate(now);
      const next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
      timer = setTimeout(update, next.getTime() - now.getTime() + 50);
    };
    const visible = () => {
      if (!document.hidden) update();
    };
    update();
    document.addEventListener("visibilitychange", visible);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, []);
  const day = date
    ? [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0"),
      ].join("-")
    : undefined;
  return (
    <time aria-label={t("today")} dateTime={day} className="block text-xs text-text-3">
      {date
        ? new Intl.DateTimeFormat(locale, {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
          }).format(date)
        : "—"}
    </time>
  );
}
