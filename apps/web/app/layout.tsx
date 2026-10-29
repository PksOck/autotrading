import type { Metadata, Viewport } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages, getTranslations } from "next-intl/server";
import { cookies } from "next/headers";
import type { ReactNode } from "react";
import { Providers } from "@/components/providers";
import { AppShell } from "@/components/shell/AppShell";
import { THEME_COOKIE, isThemePreference } from "@/lib/theme";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#141920" },
  ],
};

export const metadata: Metadata = {
  title: { default: "Preža", template: "%s · Preža" },
  description: "Radar priložnosti za dolgoročne vlagatelje",
  robots: { index: false, follow: false },
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages();
  const t = await getTranslations("table");
  const stored = (await cookies()).get(THEME_COOKIE)?.value;
  const theme = isThemePreference(stored) ? stored : "system";

  return (
    <html
      lang={locale}
      data-theme={theme === "system" ? undefined : theme}
      suppressHydrationWarning
    >
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Providers>
            {process.env.PREZA_DEMO === "1" && (
              <div
                role="status"
                className="border-b border-warn bg-warn-soft px-4 py-2 text-center text-xs font-medium text-warn"
              >
                {t("demo")}
              </div>
            )}
            <AppShell themePreference={theme}>{children}</AppShell>
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
