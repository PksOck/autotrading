import { ApiError } from "@/lib/api/client";
import { isHttpUrl, thesisErrorKey } from "./thesis";
import en from "@/messages/en.json";
import sl from "@/messages/sl.json";

it.each([
  "analysis_not_finished_with_card",
  "analysis_has_no_triggers",
  "revision_not_draft",
  "revision_version_conflict",
  "claim_revision_not_active",
  "claim_status_conflict",
])("maps conflict %s to an existing friendly message in both languages", (detail) => {
  expect(thesisErrorKey(new ApiError(409, detail))).toBe(`errors.${detail}`);
  expect(en.thesis.errors).toHaveProperty(detail);
  expect(sl.thesis.errors).toHaveProperty(detail);
});

it("maps unknown conflicts, validation, missing resources and network errors", () => {
  expect(thesisErrorKey(new ApiError(409, "unknown"))).toBe("errors.conflict");
  expect(thesisErrorKey(new ApiError(422, "error"))).toBe("errors.invalid");
  expect(thesisErrorKey(new ApiError(404, "thesis_not_found"))).toBe("errors.notFound");
  expect(thesisErrorKey(new Error("network"))).toBe("errors.failed");
});

it.each([
  ["https://www.sec.gov/x", true],
  ["http://example.com", true],
  ["https:///example.com", false],
  ["/relative/path", false],
  ["ftp://example.com", false],
  ["example.com", false],
])("isHttpUrl(%s) is %s, like the API check", (value, expected) => {
  expect(isHttpUrl(value)).toBe(expected);
});
