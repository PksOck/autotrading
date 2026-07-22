"use client";

import { useEffect, useState } from "react";

import { isStale } from "@/lib/market-data";

const maximumTimerDelay = 2_147_483_647;

export function FreshnessStatus({
  asOf,
  maxAgeHours = 48,
}: {
  asOf: string;
  maxAgeHours?: number;
}) {
  const [stale, setStale] = useState<boolean | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    function refresh() {
      const now = new Date();
      const nextStale = isStale(asOf, now, maxAgeHours);
      setStale(nextStale);

      if (!nextStale) {
        const staleAt = new Date(asOf).getTime() + maxAgeHours * 3_600_000;
        const delay = Math.min(Math.max(staleAt - now.getTime() + 1, 1), maximumTimerDelay);
        timer = setTimeout(refresh, delay);
      }
    }

    refresh();
    return () => {
      if (timer !== undefined) clearTimeout(timer);
    };
  }, [asOf, maxAgeHours]);

  if (stale === null) return <span className="status">Checking data freshness…</span>;
  return stale
    ? <span className="status stale">Stale fixture data</span>
    : <span className="status">Fixture current</span>;
}
