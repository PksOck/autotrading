import { act, fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import { useCreateProposal } from "@/lib/api/hooks";
import { api, ApiError } from "@/lib/api/client";
import en from "@/messages/en.json";
import sl from "@/messages/sl.json";
import { PROPOSE_EVENT } from "@/stores/proposals";
import { ProposalComposer } from "./ProposalComposer";
import {
  DRAFT_KEY,
  DEFAULT_FIELDS,
  loadDraft,
  prepareOperation,
  saveDraftFields,
} from "@/lib/proposal-draft";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
const invalidate = vi.hoisted(() => vi.fn());
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: invalidate }),
}));
vi.mock("@/lib/api/hooks", () => ({
  useCreateProposal: vi.fn(),
  keys: { proposals: ["proposals"] },
}));
vi.mock("@/lib/api/client", async (original) => ({
  ...(await original<typeof import("@/lib/api/client")>()),
  api: { get: vi.fn() },
}));
vi.mock("@/lib/useBackToClose", () => ({
  useBackToClose: (_: boolean, close: () => void) => close,
}));
const post = vi.fn();
function show() {
  const view = render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <ProposalComposer />
    </NextIntlClientProvider>,
  );
  act(() => window.dispatchEvent(new CustomEvent(PROPOSE_EVENT, { detail: {} })));
  return view;
}
beforeEach(() => {
  localStorage.clear();
  vi.resetAllMocks();
  Object.defineProperty(navigator, "locks", {
    configurable: true,
    value: { request: (_: string, run: () => unknown) => Promise.resolve().then(run) },
  });
  vi.mocked(useCreateProposal).mockReturnValue({
    mutateAsync: post,
    isPending: false,
  } as unknown as ReturnType<typeof useCreateProposal>);
  vi.mocked(api.get).mockRejectedValue(new ApiError(404, "proposal_not_found"));
  post.mockRejectedValue(new Error("response lost"));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

it("restores focus to the actual external opener after Cancel", async () => {
  const opener = document.createElement("button");
  opener.textContent = "External proposal opener";
  document.body.append(opener);
  opener.focus();
  show();
  await waitFor(() => expect(screen.getByLabelText("Symbol(s)")).toHaveFocus());
  fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  await waitFor(() => expect(opener).toHaveFocus());
  opener.remove();
});

it("preserves the frozen request across a lost response and remount", async () => {
  post.mockRejectedValue(new Error("response lost"));
  vi.mocked(api.get).mockRejectedValue(new ApiError(404, "proposal_not_found"));
  const first = show();
  fireEvent.change(screen.getByLabelText("Symbol(s)"), { target: { value: "msft, amd" } });
  fireEvent.change(screen.getByLabelText("Hypothesis"), { target: { value: "Original idea" } });
  fireEvent.click(screen.getByRole("button", { name: "Send to analysis" }));
  await waitFor(() => expect(post).toHaveBeenCalledTimes(1));
  const original = post.mock.calls[0]![0];
  first.unmount();
  show();
  fireEvent.change(screen.getByLabelText("Hypothesis"), { target: { value: "Changed idea" } });
  fireEvent.click(screen.getByRole("button", { name: /Check submission|Send to analysis/ }));
  await waitFor(() => expect(post).toHaveBeenCalledTimes(2));
  expect(post.mock.calls[1]![0]).toEqual(original);
  expect(api.get).toHaveBeenCalledWith(`/proposals/${original.request_id}`);
});

async function savedOperation() {
  const draft = await prepareOperation(loadDraft().draft_id, {
    ...DEFAULT_FIELDS,
    symbols: "AMD",
    hypothesis: "Original idea",
  });
  return draft.operation!;
}

it("preserves another tab's complete edited draft through acknowledgement, close and reopen", async () => {
  const operation = await savedOperation();
  show();
  await act(async () => {});
  const saved = loadDraft();
  const edited = {
    ...saved.fields,
    symbols: "NVDA",
    hypothesis: "Other tab edit",
    source: "Other source",
    depth: "deep" as const,
    direction: "down" as const,
    horizon: "years" as const,
    saveTo: "active" as const,
  };
  await saveDraftFields(saved.draft_id, edited);
  vi.mocked(api.get).mockResolvedValue({ id: operation.request_id, ...operation.canonical_body });
  fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  expect(loadDraft().fields).toEqual(edited);
  act(() => window.dispatchEvent(new CustomEvent(PROPOSE_EVENT, { detail: {} })));
  await act(async () => {});
  expect(loadDraft().fields).toEqual(edited);
});

it("keeps identity and neutral wording when acceptance succeeds but acknowledgement storage fails", async () => {
  let accepted: Record<string, unknown> | null = null;
  post.mockImplementation(async (body) => {
    accepted = { ...body, id: body.request_id };
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota after acceptance");
    });
    return accepted;
  });
  show();
  fireEvent.change(screen.getByLabelText("Symbol(s)"), { target: { value: "AMD" } });
  fireEvent.click(screen.getByRole("button", { name: "Send to analysis" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Sending is paused"));
  const requestId = post.mock.calls[0]![0].request_id;
  expect(loadDraft().operation?.request_id).toBe(requestId);
  expect(screen.getByRole("alert")).not.toHaveTextContent(/nothing.*sent|not.*sent/i);
  vi.restoreAllMocks();
  vi.mocked(api.get).mockResolvedValue(accepted);
  fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
  await waitFor(() => expect(loadDraft().operation?.state).toBe("acknowledged"));
  expect(post).toHaveBeenCalledTimes(1);
  expect(api.get).toHaveBeenLastCalledWith(`/proposals/${requestId}`);
  expect(en.proposal.durable.storageError).not.toMatch(/nothing.*sent|not.*sent/i);
  expect(sl.proposal.durable.storageError).not.toMatch(/ni.*poslano/i);
});

it("looks up the exact frozen ID and acknowledges matching data without another POST", async () => {
  const operation = await savedOperation();
  vi.mocked(api.get).mockResolvedValue({ id: operation.request_id, ...operation.canonical_body });
  show();
  await act(async () => {});
  expect(api.get).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Hypothesis"), { target: { value: "Next idea" } });
  fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  expect(post).not.toHaveBeenCalled();
  expect(loadDraft()).toMatchObject({
    fields: { hypothesis: "Next idea" },
    operation: { state: "acknowledged", proposal_id: operation.request_id },
  });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["proposals"] });
  act(() => window.dispatchEvent(new CustomEvent(PROPOSE_EVENT, { detail: {} })));
  fireEvent.click(screen.getByRole("button", { name: "Start new proposal" }));
  await screen.findByRole("button", { name: "Send to analysis" });
  expect(post).not.toHaveBeenCalled();
  expect(loadDraft().operation).toBeNull();
});

it.each(["id", "hypothesis"])(
  "does not acknowledge a found record with a different %s",
  async (key) => {
    const operation = await savedOperation();
    vi.mocked(api.get).mockResolvedValue({
      id: operation.request_id,
      ...operation.canonical_body,
      [key]: key === "id" ? crypto.randomUUID() : "Different",
    });
    show();
    fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
    await waitFor(() => expect(loadDraft().operation?.state).toBe("conflict"));
    expect(screen.getByRole("alert")).toHaveTextContent("does not match");
    expect(post).not.toHaveBeenCalled();
  },
);

it("preserves an unknown submission when lookup is unavailable", async () => {
  const operation = await savedOperation();
  vi.mocked(api.get).mockRejectedValue(new ApiError(503, "unavailable"));
  show();
  fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
  await waitFor(() => expect(loadDraft().operation?.state).toBe("outcome_unknown"));
  expect(loadDraft().operation?.request_id).toBe(operation.request_id);
  expect(screen.getByRole("status")).toHaveTextContent("outcome is unknown");
  expect(screen.queryByRole("button", { name: "Start new proposal" })).not.toBeInTheDocument();
  expect(post).not.toHaveBeenCalled();
});

it("makes a POST conflict visible without automatic resubmission", async () => {
  await savedOperation();
  post.mockRejectedValue(new ApiError(409, "idempotency_conflict"));
  show();
  fireEvent.click(screen.getByRole("button", { name: "Check submission" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("does not match"));
  expect(post).toHaveBeenCalledTimes(1);
  expect(loadDraft().operation?.state).toBe("conflict");
});

it("blocks POST and keeps visible text when durable storage writes fail", async () => {
  show();
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota");
  });
  fireEvent.change(screen.getByLabelText("Symbol(s)"), { target: { value: "AMD" } });
  fireEvent.change(screen.getByLabelText("Hypothesis"), { target: { value: "Keep my text" } });
  fireEvent.click(screen.getByRole("button", { name: "Send to analysis" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Sending is paused"));
  expect(screen.getByLabelText("Hypothesis")).toHaveValue("Keep my text");
  expect(post).not.toHaveBeenCalled();
});

it("blocks POST when readback cannot confirm the prepared operation", async () => {
  show();
  fireEvent.change(screen.getByLabelText("Symbol(s)"), { target: { value: "AMD" } });
  await act(async () => {});
  vi.spyOn(Storage.prototype, "getItem").mockImplementation((key) =>
    key === DRAFT_KEY ? null : null,
  );
  fireEvent.click(screen.getByRole("button", { name: "Send to analysis" }));
  await screen.findByRole("alert");
  expect(post).not.toHaveBeenCalled();
});

it("can retry after an initial storage read failure without losing typed text", async () => {
  const read = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new Error("temporarily blocked");
  });
  show();
  fireEvent.change(screen.getByLabelText("Symbol(s)"), { target: { value: "AMD" } });
  fireEvent.change(screen.getByLabelText("Hypothesis"), {
    target: { value: "Keep through recovery" },
  });
  read.mockRestore();
  fireEvent.click(screen.getByRole("button", { name: "Send to analysis" }));
  await waitFor(() => expect(post).toHaveBeenCalledTimes(1));
  expect(post.mock.calls[0]![0].hypothesis).toBe("Keep through recovery");
});

it("does not replay on opening or double-clicking a pending verification", async () => {
  await savedOperation();
  let finish!: (value: never) => void;
  vi.mocked(api.get).mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  show();
  await act(async () => {});
  expect(api.get).not.toHaveBeenCalled();
  const check = screen.getByRole("button", { name: "Check submission" });
  fireEvent.click(check);
  fireEvent.click(check);
  await waitFor(() => expect(api.get).toHaveBeenCalledTimes(1));
  expect(post).not.toHaveBeenCalled();
  await act(async () => finish({} as never));
});
