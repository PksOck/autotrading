import { z } from "zod";

import { fetchJsonWithRetry } from "./http";

export interface FredPoint {
  date: string;
  value: number | null;
}

export interface FredSeries {
  seriesId: string;
  source: string;
  asOf: string;
  points: FredPoint[];
}

const observationsSchema = z.object({
  observations: z.array(z.object({ date: z.string(), value: z.string() })).default([]),
});

/**
 * Server-only FRED adapter for macro context (UNRATE, CPIAUCSL, DGS10...).
 * Missing FRED values (".") map to null, never zero. Macro data is
 * regime context, never a trading signal on its own.
 */
export class FredProvider {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl = "https://api.stlouisfed.org/fred",
  ) {}

  async getObservations(seriesId: string, start?: string, end?: string): Promise<FredSeries> {
    const id = seriesId.trim().toUpperCase();
    const params = new URLSearchParams({ series_id: id, file_type: "json", api_key: this.apiKey });
    if (start) params.set("observation_start", start);
    if (end) params.set("observation_end", end);

    const raw = await fetchJsonWithRetry("fred", `${this.baseUrl}/series/observations?${params}`, this.apiKey);
    const parsed = observationsSchema.parse(raw);

    return {
      seriesId: id,
      source: "FRED St. Louis Fed",
      asOf: new Date().toISOString(),
      points: parsed.observations.map((entry) => ({
        date: entry.date,
        value: entry.value === "." ? null : Number(entry.value),
      })),
    };
  }
}
