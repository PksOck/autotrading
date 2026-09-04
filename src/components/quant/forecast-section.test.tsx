import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ForecastSection } from "./forecast-section";

describe("ForecastSection", () => {
  it("renders baselines with metrics and a non-promoted label", () => {
    const closes = Array.from({ length: 60 }, (_, i) => 100 + Math.sin(i) * 2);
    render(<ForecastSection closes={closes} currency="USD" />);

    expect(screen.getByRole("heading", { name: "Next-close forecast" })).toBeInTheDocument();
    expect(screen.getByText(/naive last/i)).toBeInTheDocument();
    expect(screen.getByText(/simulation.*not.*advice/i)).toBeInTheDocument();
  });

  it("shows one unavailable message on short history", () => {
    render(<ForecastSection closes={[100]} currency="USD" />);
    expect(screen.getAllByText("Forecast is not available for this history length")).toHaveLength(1);
  });
});
