"use client";

import { useId, useState } from "react";
import { useTranslations } from "next-intl";
import type { components } from "@/lib/api/schema";
import { useAppLocale } from "@/lib/use-app-locale";
import { formatMoney } from "@/lib/format";
import { cn } from "@/lib/cn";
import { DataDetails } from "@/components/common/DataDetails";

type Calendar = components["schemas"]["DividendCalendar"];

/** Only server-aggregated money is displayed; JavaScript computes bar geometry, never totals. */
export function DividendCalendar({
  calendar,
  asOf,
}: {
  calendar?: Calendar;
  asOf?: string | null;
}) {
  const t = useTranslations("screenRefinement");
  const descriptionId = useId();
  const locale = useAppLocale();
  const anchor = Number(asOf?.slice(0, 4)) || new Date().getFullYear();
  const [chosenYear, setYear] = useState<number | null>(null);
  const year = chosenYear ?? anchor;
  const currencies = [
    ...new Set([
      ...(calendar?.years ?? []).map((row) => row.currency),
      ...(calendar?.issues ?? []).map((row) => row.currency),
    ]),
  ].sort();
  const [chosenCurrency, setCurrency] = useState("");
  const currency = currencies.includes(chosenCurrency) ? chosenCurrency : (currencies[0] ?? "");
  const [month, setMonth] = useState<string | null>(null);
  const [limit, setLimit] = useState(20);
  const years = [
    ...new Set([
      anchor - 1,
      anchor,
      anchor + 1,
      year,
      ...(calendar?.years ?? []).map((row) => row.year),
    ]),
  ].sort();
  const rows = (calendar?.months ?? []).filter(
    (row) => row.currency === currency && row.month.startsWith(`${year}-`),
  );
  const total = calendar?.years?.find((row) => row.year === year && row.currency === currency);
  const events = (calendar?.events ?? []).filter(
    (row) => row.currency === currency && row.payment_date.startsWith(month ?? `${year}-`),
  );
  const issues = (calendar?.issues ?? []).filter((row) => row.currency === currency);
  const peak = Math.max(
    1,
    ...rows.flatMap((row) => [
      Math.abs(Number(row.received_gross ?? 0)),
      Math.abs(Number(row.scheduled_gross ?? 0)),
    ]),
  );
  const money = (value: string | null | undefined) =>
    value == null ? "—" : formatMoney(locale, Number(value), currency);
  return (
    <section className="card min-w-0 space-y-4 p-4 sm:p-5" aria-label={t("calendarTitle")}>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="mr-auto text-lg font-semibold">{t("calendarTitle")}</h2>
        {asOf && (
          <time dateTime={asOf} className="text-xs text-text-3">
            {t("calendarAsOf", { date: asOf.slice(0, 10) })}
          </time>
        )}
        <label className="text-xs">
          {t("calendarYear")}{" "}
          <select
            className="min-h-12 rounded-md border border-border bg-surface px-2"
            value={year}
            onChange={(e) => {
              setYear(Number(e.target.value));
              setMonth(null);
              setLimit(20);
            }}
          >
            {years.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label className="text-xs">
          {t("calendarCurrency")}{" "}
          <select
            className="min-h-12 rounded-md border border-border bg-surface px-2"
            value={currency}
            disabled={!currencies.length}
            onChange={(e) => {
              setCurrency(e.target.value);
              setLimit(20);
            }}
          >
            {currencies.length ? (
              currencies.map((value) => <option key={value}>{value}</option>)
            ) : (
              <option value="">—</option>
            )}
          </select>
        </label>
        <DataDetails label={t("calendarHelp")}>
          <p>{t("calendarMethod")}</p>
          <p>{t("calendarNoSchedule")}</p>
        </DataDetails>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {(["received_gross", "scheduled_gross", "received_net"] as const).map((key) => (
          <dl key={key} className="rounded-lg bg-surface-2 p-3">
            <dt className="text-xs text-text-3">{t(key)}</dt>
            <dd className="num mt-1 text-lg">{money(total?.[key])}</dd>
          </dl>
        ))}
      </div>
      <p className="flex flex-wrap gap-x-4 text-xs">
        <span className="text-pos">● {t("received_gross")}</span>
        <span className="text-accent">● {t("scheduled_gross")}</span>
      </p>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4 2xl:grid-cols-6">
        {Array.from({ length: 12 }, (_, index) => {
          const period = `${year}-${String(index + 1).padStart(2, "0")}`;
          const row = rows.find((value) => value.month === period);
          const date = new Date(`${period}-01T12:00:00Z`);
          const name = new Intl.DateTimeFormat(locale, { month: "long", timeZone: "UTC" }).format(
            date,
          );
          return (
            <button
              key={period}
              type="button"
              aria-label={`${name} ${year}`}
              aria-describedby={`${descriptionId}-${period}`}
              aria-pressed={month === period}
              onClick={() => {
                setMonth(month === period ? null : period);
                setLimit(20);
              }}
              className={cn(
                "min-w-0 space-y-2 rounded-lg border p-3 text-left",
                month === period
                  ? "border-accent bg-accent-soft"
                  : "border-border hover:bg-surface-2",
              )}
            >
              <span className="sr-only" id={`${descriptionId}-${period}`}>
                {t("received_gross")}: {money(row?.received_gross)}; {t("scheduled_gross")}:{" "}
                {money(row?.scheduled_gross)};{" "}
                {row
                  ? t("calendarEntryCount", { count: row.received_count + row.scheduled_count })
                  : t("calendarUnscheduled")}
              </span>
              <span className="block text-sm font-medium">{name}</span>
              <span className="block text-[11px] text-text-3">
                {row
                  ? t("calendarEntryCount", { count: row.received_count + row.scheduled_count })
                  : t("calendarUnscheduled")}
              </span>
              {(["received_gross", "scheduled_gross"] as const).map((key) => (
                <span className="block" key={key}>
                  <span className="num block text-xs">{money(row?.[key])}</span>
                  <span className="mt-1 block h-1.5 rounded bg-surface-2">
                    <span
                      className={cn(
                        "block h-full rounded",
                        Number(row?.[key] ?? 0) < 0
                          ? "bg-neg"
                          : key === "received_gross"
                            ? "bg-pos"
                            : "bg-accent",
                      )}
                      style={{
                        width: `${Math.min(100, (Math.abs(Number(row?.[key] ?? 0)) / peak) * 100)}%`,
                      }}
                    />
                  </span>
                </span>
              ))}
            </button>
          );
        })}
      </div>
      <p className="text-xs text-text-3">{t("calendarNoSchedule")}</p>
      <h3 className="font-medium">
        {month ?? year} · {t("paymentDates")}
      </h3>
      {!events.length && <p className="text-sm text-text-3">{t("noDatedEvents")}</p>}
      <ul className="divide-y divide-border">
        {events.slice(0, limit).map((event) => (
          <li key={event.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3 text-sm">
            <time dateTime={event.payment_date} className="num">
              {event.payment_date}
            </time>
            <strong>{event.symbol ?? "—"}</strong>
            <span className={event.state === "received" ? "text-pos" : "text-accent"}>
              {t(event.state)}
            </span>
            <span className={cn("num ml-auto", Number(event.gross) < 0 && "text-neg")}>
              {money(event.gross)}
            </span>
            <span className="basis-full text-xs text-text-3">
              {event.account_id} · {event.source} · {event.as_of.slice(0, 10)}
            </span>
          </li>
        ))}
      </ul>
      {events.length > limit && (
        <button
          type="button"
          className="min-h-12 rounded-md border border-border px-3"
          onClick={() => setLimit(limit + 20)}
        >
          {t("morePayments")}
        </button>
      )}
      {!!issues.length && (
        <div className="space-y-1 rounded-lg bg-warn-soft p-3 text-xs text-warn">
          <h3 className="font-medium">{t("calendarIssues")}</h3>
          {issues.map((issue) => (
            <p key={issue.id}>
              {issue.symbol ?? "—"} · {issue.account_id} · {t(issue.reason)}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
