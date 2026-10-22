"use client";

import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { ApiError } from "@/lib/api/client";
import { useWatchlist, useWatchlistMutations } from "@/lib/api/hooks";
import { cn } from "@/lib/cn";

/** Adds or removes an instrument from the watchlist (with undo, MO-10). */
export function WatchButton({ symbol, className }: { symbol: string; className?: string }) {
  const t = useTranslations("watchlist");
  const { data } = useWatchlist();
  const { add, remove } = useWatchlistMutations();
  const item = data?.find((w) => w.symbol === symbol.toUpperCase());

  const onClick = async () => {
    try {
      if (item) {
        await remove.mutateAsync(item.id);
        toast(t("removed"), {
          action: { label: t("addShort"), onClick: () => add.mutate({ symbol, tier: item.tier, note: item.note }) },
        });
      } else {
        await add.mutateAsync({ symbol, tier: "active" });
      }
    } catch (error) {
      toast.error(error instanceof ApiError && error.status === 409 ? t("duplicate") : String(error));
    }
  };

  return (
    <button
      type="button"
      aria-pressed={Boolean(item)}
      onClick={onClick}
      disabled={add.isPending || remove.isPending}
      className={cn(
        "inline-flex h-10 items-center gap-1.5 rounded-md border px-4 font-medium transition-colors duration-[var(--dur-fast)]",
        item ? "border-accent bg-accent-soft text-accent" : "border-border hover:bg-surface-2",
        className,
      )}
    >
      <span aria-hidden>{item ? "✓" : "+"}</span>
      {item ? t("onWatchlist") : t("addShort")}
    </button>
  );
}
