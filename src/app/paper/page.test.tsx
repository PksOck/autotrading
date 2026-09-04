import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PaperPage from "./page";

describe("PaperPage", () => {
  it("renders the demo audit trail and risk configuration", async () => {
    render(await PaperPage());

    expect(screen.getByRole("heading", { name: "Paper trading simulator" })).toBeInTheDocument();
    expect(screen.getAllByText(/kill switch/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("table")).toBeInTheDocument();
  });
});
