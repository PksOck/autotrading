import type { components } from "./schema";

type S = components["schemas"];

export type SystemStatus = S["SystemStatus"];
export type ServiceStatus = S["ServiceStatus"];
export type ServiceState = ServiceStatus["state"];
export type InstrumentOut = S["InstrumentOut"];
export type InstrumentDetail = S["InstrumentDetail"];
export type BarsOut = S["BarsOut"];
export type Bar = S["BarOut"];
export type Provenance = S["Provenance"];
export type PortfolioOut = S["PortfolioOut"];
export type PortfolioImportOut = S["PortfolioImportOut"];
export type PositionOut = S["PositionOut"];
export type WatchlistOut = S["WatchlistOut"];
// Fields with server defaults are optional for callers.
export type WatchlistCreate = Pick<S["WatchlistCreate"], "symbol"> &
  Partial<Omit<S["WatchlistCreate"], "symbol">>;
export type WatchlistUpdate = S["WatchlistUpdate"];
export type WatchTier = S["WatchTier"];
export type BarsRange = "1m" | "3m" | "1y" | "2y" | "5y";
export type EventOut = S["EventOut"];
export type EventType = NonNullable<EventOut["event_type"]>;
export type RadarView = S["RadarView"];
export type SignalOut = S["SignalOut"];
export type SignalStatus = S["SignalStatus"];
export type ProposalOut = S["ProposalOut"];
export type ProposalCreate = Pick<S["ProposalCreate"], "symbols"> &
  Partial<Omit<S["ProposalCreate"], "symbols">>;
export type EntryOut = S["EntryOut"];
export type EntryView = S["EntryView"];
export type OutcomeStat = S["OutcomeStat"];
export type AnalysisSummary = S["AnalysisSummary"];
export type AnalysisOut = S["AnalysisOut"];
export type AnalysisStep = S["AnalysisStepOut"];
export type AnalysisStatus = S["AnalysisStatus"];
export type AnalysisCreate = Pick<S["AnalysisCreate"], "symbol"> &
  Partial<Omit<S["AnalysisCreate"], "symbol">>;
export type DecisionCard = NonNullable<AnalysisOut["card"]>;
export type AnalysisQuota = S["AnalysisQuota"];
export type Outlook = S["Outlook"];
export type HorizonOutlook = S["HorizonOutlook"];
export type OutlookEvidence = S["Evidence"];
export type OutlookBrief = S["OutlookBrief"];
export type ThesisSummary = S["ThesisSummary"];
export type ThesisOut = S["ThesisOut"];
export type ThesisRevisionOut = S["ThesisRevisionOut"];
export type ThesisRevisionPatch = S["ThesisRevisionPatch"];
export type ThesisDraftCreate = S["ThesisDraftCreate"];
export type ThesisClaimOut = S["ThesisClaimOut"];
export type ThesisClaimEventOut = S["ThesisClaimEventOut"];
export type ThesisClaimStatusChange = S["ThesisClaimStatusChange"];
export type ThesisEvidence = S["ThesisEvidence"];
export type ClaimStatus = ThesisClaimOut["status"];
export type ReviewOut = S["ReviewOut"];
export type ClaimReviewProposalOut = S["ClaimReviewProposalOut"];
export type AcceptProposal = S["AcceptProposal"];
export type DismissProposal = S["DismissProposal"];
export type TrackRecordOut = S["TrackRecordOut"];
export type TrackStat = S["TrackStat"];
export type CalibrationOut = S["CalibrationOut"];
export type WeightSetOut = S["WeightSetOut"];
export type GroupProposal = S["GroupProposal"];
