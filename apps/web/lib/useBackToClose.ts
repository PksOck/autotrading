"use client";

import { useCallback, useEffect, useRef } from "react";

const MARKER = "prezaOverlays";
let nextOverlay = 0;
const stack = (state: Record<string, unknown> | null): string[] =>
  Array.isArray(state?.[MARKER]) ? (state[MARKER] as string[]) : [];

/** One same-URL entry per overlay; preserve Next's router state and nested overlays. */
export function useBackToClose(open: boolean, onClose: () => void) {
  const active = useRef<string | null>(null);
  const closing = useRef(false);
  const callback = useRef(onClose);
  const afterClose = useRef<(() => void) | undefined>(undefined);

  useEffect(() => {
    callback.current = onClose;
  }, [onClose]);

  const close = useCallback((after?: () => void) => {
    if (closing.current) return;
    if (active.current && stack(window.history.state).at(-1) === active.current) {
      closing.current = true;
      afterClose.current = after;
      window.history.back();
    } else {
      active.current = null;
      callback.current();
      after?.();
    }
  }, []);

  useEffect(() => {
    if (open && !active.current) {
      const token = `overlay-${++nextOverlay}`;
      window.history.pushState(
        { ...window.history.state, [MARKER]: [...stack(window.history.state), token] },
        "",
        window.location.href,
      );
      active.current = token;
    } else if (!open && active.current) {
      close();
    }
    const onPop = (event: PopStateEvent) => {
      if (!active.current || stack(event.state).includes(active.current)) return;
      active.current = null;
      closing.current = false;
      callback.current();
      const after = afterClose.current;
      afterClose.current = undefined;
      after?.();
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [open, close]);

  return close;
}
