"use client";

import { AnimatePresence, motion } from "motion/react";
import { useFormatter, useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { EntityLink } from "@/components/common/EntityLink";
import { TranslatedText } from "@/components/common/TranslatedText";
import { useSignalUpdate, useSignals } from "@/lib/api/hooks";
import type { SignalOut, SignalStatus } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { formatNumber } from "@/lib/format";
import { listItem, spring } from "@/lib/motion";
import { useAppLocale } from "@/lib/use-app-locale";

const TABS: SignalStatus[] = ["new", "watching", "accepted", "dismissed", "expired"];
const KIND_STYLE: Record<string, string> = {
  catalyst: "bg-pos-soft text-pos",
  entry: "bg-accent-soft text-accent",
  exit_warning: "bg-warn-soft text-warn",
  thesis_break: "bg-neg-soft text-neg",
  options_idea: "bg-surface-2 text-text-2",
};

function SignalCard({ signal }: { signal: SignalOut }) {
  const t = useTranslations();
  const format = useFormatter();
  const locale = useAppLocale();
  const update = useSignalUpdate();

  const setStatus = async (status: SignalStatus, message: string) => {
    const previous = signal.status;
    try { await update.mutateAsync({ id: signal.id, status }); }
    catch { toast.error(t("researchUx.actionFailed")); return; }
    toast(message, {
      action: { label: t("proposal.undo"), onClick: () => update.mutate({ id: signal.id, status: previous }) },
    });
  };

  return (
    <motion.li
      layout
      {...listItem}
      className={cn("card flex flex-col gap-3 p-4", signal.is_rumor && "border-dashed border-rumor")}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className={cn("rounded-full px-2 text-xs leading-5 font-medium", signal.is_rumor ? "bg-rumor-soft text-rumor" : KIND_STYLE[signal.kind])}>
          {signal.is_rumor ? t("radar.rumor") : t(`signal.kind.${signal.kind}`)}
        </span>
        <EntityLink entity={{ kind: "instrument", id: signal.symbol }} className="text-base" />
        <span className="rounded-full bg-surface-2 px-2 text-xs leading-5 text-text-2">
          {t(`signalsPage.source.${signal.source}`)} · {t(`signalsPage.direction.${signal.direction}`)} · {t(`signal.horizon.${signal.horizon}`)}
        </span>
        <span className="ml-auto flex items-center gap-2 text-xs text-text-3">
          {t("signal.strength")}
          <span className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2">
            <motion.span className="block h-1.5 origin-left rounded-full bg-accent" initial={{ scaleX: 0 }} animate={{ scaleX: Number(signal.strength) }} transition={spring.soft} />
          </span>
          <span className="num text-text">{formatNumber(locale, Number(signal.strength), 2)}</span>
        </span>
      </div>
      <p className="text-text-2">
        <TranslatedText original={signal.rationale} translations={signal.rationale_translations} />
      </p>
      {signal.evidence.length > 0 && (
        <details className="text-[13px]">
          <summary className="cursor-pointer text-text-3">
            {t("signalsPage.evidence")} ({signal.evidence.length})
          </summary>
          <ul className="mt-2 flex flex-col gap-1">
            {signal.evidence.map((e, i) => (
              <li key={`${e.label}-${i}`}>
                {e.url ? (
                  <a href={e.url} target="_blank" rel="noreferrer" className="text-accent">{e.label}</a>
                ) : (
                  <span className="text-text-2">{e.label}</span>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        <span className="text-text-3">
          {format.relativeTime(new Date(signal.created_at), new Date())}
          {signal.expires_at && ` · ${t("signalsPage.expires", { time: format.relativeTime(new Date(signal.expires_at), new Date()) })}`}
        </span>
        <span className="ml-auto flex flex-wrap gap-2" aria-busy={update.isPending}>
          {update.isPending && <span role="status">{t("researchUx.pending")}</span>}
          <EntityLink entity={{kind:"signal", id:signal.id}}>{t("signalsPage.evidence")}</EntityLink>
          {signal.status !== "expired" && <>
          {signal.status !== "accepted" && (
            <button
              type="button"
              disabled={signal.is_rumor || update.isPending}
              title={signal.is_rumor ? t("signalsPage.rumorCannotAccept") : undefined}
              onClick={() => setStatus("accepted", t("signalsPage.accepted"))}
              className="h-9 rounded-md bg-accent px-3 font-medium text-on-accent hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {t("action.accept")}
            </button>
          )}
          {signal.status !== "watching" && (
            <button type="button" disabled={update.isPending} onClick={() => setStatus("watching", t("signalsPage.watched"))} className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2 disabled:opacity-40">
              {t("action.watch")}
            </button>
          )}
          {signal.status !== "dismissed" && (
            <button type="button" disabled={update.isPending} onClick={() => setStatus("dismissed", t("signalsPage.dismissed"))} className="h-9 rounded-md border border-border px-3 font-medium hover:bg-surface-2 disabled:opacity-40">
              {t("action.dismiss")}
            </button>
          )}
          </>}
        </span>
      </div>
    </motion.li>
  );
}

/** SCR-04 Signals inbox (BL-050). Status tab lives in the URL. */
export function SignalsInbox() {
  const t = useTranslations();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const tab = (TABS.includes(params.get("status") as SignalStatus) ? params.get("status") : "new") as SignalStatus;
  const { data, isLoading, error } = useSignals(tab);

  return (
    <div className="flex flex-col gap-5">
      <div role="tablist" className="flex flex-wrap border-b border-border">
        {TABS.map((key) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => {const next = new URLSearchParams(params.toString()); next.set("status",key); router.replace(`${pathname}?${next}`, {scroll:false});}}
            className={cn("relative h-11 px-4 font-medium text-text-2", tab === key && "text-accent")}
          >
            {key === "expired" ? t("researchUx.expired") : t(`signalsPage.tabs.${key}`)}
            {tab === key && <motion.span layoutId="signals-tab" transition={spring.snappy} className="absolute inset-x-0 -bottom-px h-0.5 bg-accent" />}
          </button>
        ))}
      </div>
      {isLoading && <div className="card h-40 animate-pulse" />}
      {error && <p className="card p-6 text-warn">{t("system.unreachable")}</p>}
      {data && data.length === 0 && <p className="card p-6 text-text-3">{t("signalsPage.empty")}</p>}
      <ul className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {data?.map((signal) => <SignalCard key={signal.id} signal={signal} />)}
        </AnimatePresence>
      </ul>
    </div>
  );
}
