"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { ApiError } from "@/lib/api/client";
import {
  useSaveAutomationPolicy,
  useRunProcess,
  type AutomationPolicy,
} from "@/lib/api/automation";
import { policyBody } from "@/lib/automation-form";

const field = "min-h-12 w-full rounded-md border border-border bg-surface px-3 text-text";
const button = "min-h-12 rounded-md border border-border px-4 disabled:opacity-50";

export function ProcessPolicyEditor({
  policy,
  reload,
  onDirtyChange,
  onSaved,
  locked = false,
}: {
  policy: AutomationPolicy;
  reload: () => Promise<AutomationPolicy[]>;
  onDirtyChange: (dirty: boolean) => void;
  onSaved: (policy: AutomationPolicy) => void;
  locked?: boolean;
}) {
  const t = useTranslations("automation");
  const feedback = useTranslations("settingsFeedback");
  const locale = useLocale();
  const [draft, setDraft] = useState(policy);
  const [outside, setOutside] = useState(false);
  const [baseline, setBaseline] = useState(policy);
  const save = useSaveAutomationPolicy(policy.process_key);
  const run = useRunProcess(policy.process_key);
  const dirty = JSON.stringify(policyBody(draft)) !== JSON.stringify(policyBody(baseline));
  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);
  const ui = useTranslations("automationSimple");
  const [reloadFailed, setReloadFailed] = useState(false);
  const [reloading, setReloading] = useState(false);
  const pending = save.isPending || run.isPending || locked || reloading;
  const conflict = save.error instanceof ApiError && save.error.status === 409;
  const patch = <K extends keyof AutomationPolicy>(key: K, value: AutomationPolicy[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));
  async function discard() {
    setReloading(true);
    try {
      const fresh = (await reload()).find((item) => item.process_key === policy.process_key);
      if (!fresh) {
        setReloadFailed(true);
        return;
      }
      setDraft(fresh);
      setBaseline(fresh);
      save.reset();
      setReloadFailed(false);
      onSaved(fresh);
    } catch {
      setReloadFailed(true);
    } finally {
      setReloading(false);
    }
  }
  return (
    <section
      aria-label={t(`processes.${policy.process_key}`)}
      className="space-y-4 rounded-xl border border-accent bg-surface p-4"
    >
      <p className="text-sm text-text-2">{feedback(`processHelp.${policy.process_key}`)}</p>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-medium">{t(`processes.${policy.process_key}`)}</h3>
          <p className="mt-1 text-xs text-text-2">
            {t("revision", { revision: draft.revision ?? 0 })} · {dirty ? t("dirty") : t("saved")}
          </p>
        </div>
        <label className="flex min-h-12 items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.enabled}
            disabled={pending}
            onChange={(e) => patch("enabled", e.target.checked)}
          />
          {t("enabled")}
        </label>
      </div>
      <fieldset disabled={pending} className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-1 text-sm">
          {t("schedule")}
          <select
            aria-label={t("schedule")}
            className={field}
            value={draft.schedule_kind}
            onChange={(e) =>
              patch("schedule_kind", e.target.value as AutomationPolicy["schedule_kind"])
            }
          >
            {(["legacy", "manual", "daily", "interval"] as const)
              .filter((kind) => kind !== "legacy" || policy.process_key !== "batch_analyses")
              .map((kind) => (
                <option key={kind} value={kind}>
                  {t(`schedules.${kind}`)}
                </option>
              ))}
          </select>
        </label>
        {draft.schedule_kind === "daily" && (
          <label className="grid gap-1 text-sm">
            {t("localTime")}
            <input
              type="time"
              className={field}
              value={draft.local_time}
              onChange={(e) => patch("local_time", e.target.value)}
            />
          </label>
        )}
        {draft.schedule_kind === "interval" && (
          <label className="grid gap-1 text-sm">
            {t("interval")}
            <input
              type="number"
              min="5"
              max="10080"
              className={field}
              value={draft.interval_minutes}
              onChange={(e) => patch("interval_minutes", Number(e.target.value))}
            />
          </label>
        )}
        {policy.process_key === "batch_analyses" && (
          <>
            <label className="grid gap-1 text-sm">
              {t("cap")}
              <input
                type="number"
                min="1"
                max="100"
                className={field}
                value={draft.cap}
                onChange={(e) => patch("cap", Number(e.target.value))}
              />
            </label>
            <label className="grid gap-1 text-sm">
              {t("scope")}
              <select
                className={field}
                value={draft.scope}
                onChange={(e) => patch("scope", e.target.value as AutomationPolicy["scope"])}
              >
                {(["portfolio", "watchlist", "both"] as const).map((scope) => (
                  <option key={scope} value={scope}>
                    {t(`scopes.${scope}`)}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
      </fieldset>
      <details className="rounded-lg border border-border p-3">
        <summary className="min-h-12 cursor-pointer content-center font-medium">
          {ui("advanced")}
        </summary>
        <fieldset disabled={pending} className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-1 text-sm">
            {t("timezone")}
            <input
              className={field}
              value={draft.timezone}
              onChange={(e) => patch("timezone", e.target.value)}
              spellCheck={false}
            />
          </label>
          <label className="grid gap-1 text-sm">
            {t("windowStart")}
            <input
              type="time"
              className={field}
              value={draft.window_start ?? ""}
              onChange={(e) => patch("window_start", e.target.value || null)}
            />
          </label>
          <label className="grid gap-1 text-sm">
            {t("windowEnd")}
            <input
              type="time"
              className={field}
              value={draft.window_end ?? ""}
              onChange={(e) => patch("window_end", e.target.value || null)}
            />
          </label>
        </fieldset>
        <fieldset disabled={pending} className="flex flex-wrap gap-2">
          <legend className="mb-1 text-sm">{t("weekdays")}</legend>
          {Array.from({ length: 7 }, (_, day) => (
            <label
              key={day}
              className="flex min-h-12 items-center gap-2 rounded-md border border-border px-3 text-sm"
            >
              <input
                type="checkbox"
                checked={draft.weekdays?.includes(day) ?? false}
                onChange={(e) =>
                  patch(
                    "weekdays",
                    e.target.checked
                      ? [...(draft.weekdays ?? []), day].sort()
                      : draft.weekdays?.filter((value) => value !== day),
                  )
                }
              />
              {t(`days.${day}`)}
            </label>
          ))}
        </fieldset>
        <p className="text-xs text-text-2">{t("windowHelp")}</p>
      </details>
      <div className="flex flex-wrap gap-2">
        <button
          className={button + " bg-accent text-on-accent"}
          type="button"
          disabled={!dirty || pending || conflict}
          onClick={() =>
            save.mutate(policyBody(draft), {
              onSuccess: (saved) => {
                setDraft(saved);
                setBaseline(saved);
                onSaved(saved);
              },
            })
          }
        >
          {save.isPending ? t("pending") : t("save")}
        </button>
        <button
          className={button}
          type="button"
          disabled={pending}
          onClick={() => {
            void discard();
          }}
        >
          {conflict ? t("reload") : t("discard")}
        </button>
      </div>
      {reloadFailed && (
        <p role="alert" className="text-sm text-neg">
          {t("requestError")}
        </p>
      )}
      {save.error && (
        <p role="alert" className="text-sm text-neg">
          {conflict ? t("conflict") : t("invalidPolicy")}
        </p>
      )}
      {!dirty && (
        <details className="space-y-2 border-t border-border pt-3">
          <summary className="min-h-12 cursor-pointer content-center text-sm">
            {ui("manualRun")}
          </summary>
          <label className="flex min-h-12 items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={outside}
              disabled={pending}
              onChange={(e) => setOutside(e.target.checked)}
            />
            {t("outsideWindow")}
          </label>
          <button
            className={button}
            type="button"
            disabled={pending || !draft.enabled}
            onClick={() => run.mutate({ revision: draft.revision ?? 0, outside_window: outside })}
          >
            {t("runNow")}
          </button>
          {run.error && (
            <p role="alert" className="text-sm text-neg">
              {t("runError")}
            </p>
          )}
          {run.isSuccess && (
            <p aria-live="polite" className="text-sm">
              {t("queued")}
            </p>
          )}
        </details>
      )}
      {!!policy.next_runs?.length && (
        <p className="text-xs text-text-2">
          {t("nextRuns")}:{" "}
          {policy.next_runs
            .slice(0, 3)
            .map((date) => new Date(date).toLocaleString(locale))
            .join(" · ")}
        </p>
      )}
    </section>
  );
}
