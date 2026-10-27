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
  TrackRecordOut,
  CalibrationOut,
  WeightSetOut,
  WatchlistCreate,
  WatchlistOut,
  WatchlistUpdate,
  ThesisSummary,
  ThesisOut,
  ThesisRevisionOut,
  ThesisRevisionPatch,
  ThesisDraftCreate,
  ThesisClaimOut,
  ThesisClaimStatusChange,
  ReviewOut,
  ClaimReviewProposalOut,
  AcceptProposal,
  DismissProposal,
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
  theses: (symbol?: string, limit = 30, offset = 0) =>
    ["theses", symbol ?? null, limit, offset] as const,
  thesis: (id: string) => ["thesis", id] as const,
  thesisReviews: (id: string, limit = 30, offset = 0) =>
    ["thesis-reviews", id, limit, offset] as const,
  thesisReviewProposals: (id: string) => ["thesis-review-proposals", id] as const,
  trackRecord: (horizonDays: number) => ["track-record", horizonDays] as const,
  calibration: ["calibration"] as const,
};

export const useSystemStatus = () =>
  useQuery({
    queryKey: keys.status,
    queryFn: () => api.get<SystemStatus>("/system/status"),
    refetchInterval: 30_000,
  });

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
      api.get<BarsOut>(
        `/instruments/${encodeURIComponent(symbol)}/bars?range=${range}&refresh=${refresh}`,
      ),
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
    queryFn: () =>
      api.get<SignalOut[]>(status === "all" ? "/signals" : `/signals?status=${status}`),
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
      query.state.data?.some((p) => p.status === "queued" || p.status === "running")
        ? 4_000
        : false,
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
      api.get<AnalysisSummary[]>(
        symbol ? `/analyses?symbol=${encodeURIComponent(symbol)}` : "/analyses",
      ),
    refetchInterval: (query) =>
      query.state.data?.some((a) => a.status === "queued" || a.status === "running")
        ? 5_000
        : false,
  });

export const useAnalysis = (id: string) =>
  useQuery({
    queryKey: keys.analysis(id),
    queryFn: () => api.get<AnalysisOut>(`/analyses/${encodeURIComponent(id)}`),
    retry: false,
  });

/** Daily deep-analysis limit (BL-093); limit 0 means unlimited. */
export const useAnalysisQuota = () =>
  useQuery({
    queryKey: keys.analysisQuota,
    queryFn: () => api.get<AnalysisQuota>("/analyses/quota"),
    staleTime: 30_000,
  });

export const quotaReached = (q: AnalysisQuota | undefined) =>
  !!q && q.limit > 0 && q.used >= q.limit;

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

export const useTheses = (symbol?: string, limit = 30, offset = 0) =>
  useQuery({
    queryKey: keys.theses(symbol, limit, offset),
    queryFn: () =>
      api.get<ThesisSummary[]>(
        `/theses?limit=${limit}&offset=${offset}${symbol ? `&symbol=${encodeURIComponent(symbol)}` : ""}`,
      ),
  });

export const useThesis = (id: string) =>
  useQuery({
    queryKey: keys.thesis(id),
    queryFn: () => api.get<ThesisOut>(`/theses/${encodeURIComponent(id)}`),
    retry: false,
  });

function useInvalidateTheses() {
  const client = useQueryClient();
  return async () => {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["theses"] }),
      client.invalidateQueries({ queryKey: ["thesis"] }),
    ]);
  };
}

async function reviewPages<T>(
  path: string,
  limit: number,
  offset: number,
  all: boolean,
  firstPath?: string,
): Promise<T[]> {
  const result: T[] = [];
  let page: T[];
  do {
    page = await api.get<T[]>(
      firstPath ?? `${path}${path.endsWith("?") ? "" : "&"}limit=${limit}&offset=${offset}`,
    );
    if (!Array.isArray(page)) throw new Error("Invalid review response");
    result.push(...page);
    firstPath = undefined;
    offset += page.length;
  } while (all && page.length === limit);
  return result;
}

export const useThesisReviews = (id: string, limit = 30, offset = 0, allPages = false) =>
  useQuery({
    queryKey: allPages
      ? [...keys.thesisReviews(id, limit, offset), "all"]
      : keys.thesisReviews(id, limit, offset),
    queryFn: () =>
      reviewPages<ReviewOut>(
        `/theses/${encodeURIComponent(id)}/reviews?`,
        limit,
        offset,
        allPages,
        `/theses/${encodeURIComponent(id)}/reviews?limit=${limit}&offset=${offset}`,
      ),
    retry: false,
  });

export const useThesisReviewProposals = (id: string) =>
  useQuery({
    queryKey: keys.thesisReviewProposals(id),
    queryFn: () =>
      reviewPages<ClaimReviewProposalOut>(
        `/theses/${encodeURIComponent(id)}/review-proposals?state=pending`,
        30,
        0,
        true,
        `/theses/${encodeURIComponent(id)}/review-proposals?state=pending`,
      ),
    retry: false,
  });

function useInvalidateThesisReviews() {
  const client = useQueryClient();
  return async () => {
    await Promise.all(
      ["thesis-reviews", "thesis-review-proposals", "thesis", "theses", "signals"].map((key) =>
        client.invalidateQueries({ queryKey: [key] }),
      ),
    );
  };
}

export function useAcceptThesisReviewProposal(thesisId: string, proposalId: string) {
  const invalidate = useInvalidateThesisReviews();
  return useMutation({
    mutationFn: (body: AcceptProposal) =>
      api.send<ClaimReviewProposalOut>(
        `/theses/${encodeURIComponent(thesisId)}/review-proposals/${encodeURIComponent(proposalId)}/accept`,
        "POST",
        body,
      ),
    onSettled: invalidate,
  });
}

export function useDismissThesisReviewProposal(thesisId: string, proposalId: string) {
  const invalidate = useInvalidateThesisReviews();
  return useMutation({
    mutationFn: (body: DismissProposal) =>
      api.send<ClaimReviewProposalOut>(
        `/theses/${encodeURIComponent(thesisId)}/review-proposals/${encodeURIComponent(proposalId)}/dismiss`,
        "POST",
        body,
      ),
    onSettled: invalidate,
  });
}

export function useCreateThesisDraft() {
  const invalidate = useInvalidateTheses();
  return useMutation({
    mutationFn: (data: ThesisDraftCreate) =>
      api.send<ThesisRevisionOut>("/theses/drafts", "POST", data),
    onSettled: invalidate,
  });
}

export function usePatchThesisRevision(thesisId: string, revisionId: string) {
  const invalidate = useInvalidateTheses();
  return useMutation({
    mutationFn: (data: ThesisRevisionPatch) =>
      api.send<ThesisRevisionOut>(
        `/theses/${encodeURIComponent(thesisId)}/revisions/${encodeURIComponent(revisionId)}`,
        "PATCH",
        data,
      ),
    onSettled: invalidate,
  });
}

export function useConfirmThesisRevision(thesisId: string, revisionId: string) {
  const invalidate = useInvalidateTheses();
  return useMutation({
    mutationFn: () =>
      api.send<ThesisRevisionOut>(
        `/theses/${encodeURIComponent(thesisId)}/revisions/${encodeURIComponent(revisionId)}/confirm`,
        "POST",
      ),
    onSettled: invalidate,
  });
}

export function useChangeClaimStatus(thesisId: string, claimId: string) {
  const invalidate = useInvalidateTheses();
  return useMutation({
    mutationFn: (data: ThesisClaimStatusChange) =>
      api.send<ThesisClaimOut>(
        `/theses/${encodeURIComponent(thesisId)}/claims/${encodeURIComponent(claimId)}/status`,
        "POST",
        data,
      ),
    onSettled: invalidate,
  });
}

/**
 * Live steps of a run (ADR-0011): starts from the steps already loaded, then follows
 * `/analyses/{id}/events` while the run is queued/running. Dedupes by seq and closes on `end`.
 */
export function useAnalysisStream(
  id: string,
  initialSteps: AnalysisStep[],
  status: AnalysisStatus | undefined,
) {
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
    const source = new EventSource(
      `/api/analyses/${encodeURIComponent(id)}/events?after=${seqRef.current}`,
    );
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

/** SCR-10 track record at one horizon (BL-102). */
export const useTrackRecord = (horizonDays: number) =>
  useQuery({
    queryKey: keys.trackRecord(horizonDays),
    queryFn: () => api.get<TrackRecordOut>(`/track-record?horizon_days=${horizonDays}`),
    placeholderData: keepPreviousData,
  });

export const useCalibration = () =>
  useQuery({ queryKey: keys.calibration, queryFn: () => api.get<CalibrationOut>("/calibration") });

/** Weight proposals change nothing until confirmed (ADR-0015). */
function useCalibrationMutation<A>(mutationFn: (arg: A) => Promise<WeightSetOut>) {
  const client = useQueryClient();
  return useMutation({ mutationFn, onSettled: () => client.invalidateQueries({ queryKey: keys.calibration }) });
}

export const useProposeWeights = () =>
  useCalibrationMutation((horizonDays: number) =>
    api.send<WeightSetOut>(`/calibration/proposals?horizon_days=${horizonDays}`, "POST"),
  );

export const useConfirmWeights = () =>
  useCalibrationMutation((id: string) =>
    api.send<WeightSetOut>(`/calibration/${encodeURIComponent(id)}/confirm`, "POST", { confirm: true }),
  );

export const useRejectWeights = () =>
  useCalibrationMutation((id: string) => api.send<WeightSetOut>(`/calibration/${encodeURIComponent(id)}/reject`, "POST"));
