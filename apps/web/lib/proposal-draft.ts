import { parseSymbols } from "@/stores/proposals";

export const DRAFT_KEY = "preza.proposal.draft.v2";
export const LEGACY_KEY = "preza.proposal.draft.v1";
export type DraftFields = {
  symbols: string;
  hypothesis: string;
  source: string;
  direction: "up" | "down" | "unsure";
  horizon: "days" | "weeks" | "months" | "years";
  depth: "quick" | "standard" | "deep";
  saveTo: "active" | "reserve" | "once";
};
export const DEFAULT_FIELDS: DraftFields = {
  symbols: "",
  hypothesis: "",
  source: "",
  direction: "unsure",
  horizon: "months",
  depth: "standard",
  saveTo: "reserve",
};
export type CanonicalBody = {
  symbols: string[];
  hypothesis: string;
  source_text: string;
  direction: DraftFields["direction"];
  horizon: DraftFields["horizon"];
  depth: DraftFields["depth"];
  save_to: DraftFields["saveTo"];
};
export type OperationState =
  "prepared" | "submitting" | "outcome_unknown" | "acknowledged" | "conflict";
export type DraftOperation = {
  request_id: string;
  canonical_body: CanonicalBody;
  state: OperationState;
  proposal_id?: string;
};
export type ProposalDraft = {
  version: 2;
  draft_id: string;
  fields: DraftFields;
  operation: DraftOperation | null;
  saved_at: string;
};

export class DraftStorageError extends Error {}
const object = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
const uuid = (value: unknown): value is string =>
  typeof value === "string" &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);

function recoverFields(value: unknown): DraftFields {
  const raw = object(value) ?? {};
  const fields = { ...DEFAULT_FIELDS };
  for (const key of ["symbols", "hypothesis", "source"] as const)
    if (typeof raw[key] === "string") fields[key] = raw[key];
  if (["up", "down", "unsure"].includes(String(raw.direction)))
    fields.direction = raw.direction as DraftFields["direction"];
  if (["days", "weeks", "months", "years"].includes(String(raw.horizon)))
    fields.horizon = raw.horizon as DraftFields["horizon"];
  if (["quick", "standard", "deep"].includes(String(raw.depth)))
    fields.depth = raw.depth as DraftFields["depth"];
  if (["active", "reserve", "once"].includes(String(raw.saveTo)))
    fields.saveTo = raw.saveTo as DraftFields["saveTo"];
  return fields;
}

export function canonicalBody(fields: DraftFields): CanonicalBody {
  return {
    symbols: parseSymbols(
      `${fields.symbols} ${fields.source.match(/\$[A-Za-z.]{1,10}/g)?.join(" ") ?? ""}`,
    ).sort(),
    hypothesis: fields.hypothesis.trim(),
    source_text: fields.source.trim(),
    direction: fields.direction,
    horizon: fields.horizon,
    depth: fields.depth,
    save_to: fields.saveTo,
  };
}

function validBody(value: unknown): value is CanonicalBody {
  const body = object(value);
  if (
    !body ||
    !Array.isArray(body.symbols) ||
    !body.symbols.length ||
    body.symbols.length > 8 ||
    !body.symbols.every((s) => typeof s === "string" && /^[A-Z][A-Z0-9.]{0,9}$/.test(s))
  )
    return false;
  return (
    JSON.stringify(body.symbols) === JSON.stringify([...new Set(body.symbols)].sort()) &&
    typeof body.hypothesis === "string" &&
    body.hypothesis.length <= 4000 &&
    typeof body.source_text === "string" &&
    body.source_text.length <= 20000 &&
    ["up", "down", "unsure"].includes(String(body.direction)) &&
    ["days", "weeks", "months", "years"].includes(String(body.horizon)) &&
    ["quick", "standard", "deep"].includes(String(body.depth)) &&
    ["active", "reserve", "once"].includes(String(body.save_to))
  );
}

function fresh(fields: DraftFields): ProposalDraft {
  return {
    version: 2,
    draft_id: newId(),
    fields,
    operation: null,
    saved_at: new Date().toISOString(),
  };
}

function newId(): string {
  if (crypto.randomUUID) return crypto.randomUUID();
  // getRandomValues is also available on ordinary HTTP private-network origins.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6]! & 15) | 64;
  bytes[8] = (bytes[8]! & 63) | 128;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function loadDraft(): ProposalDraft {
  const stored = localStorage.getItem(DRAFT_KEY);
  if (stored !== null) {
    // Never discard an unreadable v2 operation and accidentally create a second submission.
    const raw = object(JSON.parse(stored));
    if (!raw || raw.version !== 2 || !uuid(raw.draft_id) || typeof raw.saved_at !== "string")
      throw new DraftStorageError("invalid saved draft");
    const operation = object(raw.operation);
    if (
      raw.operation !== null &&
      (!operation ||
        !uuid(operation.request_id) ||
        !validBody(operation.canonical_body) ||
        !["prepared", "submitting", "outcome_unknown", "acknowledged", "conflict"].includes(
          String(operation.state),
        ) ||
        (operation.state === "acknowledged" && operation.proposal_id !== operation.request_id))
    )
      throw new DraftStorageError("invalid saved operation");
    return {
      version: 2,
      draft_id: raw.draft_id,
      fields: recoverFields(raw.fields),
      operation: operation as DraftOperation | null,
      saved_at: raw.saved_at,
    };
  }
  let legacy: unknown = null;
  try {
    legacy = JSON.parse(localStorage.getItem(LEGACY_KEY) ?? "null");
  } catch {
    /* Recover independently valid v1 fields only. */
  }
  return fresh(recoverFields(legacy));
}

/** IndexedDB transactions serialize every browser writer, also on ordinary HTTP. */
export async function coordinateDraft<T>(run: () => T): Promise<T> {
  if (typeof indexedDB === "undefined") {
    if (navigator.locks) return navigator.locks.request(DRAFT_KEY, run);
    throw new DraftStorageError("browser storage coordination unavailable");
  }
  return new Promise<T>((resolve, reject) => {
    const opening = indexedDB.open("preza.proposal.coordination", 1);
    opening.onupgradeneeded = () => opening.result.createObjectStore("draft");
    opening.onerror = () => reject(new DraftStorageError("browser storage unavailable"));
    opening.onblocked = () => reject(new DraftStorageError("browser storage blocked"));
    opening.onsuccess = () => {
      const db = opening.result;
      const transaction = db.transaction("draft", "readwrite");
      const store = transaction.objectStore("draft");
      let result: T;
      store.get("lock").onsuccess = () => {
        try {
          result = run();
          store.put(1, "lock");
        } catch (error) {
          transaction.abort();
          reject(error);
        }
      };
      transaction.oncomplete = () => {
        db.close();
        resolve(result);
      };
      transaction.onabort = transaction.onerror = () => {
        db.close();
        reject(new DraftStorageError("browser storage coordination failed"));
      };
    };
  });
}

function persist(draft: ProposalDraft): ProposalDraft {
  draft.saved_at = new Date().toISOString();
  const json = JSON.stringify(draft);
  localStorage.setItem(DRAFT_KEY, json);
  if (localStorage.getItem(DRAFT_KEY) !== json)
    throw new DraftStorageError("draft write verification failed");
  return draft;
}

export function saveDraftFields(draftId: string, fields: DraftFields): Promise<ProposalDraft> {
  return coordinateDraft(() => {
    const exists = localStorage.getItem(DRAFT_KEY) !== null;
    const draft = loadDraft();
    if (!exists) draft.draft_id = draftId;
    // A tab holding an older intention cannot overwrite a newly started draft.
    if (draft.draft_id === draftId) draft.fields = fields;
    return persist(draft);
  });
}

export function prepareOperation(draftId: string, fields: DraftFields): Promise<ProposalDraft> {
  return coordinateDraft(() => {
    const exists = localStorage.getItem(DRAFT_KEY) !== null;
    const draft = loadDraft();
    if (!exists) draft.draft_id = draftId;
    if (!draft.operation) {
      if (draft.draft_id !== draftId) return persist(draft);
      const body = canonicalBody(fields);
      if (!validBody(body)) throw new DraftStorageError("invalid proposal fields");
      draft.fields = fields;
      draft.operation = { request_id: newId(), canonical_body: body, state: "prepared" };
    }
    return persist(draft);
  });
}

export function setOperationState(
  requestId: string,
  state: OperationState,
): Promise<ProposalDraft> {
  return coordinateDraft(() => {
    const draft = loadDraft();
    const operation = draft.operation;
    if (!operation || operation.request_id !== requestId)
      throw new DraftStorageError("operation changed");
    if (operation.state !== "acknowledged" && operation.state !== "conflict") {
      operation.state = state;
      if (state === "acknowledged") operation.proposal_id = requestId;
    }
    return persist(draft);
  });
}

export function startNewIntention(draftId: string, fields: DraftFields): Promise<ProposalDraft> {
  return coordinateDraft(() => {
    const current = loadDraft();
    if (
      current.draft_id !== draftId ||
      !current.operation ||
      !["acknowledged", "conflict"].includes(current.operation.state)
    )
      throw new DraftStorageError("unresolved submission");
    return persist(fresh(fields));
  });
}

export function clearAcknowledgedFields(
  requestId: string,
  expectedFields: DraftFields,
): Promise<ProposalDraft> {
  return coordinateDraft(() => {
    const draft = loadDraft();
    if (draft.operation?.request_id !== requestId || draft.operation.state !== "acknowledged")
      throw new DraftStorageError("operation changed");
    // Compare all persisted editable fields while holding the same writer transaction.
    // A different tab may already have saved the next idea under this draft ID.
    if (JSON.stringify(draft.fields) === JSON.stringify(expectedFields)) {
      draft.fields = { ...draft.fields, symbols: "", hypothesis: "", source: "" };
    }
    return persist(draft);
  });
}

export function matchesOperation(operation: DraftOperation, value: unknown): boolean {
  const response = object(value);
  if (
    !response ||
    response.id !== operation.request_id ||
    !Array.isArray(response.symbols) ||
    !response.symbols.every((s) => typeof s === "string")
  )
    return false;
  const expected = operation.canonical_body;
  return (
    JSON.stringify([...new Set(response.symbols.map((s) => s.toUpperCase()))].sort()) ===
      JSON.stringify(expected.symbols) &&
    (["hypothesis", "source_text", "direction", "horizon", "depth", "save_to"] as const).every(
      (key) => response[key] === expected[key],
    )
  );
}
