"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { AnalysisSummary, EntryOut, EventOut, ProposalOut, TrackRecordOut, TrackOutcomePage } from "./types";

export type AnalysisFilters = {
  symbol?: string;
  status?: AnalysisSummary["status"];
  latest_per_instrument?: boolean;
  limit?: number;
  sort?: "created_at" | "symbol" | "trade_date";
  direction?: "asc" | "desc";
};

export function useResearchAnalyses(filters: AnalysisFilters) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) params.set(key, String(value));
  }
  return useQuery({
    queryKey: ["analyses", "research", filters],
    queryFn: () => api.get<AnalysisSummary[]>(`/analyses?${params}`),
    refetchInterval: (q) => q.state.data?.some((r) => ["queued", "running"].includes(r.status)) ? 5_000 : false,
  });
}

export function useRadarEvent(id: number | null) {
  return useQuery({
    queryKey: ["radar-event", id],
    queryFn: () => api.get<EventOut>(`/radar/events/${id}`),
    enabled: id !== null && Number.isSafeInteger(id) && id > 0,
    retry: false,
  });
}

export function useRetryProposal() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.send<ProposalOut>(`/proposals/${encodeURIComponent(id)}/retry`, "POST"),
    onSuccess: () => client.invalidateQueries({ queryKey: ["proposals"] }),
  });
}

export function useResearchEntry(symbol: string | null) {
  return useQuery({
    queryKey:["entry", "research", symbol],
    queryFn:() => api.get<EntryOut>(`/entries/${encodeURIComponent(symbol ?? "")}`),
    enabled: symbol !== null && symbol.length > 0,
    retry: false,
  });
}

export type TrackFilters = {horizon_days: number; created_from?: string; created_to?: string};
function trackQuery(filters: TrackFilters) {
  const params = new URLSearchParams({horizon_days:String(filters.horizon_days)});
  if (filters.created_from) params.set("created_from",filters.created_from);
  if (filters.created_to) params.set("created_to",filters.created_to);
  return params;
}
export function useResearchTrackRecord(filters: TrackFilters) {
  return useQuery({queryKey:["track-record", "research",filters], queryFn:() => api.get<TrackRecordOut>(`/track-record?${trackQuery(filters)}`)});
}
export function useResearchOutcomes(filters: TrackFilters, offset: number) {
  const params = trackQuery(filters);
  params.set("offset",String(offset));
  return useQuery({queryKey:["track-record-outcomes",filters,offset], queryFn:() => api.get<TrackOutcomePage>(`/track-record/outcomes?${params}`)});
}
