import { Suspense, type ReactNode } from "react";
import { PeekPanel } from "@/components/common/PeekPanel";
import { ProposalComposer } from "@/components/proposals/ProposalComposer";
import { BottomNav } from "@/components/shell/BottomNav";
import { CommandPalette } from "@/components/shell/CommandPalette";
import { Header } from "@/components/shell/Header";
import { Shortcuts } from "@/components/shell/Shortcuts";
import { Sidebar } from "@/components/shell/Sidebar";
import type { ThemePreference } from "@/lib/theme";

/** CMP-01. Peek, palette and composer are global so every screen can open them. */
export function AppShell({ children, themePreference }: { children: ReactNode; themePreference: ThemePreference }) {
  return (
    <div className="flex min-h-dvh">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header themePreference={themePreference} />
        <main id="main" className="mx-auto w-full max-w-[1440px] flex-1 px-4 pt-6 pb-24 md:px-6 md:pb-10">
          {children}
        </main>
      </div>
      <BottomNav />
      <Suspense>
        <PeekPanel />
        <CommandPalette />
      </Suspense>
      <ProposalComposer />
      <Shortcuts />
    </div>
  );
}
