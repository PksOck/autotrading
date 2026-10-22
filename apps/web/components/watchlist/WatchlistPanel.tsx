"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import { useId, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { EntityLink } from "@/components/common/EntityLink";
import { Sparkline } from "@/components/overview/Sparkline";
import { ApiError } from "@/lib/api/client";
import { useBars, useWatchlist, useWatchlistMutations } from "@/lib/api/hooks";
import type { WatchlistOut, WatchTier } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatChange, formatNumber } from "@/lib/format";
import { listItem } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";

const TIERS: WatchTier[] = ["active", "reserve"];

function RowSparkline({ symbol }: { symbol: string }) {
  const { data } = useBars(symbol, "3m", false);
  const closes = (data?.bars ?? []).map((b) => Number(b.close));
  return closes.length > 1 ? <Sparkline values={closes} width={96} height={28} /> : <span className="h-7 w-24" />;
}

function Row({ item }: { item: WatchlistOut }) {
  const t = useTranslations("watchlist");
  const format = useFormatter();
  const locale = useAppLocale();
  const { update, remove, add } = useWatchlistMutations();
  const other: WatchTier = item.tier === "active" ? "reserve" : "active";

  const onRemove = async () => {
    await remove.mutateAsync(item.id);
    toast(t("removed"), {
      action: {
        label: t("addShort"),
        onClick: () => add.mutate({ symbol: item.symbol, tier: item.tier, note: item.note, tags: item.tags }),
      },
    });
  };

  return (
    <motion.li layout {...listItem} className="card flex flex-wrap items-center gap-x-4 gap-y-2 p-4">
      <div className="min-w-[160px] flex-1">
        <div className="flex items-center gap-2">
          <EntityLink entity={{ kind: "instrument", id: item.symbol }} />
          {!item.reviewed_at && (
            <span className="rounded-full bg-accent-soft px-1.5 text-xs leading-5 font-medium text-accent">{t("new")}</span>
          )}
          {item.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-surface-2 px-1.5 text-xs leading-5 text-text-2">{tag}</span>
          ))}
        </div>
        <div className="truncate text-xs text-text-3">
          {item.name ?? ""} · {t("added", { date: format.dateTime(new Date(item.added_at), { dateStyle: "medium" }) })}
        </div>
        {item.note && <p className="mt-1 text-[13px] text-text-2">{item.note}</p>}
      </div>
      <RowSparkline symbol={item.symbol} />
      <div className="w-24 text-right">
        <div className="label">{t("sinceAdded")}</div>
        <div className={cn("num text-[13px]", Number(item.since_added_pct ?? 0) >= 0 ? "text-pos" : "text-neg")}>
          {item.since_added_pct == null ? "—" : formatChange(locale, Number(item.since_added_pct))}
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {!item.reviewed_at && (
          <button type="button" onClick={() => update.mutate({ id: item.id, data: { reviewed: true } })} className="h-9 rounded-md px-3 text-[13px] text-text-2 hover:bg-surface-2">
            {t("markReviewed")}
          </button>
        )}
        <button type="button" onClick={() => update.mutate({ id: item.id, data: { tier: other } })} className="h-9 rounded-md border border-border px-3 text-[13px] hover:bg-surface-2">
          {t("moveTo", { tier: t(`tiers.${other}`) })}
        </button>
        <button type="button" onClick={onRemove} className="h-9 rounded-md border border-border px-3 text-[13px] hover:bg-surface-2">
          {t("remove")}
        </button>
      </div>
      {item.last_close != null && item.added_price != null && (
        <span className="sr-only">{formatNumber(locale, Number(item.last_close), 2)}</span>
      )}
    </motion.li>
  );
}

/** Watchlist (BL-030, BL-032): two tiers, notes, performance since added, undo on remove. */
export function WatchlistPanel() {
  const t = useTranslations("watchlist");
  const id = useId();
  const { data, isLoading } = useWatchlist();
  const { add } = useWatchlistMutations();
  const [symbol, setSymbol] = useState("");
  const [tier, setTier] = useState<WatchTier>("active");
  const [note, setNote] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!symbol.trim()) return;
    try {
      await add.mutateAsync({ symbol: symbol.trim().toUpperCase(), tier, note: note.trim() || null });
      setSymbol("");
      setNote("");
    } catch (error) {
      toast.error(error instanceof ApiError && error.status === 409 ? t("duplicate") : String(error));
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={submit} className="card flex flex-wrap items-end gap-3 p-4" aria-label={t("add")}>
        <div className="w-36">
          <label htmlFor={`${id}-symbol`} className="label">{t("symbol")}</label>
          <input id={`${id}-symbol`} value={symbol} onChange={(e) => setSymbol(e.target.value)} autoComplete="off" className="num mt-1 h-10 w-full rounded-md border border-border bg-surface-2 px-3 uppercase focus:border-accent focus:outline-none" />
        </div>
        <div className="min-w-[200px] flex-1">
          <label htmlFor={`${id}-note`} className="label">{t("note")}</label>
          <input id={`${id}-note`} value={note} onChange={(e) => setNote(e.target.value)} className="mt-1 h-10 w-full rounded-md border border-border bg-surface-2 px-3 focus:border-accent focus:outline-none" />
        </div>
        <fieldset>
          <legend className="label">{t("tier")}</legend>
          <div className="mt-1 flex gap-0.5 rounded-md bg-surface-2 p-0.5">
            {TIERS.map((value) => (
              <label key={value} className={cn("flex h-9 cursor-pointer items-center rounded-[5px] px-3 text-[13px] font-medium text-text-2 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent", tier === value && "bg-surface text-text shadow-[0_0_0_1px_var(--border)]")}>
                <input type="radio" name={`${id}-tier`} value={value} checked={tier === value} onChange={() => setTier(value)} className="sr-only" />
                {t(`tiers.${value}`)}
              </label>
            ))}
          </div>
        </fieldset>
        <button type="submit" disabled={add.isPending} className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90 disabled:opacity-60">
          {add.isPending ? t("adding") : t("add")}
        </button>
      </form>

      {isLoading && <div className="card h-40 animate-pulse" />}
      {data && data.length === 0 && <p className="card p-6 text-text-3">{t("empty")}</p>}
      {data &&
        TIERS.map((value) => {
          const items = data.filter((w) => w.tier === value);
          if (!items.length) return null;
          return (
            <section key={value} className="flex flex-col gap-2">
              <h2 className="text-base font-semibold">
                {t(`tiers.${value}`)} <span className="num text-text-3">{items.length}</span>
              </h2>
              <ul className="flex flex-col gap-2">
                <AnimatePresence initial={false}>
                  {items.map((item) => (
                    <Row key={item.id} item={item} />
                  ))}
                </AnimatePresence>
              </ul>
            </section>
          );
        })}
    </div>
  );
}
