import { describe, expect, it } from "vitest";

import { instrumentTypeSchema } from "./instrument";

describe("instrument domain", () => {
  it("defines the supported instrument types", () => {
    expect(instrumentTypeSchema.options).toEqual([
      "stock",
      "etf",
      "crypto",
      "commodity",
    ]);
  });
});
