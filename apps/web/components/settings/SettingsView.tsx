"use client";

import { useTranslations } from "next-intl";
import { PageHelp } from "@/components/common/PageHelp";
import { useSystemStatus } from "@/lib/api/hooks";
import { LocaleSwitch } from "@/components/shell/LocaleSwitch";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import type { ThemePreference } from "@/lib/theme";
import { EmailSettings } from "./EmailSettings";
import { AutomationSettings } from "./AutomationSettings";

export function SettingsView({ theme }: { theme: ThemePreference }) {
  const t = useTranslations("automation");
  const systemT = useTranslations("system");
  const status = useSystemStatus();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
      <header className="flex items-center gap-2">
        <h1 className="text-2xl font-semibold">{t("title")}</h1>
        <PageHelp pageKey="settings" title={t("title")} />
      </header>
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="text-lg font-medium">{t("appearance")}</h2>
        <div className="mt-3 flex items-center gap-4">
          <LocaleSwitch />
          <ThemeToggle initial={theme} />
        </div>
      </section>
      <AutomationSettings />
      <section className="space-y-3 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-lg font-medium">{t("connections")}</h2>
        <p className="text-sm text-text-2">{t("connectionHelp")}</p>
        {status.isError && <p role="alert">{t("requestError")}</p>}
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {status.data?.services.map((service) => (
            <div
              key={service.id}
              className="flex justify-between gap-3 rounded-md border border-border p-3 text-sm"
            >
              <span>{systemT(service.id)}</span>
              <span className={service.state === "up" ? "text-positive" : "text-text-2"}>
                {systemT(`state.${service.state}`)}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-text-2">{t("unsupportedConnections")}</p>
        <p className="text-xs text-text-2">{t("rolesHelp")}</p>
      </section>
      <EmailSettings />
    </div>
  );
}
