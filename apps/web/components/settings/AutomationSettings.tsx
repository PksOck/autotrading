"use client";

import { useCallback, useId, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { ApiError } from "@/lib/api/client";
import {
  useAutomationPolicies,
  useAutomationControl,
  useSetAutomationControl,
  useAutomationExecutions,
  useSaveAutomationPolicy,
  type AutomationPolicy,
  type AutomationControl,
} from "@/lib/api/automation";
import { policyBody } from "@/lib/automation-form";
import { DataDetails } from "@/components/common/DataDetails";
import { AutomationBatchPanel } from "./AutomationBatchPanel";
import { ProcessPolicyEditor } from "./ProcessPolicyEditor";

const button = "min-h-12 rounded-md border border-border px-3 text-sm disabled:opacity-50";
const groups: Record<string, string> = {
  sync_flex: "data",
  refresh_bars: "data",
  fundamentals: "data",
  refresh_etf_profiles: "data",
  radar: "research",
  entries: "research",
  batch_analyses: "research",
  discover_thesis_reviews: "research",
  outcomes: "research",
  notify: "notifications",
  digest: "notifications",
};
const modelGated = new Set(["entries", "discover_thesis_reviews", "batch_analyses"]);

function Toggle({
  label,
  checked,
  disabled,
  onClick,
  describedBy,
}: {
  label: string;
  checked: boolean;
  disabled: boolean;
  onClick: () => void;
  describedBy?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={checked}
      aria-describedby={describedBy}
      disabled={disabled}
      onClick={onClick}
      className="flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded-md px-1 focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-50"
    >
      <span
        aria-hidden="true"
        className={`flex h-6 w-11 items-center rounded-full p-1 ${checked ? "bg-accent" : "bg-text-3"}`}
      >
        <span className={`h-4 w-4 rounded-full bg-surface ${checked ? "translate-x-5" : ""}`} />
      </span>
    </button>
  );
}

function ModuleRow({
  policy,
  control,
  editor,
  onDirtyChange,
  onEditorSaved,
  dirty,
  available,
  onEdit,
  onSaved,
  reload,
}: {
  policy: AutomationPolicy;
  control?: AutomationControl;
  editor: AutomationPolicy | null;
  onDirtyChange: (dirty: boolean) => void;
  onEditorSaved: (policy: AutomationPolicy) => void;
  dirty: boolean;
  available: boolean;
  onEdit: () => void;
  onSaved: (policy: AutomationPolicy) => void;
  reload: () => Promise<AutomationPolicy[]>;
}) {
  const t = useTranslations("automation");
  const ui = useTranslations("automationSimple");
  const save = useSaveAutomationPolicy(policy.process_key);
  const editing = Boolean(editor);
  const conflict = save.error instanceof ApiError && save.error.status === 409;
  const hintId = useId();
  const name = t(`processes.${policy.process_key}`);
  const state = !policy.enabled
    ? "off"
    : policy.schedule_kind === "manual"
      ? "manual"
      : !control
        ? "unavailable"
        : control.paused
          ? "paused"
          : modelGated.has(policy.process_key) && !control.automatic_analyses_enabled
            ? "modelOff"
            : "scheduled";
  return (
    <div
      className="space-y-2 border-t border-border py-2 first:border-0"
      data-testid={`module-${policy.process_key}`}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <div className="min-w-0 flex-1 basis-40">
          <h4 className="text-sm font-medium">{name}</h4>
          <p className="text-xs text-text-3">
            {t(`schedules.${policy.schedule_kind}`)}
            {policy.schedule_kind === "daily"
              ? ` · ${policy.local_time} · ${policy.timezone}`
              : policy.schedule_kind === "interval"
                ? ` · ${ui("minutes", { count: policy.interval_minutes ?? 60 })}`
                : ""}
          </p>
        </div>
        <span
          className={`text-xs ${state === "scheduled" ? "text-pos" : state === "off" || state === "manual" ? "text-text-3" : "text-warn"}`}
        >
          {ui(`states.${state}`)}
        </span>
        <Toggle
          label={ui("enableModule", { name })}
          checked={Boolean(policy.enabled)}
          disabled={save.isPending || conflict || !available || (editing && dirty)}
          describedBy={editing && dirty ? hintId : undefined}
          onClick={() =>
            save.mutate({ ...policyBody(policy), enabled: !policy.enabled }, { onSuccess: onSaved })
          }
        />
        <button
          type="button"
          className={button}
          aria-label={ui("editModule", { name })}
          aria-expanded={editing}
          disabled={dirty || save.isPending}
          onClick={onEdit}
        >
          {editing ? ui("closeEditor") : ui("edit")}
        </button>
      </div>
      {editing && dirty && (
        <p id={hintId} className="text-xs text-warn">
          {ui("draftHelp")}
        </p>
      )}
      {save.isPending && (
        <p role="status" className="text-xs">
          {t("pending")}
        </p>
      )}
      {save.error && (
        <div role="alert" className="flex flex-wrap items-center gap-2 text-sm text-neg">
          <p>
            {save.error instanceof ApiError && save.error.status === 409
              ? t("conflict")
              : t("requestError")}
          </p>
          <button
            type="button"
            className={button}
            aria-label={ui("reloadModule", { name })}
            onClick={async () => {
              try {
                await reload();
                save.reset();
              } catch {
                /* Keep the conflict and the last confirmed state. */
              }
            }}
          >
            {t("reload")}
          </button>
        </div>
      )}
      {editor && (
        <ProcessPolicyEditor
          key={`${editor.process_key}:${editor.revision}`}
          policy={editor}
          reload={reload}
          onDirtyChange={onDirtyChange}
          onSaved={onEditorSaved}
          locked={save.isPending || conflict}
        />
      )}
    </div>
  );
}

export function AutomationSettings() {
  const t = useTranslations("automation");
  const ui = useTranslations("automationSimple");
  const feedback = useTranslations("settingsFeedback");
  const locale = useLocale();
  const policies = useAutomationPolicies();
  const control = useAutomationControl();
  const change = useSetAutomationControl();
  const history = useAutomationExecutions();
  const [editing, setEditing] = useState<{
    policy: AutomationPolicy;
    dirty: boolean;
    token: number;
  } | null>(null);
  const nextEditorToken = useRef(0);
  const editorToken = editing?.token;
  const editor = editing?.policy ?? null;
  const dirty = editing?.dirty ?? false;
  const onDirty = useCallback(
    (value: boolean) =>
      setEditing((current) =>
        current !== null && current.token === editorToken && current.dirty !== value
          ? { ...current, dirty: value }
          : current,
      ),
    [editorToken],
  );
  const ready =
    !control.isError &&
    control.data &&
    typeof control.data.paused === "boolean" &&
    typeof control.data.automatic_analyses_enabled === "boolean";
  const saved = (policy: AutomationPolicy, token: number | undefined) => {
    setEditing((current) =>
      current !== null &&
      current.token === token &&
      current?.policy.process_key === policy.process_key &&
      (policy.revision ?? 0) >= (current.policy.revision ?? 0)
        ? { ...current, policy, dirty: false }
        : current,
    );
  };
  const reload = async () => {
    const result = await policies.refetch();
    if (result.isError) throw result.error;
    return result.data ?? [];
  };
  const controlConflict = change.error instanceof ApiError && change.error.status === 409;
  return (
    <section
      className="space-y-4 rounded-xl border border-border bg-surface p-4 sm:p-5"
      aria-label={t("processTitle")}
    >
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium">{t("processTitle")}</h2>
        <DataDetails compact label={ui("helpTitle")}>
          <p>{ui("moduleHelp")}</p>
          <p>{ui("statusHelp")}</p>
        </DataDetails>
      </div>
      <div className="rounded-lg border border-border bg-surface-2 px-3">
        <div className="flex items-center justify-between gap-3 py-2">
          <div>
            <h3 className="font-medium">{ui("all")}</h3>
            <p
              className={`text-xs ${!ready ? "text-warn" : control.data?.paused ? "text-warn" : "text-pos"}`}
            >
              {!ready
                ? ui("states.unavailable")
                : control.data?.paused
                  ? ui("allOff")
                  : ui("allOn")}
            </p>
          </div>
          <Toggle
            label={ui("all")}
            checked={Boolean(ready && !control.data?.paused)}
            disabled={!ready || change.isPending || controlConflict}
            onClick={() => {
              if (control.data) change.mutate({ ...control.data, paused: !control.data.paused });
            }}
          />
        </div>
        <p className="pb-3 text-xs text-text-2">{t("pauseHelp")}</p>
        <div className="flex items-center justify-between gap-3 border-t border-border py-2">
          <h3 className="text-sm">{feedback("analysisTitle")}</h3>
          <Toggle
            label={feedback("analysisEnabled")}
            checked={Boolean(ready && control.data?.automatic_analyses_enabled)}
            disabled={!ready || change.isPending || controlConflict}
            onClick={() => {
              if (control.data)
                change.mutate({
                  ...control.data,
                  automatic_analyses_enabled: !control.data.automatic_analyses_enabled,
                });
            }}
          />
        </div>
        <DataDetails compact label={feedback("analysisTitle")}>
          <p>{feedback("analysisHelp")}</p>
        </DataDetails>
      </div>
      {change.isSuccess && (
        <p role="status" className="text-xs">
          {feedback("controlSaved")}
        </p>
      )}
      {(control.isError || change.isError) && (
        <div role="alert" className="space-y-2 text-sm text-neg">
          <p>
            {change.error instanceof ApiError && change.error.status === 409
              ? t("conflict")
              : t("requestError")}
          </p>
          <button
            type="button"
            className={button}
            onClick={async () => {
              const result = await control.refetch();
              if (!result.isError) change.reset();
            }}
          >
            {ui("reloadControls")}
          </button>
        </div>
      )}
      {policies.isPending && <p role="status">{t("loading")}</p>}
      {policies.isError && (
        <p role="alert">
          {t("requestError")}{" "}
          <button type="button" className={button} onClick={() => void policies.refetch()}>
            {ui("reloadControls")}
          </button>
        </p>
      )}
      {(["data", "research", "notifications", "other"] as const).map((group) => {
        const rows = (policies.data ?? []).filter(
          (policy) => (groups[policy.process_key] ?? "other") === group,
        );
        if (!rows.length) return null;
        return (
          <section
            key={group}
            aria-label={ui(`groups.${group}`)}
            className="rounded-lg border border-border px-3"
          >
            <h3 className="pt-3 pb-1 text-xs font-semibold text-text-2">{ui(`groups.${group}`)}</h3>
            {rows.map((policy) => (
              <div key={policy.process_key}>
                <ModuleRow
                  policy={policy}
                  control={ready ? control.data : undefined}
                  available={!policies.isError}
                  editor={editor?.process_key === policy.process_key ? editor : null}
                  onDirtyChange={onDirty}
                  onEditorSaved={(value) => saved(value, editorToken)}
                  dirty={dirty}
                  reload={reload}
                  onEdit={() => {
                    const token = ++nextEditorToken.current;
                    setEditing((current) =>
                      current?.policy.process_key === policy.process_key
                        ? null
                        : { policy, dirty: false, token },
                    );
                  }}
                  onSaved={(value) => {
                    setEditing((current) =>
                      current !== null &&
                      current.token === editorToken &&
                      current?.policy.process_key === value.process_key &&
                      !current.dirty &&
                      (value.revision ?? 0) >= (current.policy.revision ?? 0)
                        ? { ...current, policy: value, dirty: false }
                        : current,
                    );
                  }}
                />
              </div>
            ))}
          </section>
        );
      })}
      <details className="rounded-lg border border-border p-3">
        <summary className="min-h-12 cursor-pointer content-center font-medium">
          {feedback("batchTitle")}
        </summary>
        <AutomationBatchPanel />
      </details>
      <details className="space-y-3 rounded-lg border border-border p-3">
        <summary className="min-h-12 cursor-pointer content-center font-medium">
          {t("history")}
        </summary>
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
      </details>
    </section>
  );
}
