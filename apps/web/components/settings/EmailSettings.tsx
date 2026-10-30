"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import {
  useEmailPreferences,
  useSaveEmailPreferences,
  type EmailPreferences,
} from "@/lib/api/email";

function EmailForm({ initial }: { initial: EmailPreferences }) {
  const t = useTranslations("settingsFeedback.email");
  const [addresses, setAddresses] = useState(initial.recipients?.join("\n") ?? "");
  const [enabled, setEnabled] = useState(initial.enabled ?? false);
  const [kinds, setKinds] = useState(initial.kinds ?? ["signals"]);
  const save = useSaveEmailPreferences();
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate({
          revision: initial.revision,
          enabled,
          recipients: addresses
            .split(/[\n,;]/)
            .map((value) => value.trim())
            .filter(Boolean),
          kinds,
        });
      }}
    >
      <p role="status" className="text-sm">
        {initial.configured ? t("configured") : t("unconfigured")}
      </p>
      <p className="text-sm text-text-2">
        {t("deliveryStatus", {
          queued: initial.queued_deliveries ?? 0,
          sent: initial.sent_deliveries ?? 0,
        })}
      </p>
      {!!initial.uncertain_deliveries && (
        <p role="status" className="text-sm text-neg">
          {t("uncertain", { count: initial.uncertain_deliveries })}
        </p>
      )}
      <label className="flex min-h-12 items-center gap-2">
        <input
          type="checkbox"
          checked={enabled}
          disabled={!initial.configured || save.isPending}
          onChange={(event) => setEnabled(event.target.checked)}
        />
        {t("enabled")}
      </label>
      <label className="grid gap-2 text-sm">
        {t("recipients")}
        <textarea
          className="min-h-28 rounded-md border border-border bg-surface p-3"
          value={addresses}
          onChange={(event) => setAddresses(event.target.value)}
          disabled={save.isPending}
        />{" "}
        <span className="text-text-2">{t("recipientsHelp")}</span>
      </label>
      <fieldset className="space-y-2">
        <legend>{t("kinds")}</legend>
        {(["signals", "daily_digest", "analysis_complete"] as const).map((kind) => (
          <label key={kind} className="flex min-h-12 items-center gap-2">
            <input
              type="checkbox"
              checked={kinds.includes(kind)}
              disabled={save.isPending}
              onChange={(event) =>
                setKinds(
                  event.target.checked ? [...kinds, kind] : kinds.filter((item) => item !== kind),
                )
              }
            />
            {t(kind)}
          </label>
        ))}
      </fieldset>
      <p className="text-xs text-text-2">{t("security")}</p>
      <button
        className="min-h-12 rounded-md border border-border px-4 disabled:opacity-50"
        disabled={save.isPending}
      >
        {save.isPending ? t("saving") : t("save")}
      </button>
      {save.isError && (
        <p role="alert" className="text-sm text-neg">
          {t("error")}
        </p>
      )}
      {save.isSuccess && (
        <p role="status" className="text-sm">
          {t("saved")}
        </p>
      )}
    </form>
  );
}

export function EmailSettings() {
  const t = useTranslations("settingsFeedback.email");
  const preferences = useEmailPreferences();
  return (
    <details className="rounded-xl border border-border bg-surface p-5">
      <summary className="min-h-12 cursor-pointer text-lg font-medium">{t("title")}</summary>
      <div className="pt-3">
        {preferences.data && (
          <EmailForm key={preferences.data.revision} initial={preferences.data} />
        )}
        {preferences.isError && <p role="alert">{t("loadError")}</p>}
        {preferences.isPending && <p role="status">{t("loading")}</p>}
      </div>
    </details>
  );
}
