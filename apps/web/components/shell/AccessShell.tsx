"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { ThemePreference } from "@/lib/theme";
import { PUBLIC_PAGES } from "@/lib/access";
import { AppShell } from "./AppShell";
import { SupportingLinks } from "./SupportingLinks";
import { SessionGuard } from "./SessionGuard";

export function AccessShell({
  children,
  themePreference,
}: {
  children: ReactNode;
  themePreference: ThemePreference;
}) {
  return PUBLIC_PAGES.has(usePathname()) ? (
    <div className="flex flex-1 flex-col">
      <main className="mx-auto w-full max-w-2xl flex-1 px-5 py-12">{children}</main>
      <SupportingLinks />
    </div>
  ) : (
    <SessionGuard>
      <AppShell themePreference={themePreference}>{children}</AppShell>
    </SessionGuard>
  );
}
