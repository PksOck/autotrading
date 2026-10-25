"use client";

import { useSyncExternalStore } from "react";

type PlatformNavigator = {
  userAgentData?: { platform?: string };
  platform?: string;
  userAgent?: string;
  maxTouchPoints?: number;
};

export function shortcutLabel(nav?: PlatformNavigator): string {
  if (!nav) return "Ctrl K";
  const platform = nav.userAgentData?.platform || nav.platform || nav.userAgent || "";
  const touchApple =
    /iPhone|iPad|iPod/i.test(`${platform} ${nav.userAgent ?? ""}`) ||
    (/Mac/i.test(platform) && (nav.maxTouchPoints ?? 0) > 1);
  return /Mac/i.test(platform) && !touchApple ? "⌘K" : "Ctrl K";
}

const subscribe = () => () => {};
const serverSnapshot = () => shortcutLabel();
const clientSnapshot = () => shortcutLabel(navigator);

export function useShortcutLabel() {
  return useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
}
