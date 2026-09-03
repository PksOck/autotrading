import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ValuationSection } from "./valuation-section";

const props = {
  currency: "USD",
  unit: "millions",
  latestFcf: { value: 38219, period: "2024" },
  dilutedShares: 10670,
};

describe("ValuationSection", () => {
  it("renders three scenarios and labels the estimate as non-advice", async () => {
    render(<ValuationSection {...props} />);

    expect(screen.getByRole("heading", { name: "Valuation scenarios" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Base" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/estimate.*not a recommendation or target price/i)).toBeInTheDocument();
    expect(screen.getByText(/normalized fcf.*38,219.*2024/i)).toBeInTheDocument();
  });

  it("recomputes the per-share estimate when the scenario changes", async () => {
    const user = userEvent.setup();
    render(<ValuationSection {...props} />);

    const result = screen.getByRole("region", { name: /valuation result/i });
    const before = result.textContent;

    await user.click(screen.getByRole("button", { name: "Optimistic" }));

    expect(screen.getByRole("button", { name: "Optimistic" })).toHaveAttribute("aria-pressed", "true");
    const after = screen.getByRole("region", { name: /valuation result/i }).textContent;
    expect(after).not.toBe(before);
  });

  it("refuses terminal growth at or above the discount rate", async () => {
    const user = userEvent.setup();
    render(<ValuationSection {...props} />);

    const terminalInput = screen.getByLabelText(/terminal growth \(%\)/i);
    await user.clear(terminalInput);
    await user.type(terminalInput, "10");

    expect(screen.getByText(/terminal growth must stay below the discount rate/i)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: /valuation result/i })).not.toBeInTheDocument();
  });

  it("warns on extreme growth while still estimating", async () => {
    const user = userEvent.setup();
    render(<ValuationSection {...props} />);

    await user.clear(screen.getByLabelText(/annual growth \(%\)/i));
    await user.type(screen.getByLabelText(/annual growth \(%\)/i), "20");

    expect(screen.getByText(/unusually aggressive/i)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /valuation result/i })).toBeInTheDocument();
  });

  it("shows one unavailable message when FCF or shares are missing", () => {
    const { rerender } = render(<ValuationSection {...props} latestFcf={null} />);
    expect(screen.getAllByText("Valuation is not available for this instrument")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Base" })).not.toBeInTheDocument();

    rerender(<ValuationSection {...props} dilutedShares={null} />);
    expect(screen.getAllByText("Valuation is not available for this instrument")).toHaveLength(1);
  });
});
