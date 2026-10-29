import type { AutomationPolicyInput } from "./api/automation";

export function policyBody(draft: AutomationPolicyInput & Record<string, unknown>): AutomationPolicyInput {
  return {
    revision: draft.revision, enabled: draft.enabled, timezone: draft.timezone,
    schedule_kind: draft.schedule_kind, local_time: draft.local_time,
    interval_minutes: draft.interval_minutes, weekdays: draft.weekdays,
    window_start: draft.window_start || null, window_end: draft.window_end || null,
    cap: draft.cap, scope: draft.scope,
  };
}
export function batchReason(reason: string) {
  return ["ready", "active", "cap", "quota", "disabled", "outside_window"].includes(reason) ? reason : "unavailable";
}
