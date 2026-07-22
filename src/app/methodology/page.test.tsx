import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MethodologyPage from "./page";

describe("MethodologyPage", () => {
  it("explains fixture provenance, missing values, freshness, and limitations", () => {
    render(<MethodologyPage />);
    expect(screen.getByRole("heading", { name: "Methodology" })).toBeInTheDocument();
    expect(screen.getByText(/illustrative fixture data/i)).toBeInTheDocument();
    expect(screen.getByText(/missing values.*not available/i)).toBeInTheDocument();
    expect(screen.getByText(/ISO-8601 UTC/i)).toBeInTheDocument();
    expect(screen.getByText(/not financial advice/i)).toBeInTheDocument();
  });
});
