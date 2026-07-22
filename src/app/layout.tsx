import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppFooter } from "@/components/layout/app-footer";
import { AppHeader } from "@/components/layout/app-header";

import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Research",
  description: "Fixture-backed stock research with transparent data context.",
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
