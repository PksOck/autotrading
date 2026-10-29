"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { ApiError } from "@/lib/api/client";
import { useSystemStatus } from "@/lib/api/hooks";
import {
  useAutomationPolicies,
  useAutomationControl,
  useSetAutomationControl,
  useAutomationExecutions,
  useSaveAutomationPolicy,
  useRunProcess,
  type AutomationPolicy,
} from "@/lib/api/automation";
import { policyBody } from "@/lib/automation-form";
import { LocaleSwitch } from "@/components/shell/LocaleSwitch";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import type { ThemePreference } from "@/lib/theme";
import { AutomationBatchPanel } from "./AutomationBatchPanel";

const field = "min-h-12 w-full rounded-md border border-border bg-surface px-3 text-text";
const button = "min-h-12 rounded-md border border-border px-4 disabled:opacity-50";

function ProcessCard({
  policy,
  reload,
}: {
  policy: AutomationPolicy;
  reload: () => Promise<AutomationPolicy[]>;
}) {
  const t = useTranslations("automation");
  const locale = useLocale();
  const [draft, setDraft] = useState(policy);
  const [outside, setOutside] = useState(false);
  const [baseline, setBaseline] = useState(policy);
  const save = useSaveAutomationPolicy(policy.process_key);
  const run = useRunProcess(policy.process_key);
  const dirty = JSON.stringify(policyBody(draft)) !== JSON.stringify(policyBody(baseline));
  const pending = save.isPending || run.isPending;
  const conflict = save.error instanceof ApiError && save.error.status === 409;
  const patch = <K extends keyof AutomationPolicy>(key: K, value: AutomationPolicy[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));
  async function discard() {
    const fresh = (await reload()).find((item) => item.process_key === policy.process_key);
    if (fresh) {
      setDraft(fresh);
      setBaseline(fresh);
      save.reset();
    }
  }
  return (
    <article className="space-y-4 rounded-xl border border-border bg-surface p-5">
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
        <label className="grid gap-1 text-sm">
          {t("timezone")}
          <input
            className={field}
            value={draft.timezone}
            onChange={(e) => patch("timezone", e.target.value)}
            spellCheck={false}
          />
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
      <div className="flex flex-wrap gap-2">
        <button
          className={button + " bg-accent text-on-accent"}
          type="button"
          disabled={!dirty || pending}
          onClick={() =>
            save.mutate(policyBody(draft), {
              onSuccess: (saved) => {
                setDraft(saved);
                setBaseline(saved);
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
      {save.error && (
        <p role="alert" className="text-sm text-neg">
          {conflict ? t("conflict") : t("invalidPolicy")}
        </p>
      )}
      {!dirty && (
        <div className="space-y-2 border-t border-border pt-3">
          <label className="flex min-h-12 items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={outside}
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
        </div>
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
    </article>
  );
}

export function SettingsView({ theme }: { theme: ThemePreference }) {
  const t = useTranslations("automation");
  const systemT = useTranslations("system");
  const locale = useLocale();
  const policies = useAutomationPolicies();
  const control = useAutomationControl();
  const pause = useSetAutomationControl();
  const history = useAutomationExecutions();
  const status = useSystemStatus();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
      <header>
        <h1 className="text-2xl font-semibold">{t("title")}</h1>
        <p className="mt-2 max-w-3xl text-sm text-text-2">{t("help")}</p>
      </header>
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="text-lg font-medium">{t("appearance")}</h2>
        <div className="mt-3 flex items-center gap-4">
          <LocaleSwitch />
          <ThemeToggle initial={theme} />
        </div>
      </section>
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
      <section className="space-y-3 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-lg font-medium">{t("globalControl")}</h2>
        <p className="text-sm text-text-2">{t("pauseHelp")}</p>
        {control.data && (
          <button
            className={button}
            type="button"
            disabled={pause.isPending}
            onClick={() =>
              pause.mutate({ revision: control.data.revision, paused: !control.data.paused })
            }
          >
            {pause.isPending ? t("pending") : control.data.paused ? t("resume") : t("pause")}
          </button>
        )}
        {(control.isError || pause.isError) && (
          <p role="alert" className="text-sm text-neg">
            {pause.error instanceof ApiError && pause.error.status === 409
              ? t("conflict")
              : t("requestError")}
          </p>
        )}
      </section>
      <h2 className="text-lg font-medium">{t("processTitle")}</h2>
      {policies.isPending && <p role="status">{t("loading")}</p>}
      {policies.isError && <p role="alert">{t("requestError")}</p>}
      <div className="grid items-start gap-4 xl:grid-cols-2">
        {policies.data?.map((policy) => (
          <ProcessCard
            key={policy.process_key}
            policy={policy}
            reload={async () => (await policies.refetch()).data ?? []}
          />
        ))}
      </div>
      <AutomationBatchPanel />
      <section className="space-y-3 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-lg font-medium">{t("history")}</h2>
        {history.isError && <p role="alert">{t("requestError")}</p>}
        {history.data?.length === 0 && <p className="text-sm text-text-2">{t("noExecutions")}</p>}
        <ul className="space-y-2">
          {history.data?.slice(0, 20).map((execution) => (
            <li
              key={execution.id}
              className="flex flex-wrap justify-between gap-2 border-b border-border py-3 text-sm"
            >
              <span>
                {t(`processes.${execution.process_key}`)} ·{" "}
                {new Date(execution.scheduled_for).toLocaleString(locale)}
              </span>
              <span>
                {t(`executionStates.${execution.state}`)}
                {execution.reason ? ` · ${t(`executionReasons.${execution.reason}`)}` : ""}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
