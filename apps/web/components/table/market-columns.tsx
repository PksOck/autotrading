"use client";
import { useTranslations } from "next-intl";
import type { components } from "@/lib/api/schema";
import type { ColumnDefinition } from "./DataTable";
import { MetricCell } from "./MetricCell";

const METRICS = [
  "pe",
  "forward_pe",
  "dividend_yield_pct",
  "payout_ratio_pct",
  "dividend_per_share",
  "ev_ebit",
  "fcf_yield",
  "roe_pct",
  "gross_margin_pct",
  "net_margin_pct",
  "revenue_growth_pct",
  "debt_to_equity",
  "ter",
  "index_name",
  "distribution",
];
export function useMarketColumns<
  T extends { metrics?: Record<string, components["schemas"]["MetricValue"]> },
>(): ColumnDefinition<T>[] {
  const t = useTranslations("table.metric");
  return METRICS.map((id) => ({
    id,
    label: t(id),
    numeric: !["index_name", "distribution"].includes(id),
    defaultVisible: false,
    sortable: true,
    render: (row: T) => <MetricCell metric={row.metrics?.[id]} />,
  }));
}
