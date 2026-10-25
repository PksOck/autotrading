"use client";

import { SegmentedButtons } from "@/components/common/SegmentedButtons";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { setLocale } from "@/app/actions";
import { LOCALES } from "@/i18n/config";

export function LocaleSwitch() {
  const t = useTranslations("locale");
  const locale = useLocale();
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <SegmentedButtons
      semantics="pressed"
      compact
      label={t("label")}
      value={locale}
      disabled={pending}
      options={LOCALES.map((option) => ({
        value: option,
        label: option.toUpperCase(),
        title: t(option),
      }))}
      onChange={(option) =>
        startTransition(async () => {
          await setLocale(option);
          router.refresh();
        })
      }
    />
  );
}
