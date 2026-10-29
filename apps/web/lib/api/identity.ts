"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

type S = components["schemas"];

export function useIdentityFacts(symbol: string) {
  return useQuery({
    queryKey: ["instrument", symbol],
    queryFn: () => api.get<S["InstrumentDetail"]>(`/instruments/${encodeURIComponent(symbol)}`),
  });
}

export function useEnrichIdentity(symbol: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: S["IdentityEnrichInput"]) =>
      api.send<S["IdentityEnrichOut"]>(
        `/instruments/${encodeURIComponent(symbol)}/identity/enrich`,
        "POST",
        body,
      ),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["instrument", symbol] }),
        client.invalidateQueries({ queryKey: ["portfolio"] }),
        client.invalidateQueries({ queryKey: ["watchlist"] }),
        client.invalidateQueries({ queryKey: ["search"] }),
      ]);
    },
  });
}
