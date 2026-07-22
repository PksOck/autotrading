import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PricePoint } from "@/domain/price-history";

import { PriceChart } from "./price-chart";

const { chartAdapter, mountPriceVolumeChart } = vi.hoisted(() => ({
  chartAdapter: {
    updateTheme: vi.fn(),
    resize: vi.fn(),
    destroy: vi.fn(),
  },
  mountPriceVolumeChart: vi.fn(),
}));

mountPriceVolumeChart.mockImplementation(() => chartAdapter);

vi.mock("./lightweight-chart-adapter", () => ({ mountPriceVolumeChart }));

const points: PricePoint[] = [
  { timestamp: "2025-07-22T00:00:00Z", close: 210, volume: 1_000_000 },
  { timestamp: "2026-06-22T00:00:00Z", close: 220, volume: 1_100_000 },
  { timestamp: "2026-07-22T00:00:00Z", close: 217.35, volume: 1_200_000 },
];

describe("PriceChart", () => {
  beforeEach(() => {
    mountPriceVolumeChart.mockClear();
    chartAdapter.destroy.mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("updates the selected range and reports its absolute and percentage change", async () => {
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
    expect(screen.getByText(
      "1Y · 3 observations: $210.00 to $217.35. Change: $7.35 (3.5%).",
    )).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "1M" }));

    expect(screen.getByRole("button", { name: "1M" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(
      "1M · 2 observations: $220.00 to $217.35. Change: -$2.65 (-1.2%).",
    )).toBeInTheDocument();
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

    const emptyStatus = screen.getByRole("status", { name: "No price history available" });
    expect(screen.getByTestId("price-volume-chart-frame")).toContainElement(emptyStatus);
    expect(mountPriceVolumeChart).not.toHaveBeenCalled();
  });

  it("disconnects observers and destroys the adapter on unmount", () => {
    const resizeDisconnect = vi.fn();
    const mutationDisconnect = vi.fn();
    vi.stubGlobal("ResizeObserver", class {
      observe = vi.fn();
      disconnect = resizeDisconnect;
    });
    vi.stubGlobal("MutationObserver", class {
      observe = vi.fn();
      disconnect = mutationDisconnect;
    });

    const { unmount } = render(
      <PriceChart
        points={points}
        currency="USD"
        source="Illustrative fixture data"
        asOf="2026-07-22T20:05:00Z"
        initialRange="1Y"
      />,
    );

    unmount();

    expect(resizeDisconnect).toHaveBeenCalledOnce();
    expect(mutationDisconnect).toHaveBeenCalledOnce();
    expect(chartAdapter.destroy).toHaveBeenCalledOnce();
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
