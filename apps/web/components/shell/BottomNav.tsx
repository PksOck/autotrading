"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { Icon } from "@/components/common/Icon";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";
import { NAV, isActive } from "@/lib/nav";
import { openCommandPalette } from "@/components/shell/CommandPalette";

/** Phone navigation (DESIGN.md §2.4): five main modules, the rest under "More" (⌘K). */
export function BottomNav() {
  const t = useTranslations();
  const pathname = usePathname();
  const main = NAV.filter((n) => n.main);

  return (
    <nav
      aria-label={t("nav.mainLabel")}
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-6 border-t border-border bg-surface pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      {main.map((item) => {
        const active = isActive(item.href, pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] text-text-2 no-underline",
              active && "text-accent",
            )}
          >
            {active && (
              <motion.span layoutId="bottom-active" transition={spring.snappy} className="absolute top-0 h-0.5 w-8 rounded-full bg-accent" />
            )}
            <Icon name={item.key} size={20} />
            {t(`nav.${item.key}`)}
          </Link>
        );
      })}
      <button
        type="button"
        onClick={openCommandPalette}
        className="flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] text-text-2"
      >
        <Icon name="more" size={20} />
        {t("nav.more")}
      </button>
    </nav>
  );
}
