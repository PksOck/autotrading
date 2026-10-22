"use client";

import { useTranslations } from "next-intl";
import { Icon } from "@/components/common/Icon";
import { openCommandPalette } from "@/components/shell/CommandPalette";
import { LocaleSwitch } from "@/components/shell/LocaleSwitch";
import { SystemStatus } from "@/components/shell/SystemStatus";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import type { ThemePreference } from "@/lib/theme";
import { openProposalComposer } from "@/stores/proposals";

export function Header({ themePreference }: { themePreference: ThemePreference }) {
  const t = useTranslations();

  return (
    <header className="sticky top-0 z-20 flex flex-wrap items-center gap-3 border-b border-border bg-surface/90 px-4 py-3 backdrop-blur md:px-6">
      <button
        type="button"
        onClick={openCommandPalette}
        className="flex h-10 min-w-0 flex-1 basis-56 items-center gap-2 rounded-md border border-border bg-surface-2 px-3 text-left text-text-3 hover:border-text-3"
      >
        <Icon name="search" size={16} />
        <span className="flex-1 truncate">{t("header.search")}</span>
        <kbd className="num text-xs">⌘K</kbd>
      </button>
      <SystemStatus />
      <button
        type="button"
        onClick={() => openProposalComposer()}
        className="inline-flex h-10 items-center gap-1.5 rounded-md bg-accent px-3.5 font-medium text-on-accent hover:opacity-90"
      >
        <Icon name="proposals" size={16} />
        {t("header.propose")}
      </button>
      <LocaleSwitch />
      <ThemeToggle initial={themePreference} />
    </header>
  );
}
