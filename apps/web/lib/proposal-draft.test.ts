import { vi } from "vitest";
import {
  DRAFT_KEY,
  LEGACY_KEY,
  DEFAULT_FIELDS,
  canonicalBody,
  loadDraft,
  prepareOperation,
  saveDraftFields,
  setOperationState,
  startNewIntention,
  matchesOperation,
  coordinateDraft,
  clearAcknowledgedFields,
} from "./proposal-draft";

beforeEach(() => {
  localStorage.clear();
  // A queue models the browser's cross-tab exclusive lock, including simultaneous calls.
  let tail = Promise.resolve();
  Object.defineProperty(navigator, "locks", {
    configurable: true,
    value: {
      request: (_: string, run: () => unknown) => {
        const result = tail.then(run);
        tail = result.then(
          () => undefined,
          () => undefined,
        );
        return result;
      },
    },
  });
});
afterEach(() => vi.restoreAllMocks());

it("conditionally clears only unchanged persisted fields after acknowledgement", async () => {
  const original = { ...DEFAULT_FIELDS, symbols: "AMD", hypothesis: "Original idea" };
  const draft = await prepareOperation(loadDraft().draft_id, original);
  const edited = {
    ...original,
    symbols: "NVDA",
    hypothesis: "Other tab edit",
    source: "Other source",
    depth: "deep" as const,
    direction: "down" as const,
    horizon: "years" as const,
    saveTo: "active" as const,
  };
  await saveDraftFields(draft.draft_id, edited);
  await setOperationState(draft.operation!.request_id, "acknowledged");
  await clearAcknowledgedFields(draft.operation!.request_id, original);
  expect(loadDraft().fields).toEqual(edited);
  await clearAcknowledgedFields(draft.operation!.request_id, edited);
  expect(loadDraft().fields).toEqual({ ...edited, symbols: "", hypothesis: "", source: "" });
});

it("canonicalizes symbols like the server and includes all business fields", () => {
  expect(
    canonicalBody({
      ...DEFAULT_FIELDS,
      symbols: "msft, AMD msft",
      source: "$nvda news",
      hypothesis: " idea ",
    }),
  ).toEqual({
    symbols: ["AMD", "MSFT", "NVDA"],
    hypothesis: "idea",
    source_text: "$nvda news",
    direction: "unsure",
    horizon: "months",
    depth: "standard",
    save_to: "reserve",
  });
});

it("reloads the same immutable operation while preserving independent edits", async () => {
  const initial = loadDraft();
  const prepared = await prepareOperation(initial.draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" });
  await saveDraftFields(prepared.draft_id, { ...prepared.fields, hypothesis: "new edit" });
  const reloaded = loadDraft();
  const repeat = await prepareOperation(reloaded.draft_id, reloaded.fields);
  expect(repeat.operation).toEqual(prepared.operation);
  expect(repeat.fields.hypothesis).toBe("new edit");
  expect(repeat.operation?.canonical_body.hypothesis).toBe("");
});

it("serializes two tabs and stale edits cannot erase or regress safety state", async () => {
  const a = loadDraft();
  const b = loadDraft();
  const [first, second] = await Promise.all([
    prepareOperation(a.draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" }),
    prepareOperation(b.draft_id, { ...DEFAULT_FIELDS, symbols: "MSFT" }),
  ]);
  expect(first.operation?.request_id).toBe(second.operation?.request_id);
  const requestId = first.operation!.request_id;
  await setOperationState(requestId, "acknowledged");
  await saveDraftFields(first.draft_id, { ...first.fields, hypothesis: "stale edit" });
  await setOperationState(requestId, "outcome_unknown");
  expect(loadDraft().operation?.state).toBe("acknowledged");
  const fresh = await startNewIntention(first.draft_id, { ...first.fields, symbols: "NVDA" });
  await saveDraftFields(first.draft_id, { ...first.fields, symbols: "OLD" });
  expect(loadDraft().draft_id).toBe(fresh.draft_id);
  expect(loadDraft().fields.symbols).toBe("NVDA");
});

it("blocks unknown abandonment and only rotates after an explicit terminal action", async () => {
  const draft = await prepareOperation(loadDraft().draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" });
  await expect(startNewIntention(draft.draft_id, draft.fields)).rejects.toThrow();
  await setOperationState(draft.operation!.request_id, "conflict");
  const fresh = await startNewIntention(draft.draft_id, draft.fields);
  expect(fresh.draft_id).not.toBe(draft.draft_id);
  expect(fresh.operation).toBeNull();
});

it("validates legacy fields individually without inventing a previous operation", () => {
  localStorage.setItem(
    LEGACY_KEY,
    JSON.stringify({
      symbols: "AMD",
      hypothesis: 23,
      source: "saved text",
      depth: "bogus",
      direction: "down",
    }),
  );
  expect(loadDraft()).toMatchObject({
    fields: {
      symbols: "AMD",
      hypothesis: "",
      source: "saved text",
      depth: "standard",
      direction: "down",
    },
    operation: null,
  });
});

it("rejects a malformed saved operation rather than silently generating another ID", () => {
  localStorage.setItem(
    DRAFT_KEY,
    JSON.stringify({
      version: 2,
      fields: { ...DEFAULT_FIELDS, symbols: "AMD" },
      operation: { request_id: "invalid" },
    }),
  );
  expect(() => loadDraft()).toThrow();
});

it("requires durable write/readback and preserves existing data on failure", async () => {
  const draft = loadDraft();
  const write = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota");
  });
  await expect(
    prepareOperation(draft.draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" }),
  ).rejects.toThrow();
  write.mockRestore();
  const read = vi.spyOn(Storage.prototype, "getItem").mockReturnValue(null);
  await expect(
    prepareOperation(draft.draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" }),
  ).rejects.toThrow();
  read.mockRestore();
});

it("checks both exact ID and all canonical fields in a server acknowledgement", async () => {
  const draft = await prepareOperation(loadDraft().draft_id, { ...DEFAULT_FIELDS, symbols: "AMD" });
  const operation = draft.operation!;
  const response = { id: operation.request_id, ...operation.canonical_body };
  expect(matchesOperation(operation, response)).toBe(true);
  expect(matchesOperation(operation, { ...response, id: crypto.randomUUID() })).toBe(false);
  expect(matchesOperation(operation, { ...response, hypothesis: "other" })).toBe(false);
  expect(matchesOperation(operation, { ...response, depth: "deep" })).toBe(false);
});

it("fails closed when neither cross-tab coordinator is available", async () => {
  Object.defineProperty(navigator, "locks", { configurable: true, value: undefined });
  await expect(coordinateDraft(() => "unsafe")).rejects.toThrow();
});
