"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { SESSION_ENDED } from "@/lib/client-access";

export function SessionGuard({ children }: { children: ReactNode }) {
  const query = useQueryClient();
  const [ready, setReady] = useState(false);
  const [concealed, setConcealed] = useState(true);
  useEffect(() => {
    let stopped = false,
      checking = false,
      lastActivity = 0,
      enabled = false,
      locked = false;
    function lock() {
      if (stopped) return;
      locked = true;
      setReady(false);
      query.clear();
      window.location.replace("/login");
    }
    async function check() {
      if (checking || stopped || locked) return;
      checking = true;
      try {
        const response = await fetch("/api/auth/session", { cache: "no-store" });
        const state = response.ok ? await response.json() : null;
        if (!response.ok || state?.authenticated !== true) {
          lock();
          return;
        }
        if (!stopped && !locked) {
          enabled = state.enabled === true;
          setReady(true);
          setConcealed(document.hidden);
        }
      } catch {
        lock();
      } finally {
        checking = false;
      }
    }
    function storage(event: StorageEvent) {
      if (event.key === SESSION_ENDED) lock();
    }
    function visibility() {
      if (document.hidden) setConcealed(true);
      else void check();
    }
    function restored() {
      setConcealed(true);
      void check();
    }
    function activity(event: Event) {
      if (
        !enabled ||
        locked ||
        !event.isTrusted ||
        document.hidden ||
        Date.now() - lastActivity < 60000
      )
        return;
      lastActivity = Date.now();
      void fetch("/api/auth/activity", { method: "POST", cache: "no-store" })
        .then((response) => {
          if (response.status === 401 || response.status === 503) lock();
        })
        .catch(() => {});
    }
    void check();
    const timer = setInterval(check, 30000);
    window.addEventListener(SESSION_ENDED, lock);
    window.addEventListener("storage", storage);
    window.addEventListener("pageshow", restored);
    window.addEventListener("pointerdown", activity);
    window.addEventListener("keydown", activity);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      stopped = true;
      clearInterval(timer);
      window.removeEventListener(SESSION_ENDED, lock);
      window.removeEventListener("storage", storage);
      window.removeEventListener("pageshow", restored);
      window.removeEventListener("pointerdown", activity);
      window.removeEventListener("keydown", activity);
      document.removeEventListener("visibilitychange", visibility);
    };
  }, [query]);
  return ready ? <div hidden={concealed}>{children}</div> : null;
}
