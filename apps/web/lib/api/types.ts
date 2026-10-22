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
export type PositionOut = S["PositionOut"];
export type WatchlistOut = S["WatchlistOut"];
// Fields with server defaults are optional for callers.
export type WatchlistCreate = Pick<S["WatchlistCreate"], "symbol"> & Partial<Omit<S["WatchlistCreate"], "symbol">>;
export type WatchlistUpdate = S["WatchlistUpdate"];
export type WatchTier = S["WatchTier"];
export type BarsRange = "1m" | "3m" | "1y" | "2y" | "5y";
export type EventOut = S["EventOut"];
export type EventType = NonNullable<EventOut["event_type"]>;
export type RadarView = S["RadarView"];
export type SignalOut = S["SignalOut"];
export type SignalStatus = S["SignalStatus"];
export type ProposalOut = S["ProposalOut"];
export type ProposalCreate = Pick<S["ProposalCreate"], "symbols"> & Partial<Omit<S["ProposalCreate"], "symbols">>;
export type EntryOut = S["EntryOut"];
export type EntryView = S["EntryView"];
export type OutcomeStat = S["OutcomeStat"];
