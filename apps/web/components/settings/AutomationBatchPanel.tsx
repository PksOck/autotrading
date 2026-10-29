"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useBatchPreview, useRunBatch, type AutomationBatchInput } from "@/lib/api/automation";
import { batchReason } from "@/lib/automation-form";

export function AutomationBatchPanel({ accountId }: { accountId?: string }) {
  const t = useTranslations("automation");
  const locale = useLocale();
  const [scope, setScope] = useState<"portfolio" | "watchlist" | "both">("portfolio");
  const [cap, setCap] = useState(5);
  const [outside, setOutside] = useState(false);
  const preview = useBatchPreview();
  const run = useRunBatch();
  const body: AutomationBatchInput = {
    scope,
    cap,
    account_id: accountId ?? null,
    outside_window: outside,
  };
  const result = run.data ?? preview.data;
  const pending = preview.isPending || run.isPending;
  const error = preview.error || run.error;
  function change() {
    preview.reset();
    run.reset();
  }
  return (
    <section className="space-y-4 rounded-xl border border-border bg-surface p-5">
      <div>
        <h2 className="text-lg font-medium">{t("batchTitle")}</h2>
        <p className="mt-1 text-sm text-text-2">{t("batchHelp")}</p>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <label className="grid gap-1 text-sm">
          {t("scope")}
          <select
            className="min-h-12 rounded-md border border-border bg-surface px-3"
            value={scope}
            disabled={pending}
            onChange={(e) => {
              setScope(e.target.value as typeof scope);
              change();
            }}
          >
            {(["portfolio", "watchlist", "both"] as const).map((value) => (
              <option key={value} value={value}>
                {t(`scopes.${value}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          {t("cap")}
          <input
            className="min-h-12 w-24 rounded-md border border-border bg-surface px-3"
            type="number"
            min="1"
            max="100"
            value={cap}
            disabled={pending}
            onChange={(e) => {
              setCap(Number(e.target.value));
              change();
            }}
          />
        </label>
        <button
          type="button"
          className="min-h-12 rounded-md border border-border px-4"
          disabled={pending || cap < 1 || cap > 100}
          onClick={() => preview.mutate(body)}
        >
          {t("preview")}
        </button>
        <button
          type="button"
          className="min-h-12 rounded-md bg-accent px-4 text-on-accent disabled:opacity-50"
          disabled={
            pending || !preview.data?.items.some((item) => item.reason === "ready") || !!run.data
          }
          onClick={() => run.mutate({ ...body, revision: preview.data?.policy_revision })}
        >
          {pending ? t("pending") : t("runBatch")}
        </button>
      </div>
      <label className="flex min-h-12 items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={outside}
          onChange={(e) => {
            setOutside(e.target.checked);
            change();
          }}
        />
        {t("outsideWindow")}
      </label>
      {result?.blocked_reason === "disabled" && (
        <p className="text-sm text-text-2">{t("enableBatch")}</p>
      )}
      {error && (
        <p role="alert" className="text-sm text-neg">
          {t("requestError")}
        </p>
      )}
      {result && (
        <div aria-live="polite" className="space-y-3 text-sm">
          <p>
            {t("quota", { used: result.quota_used, limit: result.quota_limit || t("unlimited") })} ·{" "}
            {t("reset", { time: new Date(result.resets_at).toLocaleString(locale) })}
          </p>
          {result.items.length === 0 ? (
            <p className="text-text-2">{t("emptyBatch")}</p>
          ) : (
            <ul className="grid gap-2 sm:grid-cols-2">
              {result.items.map((item) => (
                <li
                  key={item.instrument_id}
                  className="flex justify-between rounded-md border border-border p-3"
                >
                  <Link
                    href={`/i/${encodeURIComponent(item.symbol)}`}
                    className="font-mono hover:underline"
                  >
                    {item.symbol}
                  </Link>
                  <span className="text-text-2">{t(`reasons.${batchReason(item.reason)}`)}</span>
                </li>
              ))}
            </ul>
          )}
          {run.data && <p>{t("accepted", { count: run.data.run_ids?.length ?? 0 })}</p>}
        </div>
      )}
    </section>
  );
}
