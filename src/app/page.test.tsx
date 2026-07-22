import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("HomePage", () => {
  it("identifies the product as stock research", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: /research stocks/i }),
    ).toBeInTheDocument();
  });
});
