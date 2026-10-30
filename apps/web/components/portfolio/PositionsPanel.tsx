"use client";
import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";
import { useRef } from "react";
import { useSearchParams, usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";
import { EntityLink } from "@/components/common/EntityLink";
import { Treemap } from "@/components/overview/Treemap";
import { DataTable, type ColumnDefinition } from "@/components/table/DataTable";
import { DataQualityBadges } from "@/components/table/MetricCell";
import { useMarketColumns } from "@/components/table/market-columns";
import { useEntries, usePortfolio, usePortfolioImport, usePortfolioSync } from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";
import type { PositionOut } from "@/lib/api/types";
import { formatMoney, formatNumber } from "@/lib/format";
import { EntryZoneBadge, PriceTrend, SignedChange, type StoredPriceTrend } from "./MarketContext";
import { useAppLocale } from "@/lib/use-app-locale";

export function PositionsPanel() {
  const t = useTranslations();
  const labels = useTranslations("table");
  const locale = useAppLocale();
  const format = useFormatter();
  const params = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const query = new URLSearchParams();
  for (const key of ["account_id", "sort", "direction", "q"])
    if (params.get(key)) query.set(key, params.get(key)!);
  const { data, isLoading, error, refetch } = usePortfolio(query.toString());
  const { data: entries } = useEntries("portfolio");
  const upload = usePortfolioImport();
  const sync = usePortfolioSync();
  const fileInput = useRef<HTMLInputElement>(null);
  const market = useMarketColumns<PositionOut>();
  const money = (value: string | number | null | undefined, currency: string) =>
    value == null ? "—" : formatMoney(locale, Number(value), currency);
  const columns: ColumnDefinition<PositionOut>[] = [
    {
      id: "symbol",
      label: labels("instrument"),
      required: true,
      sortable: true,
      width: 240,
      render: (row) => (
        <div className="space-y-1">
          <EntityLink entity={{ kind: "instrument", id: row.symbol }} />
          <div className="text-xs text-text-3">{row.name}</div>
          <div className="text-[11px] text-text-3">
            {row.account_id} · {row.exchange ?? "—"} · {row.currency}
          </div>
          <PriceTrend
            trend={(row as PositionOut & { price_trend?: StoredPriceTrend | null }).price_trend}
          />
          <EntryZoneBadge entry={entries?.find((entry) => entry.symbol === row.symbol)} />
          <DataQualityBadges
            identity={row.identity_status}
            price={row.price_meta}
            metrics={row.metrics}
          />
        </div>
      ),
    },
    {
      id: "quantity",
      label: t("portfolio.col.quantity"),
      numeric: true,
      sortable: true,
      render: (row) =>
        new Intl.NumberFormat(locale, { maximumFractionDigits: 8, useGrouping: "always" }).format(
          Number(row.quantity),
        ),
    },
    {
      id: "market_price",
      label: labels("snapshotPrice"),
      numeric: true,
      sortable: true,
      render: (row) => (
        <div>
          {money(row.market_price, row.currency)}
          <div className="text-[11px] text-text-3">{row.report_date}</div>
        </div>
      ),
    },
    {
      id: "market_value",
      label: t("portfolio.col.value"),
      numeric: true,
      sortable: true,
      render: (row) => money(row.market_value, row.currency),
    },
    {
      id: "weight_pct",
      label: t("portfolio.col.weight"),
      numeric: true,
      sortable: true,
      render: (row) =>
        row.weight_pct == null ? "—" : `${formatNumber(locale, row.weight_pct, 2)} %`,
    },
    {
      id: "unrealized_pnl",
      label: t("portfolio.col.pnl"),
      numeric: true,
      sortable: true,
      render: (row) => (
        <SignedChange
          value={row.unrealized_pnl == null ? null : Number(row.unrealized_pnl)}
          currency={row.currency}
        />
      ),
    },
    {
      id: "change_pct",
      label: labels("daily"),
      numeric: true,
      sortable: true,
      render: (row) => (
        <div>
          <SignedChange value={row.change_pct} />
          <div className="text-[11px] text-text-3" title={row.price_meta?.source ?? undefined}>
            {row.price_meta?.market_date}
          </div>
        </div>
      ),
    },
    {
      id: "latest_close",
      label: labels("close"),
      numeric: true,
      defaultVisible: false,
      sortable: true,
      render: (row) => (
        <div
          title={[row.price_meta?.source, row.price_meta?.market_date].filter(Boolean).join(" · ")}
        >
          {money(row.latest_close, row.currency)}
          <div className="text-[11px] text-text-3">{row.price_meta?.market_date}</div>
        </div>
      ),
    },
    ...market,
    {
      id: "actions",
      label: labels("actions"),
      required: true,
      width: 100,
      render: (row) => (
        <Link
          href={`/i/${encodeURIComponent(row.symbol)}`}
          className="inline-flex min-h-12 items-center rounded border border-border px-2 text-xs"
        >
          {t("peek.open")}
        </Link>
      ),
    },
  ];
  const onUpload = async (file: File) => {
    try {
      const result = await upload.mutateAsync(file);
      toast.success(t("portfolio.importSuccess", result.counts));
    } catch (error) {
      toast.error(
        t(
          error instanceof ApiError && error.status === 413
            ? "portfolio.importTooLarge"
            : error instanceof ApiError && error.status === 422
              ? "portfolio.importInvalid"
              : "portfolio.importFailed",
        ),
      );
    }
  };
  const onSync = async () => {
    try {
      await sync.mutateAsync();
      toast.success(t("portfolio.syncQueued"));
    } catch (error) {
      toast.error(
        t(
          error instanceof ApiError && error.detail === "flex_unconfigured"
            ? "portfolio.flexUnconfigured"
            : "portfolio.syncFailed",
        ),
      );
    }
  };
  if (isLoading) return <div className="card h-80 animate-pulse" aria-busy="true" />;
  if (error || !data)
    return (
      <div role="alert" className="card p-5 text-warn">
        {t("system.unreachable")}{" "}
        <button type="button" onClick={() => void refetch()}>
          {labels("retry")}
        </button>
      </div>
    );
  return (
    <div className="flex min-w-0 flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="label">{t("portfolio.total")}</div>
          <div className="num text-[28px] font-medium">
            {money(data.total_value, data.base_currency)}
          </div>
          <p className="text-xs text-text-3">
            {data.as_of
              ? t("portfolio.asOf", {
                  date: format.dateTime(new Date(data.as_of), { dateStyle: "medium" }),
                })
              : t("portfolio.never")}{" "}
            · {labels("snapshotBasis")}
          </p>
          {data.source === "demo" && (
            <span className="text-xs text-warn">{t("provenance.demo")}</span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs">
            {labels("account")}{" "}
            <select
              aria-label={labels("account")}
              value={params.get("account_id") ?? ""}
              className="h-12 rounded border border-border bg-surface px-2"
              onChange={(event) => {
                const next = new URLSearchParams(params.toString());
                if (event.target.value) next.set("account_id", event.target.value);
                else next.delete("account_id");
                next.delete("page");
                router.replace(`${pathname}?${next}`, { scroll: false });
              }}
            >
              <option value="">{labels("allAccounts")}</option>
              {data.accounts?.map((account) => (
                <option key={account} value={account}>
                  {account}
                </option>
              ))}
            </select>
          </label>
          <input
            ref={fileInput}
            type="file"
            hidden
            accept=".xml,application/xml,text/xml"
            aria-label={t("portfolio.import")}
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (file) void onUpload(file);
            }}
          />
          <button
            type="button"
            disabled={upload.isPending || sync.isPending}
            onClick={() => fileInput.current?.click()}
            className="h-12 rounded border border-border px-3"
          >
            {upload.isPending ? t("portfolio.importing") : t("portfolio.import")}
          </button>
          <button
            type="button"
            disabled={upload.isPending || sync.isPending}
            onClick={() => void onSync()}
            className="h-12 rounded border border-border px-3"
          >
            {sync.isPending ? t("portfolio.syncing") : t("portfolio.sync")}
          </button>
          <Link
            href="/settings"
            className="inline-flex min-h-12 items-center px-2 text-xs text-accent"
          >
            {labels("refreshSettings")}
          </Link>
        </div>
      </div>
      {data.valuation_meta?.reason_code === "missing_fx" && (
        <p role="status" className="rounded border border-warn p-3 text-sm text-warn">
          {labels("fxPartial")}
        </p>
      )}
      {data.positions.length > 1 && (
        <details className="card p-4">
          <summary className="cursor-pointer text-sm font-medium">
            {t("portfolio.exposure")}
          </summary>
          <Treemap
            items={data.positions
              .filter((row) => row.weight_pct != null && row.change_pct != null)
              .map((row) => ({
                symbol: row.symbol,
                change: Number(row.change_pct),
                weight: Number(row.weight_pct),
                thesis: "none",
              }))}
            height={200}
          />
        </details>
      )}
      <DataTable
        module="positions"
        label={t("portfolio.tabPositions")}
        columns={columns}
        rows={data.positions}
        rowKey={(row) => `${row.account_id}:${row.instrument_id ?? row.symbol}`}
        profiles={[
          {
            label: labels("valuation"),
            columns: [
              "symbol",
              "latest_close",
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
              "quantity",
              "dividend_yield_pct",
              "payout_ratio_pct",
              "dividend_per_share",
              "actions",
            ],
          },
        ]}
      />
      {data.cash.length > 0 && (
        <section className="card flex flex-wrap gap-4 p-4 text-sm">
          <span className="label">{t("portfolio.cash")}</span>
          {data.cash.map((cash) => (
            <span key={`${cash.account_id}:${cash.currency}`} className="num">
              {cash.account_id} · {money(cash.amount, cash.currency)}
            </span>
          ))}
        </section>
      )}
    </div>
  );
}
