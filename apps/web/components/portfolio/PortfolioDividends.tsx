"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDividends } from "@/lib/api/dividends";
import { formatMoney, formatNumber, type AppLocale } from "@/lib/format";

/** Cash, entitlement snapshots and estimates deliberately have independent sections. */
export function PortfolioDividends() {
  const t = useTranslations("dividends");
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
  const stamp = (value: string | null | undefined, basis?: string) =>
    value
      ? basis === "statement_report_date_utc_boundary"
        ? new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone: "UTC" }).format(
            new Date(value),
          )
        : new Date(value).toLocaleString(locale === "sl" ? "sl-SI" : "en-GB")
      : t("unknown");
  const data = query.data;
  const inputClass = "min-h-12 rounded-lg border border-border bg-surface px-3 text-text";

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
        <div role="alert" className="rounded-xl border border-border p-4">
          <p>{t("error")}</p>
          <button className="min-h-12 text-accent" onClick={() => query.refetch()}>
            {t("retry")}
          </button>
        </div>
      ) : (
        data && (
          <>
            <section aria-label={t("received")} className="rounded-xl border border-border p-4">
              <h2 className="font-semibold">{t("received")}</h2>
              <p className="mt-1 text-sm text-text-3">{t("cashNote")}</p>
              <div className="my-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {data.received.map((row) => (
                  <dl
                    key={row.currency}
                    className="grid grid-cols-2 gap-2 rounded-lg bg-surface-2 p-3 text-sm"
                  >
                    <dt>{t("gross")}</dt>
                    <dd className="text-right font-mono">{money(row.gross, row.currency)}</dd>
                    <dt>{t("tax")}</dt>
                    <dd className="text-right font-mono">{money(row.withholding, row.currency)}</dd>
                    <dt>{t("net")}</dt>
                    <dd className="text-right font-mono">{money(row.net, row.currency)}</dd>
                    <dt>{t("pil")}</dt>
                    <dd className="text-right font-mono">
                      {money(row.payment_in_lieu, row.currency)}
                    </dd>
                    {row.unresolved_withholding != null && (
                      <>
                        <dt>{t("unresolved")}</dt>
                        <dd className="text-right font-mono">
                          {money(row.unresolved_withholding, row.currency)}
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
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr>
                        {["date", "account", "symbol", "kind", "amount", "source"].map((key) => (
                          <th className="p-2" key={key}>
                            {t(key)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.cash_events.map((row) => (
                        <tr
                          key={`${row.broker}:${row.account_id}:${row.transaction_id}`}
                          className="border-t border-border"
                        >
                          <td className="p-2 whitespace-nowrap">{row.booking_date}</td>
                          <td className="p-2">{row.account_id}</td>
                          <td className="p-2">{row.symbol ?? row.con_id ?? t("unknown")}</td>
                          <td className="p-2">{t(row.kind)}</td>
                          <td className="p-2 whitespace-nowrap font-mono">
                            {money(row.amount, row.currency)}
                          </td>
                          <td className="p-2 text-text-3">
                            {row.source}
                            <br />
                            {stamp(row.as_of, row.as_of_basis)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <section aria-label={t("accruals")} className="rounded-xl border border-border p-4">
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
                        <dd>{money(row.gross_amount, row.currency)}</dd>
                        <dt>{t("tax")}</dt>
                        <dd>{money(row.tax, row.currency)}</dd>
                        <dt>{t("net")}</dt>
                        <dd>{money(row.net_amount, row.currency)}</dd>
                      </dl>
                      <p className="mt-2 text-text-3">
                        {row.source} · {stamp(row.as_of, row.as_of_basis)}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
            <section aria-label={t("projection")} className="rounded-xl border border-border p-4">
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
                      <p>{row.reason ? t(row.reason) : row.basis ? t(row.basis) : t("unknown")}</p>
                      {row.includes_special && <p>{t("special")}</p>}
                      <p className="mt-2 text-text-3">
                        {t("source")}: {row.source ?? t("unknown")} · {stamp(row.as_of)}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
            <section className="rounded-xl border border-border p-4 text-sm">
              <h2 className="font-semibold">{t("coverage")}</h2>
              <p className="mt-2 text-text-3">{t("instructions")}</p>
              <p className="mt-2 text-text-3">{t("contract")}</p>
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
          </>
        )
      )}
    </div>
  );
}
