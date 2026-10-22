"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";
import { useAppLocale } from "@/lib/use-app-locale";

/** Picks the machine translation for the UI locale and marks it (BL-055, VOICE §7). */
export function useTranslatedText(original: string | null | undefined, translations?: Record<string, string> | null) {
  const locale = useAppLocale();
  const translated = translations?.[locale];
  return translated ? { text: translated, translated: true } : { text: original ?? "", translated: false };
}

export function TranslatedText({
  original,
  translations,
  className,
}: {
  original: string | null | undefined;
  translations?: Record<string, string> | null;
  className?: string;
}) {
  const t = useTranslations("provenance");
  const { text, translated } = useTranslatedText(original, translations);
  return (
    <span className={className}>
      {text}
      {translated && (
        <span
          title={t("translatedTitle", { original: original ?? "" })}
          className={cn("ml-1.5 inline-block rounded-full bg-surface-2 px-1.5 align-middle text-[11px] leading-5 text-text-3")}
        >
          {t("translated")}
        </span>
      )}
    </span>
  );
}
