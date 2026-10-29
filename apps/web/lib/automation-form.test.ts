import { describe, expect, it } from "vitest";
import { policyBody, batchReason } from "./automation-form";

describe("automation drafts", () => {
  it("sends only editable fields while retaining optimistic revision", () => {
    const result = policyBody({ process_key: "radar", revision: 4, next_runs: ["later"], enabled: false, timezone: "UTC", schedule_kind: "manual", local_time: "06:00", interval_minutes: 60, weekdays: [0], window_start: "", window_end: "", cap: 5, scope: "portfolio" });
    expect(result.revision).toBe(4);
    expect(result.window_start).toBeNull();
    expect(result).not.toHaveProperty("process_key");
    expect(result).not.toHaveProperty("next_runs");
  });
  it("preserves the documented skip reasons", () => {
    expect(batchReason("active")).toBe("active");
    expect(batchReason("alien")).toBe("unavailable");
  });
});
