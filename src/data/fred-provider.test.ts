import { describe, expect, it, vi } from "vitest";

import { FredProvider } from "./fred-provider";

const observations = {
  observations: [
    { date: "2026-07-01", value: "4.1" },
    { date: "2026-08-01", value: "." },
  ],
};

describe("FredProvider", () => {
  it("maps observations to nullable points with provenance", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(observations), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    try {
      const provider = new FredProvider("test-key");
      const series = await provider.getObservations("UNRATE", "2026-07-01", "2026-08-31");

      expect(series.seriesId).toBe("UNRATE");
      expect(series.source).toContain("FRED");
      expect(series.points).toEqual([
        { date: "2026-07-01", value: 4.1 },
        { date: "2026-08-01", value: null },
      ]);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("requires an API key", async () => {
    const provider = new FredProvider("");
    await expect(provider.getObservations("UNRATE")).rejects.toThrow();
  });
});
