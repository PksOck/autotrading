"use client";

import { useState } from "react";
import { useFormatter, useTranslations } from "next-intl";
import { useBacktest, type BacktestRequest } from "@/lib/api/backtest";
import { formatChange, formatNumber, formatShare } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";
import { cn } from "@/lib/cn";

export function BacktestPanel() {
  const t = useTranslations("backtestFeedback");
  const common = useTranslations();
  const locale = useAppLocale();
  const format = useFormatter();
  const [source, setSource] = useState<"all" | "signal" | "analysis">("all");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [horizon, setHorizon] = useState<1 | 5 | 20 | 60>(20);
  const [cost, setCost] = useState("10");
  const [strength, setStrength] = useState("0");
  const [status, setStatus] = useState<NonNullable<BacktestRequest["signal_status"]>>("all");
  const [limit, setLimit] = useState(1000);
  const calculation = useBacktest();
  const data = calculation.data;
  const inputClass =
    "mt-1 min-h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-text";
  const number = (value: string | number | null | undefined) =>
    value == null ? "—" : formatNumber(locale, Number(value), 2);
  const price = (value: string | number | null | undefined) =>
    value == null ? "—" : formatNumber(locale, Number(value), 6);
  const change = (value: string | number | null | undefined) =>
    value == null ? "—" : formatChange(locale, Number(value));
  return (
    <section className="card space-y-4 p-5">
      <h2 className="text-xl font-semibold">{t("title")}</h2>
      <p className="text-sm text-text-2">{t("intro")}</p>
      <p className="text-xs text-text-3">{t("method")}</p>
      <form
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
        onSubmit={(event) => {
          event.preventDefault();
          calculation.mutate({
            source,
            available_from: from || null,
            available_to: to || null,
            horizon_sessions: horizon,
            cost_bps: cost,
            min_strength: strength,
            signal_status: status,
            limit,
          });
        }}
      >
        <label className="text-xs text-text-2">
          {t("source")}
          <select
            className={inputClass}
            value={source}
            onChange={(e) => setSource(e.target.value as typeof source)}
          >
            {(["all", "signal", "analysis"] as const).map((item) => (
              <option key={item} value={item}>
                {t(item)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-text-2">
          {t("from")}
          <input
            className={inputClass}
            type="date"
            value={from}
            max={to || undefined}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label className="text-xs text-text-2">
          {t("to")}
          <input
            className={inputClass}
            type="date"
            value={to}
            min={from || undefined}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
        <label className="text-xs text-text-2">
          {t("horizon")}
          <select
            className={inputClass}
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value) as typeof horizon)}
          >
            {([1, 5, 20, 60] as const).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-text-2">
          {t("cost")}
          <input
            required
            className={inputClass}
            type="number"
            min={0}
            max={1000}
            step="0.1"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
          />
        </label>
        <label className="text-xs text-text-2">
          {t("strength")}
          <input
            required
            className={inputClass}
            type="number"
            min={0}
            max={1}
            step="0.01"
            disabled={source === "analysis"}
            value={strength}
            onChange={(e) => setStrength(e.target.value)}
          />
        </label>
        <label className="text-xs text-text-2">
          {t("status")}
          <select
            className={inputClass}
            disabled={source === "analysis"}
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <option value="all">{t("allStatus")}</option>
            {(["new", "watching", "accepted", "dismissed", "expired"] as const).map((item) => (
              <option key={item} value={item}>
                {common(`signal.status.${item}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-text-2">
          {t("limit")}
          <input
            required
            className={inputClass}
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          />
        </label>
        <p className="text-xs text-text-3 sm:col-span-2 lg:col-span-4">{t("signalFilters")}</p>
        <button
          type="submit"
          disabled={calculation.isPending}
          className="min-h-11 rounded-md bg-accent px-4 font-medium text-white disabled:opacity-50 sm:col-span-2 lg:col-span-4"
        >
          {t(calculation.isPending ? "calculating" : "calculate")}
        </button>
      </form>
      {calculation.error && (
        <p role="alert" className="text-warn">
          {common("table.loadFailed")}
        </p>
      )}
      {data && (
        <div className="space-y-3" aria-live="polite">
          <p className="text-sm font-medium">
            {t("summary", {
              completed: data.completed,
              skipped: data.skipped,
              evaluated: data.evaluated,
              total: data.total_matching,
            })}
          </p>
          <p className="text-xs text-text-3">
            {t("parameterScope")} · {t("horizon")}: {data.parameters.horizon_sessions} · {t("cost")}
            : {number(data.parameters.cost_bps)}
            {" · "}
            {t(data.parameters.source ?? "all")} · {data.parameters.available_from ?? "—"} –{" "}
            {data.parameters.available_to ?? "—"}
            {" · "}
            {t("strength")}: {number(data.parameters.min_strength)} · {t("status")}:{" "}
            {data.parameters.signal_status && data.parameters.signal_status !== "all"
              ? common(`signal.status.${data.parameters.signal_status}`)
              : t("allStatus")}
          </p>
          {data.truncated && (
            <p role="status" className="rounded bg-warn-soft p-3 text-sm text-warn">
              {t("truncated")}
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md bg-surface-2 p-3">
              <p className="label">{t("mean")}</p>
              <p
                className={cn(
                  "num text-xl",
                  data.mean_net_return_pct == null
                    ? "text-text-3"
                    : Number(data.mean_net_return_pct) > 0
                      ? "text-pos"
                      : Number(data.mean_net_return_pct) < 0
                        ? "text-neg"
                        : "text-text",
                )}
              >
                {change(data.mean_net_return_pct)}
              </p>
            </div>
            <div className="rounded-md bg-surface-2 p-3">
              <p className="label">{t("positive")}</p>
              <p className="num text-xl">
                {data.positive_share == null
                  ? "—"
                  : formatShare(locale, Number(data.positive_share))}
              </p>
            </div>
          </div>
          <div className="max-h-[36rem] overflow-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-text-3">
                  <th className="p-2">{common("table.symbol")}</th>
                  <th className="p-2">{t("availability")}</th>
                  <th className="p-2">{t("entry")}</th>
                  <th className="p-2">{t("exit")}</th>
                  <th className="p-2">{t("result")}</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row) => (
                  <tr key={`${row.source}:${row.id}`} className="border-b border-border align-top">
                    <td className="p-2">
                      <a
                        className="font-medium text-accent"
                        href={`?peek=${row.source}:${encodeURIComponent(row.id)}`}
                      >
                        {row.symbol}
                      </a>
                      <p className="text-text-3">
                        {t(row.source)} · {row.origin} ·{" "}
                        {t(
                          row.direction === "up" || row.direction === "down"
                            ? row.direction
                            : "neutral",
                        )}
                      </p>
                    </td>
                    <td className="p-2">
                      <time dateTime={row.available_at}>
                        {format.dateTime(new Date(row.available_at), {
                          dateStyle: "short",
                          timeStyle: "short",
                          timeZone: "UTC",
                        })}{" "}
                        UTC
                      </time>
                    </td>
                    <td className="p-2">
                      <p className="num" title={String(row.entry_price ?? "")}>
                        {price(row.entry_price)} {row.currency ?? ""}
                      </p>
                      <p className="whitespace-nowrap text-text-3">
                        {row.entry_date ?? "—"} · {row.entry_source ?? "—"}
                      </p>
                    </td>
                    <td className="p-2">
                      <p className="num" title={String(row.exit_price ?? "")}>
                        {price(row.exit_price)} {row.currency ?? ""}
                      </p>
                      <p className="whitespace-nowrap text-text-3">
                        {row.exit_date ?? "—"} · {row.exit_source ?? "—"}
                      </p>
                    </td>
                    <td
                      className={cn(
                        "p-2",
                        row.skip_reason
                          ? "text-warn"
                          : Number(row.net_return_pct) > 0
                            ? "text-pos"
                            : Number(row.net_return_pct) < 0
                              ? "text-neg"
                              : "text-text-2",
                      )}
                    >
                      {row.skip_reason ? t(row.skip_reason) : change(row.net_return_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!data.rows.length && <p className="text-text-3">{common("table.empty")}</p>}
          <p className="text-xs text-text-3">
            {t("completedAt")}{" "}
            {format.dateTime(new Date(data.as_of), { dateStyle: "short", timeStyle: "short" })} ·{" "}
            {data.source}
          </p>
        </div>
      )}
      <p className="rounded-md bg-warn-soft p-3 text-xs text-warn">{t("limitations")}</p>
    </section>
  );
}
