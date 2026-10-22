"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { Icon } from "@/components/common/Icon";
import { BrandMark } from "@/components/shell/Brand";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";
import { NAV, isActive } from "@/lib/nav";

/** CMP-01 side menu with a sliding active indicator (MO-02). Hidden below md (BottomNav). */
export function Sidebar() {
  const t = useTranslations();
  const pathname = usePathname();

  return (
    <nav
      aria-label={t("nav.mainLabel")}
      className="sticky top-0 hidden h-dvh w-[232px] shrink-0 flex-col gap-1 border-r border-border bg-surface px-3 py-5 md:flex"
    >
      <Link href="/" className="mb-4 flex items-center gap-2.5 px-3 text-text no-underline">
        <BrandMark />
        <span className="text-lg font-semibold tracking-tight">{t("app.name")}</span>
      </Link>
      <ul className="flex flex-col gap-0.5">
        {NAV.map((item) => {
          const active = isActive(item.href, pathname);
          return (
            <li key={item.href} className="relative">
              {active && (
                <motion.span
                  layoutId="nav-active"
                  transition={spring.snappy}
                  className="absolute inset-0 rounded-md bg-accent-soft"
                />
              )}
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-11 items-center gap-2.5 rounded-md px-3 text-text-2 no-underline transition-colors duration-[var(--dur-fast)] hover:text-text",
                  active && "font-medium text-accent hover:text-accent",
                )}
              >
                <Icon name={item.key} />
                <span className="flex-1">{t(`nav.${item.key}`)}</span>
                {item.milestone && (
                  <span className="num text-[11px] text-text-3" title={item.screen}>
                    {item.milestone}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-auto flex flex-col gap-3 px-3">
        <Link
          href="/ux"
          className={cn(
            "flex items-center gap-2 text-[13px] text-text-3 no-underline hover:text-text",
            pathname === "/ux" && "text-accent",
          )}
        >
          <Icon name="ux" size={16} />
          {t("nav.ux")}
        </Link>
        <p className="text-xs leading-[18px] text-text-3">{t("disclaimer")}</p>
      </div>
    </nav>
  );
}
