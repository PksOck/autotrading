"use client";

import { useQuery } from "@tanstack/react-query";
import type { components } from "./schema";
import { api } from "./client";

export type DividendsOut = components["schemas"]["DividendsOut"];
export type DividendFilters = {
  account_id?: string;
  currency?: string;
  from_date?: string;
  to_date?: string;
};

export function useDividends(filters: DividendFilters, enabled = true) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) if (value) query.set(key, value);
  return useQuery({
    queryKey: ["dividends", filters],
    queryFn: () => api.get<DividendsOut>(`/portfolio/dividends?${query}`),
    enabled,
  });
}
