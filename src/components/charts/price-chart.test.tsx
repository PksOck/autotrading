import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PricePoint } from "@/domain/price-history";

import { PriceChart } from "./price-chart";

const { mountPriceVolumeChart } = vi.hoisted(() => ({
  mountPriceVolumeChart: vi.fn(() => ({
    updateTheme: vi.fn(),
    resize: vi.fn(),
    destroy: vi.fn(),
  })),
}));

vi.mock("./lightweight-chart-adapter", () => ({ mountPriceVolumeChart }));

const points: PricePoint[] = [
  { timestamp: "2025-07-22T00:00:00Z", close: 210, volume: 1_000_000 },
  { timestamp: "2026-06-22T00:00:00Z", close: 220, volume: 1_100_000 },
  { timestamp: "2026-07-22T00:00:00Z", close: 217.35, volume: 1_200_000 },
];

describe("PriceChart", () => {
  beforeEach(() => mountPriceVolumeChart.mockClear());

  it("updates the selected range with native pressed buttons and shows an observation summary", async () => {
    const user = userEvent.setup();
    render(
      <PriceChart
        points={points}
        currency="USD"
        source="Illustrative fixture data"
        asOf="2026-07-22T12:00:00Z"
        initialRange="1Y"
      />,
    );

    expect(screen.getByRole("button", { name: "1Y" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "1M" }));

    expect(screen.getByRole("button", { name: "1M" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/observations/i)).toBeInTheDocument();
  });

  it("shows the empty state without creating a chart", () => {
    render(
      <PriceChart
        points={[]}
        currency="USD"
        source="Illustrative fixture data"
        asOf="2026-07-22T12:00:00Z"
        initialRange="1Y"
      />,
    );

    expect(screen.getByText("No price history available")).toBeInTheDocument();
    expect(mountPriceVolumeChart).not.toHaveBeenCalled();
  });

  it("keeps source and as-of metadata visible for stale data", () => {
    render(
      <PriceChart
        points={points}
        currency="USD"
        source="Illustrative fixture data"
        asOf="2020-07-22T12:00:00Z"
        initialRange="1Y"
      />,
    );

    expect(screen.getByText(/Illustrative fixture data/i)).toBeInTheDocument();
    expect(screen.getByText(/2020-07-22/i)).toBeInTheDocument();
  });

  it("reports unavailable volume and does not request a volume series when every value is null", () => {
    render(
      <PriceChart
        points={points.map((point) => ({ ...point, volume: null }))}
        currency="USD"
        source="Illustrative fixture data"
        asOf="2026-07-22T12:00:00Z"
        initialRange="1Y"
      />,
    );

    expect(screen.getByText("Volume not available")).toBeInTheDocument();
    expect(mountPriceVolumeChart).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.arrayContaining([expect.objectContaining({ volume: null })]),
      expect.objectContaining({ showVolume: false }),
    );
  });
});
