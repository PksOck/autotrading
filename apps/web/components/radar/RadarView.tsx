"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { EntityLink } from "@/components/common/EntityLink";
import { useRadarEvents } from "@/lib/api/hooks";
import type { EventOut, EventType, RadarView as View } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";
import { listItem, spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";
import { openProposalComposer } from "@/stores/proposals";
import { useFocusStore } from "@/stores/focus";

const VIEWS: View[] = ["discover", "watchlist", "portfolio"];
const FILTERS: (EventType | "all")[] = ["all", "earnings", "guidance", "merger", "filing", "insider", "analyst", "macro", "rumor"];

function ScoreBar({ score }: { score: number | null }) {
  const locale = useAppLocale();
  return (
    <span className="flex w-32 items-center gap-2">
      <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-2">
        <motion.span
          className={cn("block h-1.5 origin-left rounded-full", (score ?? 0) >= 0.6 ? "bg-accent" : "bg-text-3")}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: score ?? 0 }}
          transition={spring.soft}
        />
      </span>
      <span className="num w-9 text-right text-[13px]">{score == null ? "—" : formatNumber(locale, score, 2)}</span>
    </span>
  );
}

/** SCR-02 Radar (BL-049): three views, filters, live list (MO-03) and detail panel. */
export function RadarView() {
  const t = useTranslations();
  const format = useFormatter();
  const locale = useAppLocale();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const reduceMotion = useReducedMotion();
  const view = (VIEWS.includes(params.get("view") as View) ? params.get("view") : "discover") as View;
  const selectedId = Number(params.get("event")) || null;
  const [filter, setFilter] = useState<EventType | "all">("all");
  const [minScore, setMinScore] = useState(0);
  const { data, isLoading, error } = useRadarEvents(view, minScore);
  const hovered = useFocusStore((s) => s.hovered);
  const setHovered = useFocusStore((s) => s.setHovered);

  // MO-09: events that appear while the page is open get a one-time pulse.
  const seen = useRef<Set<number> | null>(null);
  const [fresh, setFresh] = useState<Set<number>>(new Set());
  useEffect(() => {
    if (!data) return;
    const ids = new Set(data.map((e) => e.id));
    if (seen.current) {
      const added = [...ids].filter((id) => !seen.current!.has(id));
      if (added.length) setFresh(new Set(added));
    }
    seen.current = ids;
  }, [data]);

  const events = useMemo(
    () =>
      (data ?? []).filter((e) =>
        filter === "all" ? true : filter === "rumor" ? e.is_rumor : e.event_type === filter,
      ),
    [data, filter],
  );
  const selected = events.find((e) => e.id === selectedId) ?? events[0] ?? null;

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params.toString());
    if (value === null) next.delete(key);
    else next.set(key, value);
    if (key === "view") next.delete("event");
    router.replace(next.size ? `${pathname}?${next}` : pathname, { scroll: false });
  };

  const badge = (e: EventOut) =>
    e.is_rumor
      ? "border border-dashed border-rumor bg-rumor-soft text-rumor"
      : "border border-pos bg-pos-soft text-pos";

  return (
    <div className="flex flex-col gap-5">
      <div role="tablist" aria-label={t("radar.viewsLabel")} className="flex flex-wrap border-b border-border">
        {VIEWS.map((key) => (
          <button
            key={key}
            role="tab"
            aria-selected={view === key}
            onClick={() => setParam("view", key === "discover" ? null : key)}
            className={cn("relative h-11 px-4 font-medium text-text-2", view === key && "text-accent")}
          >
            {t(`view.${key}`)}
            {view === key && (
              <motion.span layoutId="radar-tab" transition={spring.snappy} className="absolute inset-x-0 -bottom-px h-0.5 bg-accent" />
            )}
          </button>
        ))}
      </div>
      <p className="-mt-2 text-[13px] text-text-3">{t(`radar.hints.${view}`)}</p>

      <div role="group" aria-label={t("radar.filtersLabel")} className="flex flex-wrap items-center gap-2">
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
            {f === "all" ? t("radar.all") : f === "rumor" ? t("radar.onlyRumors") : t(`radar.types.${f}`)}
          </button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-[13px] text-text-2">
          {t("radar.minScore")}
          <input
            type="range"
            min={0}
            max={0.9}
            step={0.1}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="accent-[var(--accent)]"
          />
          <span className="num w-8 text-text">{formatNumber(locale, minScore, 1)}</span>
        </label>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section className="card overflow-hidden" aria-label={t("radar.listLabel")}>
          {isLoading && <div className="h-80 animate-pulse bg-surface-2" />}
          {error && <p className="p-6 text-warn">{t("system.unreachable")}</p>}
          {data && events.length === 0 && <p className="p-6 text-text-3">{t(`radar.empty.${view}`)}</p>}
          <ul>
            <AnimatePresence initial={false}>
              {events.map((event) => {
                const active = selected?.id === event.id;
                const linked = event.symbols.some((s) => hovered === `instrument:${s}`);
                return (
                  <motion.li key={event.id} layout {...listItem} className="relative border-t border-border first:border-t-0">
                    {fresh.has(event.id) && !reduceMotion && (
                      <motion.span
                        aria-hidden
                        className="pointer-events-none absolute inset-0 bg-accent-soft"
                        initial={{ opacity: 1 }}
                        animate={{ opacity: 0 }}
                        transition={{ duration: 1.2 }}
                      />
                    )}
                    <button
                      type="button"
                      aria-pressed={active}
                      onClick={() => setParam("event", String(event.id))}
                      onMouseEnter={() => event.symbols[0] && setHovered(`instrument:${event.symbols[0]}`)}
                      onMouseLeave={() => setHovered(null)}
                      className={cn(
                        "relative flex w-full flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-surface-2",
                        active && "bg-accent-soft hover:bg-accent-soft",
                        linked && !active && "bg-surface-2",
                      )}
                    >
                      <span className="num w-14 text-xs text-text-3">
                        {format.dateTime(new Date(event.last_seen_at), { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-1">
                        <span className="flex flex-wrap items-center gap-2">
                          {event.symbols.slice(0, 3).map((s) => (
                            <span key={s} className="num font-medium">{s}</span>
                          ))}
                          {event.event_type && (
                            <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">{t(`radar.types.${event.event_type}`)}</span>
                          )}
                          <span className={cn("rounded-full px-2 text-xs leading-5 font-medium", badge(event))}>
                            {event.is_rumor ? t("radar.rumor") : t("radar.confirmed")}
                          </span>
                        </span>
                        <span className="text-text">{event.summary ?? event.title}</span>
                        <span className="text-xs text-text-3">
                          {(event.sources ?? []).length} · {(event.sources ?? []).map((s) => s.source).filter((v, i, a) => a.indexOf(v) === i).join(", ")}
                          {event.score == null && ` · ${t("radar.notTriaged")}`}
                        </span>
                      </span>
                      <ScoreBar score={event.score == null ? null : Number(event.score)} />
                    </button>
                  </motion.li>
                );
              })}
            </AnimatePresence>
          </ul>
        </section>

        <aside className="card flex flex-col gap-4 p-5 lg:sticky lg:top-24 lg:self-start" aria-label={t("radar.detailLabel")}>
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex flex-col gap-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  {selected.symbols.map((s) => (
                    <EntityLink key={s} entity={{ kind: "instrument", id: s }} className="text-lg" />
                  ))}
                  <span className={cn("rounded-full px-2 text-xs leading-5 font-medium", badge(selected))}>
                    {selected.is_rumor ? t("radar.rumor") : t("radar.confirmed")}
                  </span>
                </div>
                <h2 className="text-base leading-6 font-semibold">{selected.title}</h2>
                {selected.summary && <p className="text-text-2">{selected.summary}</p>}
                <dl className="grid grid-cols-2 gap-3">
                  {(
                    [
                      ["radar.materiality", selected.materiality, 2],
                      ["radar.novelty", selected.novelty, 2],
                      ["radar.attention", selected.attention, 1],
                      ["radar.reactionZ", selected.reaction_z, 1],
                    ] as const
                  ).map(([label, value, digits]) => (
                    <div key={label}>
                      <dt className="label">{t(label)}</dt>
                      <dd className="num">{value == null ? "—" : formatNumber(locale, Number(value), digits)}</dd>
                    </div>
                  ))}
                </dl>
                <div>
                  <div className="label mb-1">{t("radar.sourcesLabel")}</div>
                  <ul className="flex flex-col gap-1.5 text-[13px]">
                    {(selected.sources ?? []).slice(0, 6).map((s) => (
                      <li key={s.url}>
                        <a href={s.url} target="_blank" rel="noreferrer" className="text-accent">
                          {s.title}
                        </a>
                        <span className="text-text-3"> · {s.source} · {format.relativeTime(new Date(s.published_at), new Date())}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => openProposalComposer({ symbols: selected.symbols.slice(0, 1), hypothesis: selected.summary ?? selected.title })}
                    className="h-10 rounded-md bg-accent px-4 font-medium text-on-accent hover:opacity-90"
                  >
                    {t("action.analyze")}
                  </button>
                </div>
              </motion.div>
            ) : (
              <p className="text-text-3">{t("radar.selectHint")}</p>
            )}
          </AnimatePresence>
        </aside>
      </div>
    </div>
  );
}
