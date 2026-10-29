"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useId, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { EntityLink } from "@/components/common/EntityLink";
import { SegmentedButtons } from "@/components/common/SegmentedButtons";
import { DataTable, type ColumnDefinition } from "@/components/table/DataTable";
import { DataQualityBadges } from "@/components/table/MetricCell";
import { useMarketColumns } from "@/components/table/market-columns";
import { ApiError } from "@/lib/api/client";
import { useWatchlist, useWatchlistMutations } from "@/lib/api/hooks";
import type { WatchlistOut, WatchTier } from "@/lib/api/types";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { useAppLocale } from "@/lib/use-app-locale";

function Actions({ item }: { item: WatchlistOut }) {
  const t = useTranslations("watchlist");
  const labels = useTranslations("table");
  const { update, remove, restore } = useWatchlistMutations();
  const pending = update.isPending || remove.isPending || restore.isPending;
  const other = item.tier === "active" ? "reserve" : "active";
  const fail = () => toast.error(labels("mutationFailed"));
  const onRemove = async () => {
    try {
      await remove.mutateAsync({ id: item.id, revision: item.revision ?? 1 });
      toast(t("removed"), {
        action: {
          label: labels("undo"),
          onClick: () =>
            restore.mutate({ id: item.id, revision: (item.revision ?? 1) + 1 }, { onError: fail }),
        },
      });
    } catch {
      fail();
    }
  };
  return (
    <div className="flex flex-col items-start gap-1 text-xs">
      <button
        type="button"
        disabled={pending}
        onClick={() => update.mutate({ id: item.id, data: { tier: other } }, { onError: fail })}
        className="min-h-7 rounded border border-border px-2 disabled:opacity-50"
      >
        {t("moveTo", { tier: t(`tiers.${other}`) })}
      </button>
      <details>
        <summary className="cursor-pointer rounded px-2 py-1 text-text-3">
          {labels("actions")}
        </summary>
        <div className="flex flex-col items-start gap-1 py-1">
          {!item.reviewed_at && (
            <button
              type="button"
              disabled={pending}
              onClick={() =>
                update.mutate({ id: item.id, data: { reviewed: true } }, { onError: fail })
              }
              className="min-h-7 px-2"
            >
              {t("markReviewed")}
            </button>
          )}
          <button
            type="button"
            disabled={pending}
            onClick={() => void onRemove()}
            className="min-h-7 px-2 text-neg"
          >
            {t("remove")}
          </button>
        </div>
      </details>
    </div>
  );
}

export function WatchlistPanel() {
  const t = useTranslations("watchlist");
  const labels = useTranslations("table");
  const format = useFormatter();
  const locale = useAppLocale();
  const params = useSearchParams();
  const query = new URLSearchParams();
  for (const key of ["sort", "direction", "q"])
    if (params.get(key)) query.set(key, params.get(key)!);
  const { data, isLoading, error, refetch } = useWatchlist(query.toString());
  const { add } = useWatchlistMutations();
  const id = useId();
  const [symbol, setSymbol] = useState("");
  const [note, setNote] = useState("");
  const [tier, setTier] = useState<WatchTier>("active");
  const market = useMarketColumns<WatchlistOut>();
  const money = (value: number | null, currency?: string | null) =>
    value == null
      ? "—"
      : currency
        ? formatMoney(locale, value, currency)
        : `${formatNumber(locale, value, 2)} (${labels("unknownCurrency")})`;
  const columns: ColumnDefinition<WatchlistOut>[] = [
    {
      id: "symbol",
      label: labels("instrument"),
      required: true,
      sortable: true,
      width: 230,
      render: (item) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <EntityLink entity={{ kind: "instrument", id: item.symbol }} />
            {!item.reviewed_at && (
              <span className="rounded bg-accent-soft px-1 text-[11px] text-accent">
                {t("new")}
              </span>
            )}
          </div>
          <div className="max-w-60 truncate text-xs text-text-3">
            {item.name ?? item.exchange ?? "—"}
          </div>
          <DataQualityBadges
            identity={item.identity_status}
            price={item.price_meta}
            metrics={item.metrics}
          />
        </div>
      ),
    },
    {
      id: "last_close",
      label: labels("close"),
      numeric: true,
      sortable: true,
      render: (item) => (
        <div
          title={[item.price_meta?.source, item.price_meta?.market_date]
            .filter(Boolean)
            .join(" · ")}
        >
          {money(item.last_close, item.currency)}
          <div className="text-[11px] text-text-3">{item.price_meta?.market_date}</div>
        </div>
      ),
    },
    {
      id: "change_pct",
      label: labels("daily"),
      numeric: true,
      sortable: true,
      render: (item) => (item.change_pct == null ? "—" : formatChange(locale, item.change_pct)),
    },
    {
      id: "since_added_pct",
      label: t("sinceAdded"),
      numeric: true,
      sortable: true,
      render: (item) =>
        item.since_added_pct == null ? "—" : formatChange(locale, item.since_added_pct),
    },
    {
      id: "currency",
      label: labels("currency"),
      defaultVisible: false,
      render: (item) => item.currency ?? labels("unknownCurrency"),
    },
    {
      id: "target_price",
      label: labels("userTarget"),
      numeric: true,
      defaultVisible: false,
      sortable: true,
      render: (item) => money(item.target_price, item.currency),
    },
    ...market,
    {
      id: "note",
      label: t("note"),
      defaultVisible: false,
      render: (item) => (
        <div className="max-w-80 whitespace-normal text-xs">
          {item.note ?? "—"}
          <p className="mt-1 text-text-3">
            {t("added", {
              date: format.dateTime(new Date(item.added_at), { dateStyle: "medium" }),
            })}
          </p>
        </div>
      ),
    },
    {
      id: "actions",
      label: labels("actions"),
      required: true,
      width: 160,
      render: (item) => <Actions item={item} />,
    },
  ];
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!symbol.trim()) return;
    try {
      await add.mutateAsync({
        symbol: symbol.trim().toUpperCase(),
        note: note.trim() || null,
        tier,
      });
      setSymbol("");
      setNote("");
    } catch (error) {
      toast.error(
        error instanceof ApiError && error.status === 409
          ? t("duplicate")
          : labels("mutationFailed"),
      );
    }
  };
  return (
    <div className="flex min-w-0 flex-col gap-5">
      <form
        onSubmit={submit}
        aria-label={t("add")}
        className="card flex flex-wrap items-end gap-3 p-4"
      >
        <label className="w-32 text-xs text-text-3" htmlFor={`${id}-symbol`}>
          {t("symbol")}
          <input
            id={`${id}-symbol`}
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            required
            autoComplete="off"
            className="num mt-1 h-10 w-full rounded-md border border-border bg-surface px-3 uppercase"
          />
        </label>
        <label className="min-w-48 flex-1 text-xs text-text-3" htmlFor={`${id}-note`}>
          {t("note")}
          <input
            id={`${id}-note`}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border border-border bg-surface px-3"
          />
        </label>
        <fieldset>
          <legend className="label">{t("tier")}</legend>
          <SegmentedButtons
            label={t("tier")}
            value={tier}
            onChange={setTier}
            options={[
              { value: "active", label: t("tiers.active") },
              { value: "reserve", label: t("tiers.reserve") },
            ]}
          />
        </fieldset>
        <button
          type="submit"
          disabled={add.isPending}
          className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent disabled:opacity-50"
        >
          {add.isPending ? t("adding") : t("add")}
        </button>
      </form>
      {isLoading && <div className="card h-40 animate-pulse" aria-busy="true" />}
      {error && (
        <div role="alert" className="card p-4 text-warn">
          {labels("loadFailed")}{" "}
          <button type="button" onClick={() => void refetch()}>
            {labels("retry")}
          </button>
        </div>
      )}
      {data &&
        (["active", "reserve"] as const).map((value) => (
          <section key={value} className="min-w-0 space-y-2">
            <h2 className="font-semibold">
              {t(`tiers.${value}`)}{" "}
              <span className="num text-text-3">
                {data.filter((item) => item.tier === value).length}
              </span>
            </h2>
            <DataTable
              module={`watchlist-${value}`}
              label={t(`tiers.${value}`)}
              columns={columns}
              rows={data.filter((item) => item.tier === value)}
              rowKey={(item) => String(item.id)}
              profiles={[
                {
                  label: labels("valuation"),
                  columns: [
                    "symbol",
                    "last_close",
                    "pe",
                    "forward_pe",
                    "ev_ebit",
                    "fcf_yield",
                    "actions",
                  ],
                },
                {
                  label: labels("dividends"),
                  columns: [
                    "symbol",
                    "last_close",
                    "dividend_yield_pct",
                    "payout_ratio_pct",
                    "dividend_per_share",
                    "actions",
                  ],
                },
              ]}
            />
          </section>
        ))}
    </div>
  );
}
