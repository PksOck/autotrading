"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { EntityLink } from "@/components/common/EntityLink";
import { useEntries } from "@/lib/api/hooks";
import type { EntryOut, EntryView } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatChange, formatMoney, formatNumber } from "@/lib/format";
import { listItem, spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";
import { openProposalComposer } from "@/stores/proposals";
import { useFocusStore } from "@/stores/focus";
import { CauseBadge } from "./CauseBadge";
import { EntryMap } from "./EntryMap";
import { EntryZoneBar } from "./EntryZoneBar";
import { LadderTable } from "./LadderTable";

const VIEWS: EntryView[] = ["all", "portfolio", "watchlist"];
type Filter = "active" | "reach" | "near" | "all";
const FILTERS: Filter[] = ["active", "reach", "near", "all"];
const STATE_STYLE: Record<string, string> = {
  in_zone: "bg-pos-soft text-pos",
  below: "bg-warn-soft text-warn",
  near: "bg-accent-soft text-accent",
  far: "bg-surface-2 text-text-3",
};

const n = (v: number | string | null | undefined) => (v == null ? null : Number(v));

function matches(e: EntryOut, filter: Filter) {
  if (filter === "active") return e.rules.length > 0;
  if (filter === "reach") return e.state === "in_zone" || e.state === "below";
  if (filter === "near") return e.state === "near";
  return true;
}

function RuleList({ entry }: { entry: EntryOut }) {
  const t = useTranslations("entriesPage.rules");
  const locale = useAppLocale();
  const v = (key: string, digits = 1) =>
    formatNumber(locale, entry.rules.find((r) => key in r.values)?.values[key] ?? 0, digits);
  if (!entry.rules.length) return <p className="text-[13px] text-text-3">{t("none")}</p>;
  return (
    <ul className="flex flex-col gap-1.5 text-[13px]">
      {entry.rules.map((r) => (
        <li key={r.rule} className="flex items-baseline gap-2">
          <span className="size-1.5 shrink-0 translate-y-[-1px] rounded-full bg-accent" />
          <span>
            <span className="font-medium">{t(`${r.rule}.name`)}</span>
            <span className="text-text-2">
              {" · "}
              {t(`${r.rule}.detail`, {
                rsi: v("rsi14"),
                sma50: v("sma50", 2),
                level: v("sma200" in r.values ? "sma200" : "swing_low", 2),
                drawdown: v("drawdown_pct"),
                z: v("reaction_z"),
                filings: v("filings", 0),
                share: formatNumber(locale, (r.values.cheap_share ?? 0) * 100, 0),
              })}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function Valuation({ entry }: { entry: EntryOut }) {
  const t = useTranslations("entriesPage.valuation");
  const locale = useAppLocale();
  const bands = (["pe", "ev_ebit", "fcf_yield"] as const)
    .map((k) => [k, entry.valuation?.[k]] as const)
    .filter(
      (
        b,
      ): b is [
        (typeof b)[0],
        {
          current: number;
          median: number;
          p20: number;
          p80: number;
          percentile: number;
          cheap: boolean | null;
        },
      ] => !!b[1],
    );
  if (!bands.length)
    return <p className="text-[13px] text-text-3">{entry.kind === "etf" ? t("etf") : t("none")}</p>;
  return (
    <ul className="flex flex-col gap-3">
      {bands.map(([key, b]) => {
        const min = Math.min(b.p20, b.current) * 0.9;
        const max = Math.max(b.p80, b.current) * 1.1;
        const pos = (v: number) => `${((v - min) / (max - min)) * 100}%`;
        return (
          <li key={key} className="flex flex-col gap-1 text-[13px]">
            <div className="flex justify-between">
              <span>{t(key)}</span>
              <span className="num">
                {formatNumber(locale, b.current, 1)}
                <span className="text-text-3">
                  {" "}
                  / {t("median")} {formatNumber(locale, b.median, 1)}
                </span>
                {b.cheap != null && (
                  <span className={cn("ml-2 text-xs", b.cheap ? "text-pos" : "text-text-3")}>
                    {b.cheap ? t("cheap") : t("rich")}
                  </span>
                )}
              </span>
            </div>
            <div className="relative h-1.5 rounded-full bg-surface-2">
              <span
                className="absolute inset-y-0 rounded-full bg-border"
                style={{ left: pos(b.p20), width: `calc(${pos(b.p80)} - ${pos(b.p20)})` }}
              />
              <span
                className="absolute -inset-y-0.5 w-px bg-text-3"
                style={{ left: pos(b.median) }}
              />
              <motion.span
                className={cn(
                  "absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full",
                  b.cheap ? "bg-pos" : "bg-text",
                )}
                initial={false}
                animate={{ left: pos(b.current) }}
                transition={spring.soft}
              />
            </div>
          </li>
        );
      })}
      <li className="text-xs text-text-3">{t("note")}</li>
    </ul>
  );
}

function Detail({ entry }: { entry: EntryOut }) {
  const t = useTranslations();
  const format = useFormatter();
  const locale = useAppLocale();
  const price = n(entry.price)!;
  return (
    <motion.div
      key={entry.symbol}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col gap-5"
    >
      <div className="flex flex-wrap items-center gap-2">
        <EntityLink entity={{ kind: "instrument", id: entry.symbol }} className="text-lg" />
        <span className="text-text-2">{entry.name}</span>
        <CauseBadge cause={entry.cause} className="ml-auto" />
      </div>
      <div className="flex items-baseline gap-3">
        <span className="num text-2xl font-semibold">
          {entry.currency
            ? formatMoney(locale, price, entry.currency)
            : formatNumber(locale, price, 2)}
        </span>
        {entry.drawdown_pct != null && (
          <span className="num text-[13px] text-neg">
            {formatChange(locale, Number(entry.drawdown_pct))} {t("entry.drawdown").toLowerCase()}
          </span>
        )}
      </div>
      <EntryZoneBar
        price={price}
        zoneLow={n(entry.zone_low)}
        zoneHigh={n(entry.zone_high)}
        stop={n(entry.stop)}
      />

      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-medium tracking-wide text-text-3 uppercase">
          {t("entry.cause.label")}
        </h3>
        {entry.dip_rationale ? (
          <>
            <p className="text-text-2">{entry.dip_rationale}</p>
            <p className="text-xs text-text-3">
              {entry.thesis_intact === false
                ? t("entriesPage.thesisBroken")
                : t("entry.thesisIntact")}
              {entry.dip_model && ` · ${entry.dip_model}`}
              {entry.analyzed_at &&
                ` · ${format.relativeTime(new Date(entry.analyzed_at), new Date())}`}
            </p>
            {(entry.dip_evidence ?? []).length > 0 && (
              <ul className="text-[13px]">
                {(entry.dip_evidence ?? []).map((ev) => (
                  <li key={String(ev.ref_id)}>
                    <Link href={`/radar?event=${ev.ref_id}`} className="text-accent">
                      {String(ev.label)}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p className="text-[13px] text-text-3">
            {entry.rules.length ? t("entriesPage.analysisPending") : t("entriesPage.noDip")}
          </p>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-medium tracking-wide text-text-3 uppercase">
          {t("entriesPage.rulesTitle")}
        </h3>
        <RuleList entry={entry} />
      </section>
      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-medium tracking-wide text-text-3 uppercase">
          {t("entriesPage.valuationTitle")}
        </h3>
        <Valuation entry={entry} />
      </section>
      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-medium tracking-wide text-text-3 uppercase">
          {t("entry.ladder")}
        </h3>
        <LadderTable
          levels={(entry.ladder ?? []).map((l) => ({
            price: Number(l.price),
            weight: Number(l.weight),
          }))}
          currency={entry.currency}
        />
      </section>

      <div className="flex flex-wrap gap-2">
        {entry.signal_id && (
          <Link
            href={`/signals?peek=signal:${entry.signal_id}`}
            className="inline-flex h-9 items-center rounded-md bg-accent px-3 text-[13px] font-medium text-on-accent"
          >
            {t("entriesPage.openSignal")}
          </Link>
        )}
        <button
          type="button"
          onClick={() =>
            openProposalComposer({ symbols: [entry.symbol], hypothesis: entry.dip_rationale ?? "" })
          }
          className="h-9 rounded-md border border-border px-3 text-[13px] font-medium hover:bg-surface-2"
        >
          {t("entriesPage.analyze")}
        </button>
        <Link
          href={`/i/${entry.symbol}`}
          className="inline-flex h-9 items-center rounded-md border border-border px-3 text-[13px] font-medium hover:bg-surface-2"
        >
          {t("entriesPage.openInstrument")}
        </Link>
      </div>
      <p className="text-xs text-text-3">
        {t("provenance.source")}: {entry.source} ·{" "}
        {format.dateTime(new Date(entry.as_of), { dateStyle: "medium" })}
      </p>
    </motion.div>
  );
}

/** SCR-03 Vstopi (BL-064): entry candidates, map (OV-05), zone, cause, ladder. */
export function EntriesView() {
  const t = useTranslations();
  const locale = useAppLocale();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const view = (
    VIEWS.includes(params.get("view") as EntryView) ? params.get("view") : "all"
  ) as EntryView;
  const [filter, setFilter] = useState<Filter>("active");
  const { data, isLoading, error } = useEntries(view);
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);

  const entries = useMemo(() => (data ?? []).filter((e) => matches(e, filter)), [data, filter]);
  const selectedSymbol = params.get("symbol");
  const selected = entries.find((e) => e.symbol === selectedSymbol) ?? entries[0] ?? null;
  const counts = useMemo(
    () =>
      Object.fromEntries(FILTERS.map((f) => [f, (data ?? []).filter((e) => matches(e, f)).length])),
    [data],
  );

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params.toString());
    if (value === null) next.delete(key);
    else next.set(key, value);
    if (key === "view") next.delete("symbol");
    router.replace(next.size ? `${pathname}?${next}` : pathname, { scroll: false });
  };

  return (
    <div className="flex flex-col gap-5">
      <div
        role="tablist"
        aria-label={t("radar.viewsLabel")}
        className="flex flex-wrap border-b border-border"
      >
        {VIEWS.map((key) => (
          <button
            key={key}
            role="tab"
            aria-selected={view === key}
            onClick={() => setParam("view", key === "all" ? null : key)}
            className={cn(
              "relative h-11 px-4 font-medium text-text-2",
              view === key && "text-accent",
            )}
          >
            {t(`entriesPage.views.${key}`)}
            {view === key && (
              <motion.span
                layoutId="entries-tab"
                transition={spring.snappy}
                className="absolute inset-x-0 -bottom-px h-0.5 bg-accent"
              />
            )}
          </button>
        ))}
      </div>

      <div
        role="group"
        aria-label={t("radar.filtersLabel")}
        className="flex flex-wrap items-center gap-2"
      >
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={cn(
              "h-9 rounded-full border border-border px-3 text-[13px] text-text-2 hover:bg-surface-2",
              filter === f && "border-accent bg-accent-soft font-medium text-accent",
            )}
          >
            {t(`entriesPage.filters.${f}`)}{" "}
            <span className="num text-text-3">{counts[f] ?? 0}</span>
          </button>
        ))}
      </div>

      {data && data.length > 0 && (
        <section className="card p-4" aria-label={t("entriesPage.map.label")}>
          <EntryMap
            entries={data.filter((e) => matches(e, filter))}
            selected={selected?.symbol}
            onSelect={(s) => setParam("symbol", s)}
          />
        </section>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
        <section className="card overflow-hidden" aria-label={t("entriesPage.listLabel")}>
          {isLoading && <div className="h-80 animate-pulse bg-surface-2" />}
          {error && <p className="p-6 text-warn">{t("system.unreachable")}</p>}
          {data && entries.length === 0 && (
            <p className="p-6 text-text-3">{t(`entriesPage.empty.${filter}`)}</p>
          )}
          <ul>
            <AnimatePresence initial={false}>
              {entries.map((e) => {
                const active = selected?.symbol === e.symbol;
                const linked = hovered === `instrument:${e.symbol}`;
                return (
                  <motion.li
                    key={e.symbol}
                    layout
                    {...listItem}
                    className="border-t border-border first:border-t-0"
                  >
                    <button
                      type="button"
                      aria-pressed={active}
                      onClick={() => setParam("symbol", e.symbol)}
                      onMouseEnter={() => setHovered(`instrument:${e.symbol}`)}
                      onMouseLeave={() => setHovered(null)}
                      className={cn(
                        "flex w-full flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-left hover:bg-surface-2",
                        active && "bg-accent-soft",
                        linked && !active && "bg-surface-2",
                      )}
                    >
                      <span className="flex w-28 flex-col">
                        <span className="num font-medium">{e.symbol}</span>
                        <span className="text-xs text-text-3">
                          {e.held
                            ? t("entriesPage.held")
                            : e.watched
                              ? t("entriesPage.watched")
                              : ""}
                        </span>
                      </span>
                      <span className="num w-20 text-right text-[13px]">
                        {formatNumber(locale, Number(e.price), 2)}
                      </span>
                      <span
                        className={cn(
                          "num w-16 text-right text-[13px]",
                          Number(e.drawdown_pct) < 0 ? "text-neg" : "text-text-2",
                        )}
                      >
                        {e.drawdown_pct == null
                          ? "—"
                          : formatChange(locale, Number(e.drawdown_pct), 0).replace(/^[▲▼] /, "")}
                      </span>
                      <span className="min-w-28 flex-1">
                        <EntryZoneBar
                          compact
                          price={Number(e.price)}
                          zoneLow={n(e.zone_low)}
                          zoneHigh={n(e.zone_high)}
                          stop={n(e.stop)}
                        />
                      </span>
                      <span
                        className={cn(
                          "rounded-full px-2 text-xs leading-5 font-medium",
                          STATE_STYLE[e.state ?? "far"],
                        )}
                      >
                        {e.state
                          ? t(`entriesPage.state.${e.state}`, {
                              atr: formatNumber(locale, Math.abs(Number(e.distance_atr ?? 0)), 1),
                            })
                          : "—"}
                      </span>
                      <span className="w-20">
                        {e.rules.length > 0 && <CauseBadge cause={e.cause} />}
                      </span>
                    </button>
                  </motion.li>
                );
              })}
            </AnimatePresence>
          </ul>
        </section>
        <aside
          className="card flex flex-col gap-4 p-5 lg:sticky lg:top-24 lg:self-start"
          aria-label={t("entriesPage.detailLabel")}
        >
          <AnimatePresence mode="wait">
            {selected ? (
              <Detail entry={selected} />
            ) : (
              <p className="text-text-3">{t("entriesPage.pick")}</p>
            )}
          </AnimatePresence>
        </aside>
      </div>
    </div>
  );
}
