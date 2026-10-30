"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { DataTable } from "@/components/table/DataTable";
import { SignedChange } from "./MarketContext";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDividends } from "@/lib/api/dividends";
import { formatMoney, formatNumber, type AppLocale } from "@/lib/format";

/** Cash, entitlement snapshots and estimates deliberately have independent sections. */
export function PortfolioDividends() {
  const t = useTranslations("dividends");
  const [showEstimates, setShowEstimates] = useState(true);
  const [showCoverage, setShowCoverage] = useState(true);
  const locale = useLocale() as AppLocale;
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const account = params.get("dvAccount") ?? "";
  const currency = params.get("dvCurrency") ?? "";
  const from = params.get("dvFrom") ?? "";
  const to = params.get("dvTo") ?? "";
  const invalid = Boolean(from && to && from > to);
  const query = useDividends(
    {
      account_id: account || undefined,
      currency: currency || undefined,
      from_date: from || undefined,
      to_date: to || undefined,
    },
    !invalid,
  );
  const change = (key: string, value: string) => {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.replace(`${pathname}?${next}`, { scroll: false });
  };
  const money = (value: string | null | undefined, denomination: string) =>
    value == null ? t("unknown") : formatMoney(locale, Number(value), denomination);
  const signedMoney = (value: string | null | undefined, denomination: string) =>
    value == null ? t("unknown") : <SignedChange value={Number(value)} currency={denomination} />;
  const stamp = (value: string | null | undefined, basis?: string) =>
    value
      ? basis === "statement_report_date_utc_boundary"
        ? new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(
            new Date(value),
          )
        : new Date(value).toLocaleString(locale === "sl" ? "sl-SI" : "en-GB")
      : t("unknown");
  const data = query.data;
  const confirmedCoverage = new Map<string, string>();
  for (const row of data?.coverage ?? []) {
    if (
      row.section === "CashTransactions" &&
      row.status !== "missing" &&
      row.to_date &&
      (!confirmedCoverage.has(row.account_id) ||
        row.to_date > confirmedCoverage.get(row.account_id)!)
    ) {
      confirmedCoverage.set(row.account_id, row.to_date);
    }
  }
  const inputClass = "min-h-12 rounded-lg border border-border bg-surface px-3 text-text";

  return (
    <div className="flex min-w-0 flex-col gap-5">
      <div className="card grid grid-cols-2 gap-3 p-4 lg:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          {t("account")}
          <select
            aria-label={t("account")}
            className={inputClass}
            value={account}
            onChange={(e) => change("dvAccount", e.target.value)}
          >
            <option value="">{t("all")}</option>
            {[...new Set([...(data?.accounts ?? []), ...(account ? [account] : [])])].map(
              (value) => (
                <option key={value}>{value}</option>
              ),
            )}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          {t("currency")}
          <select
            aria-label={t("currency")}
            className={inputClass}
            value={currency}
            onChange={(e) => change("dvCurrency", e.target.value)}
          >
            <option value="">{t("all")}</option>
            {[...new Set([...(data?.currencies ?? []), ...(currency ? [currency] : [])])].map(
              (value) => (
                <option key={value}>{value}</option>
              ),
            )}
          </select>
        </label>
        <label className="flex min-w-0 flex-col gap-1 text-sm">
          {t("from")}
          <input
            type="date"
            className={inputClass}
            value={from}
            onChange={(e) => change("dvFrom", e.target.value)}
          />
        </label>
        <label className="flex min-w-0 flex-col gap-1 text-sm">
          {t("to")}
          <input
            type="date"
            className={inputClass}
            value={to}
            onChange={(e) => change("dvTo", e.target.value)}
          />
        </label>
      </div>
      {invalid ? (
        <p role="alert">{t("rangeError")}</p>
      ) : query.isPending ? (
        <p role="status">{t("loading")}</p>
      ) : query.isError ? (
        <div role="alert" className="card min-w-0 p-5">
          <p>{t("error")}</p>
          <button className="min-h-12 text-accent" onClick={() => query.refetch()}>
            {t("retry")}
          </button>
        </div>
      ) : (
        data && (
          <>
            <section className="card space-y-3 p-5" aria-label={t("confirmedTitle")}>
              <h2 className="font-semibold">{t("confirmedTitle")}</h2>
              {confirmedCoverage.size ? (
                [...confirmedCoverage].map(([account, date]) => (
                  <p key={account} className="num text-sm">
                    {t("confirmedThrough", { account, date })}
                  </p>
                ))
              ) : (
                <p className="text-sm text-text-3">{t("confirmedUnknown")}</p>
              )}
              <p className="text-sm text-text-3">{t("estimateBoundary")}</p>
              <p className="text-sm text-text-3">{t("reconciliationNote")}</p>
              <div className="flex flex-wrap gap-4">
                <label className="flex min-h-12 items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showEstimates}
                    onChange={(event) => setShowEstimates(event.target.checked)}
                  />
                  {t("showEstimates")}
                </label>
                <label className="flex min-h-12 items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showCoverage}
                    onChange={(event) => setShowCoverage(event.target.checked)}
                  />
                  {t("showCoverage")}
                </label>
              </div>
            </section>
            <section aria-label={t("received")} className="card min-w-0 p-5">
              <h2 className="font-semibold">{t("received")}</h2>
              <p className="mt-1 text-sm text-text-3">{t("cashNote")}</p>
              <div className="my-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {data.received.map((row) => (
                  <dl
                    key={row.currency}
                    className="grid grid-cols-2 gap-2 rounded-lg bg-surface-2 p-3 text-sm"
                  >
                    <dt>{t("gross")}</dt>
                    <dd className="text-right font-mono">{signedMoney(row.gross, row.currency)}</dd>
                    <dt>{t("tax")}</dt>
                    <dd className="text-right font-mono">
                      {signedMoney(row.withholding, row.currency)}
                    </dd>
                    <dt>{t("net")}</dt>
                    <dd className="text-right font-mono">{signedMoney(row.net, row.currency)}</dd>
                    <dt>{t("pil")}</dt>
                    <dd className="text-right font-mono">
                      {signedMoney(row.payment_in_lieu, row.currency)}
                    </dd>
                    {row.unresolved_withholding != null && (
                      <>
                        <dt>{t("unresolved")}</dt>
                        <dd className="text-right font-mono">
                          {signedMoney(row.unresolved_withholding, row.currency)}
                        </dd>
                      </>
                    )}
                    {!row.fx_complete && <dd className="col-span-2 text-text-3">{t("fxGap")}</dd>}
                  </dl>
                ))}
              </div>
              {!data.cash_events.length ? (
                <p className="text-sm text-text-3">{t("emptyCash")}</p>
              ) : (
                <DataTable
                  module="dividend-cash"
                  label={t("received")}
                  rows={data.cash_events}
                  rowKey={(row) => `${row.broker}:${row.account_id}:${row.transaction_id}`}
                  columns={[
                    {
                      id: "booking_date",
                      label: t("date"),
                      required: true,
                      render: (row) => row.booking_date,
                    },
                    { id: "account_id", label: t("account"), render: (row) => row.account_id },
                    {
                      id: "symbol",
                      label: t("symbol"),
                      required: true,
                      render: (row) => row.symbol ?? row.con_id ?? t("unknown"),
                    },
                    { id: "kind", label: t("kind"), render: (row) => t(row.kind) },
                    {
                      id: "amount",
                      label: t("amount"),
                      numeric: true,
                      render: (row) => signedMoney(row.amount, row.currency),
                    },
                    {
                      id: "source",
                      label: t("source"),
                      render: (row) => (
                        <div className="text-xs text-text-3">
                          {row.source}
                          <br />
                          {stamp(row.as_of, row.as_of_basis)}
                        </div>
                      ),
                    },
                  ]}
                />
              )}
            </section>
            <section aria-label={t("accruals")} className="card min-w-0 p-5">
              <h2 className="font-semibold">{t("accruals")}</h2>
              <p className="mt-1 text-sm text-text-3">{t("accrualNote")}</p>
              {!data.accruals.length ? (
                <p className="mt-4 text-sm text-text-3">{t("emptyAccrual")}</p>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {data.accruals.map((row) => (
                    <article
                      key={`${row.account_id}:${row.natural_key}`}
                      className="rounded-lg bg-surface-2 p-3 text-sm"
                    >
                      <h3 className="font-medium">
                        {row.symbol ?? row.con_id} · {row.account_id}
                      </h3>
                      <dl className="mt-2 grid grid-cols-2 gap-2">
                        <dt>{t("exDate")}</dt>
                        <dd>{row.ex_date}</dd>
                        <dt>{t("payDate")}</dt>
                        <dd>{row.pay_date ?? t("unknown")}</dd>
                        <dt>{t("quantity")}</dt>
                        <dd>
                          {row.quantity == null
                            ? t("unknown")
                            : formatNumber(locale, Number(row.quantity), 4)}
                        </dd>
                        <dt>{t("gross")}</dt>
                        <dd>{signedMoney(row.gross_amount, row.currency)}</dd>
                        <dt>{t("tax")}</dt>
                        <dd>{signedMoney(row.tax, row.currency)}</dd>
                        <dt>{t("net")}</dt>
                        <dd>{signedMoney(row.net_amount, row.currency)}</dd>
                      </dl>
                      <p className="mt-2 text-text-3">
                        {row.source} · {stamp(row.as_of, row.as_of_basis)}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
            {showEstimates ? (
              <section aria-label={t("projection")} className="card min-w-0 p-5">
                <h2 className="font-semibold">{t("projection")}</h2>
                <p className="mt-1 text-sm text-text-3">{t("projectionNote")}</p>
                {!data.projections.length ? (
                  <p className="mt-4 text-sm text-text-3">{t("emptyProjection")}</p>
                ) : (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {data.projections.map((row) => (
                      <article
                        key={`${row.account_id}:${row.symbol}:${row.currency}`}
                        className="rounded-lg bg-surface-2 p-3 text-sm"
                      >
                        <h3 className="font-medium">
                          {row.symbol} · {row.account_id}
                        </h3>
                        <p className="my-2 font-mono text-lg">
                          {money(row.annual_gross, row.currency)}
                        </p>
                        <p className="text-xs text-text-3">
                          {t("snapshotBasis", { date: row.position_as_of ?? t("unknown") })}
                        </p>
                        <p>
                          {row.reason ? t(row.reason) : row.basis ? t(row.basis) : t("unknown")}
                        </p>
                        {row.includes_special && <p>{t("special")}</p>}
                        <p className="mt-2 text-text-3">
                          {t("source")}: {row.source ?? t("unknown")} · {stamp(row.as_of)}
                        </p>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            ) : (
              <p className="card p-4 text-sm text-text-3">{t("estimateHidden")}</p>
            )}
            {showCoverage && (
              <section className="card min-w-0 p-5 text-sm">
                <h2 className="font-semibold">{t("coverage")}</h2>
                <p className="mt-2 text-text-3">{t("instructions")}</p>
                <p className="mt-2 text-text-3">{t("contract")}</p>
                <h3 className="mt-5 font-semibold">{t("reconciliationTitle")}</h3>
                {data.reconciliation?.length ? (
                  <div className="mt-3">
                    <DataTable
                      module="dividend-reconciliation"
                      label={t("reconciliationTitle")}
                      rows={data.reconciliation}
                      rowKey={(row) =>
                        `${row.account_id}:${row.action_id}:${row.symbol}:${row.currency}`
                      }
                      columns={[
                        { id: "account_id", label: t("account"), render: (row) => row.account_id },
                        {
                          id: "symbol",
                          label: t("symbol"),
                          required: true,
                          render: (row) => row.symbol ?? t("unknown"),
                        },
                        {
                          id: "action_id",
                          label: t("actionReference"),
                          render: (row) => row.action_id,
                        },
                        {
                          id: "expected_gross",
                          label: t("expectedGross"),
                          numeric: true,
                          render: (row) => money(row.expected_gross, row.currency),
                        },
                        {
                          id: "received_gross",
                          label: t("receivedGross"),
                          numeric: true,
                          render: (row) => signedMoney(row.received_gross, row.currency),
                        },
                        {
                          id: "difference",
                          label: t("difference"),
                          numeric: true,
                          render: (row) => signedMoney(row.difference, row.currency),
                        },
                        {
                          id: "status",
                          label: t("reconciliationStatus"),
                          render: (row) =>
                            t(
                              row.status === "confirmed"
                                ? "reconciliationConfirmed"
                                : row.status === "changed"
                                  ? "reconciliationChanged"
                                  : "reconciliationAwaiting",
                            ),
                        },
                        { id: "as_of", label: t("date"), render: (row) => stamp(row.as_of) },
                      ]}
                    />
                  </div>
                ) : (
                  <p className="mt-2 text-text-3">{t("reconciliationEmpty")}</p>
                )}
                {!data.coverage.length && <p className="mt-3">{t("noCoverage")}</p>}
                <ul className="mt-3 space-y-2">
                  {data.coverage.map((row) => (
                    <li
                      key={`${row.account_id}:${row.section}:${row.from_date}:${row.to_date}:${row.as_of}`}
                      className="rounded-lg bg-surface-2 p-3"
                    >
                      <span className="font-medium">
                        {row.account_id} · {row.section}
                      </span>{" "}
                      ·{" "}
                      <span>
                        {t(
                          row.status === "missing"
                            ? "missing"
                            : row.status === "partial"
                              ? "partial"
                              : "complete",
                        )}
                      </span>
                      <br />
                      {row.from_date} – {row.to_date} · {row.source} ·{" "}
                      {stamp(row.as_of, row.as_of_basis)}
                      {(row.gaps?.length ?? 0) > 0 && (
                        <span className="block font-mono text-xs">{row.gaps?.join(", ")}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )
      )}
    </div>
  );
}
