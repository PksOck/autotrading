"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  BarsOut,
  BarsRange,
  InstrumentDetail,
  InstrumentOut,
  PortfolioOut,
  SystemStatus,
  WatchlistCreate,
  WatchlistOut,
  WatchlistUpdate,
} from "./types";

export const keys = {
  status: ["system-status"] as const,
  portfolio: ["portfolio"] as const,
  watchlist: ["watchlist"] as const,
  instrument: (symbol: string) => ["instrument", symbol] as const,
  bars: (symbol: string, range: BarsRange) => ["bars", symbol, range] as const,
  search: (q: string) => ["search", q] as const,
};

export const useSystemStatus = () =>
  useQuery({ queryKey: keys.status, queryFn: () => api.get<SystemStatus>("/system/status"), refetchInterval: 30_000 });

export const usePortfolio = () =>
  useQuery({ queryKey: keys.portfolio, queryFn: () => api.get<PortfolioOut>("/portfolio") });

export const useWatchlist = () =>
  useQuery({ queryKey: keys.watchlist, queryFn: () => api.get<WatchlistOut[]>("/watchlist") });

export const useInstrument = (symbol: string) =>
  useQuery({
    queryKey: keys.instrument(symbol),
    queryFn: () => api.get<InstrumentDetail>(`/instruments/${encodeURIComponent(symbol)}`),
    retry: false,
  });

export const useBars = (symbol: string, range: BarsRange, refresh = true) =>
  useQuery({
    queryKey: keys.bars(symbol, range),
    queryFn: () =>
      api.get<BarsOut>(`/instruments/${encodeURIComponent(symbol)}/bars?range=${range}&refresh=${refresh}`),
    placeholderData: keepPreviousData,
    retry: false,
  });

export const useInstrumentSearch = (q: string) =>
  useQuery({
    queryKey: keys.search(q),
    queryFn: () => api.get<InstrumentOut[]>(`/instruments?q=${encodeURIComponent(q)}`),
    enabled: q.trim().length > 0,
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });

export function useWatchlistMutations() {
  const client = useQueryClient();
  const invalidate = () => client.invalidateQueries({ queryKey: keys.watchlist });
  return {
    add: useMutation({
      mutationFn: (data: WatchlistCreate) => api.send<WatchlistOut>("/watchlist", "POST", data),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, data }: { id: number; data: WatchlistUpdate }) =>
        api.send<WatchlistOut>(`/watchlist/${id}`, "PATCH", data),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (id: number) => api.send<void>(`/watchlist/${id}`, "DELETE"),
      onSuccess: invalidate,
    }),
  };
}

export function usePortfolioSync() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.send<{ job_id: string }>("/portfolio/sync", "POST"),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.portfolio }),
  });
}
