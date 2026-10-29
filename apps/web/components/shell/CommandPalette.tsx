"use client";

import { Command } from "cmdk";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { setLocale } from "@/app/actions";
import { Icon } from "@/components/common/Icon";
import { NAV } from "@/lib/nav";
import { useInstrumentSearch } from "@/lib/api/hooks";
import { nextThemePreference, readThemePreference, setThemePreference } from "@/lib/theme";
import { usePeek } from "@/lib/use-peek";
import { useBackToClose } from "@/lib/useBackToClose";
import { openProposalComposer, parseSymbols } from "@/stores/proposals";

export const COMMAND_EVENT = "preza:command";
export const openCommandPalette = () => window.dispatchEvent(new Event(COMMAND_EVENT));

const item =
  "flex h-11 cursor-pointer items-center gap-3 rounded-md px-3 text-text-2 data-[selected=true]:bg-accent-soft data-[selected=true]:text-text";
const group =
  "[&_[cmdk-group-heading]]:label [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:pb-1";

/** CMP-23 / LX-06: search entities and run actions. Meta+K / Ctrl+K anywhere. */
export function CommandPalette() {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const { open: peek } = usePeek();
  const [open, setOpen] = useState(false);
  const close = useBackToClose(open, () => setOpen(false));
  const [query, setQuery] = useState("");
  const [, startTransition] = useTransition();

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        if (open) close();
        else setOpen(true);
      }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener(COMMAND_EVENT, onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener(COMMAND_EVENT, onOpen);
    };
  }, [open, close]);

  const run = (action: () => void) => {
    close(() => {
      setQuery("");
      action();
    });
  };

  const search = useInstrumentSearch(open ? query : "");
  // An empty query prioritizes a short navigation menu; symbols require a search.
  const instruments = query.trim()
    ? (search.data ?? []).map((i) => ({
        symbol: i.symbol,
        name: i.name ?? "",
        hint: i.exchange ?? "",
      }))
    : [];

  const typedSymbols = parseSymbols(query);
  // Offer "propose" only once the search has answered, so Enter never races the results.
  const unknownSymbol =
    typedSymbols.length === 1 &&
    !search.isFetching &&
    !instruments.some((i) => i.symbol === typedSymbols[0])
      ? typedSymbols[0]
      : null;

  return (
    <Command.Dialog
      open={open}
      onOpenChange={(next) => (next ? setOpen(true) : close())}
      label={t("command.placeholder")}
      overlayClassName="fixed inset-0 z-50 bg-black/40"
      contentClassName="card fixed top-[12vh] left-1/2 z-50 w-[min(640px,calc(100vw-32px))] -translate-x-1/2 overflow-hidden shadow-float data-[state=open]:animate-[fadeIn_var(--dur-base)_var(--ease-standard)]"
    >
      <div className="flex items-center gap-2 border-b border-border px-4">
        <Icon name="search" size={16} />
        <Command.Input
          value={query}
          onValueChange={setQuery}
          placeholder={t("command.placeholder")}
          className="h-12 flex-1 bg-transparent text-[15px] outline-none placeholder:text-text-3"
        />
      </div>
      <Command.List className="max-h-[60vh] overflow-y-auto p-2">
        <Command.Empty className="px-3 py-6 text-center text-text-3">
          {t("command.empty")}
        </Command.Empty>

        <Command.Group heading={t("command.groupInstruments")} className={group}>
          {instruments.map((instrument) => (
            <Command.Item
              key={instrument.symbol}
              value={`${instrument.symbol} ${instrument.name} ${instrument.hint}`}
              onSelect={() => run(() => peek({ kind: "instrument", id: instrument.symbol }))}
              className={item}
            >
              <span className="num w-14 font-medium text-text">{instrument.symbol}</span>
              <span className="flex-1 truncate">{instrument.name}</span>
              {instrument.hint && (
                <span className="num text-xs text-text-3">{instrument.hint}</span>
              )}
            </Command.Item>
          ))}
        </Command.Group>

        {unknownSymbol && (
          <Command.Group heading={t("command.groupActions")} className={group}>
            <Command.Item
              value={`propose ${unknownSymbol}`}
              onSelect={() => run(() => openProposalComposer({ symbols: [unknownSymbol] }))}
              className={item}
            >
              <Icon name="proposals" />
              {t("command.proposeQuery", { query: unknownSymbol })}
            </Command.Item>
          </Command.Group>
        )}

        <Command.Group heading={t("command.groupNav")} className={group}>
          {NAV.map((nav) => (
            <Command.Item
              key={nav.href}
              value={`${t(`nav.${nav.key}`)} ${nav.screen}`}
              onSelect={() => run(() => router.push(nav.href))}
              className={item}
            >
              <Icon name={nav.key} />
              <span className="flex-1">{t(`nav.${nav.key}`)}</span>
              {nav.shortcut && <kbd className="num text-xs text-text-3">g {nav.shortcut}</kbd>}
            </Command.Item>
          ))}
        </Command.Group>

        <Command.Group heading={t("command.groupActions")} className={group}>
          <Command.Item
            value="propose new"
            onSelect={() => run(() => openProposalComposer())}
            className={item}
          >
            <Icon name="proposals" />
            <span className="flex-1">{t("command.propose")}</span>
            <kbd className="num text-xs text-text-3">+</kbd>
          </Command.Item>
          <Command.Item
            value="theme"
            onSelect={() =>
              run(() => setThemePreference(nextThemePreference(readThemePreference())))
            }
            className={item}
          >
            <Icon name="sun" />
            {t("command.toggleTheme")}
          </Command.Item>
          <Command.Item
            value="language jezik"
            onSelect={() =>
              run(() =>
                startTransition(async () => {
                  await setLocale(locale === "sl" ? "en" : "sl");
                  router.refresh();
                }),
              )
            }
            className={item}
          >
            <Icon name="system" />
            {t("command.switchLocale")}
          </Command.Item>
        </Command.Group>
      </Command.List>
      <div className="border-t border-border px-4 py-2 text-xs text-text-3">
        {t("command.shortcuts")}
      </div>
    </Command.Dialog>
  );
}
