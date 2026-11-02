import { render, screen, fireEvent } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { DataQualityBadges } from "./MetricCell";

it("explains which hidden metric is stale with source and time, retaining other warnings", () => {
  const meta = {
    availability: "available" as const,
    reason_code: null,
    basis: null,
    stale: true,
    source: "fixture",
    fetched_at: "2026-10-01T12:00:00Z",
    market_date: "2026-09-30",
  };
  render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <DataQualityBadges
        identity="unresolved"
        price={{ ...meta, stale: false }}
        metrics={{
          forward_pe: { value: "20", meta },
          pe: { value: "18", meta: { ...meta, stale: false, availability: "partial" } },
        }}
      />
    </NextIntlClientProvider>,
  );
  fireEvent.click(screen.getByText("Stale", { exact: true }));
  expect(screen.getByText(/Forward P\/E/)).toBeVisible();
  expect(screen.getByText(/fixture/)).toBeVisible();
  expect(document.querySelector('time[datetime="2026-10-01T12:00:00Z"]')).toBeVisible();
  expect(screen.getByText(/2026-09-30/)).toBeVisible();
  expect(screen.getByText("Partial data", { exact: true })).toBeVisible();
  expect(screen.getByText("Incomplete identity", { exact: true })).toBeVisible();
});
