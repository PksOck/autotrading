"use client";

import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { AnimatedNumber } from "@/components/common/AnimatedNumber";
import { EntityLink } from "@/components/common/EntityLink";
import { Sparkline } from "@/components/overview/Sparkline";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import { listItem, spring } from "@/lib/motion";
import { INSTRUMENTS, sparkSeries } from "@/lib/sample-data";
import { useAppLocale } from "@/lib/use-app-locale";

const TOKENS = [
  "bg", "surface", "surface-2", "border", "text", "text-2", "text-3", "accent",
  "accent-soft", "pos", "pos-soft", "neg", "neg-soft", "warn", "warn-soft", "rumor", "rumor-soft",
];

function Demo({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section className="card flex flex-col gap-4 p-5">
      <h2 className="flex items-baseline gap-2 text-base font-semibold">
        <span className="num text-xs text-accent">{id}</span>
        {title}
      </h2>
      {children}
    </section>
  );
}

export function UxDemos() {
  const t = useTranslations();
  const locale = useAppLocale();
  const [price, setPrice] = useState(406.8);
  const [events, setEvents] = useState(INSTRUMENTS.slice(0, 3).map((i, n) => ({ id: n, symbol: i.symbol })));
  const [tab, setTab] = useState<"discover" | "watchlist" | "portfolio">("discover");
  const [expanded, setExpanded] = useState(false);

  const addEvent = () => {
    const pick = INSTRUMENTS[(events.length * 5) % INSTRUMENTS.length]!;
    setEvents((list) => [{ id: Date.now(), symbol: pick.symbol }, ...list].slice(0, 6));
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Demo id="§2" title={t("ux.demo.tokens")}>
        <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3 text-xs">
          {TOKENS.map((token) => (
            <div key={token} className="flex items-center gap-2">
              <span className="h-8 w-8 shrink-0 rounded-md border border-border" style={{ background: `var(--${token})` }} />
              <span className="num">--{token}</span>
            </div>
          ))}
        </div>
      </Demo>

      <Demo id="MO-04" title="AnimatedNumber">
        <div className="flex items-center gap-4">
          <AnimatedNumber value={price} format={(v) => formatMoney(locale, v)} className="text-2xl font-medium" />
          <Sparkline values={sparkSeries("MSFT", price)} width={120} height={32} />
        </div>
        <button
          type="button"
          onClick={() => setPrice((p) => Math.round(p * (1 + (Math.random() - 0.5) * 0.04) * 100) / 100)}
          className="h-10 self-start rounded-md border border-border px-4 font-medium hover:bg-surface-2"
        >
          {t("ux.change")}
        </button>
      </Demo>

      <Demo id="MO-03" title={t("ux.demo.liveList")}>
        <ul className="flex flex-col gap-2">
          <AnimatePresence initial={false}>
            {events.map((event) => (
              <motion.li
                key={event.id}
                layout
                {...listItem}
                className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-2"
              >
                <EntityLink entity={{ kind: "instrument", id: event.symbol }} />
                <button
                  type="button"
                  onClick={() => setEvents((list) => list.filter((e) => e.id !== event.id))}
                  className="h-8 rounded-md px-2 text-[13px] text-text-2 hover:bg-surface"
                >
                  {t("ux.removeEvent")}
                </button>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
        <button type="button" onClick={addEvent} className="h-10 self-start rounded-md bg-accent px-4 font-medium text-on-accent">
          {t("ux.addEvent")}
        </button>
      </Demo>

      <Demo id="MO-02" title={t("ux.demo.slider")}>
        <div role="tablist" className="flex border-b border-border">
          {(["discover", "watchlist", "portfolio"] as const).map((key) => (
            <button
              key={key}
              role="tab"
              aria-selected={tab === key}
              onClick={() => setTab(key)}
              className={cn("relative h-11 px-4 font-medium text-text-2", tab === key && "text-accent")}
            >
              {t(`view.${key}`)}
              {tab === key && (
                <motion.span layoutId="ux-tab" transition={spring.snappy} className="absolute inset-x-0 -bottom-px h-0.5 bg-accent" />
              )}
            </button>
          ))}
        </div>
      </Demo>

      <Demo id="MO-01" title={t("ux.demo.shared")}>
        <LayoutGroup>
          <motion.button
            type="button"
            layout
            transition={spring.soft}
            onClick={() => setExpanded((e) => !e)}
            aria-expanded={expanded}
            className={cn("card flex flex-col items-start gap-2 p-4 text-left", expanded && "bg-accent-soft")}
          >
            <motion.span layout="position" className="num text-lg font-medium">
              MSFT
            </motion.span>
            <AnimatePresence initial={false}>
              {expanded && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-text-2"
                >
                  {t("ux.demo.sharedDetail")}
                </motion.span>
              )}
            </AnimatePresence>
            <motion.span layout="position" className="text-xs text-accent">
              {expanded ? t("ux.collapse") : t("ux.expand")}
            </motion.span>
          </motion.button>
        </LayoutGroup>
      </Demo>

      <Demo id="MO-10 · LX-01" title={t("ux.demo.undoEntities")}>
        <p className="text-text-2">
          <EntityLink entity={{ kind: "instrument", id: "ASML" }} /> · <EntityLink entity={{ kind: "instrument", id: "VWRA" }} /> ·{" "}
          <EntityLink entity={{ kind: "instrument", id: "IUES" }} />
        </p>
        <button
          type="button"
          onClick={() =>
            toast(t("ux.dismissed"), { action: { label: t("proposal.undo"), onClick: () => toast(t("proposal.undone")) } })
          }
          className="h-10 self-start rounded-md border border-border px-4 font-medium hover:bg-surface-2"
        >
          {t("ux.toast")}
        </button>
        <p className="text-xs text-text-3">{t("ux.reduced")}</p>
      </Demo>
    </div>
  );
}
