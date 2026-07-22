import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { StockSearch } from "./stock-search";

const results = [
  { symbol: "AMZN", companyName: "Amazon.com, Inc.", exchange: "NASDAQ" },
];

describe("StockSearch", () => {
  it("links a company-name match to its stock page", async () => {
    const user = userEvent.setup();
    render(<StockSearch initialResults={results} />);

    await user.type(
      screen.getByRole("searchbox", { name: /symbol or company/i }),
      "amazon",
    );

    expect(screen.getByRole("link", { name: /amazon.com/i })).toHaveAttribute(
      "href",
      "/stocks/AMZN",
    );
  });

  it("explains empty and unmatched queries", async () => {
    const user = userEvent.setup();
    render(<StockSearch initialResults={results} />);
    expect(screen.getByText("Enter a symbol or company name")).toBeInTheDocument();

    await user.type(screen.getByRole("searchbox"), "tesla");
    expect(screen.getByText("No fixture matches")).toBeInTheDocument();
  });
});
