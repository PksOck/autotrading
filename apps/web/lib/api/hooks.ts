"use client";

import { useEffect, useRef, useState } from "react";
import { lastSeq, mergeSteps } from "@/lib/analysis";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, api } from "./client";
import type {
  AnalysisCreate,
  AnalysisOut,
  AnalysisQuota,
  AnalysisStatus,
  AnalysisStep,
  AnalysisSummary,
  EntryOut,
  EntryView,
  BarsOut,
  EventOut,
  ProposalCreate,
  ProposalOut,
  RadarView,
  SignalOut,
  SignalStatus,
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
  radar: (view: RadarView, minScore: number) => ["radar", view, minScore] as const,
  signals: (status: SignalStatus | "all") => ["signals", status] as const,
  entries: (view: EntryView) => ["entries", view] as const,
  proposals: ["proposals"] as const,
  analyses: (symbol?: string) => ["analyses", symbol ?? "all"] as const,
  analysis: (id: string) => ["analysis", id] as const,
  analysisQuota: ["analyses-quota"] as const,
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

export const useRadarEvents = (view: RadarView, minScore: number) =>
  useQuery({
    queryKey: keys.radar(view, minScore),
    queryFn: () => api.get<EventOut[]>(`/radar/events?view=${view}&min_score=${minScore}`),
    refetchInterval: 60_000,
    placeholderData: keepPreviousData,
  });

export const useEntries = (view: EntryView) =>
  useQuery({
    queryKey: keys.entries(view),
    queryFn: () => api.get<EntryOut[]>(`/entries?view=${view}`),
    refetchInterval: 5 * 60_000,
    placeholderData: keepPreviousData,
  });

/** Entry candidate for one instrument; 404 means "no zone" and resolves to null. */
export const useEntry = (symbol: string) =>
  useQuery({
    queryKey: ["entry", symbol] as const,
    queryFn: async () => {
      try {
        return await api.get<EntryOut>(`/entries/${encodeURIComponent(symbol)}`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    retry: false,
    refetchInterval: 5 * 60_000,
  });

export const useSignals = (status: SignalStatus | "all") =>
  useQuery({
    queryKey: keys.signals(status),
    queryFn: () => api.get<SignalOut[]>(status === "all" ? "/signals" : `/signals?status=${status}`),
    refetchInterval: 60_000,
  });

export function useSignalUpdate() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, reason }: { id: string; status: SignalStatus; reason?: string }) =>
      api.send<SignalOut>(`/signals/${id}`, "PATCH", { status, reason }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["signals"] }),
  });
}

export const useProposalList = () =>
  useQuery({
    queryKey: keys.proposals,
    queryFn: () => api.get<ProposalOut[]>("/proposals"),
    // Poll while something is still being analyzed.
    refetchInterval: (query) =>
      query.state.data?.some((p) => p.status === "queued" || p.status === "running") ? 4_000 : false,
  });

export function useCreateProposal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: ProposalCreate) => api.send<ProposalOut>("/proposals", "POST", data),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.proposals }),
  });
}

export const useAnalyses = (symbol?: string) =>
  useQuery({
    queryKey: keys.analyses(symbol),
    queryFn: () =>
      api.get<AnalysisSummary[]>(symbol ? `/analyses?symbol=${encodeURIComponent(symbol)}` : "/analyses"),
    refetchInterval: (query) =>
      query.state.data?.some((a) => a.status === "queued" || a.status === "running") ? 5_000 : false,
  });

export const useAnalysis = (id: string) =>
  useQuery({
    queryKey: keys.analysis(id),
    queryFn: () => api.get<AnalysisOut>(`/analyses/${encodeURIComponent(id)}`),
    retry: false,
  });

/** Daily deep-analysis limit (BL-093); limit 0 means unlimited. */
export const useAnalysisQuota = () =>
  useQuery({ queryKey: keys.analysisQuota, queryFn: () => api.get<AnalysisQuota>("/analyses/quota"), staleTime: 30_000 });

export const quotaReached = (q: AnalysisQuota | undefined) => !!q && q.limit > 0 && q.used >= q.limit;

export function useCreateAnalysis() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (data: AnalysisCreate) => api.send<AnalysisSummary>("/analyses", "POST", data),
    onSettled: () => {
      void client.invalidateQueries({ queryKey: ["analyses"] });
      void client.invalidateQueries({ queryKey: keys.analysisQuota });
    },
  });
}

/**
 * Live steps of a run (ADR-0011): starts from the steps already loaded, then follows
 * `/analyses/{id}/events` while the run is queued/running. Dedupes by seq and closes on `end`.
 */
export function useAnalysisStream(id: string, initialSteps: AnalysisStep[], status: AnalysisStatus | undefined) {
  const client = useQueryClient();
  const [streamed, setStreamed] = useState<AnalysisStep[]>([]);
  const [connected, setConnected] = useState(false);
  const seqRef = useRef(0);
  const steps = mergeSteps(initialSteps, streamed);
  const live = status === "queued" || status === "running";

  const latest = lastSeq(steps);
  useEffect(() => {
    seqRef.current = latest;
  });

  useEffect(() => {
    if (!live) return;
    const source = new EventSource(`/api/analyses/${encodeURIComponent(id)}/events?after=${seqRef.current}`);
    source.onopen = () => setConnected(true);
    source.addEventListener("step", (event) => {
      try {
        const step = JSON.parse((event as MessageEvent<string>).data) as AnalysisStep;
        setStreamed((prev) => mergeSteps(prev, [step]));
      } catch {
        /* ignore a malformed frame; the next one still applies */
      }
    });
    source.addEventListener("end", () => {
      source.close();
      setConnected(false);
      void client.invalidateQueries({ queryKey: keys.analysis(id) });
      void client.invalidateQueries({ queryKey: ["analyses"] });
    });
    // On error EventSource reconnects by itself and resends Last-Event-ID.
    source.onerror = () => setConnected(false);
    return () => {
      source.close();
      setConnected(false);
    };
  }, [id, live, client]);

  return { steps, connected: live && connected };
}
