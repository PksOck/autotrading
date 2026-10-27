import { ApiError } from "@/lib/api/client";

const conflicts = [
  "analysis_not_finished_with_card",
  "analysis_has_no_triggers",
  "revision_not_draft",
  "revision_version_conflict",
  "revision_edit_conflict",
  "claim_revision_not_active",
  "claim_status_conflict",
] as const;

/** Return translation keys, never raw backend errors. */
export function thesisErrorKey(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 409) {
      const detail = conflicts.find((value) => value === error.detail);
      return detail ? (`errors.${detail}` as const) : "errors.conflict";
    }
    if (error.status === 404) return "errors.notFound";
    if (error.status === 422) return "errors.invalid";
  }
  return "errors.failed";
}

/** Mirrors the API check: http(s) scheme and a non-empty host right after `://`. */
export function isHttpUrl(value: string) {
  return /^https?:\/\/[^/?#\s]+/i.test(value);
}
