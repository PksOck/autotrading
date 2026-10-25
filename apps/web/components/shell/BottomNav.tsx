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

/** Phone navigation: four main modules and More for all other destinations. */
export function BottomNav() {
  const t = useTranslations();
  const pathname = usePathname();
  const main = NAV.filter((n) => n.main);
  const moreActive = !main.some((item) => isActive(item.href, pathname));

  return (
    <nav
      aria-label={t("nav.mainLabel")}
      className="fixed inset-x-0 bottom-0 z-30 grid h-[calc(64px+env(safe-area-inset-bottom))] grid-cols-5 border-t border-border bg-surface pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      {main.map((item) => {
        const active = isActive(item.href, pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative flex h-full flex-col items-center justify-center gap-0.5 text-[11px] text-text-2 no-underline",
              active && "text-text font-medium",
            )}
          >
            <span className="relative grid h-8 w-16 place-items-center">
              {active && (
                <motion.span
                  layoutId="bottom-active"
                  transition={spring.snappy}
                  className="absolute inset-0 rounded-full bg-accent-soft"
                />
              )}
              <span className="relative">
                <Icon name={item.key} size={20} />
              </span>
            </span>
            {t(`nav.${item.key}`)}
          </Link>
        );
      })}
      <button
        type="button"
        onClick={openCommandPalette}
        aria-current={moreActive ? "page" : undefined}
        className={cn(
          "flex h-full flex-col items-center justify-center gap-0.5 text-[11px] text-text-2",
          moreActive && "text-text font-medium",
        )}
      >
        <span className="relative grid h-8 w-16 place-items-center">
          {moreActive && (
            <motion.span
              layoutId="bottom-active"
              transition={spring.snappy}
              className="absolute inset-0 rounded-full bg-accent-soft"
            />
          )}
          <span className="relative">
            <Icon name="more" size={20} />
          </span>
        </span>
        {t("nav.more")}
      </button>
    </nav>
  );
}
