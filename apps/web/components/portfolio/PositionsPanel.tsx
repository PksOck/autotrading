"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import { toast } from "sonner";
import { useRef } from "react";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { EntityLink } from "@/components/common/EntityLink";
import { Treemap, type TreemapItem } from "@/components/overview/Treemap";
import { ApiError } from "@/lib/api/client";
import { usePortfolio, usePortfolioImport, usePortfolioSync } from "@/lib/api/hooks";
import type { PortfolioOut } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { listItem } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";
import { useFocusStore } from "@/stores/focus";

export function PositionsPanel() {
  const t = useTranslations();
  const format = useFormatter();
  const locale = useAppLocale();
  const { data, isLoading, error } = usePortfolio();
  const sync = usePortfolioSync();
  const upload = usePortfolioImport();
  const fileInput = useRef<HTMLInputElement>(null);
  const runImport = async (file: File) => {
    try {
      const result = await upload.mutateAsync(file);
      toast.success(t("portfolio.importSuccess", result.counts));
    } catch (e) {
      toast.error(
        t(
          e instanceof ApiError && e.detail === "flex_invalid"
            ? "portfolio.importInvalid"
            : e instanceof ApiError && e.status === 413
              ? "portfolio.importTooLarge"
              : "portfolio.importFailed",
        ),
      );
    }
  };
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);

  const runSync = async () => {
    try {
      await sync.mutateAsync();
      toast.success(t("portfolio.syncQueued"));
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : "";
      toast.error(
        detail === "flex_unconfigured"
          ? t("portfolio.flexUnconfigured")
          : detail === "queue_unavailable"
            ? t("portfolio.queueUnavailable")
            : t("portfolio.syncFailed"),
      );
    }
  };

  if (isLoading) return <div className="card h-96 animate-pulse" />;
  if (error) return <p className="card p-6 text-warn">{t("system.unreachable")}</p>;

  const portfolio = data as PortfolioOut;
  const syncLine = portfolio.last_sync?.finished_at
    ? t("portfolio.lastSync", { time: format.relativeTime(new Date(portfolio.last_sync.finished_at), new Date()) })
    : t("portfolio.never");

  const header = (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="label">{t("portfolio.total")}</div>
        {portfolio.total_value != null ? (
          <AnimatedNumber
            value={portfolio.total_value}
            format={(v) => formatMoney(locale, v, portfolio.base_currency, 0)}
            className="text-[28px] leading-9 font-medium"
          />
        ) : (
          <div className="num text-[28px] leading-9 text-text-3">—</div>
        )}
        <div className="mt-1 flex flex-wrap gap-2 text-xs text-text-3">
          {portfolio.as_of && <span>{t("portfolio.asOf", { date: format.dateTime(new Date(portfolio.as_of), { dateStyle: "medium" }) })}</span>}
          <span>· {syncLine}</span>
          {portfolio.last_sync?.status === "failed" && (
            <span role="status" className="rounded-full bg-neg-soft px-1.5 leading-5 font-medium text-neg">
              {t("portfolio.lastSyncFailed", { detail: portfolio.last_sync.detail ?? "" })}
            </span>
          )}
          {portfolio.source === "demo" && (
            <span className="rounded-full bg-warn-soft px-1.5 leading-5 font-medium text-warn">{t("provenance.demo")}</span>
          )}
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <input
          ref={fileInput}
          type="file"
          hidden
          accept=".xml,application/xml,text/xml"
          aria-label={t("portfolio.import")}
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void runImport(file);
          }}
        />
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          disabled={upload.isPending || sync.isPending}
          className="h-10 rounded-md border border-border px-4 font-medium hover:bg-surface-2 disabled:opacity-60"
        >
          {upload.isPending ? t("portfolio.importing") : t("portfolio.import")}
        </button>
        <button
          type="button"
          onClick={runSync}
          disabled={sync.isPending || upload.isPending}
          className="h-10 rounded-md border border-border px-4 font-medium hover:bg-surface-2 disabled:opacity-60"
        >
          {sync.isPending ? t("portfolio.syncing") : t("portfolio.sync")}
        </button>
      </div>
    </div>
  );

  if (!portfolio.positions.length) {
    return (
      <div className="flex flex-col gap-5">
        {header}
        <section className="card flex flex-col gap-2 p-8">
          <h2 className="text-lg font-semibold">{t("portfolio.emptyTitle")}</h2>
          <p className="max-w-2xl text-text-2">{t("portfolio.emptyBody")}</p>
        </section>
      </div>
    );
  }

  const tiles: TreemapItem[] = portfolio.positions.map((p) => ({
    symbol: p.symbol,
    change: Number(p.change_pct ?? 0),
    weight: Number(p.weight_pct ?? 0),
    thesis: "none",
  }));

  return (
    <div className="flex flex-col gap-5">
      {header}
      <section className="card p-4">
        <Treemap items={tiles} height={240} />
      </section>
      <section className="card overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-[13px]">
          <thead>
            <tr className="bg-surface-2 text-left">
              {(["instrument", "quantity", "price", "value", "weight", "pnl", "today"] as const).map((col, i) => (
                <th key={col} className={cn("label px-4 py-2.5", i > 0 && "text-right")}>
                  {t(`portfolio.col.${col}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <AnimatePresence initial={false}>
              {portfolio.positions.map((p) => {
                const key = `instrument:${p.symbol}`;
                return (
                  <motion.tr
                    key={p.symbol}
                    layout
                    {...listItem}
                    onMouseEnter={() => setHovered(key)}
                    onMouseLeave={() => setHovered(null)}
                    className={cn("border-t border-border", hovered === key && "bg-accent-soft")}
                  >
                    <td className="px-4 py-3">
                      <EntityLink entity={{ kind: "instrument", id: p.symbol }} />
                      <div className="max-w-[260px] truncate text-xs text-text-3">{p.name}</div>
                    </td>
                    <td className="num px-4 py-3 text-right">{formatNumber(locale, p.quantity, 0)}</td>
                    <td className="num px-4 py-3 text-right">{p.market_price == null ? "—" : formatMoney(locale, p.market_price, p.currency)}</td>
                    <td className="num px-4 py-3 text-right">{p.market_value == null ? "—" : formatMoney(locale, p.market_value, p.currency, 0)}</td>
                    <td className="px-4 py-3 text-right">
                      <span className="inline-flex items-center gap-2">
                        <span className="h-1.5 w-14 overflow-hidden rounded-full bg-surface-2">
                          <span className="block h-1.5 rounded-full bg-accent" style={{ width: `${Math.min(100, Number(p.weight_pct ?? 0) * 3)}%` }} />
                        </span>
                        <span className="num w-12">{p.weight_pct == null ? "—" : `${formatNumber(locale, p.weight_pct, 1)} %`}</span>
                      </span>
                    </td>
                    <td className={cn("num px-4 py-3 text-right", Number(p.unrealized_pnl ?? 0) >= 0 ? "text-pos" : "text-neg")}>
                      {p.unrealized_pnl == null ? "—" : formatMoney(locale, p.unrealized_pnl, p.currency, 0)}
                    </td>
                    <td className={cn("num px-4 py-3 text-right", Number(p.change_pct ?? 0) >= 0 ? "text-pos" : "text-neg")}>
                      {p.change_pct == null ? "—" : formatChange(locale, p.change_pct)}
                    </td>
                  </motion.tr>
                );
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </section>
      {portfolio.cash.length > 0 && (
        <section className="card flex flex-wrap items-center gap-4 px-4 py-3 text-[13px]">
          <span className="label">{t("portfolio.cash")}</span>
          {portfolio.cash.map((c) => (
            <span key={c.currency} className="num">{formatMoney(locale, Number(c.amount), c.currency, 0)}</span>
          ))}
        </section>
      )}
    </div>
  );
}
