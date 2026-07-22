import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  permanentRedirect: vi.fn(),
}));

import { permanentRedirect } from "next/navigation";

import StockPage from "./page";

describe("legacy stock route", () => {
  it("permanently redirects to the canonical instrument route", async () => {
    await StockPage({ params: Promise.resolve({ symbol: "AMZN" }) });

    expect(permanentRedirect).toHaveBeenCalledWith("/instruments/AMZN");
  });
});
