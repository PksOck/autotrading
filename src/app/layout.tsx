import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppFooter } from "@/components/layout/app-footer";
import { AppHeader } from "@/components/layout/app-header";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Northstar Research — transparent stock research",
    template: "%s · Northstar Research",
  },
  description:
    "Research stocks with context: market snapshots, financial trends, DCF scenarios, and source plus freshness on every figure.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AppHeader />
        {children}
        <AppFooter />
      </body>
    </html>
  );
}
