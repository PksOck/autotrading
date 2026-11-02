"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { version } from "@/package.json";

export function SupportingLinks() {
  const t = useTranslations("supporting");
  return (
    <nav
      aria-label={t("links")}
      className="flex flex-wrap justify-center gap-x-5 gap-y-1 border-t border-border px-4 py-3 text-xs text-text-3"
    >
      {(["about", "privacy", "terms", "security"] as const).map((key) => (
        <Link key={key} href={`/${key}`} className="inline-flex min-h-8 items-center">
          {t(`${key}.title`)}
        </Link>
      ))}
      <a
        href={`https://github.com/PksOck/autotrading/releases/tag/v${version}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex min-h-8 items-center"
        aria-label={t("version", { version })}
      >
        v{version}
      </a>
    </nav>
  );
}
