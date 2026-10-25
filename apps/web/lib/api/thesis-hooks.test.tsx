import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { vi } from "vitest";
import { api } from "./client";
import {
  keys,
  useTheses,
  useThesis,
  useCreateThesisDraft,
  usePatchThesisRevision,
  useConfirmThesisRevision,
  useChangeClaimStatus,
} from "./hooks";
import { claim, revision, runId, summary, thesis, thesisId } from "@/test/thesis-fixtures";

vi.mock("./client", async (original) => ({
  ...(await original<typeof import("./client")>()),
  api: { get: vi.fn(), send: vi.fn() },
}));
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper };
}
afterEach(() => vi.clearAllMocks());

it("loads list and detail using exact backend routes and pagination", async () => {
  expect(keys.theses("all")).not.toEqual(keys.theses());
  const { wrapper } = setup();
  vi.mocked(api.get).mockResolvedValueOnce([summary]).mockResolvedValueOnce(thesis);
  const list = renderHook(() => useTheses("A B", 10, 20), { wrapper });
  await waitFor(() => expect(list.result.current.isSuccess).toBe(true));
  expect(api.get).toHaveBeenCalledWith("/theses?limit=10&offset=20&symbol=A%20B");
  const detail = renderHook(() => useThesis(thesisId), { wrapper });
  await waitFor(() => expect(detail.result.current.data).toEqual(thesis));
  expect(api.get).toHaveBeenCalledWith(`/theses/${thesisId}`);
});

it("mutations use the API contract and invalidate lists and detail on success and conflict", async () => {
  const { client, wrapper } = setup();
  client.setQueryData(keys.theses(), [summary]);
  client.setQueryData(keys.thesis(thesisId), thesis);
  vi.mocked(api.send).mockResolvedValue(revision);
  const draft = renderHook(() => useCreateThesisDraft(), { wrapper });
  await act(() => draft.result.current.mutateAsync({ analysis_run_id: runId }));
  expect(api.send).toHaveBeenLastCalledWith("/theses/drafts", "POST", { analysis_run_id: runId });
  expect(client.getQueryState(keys.theses())?.isInvalidated).toBe(true);
  expect(client.getQueryState(keys.thesis(thesisId))?.isInvalidated).toBe(true);
  const patch = renderHook(() => usePatchThesisRevision(thesisId, revision.id), { wrapper });
  const body = { expected_version: 1, claims: [{ id: claim.id, statement: "New statement" }] };
  await act(() => patch.result.current.mutateAsync(body));
  expect(api.send).toHaveBeenLastCalledWith(
    `/theses/${thesisId}/revisions/${revision.id}`,
    "PATCH",
    body,
  );
  const confirm = renderHook(() => useConfirmThesisRevision(thesisId, revision.id), { wrapper });
  await act(() => confirm.result.current.mutateAsync());
  expect(api.send).toHaveBeenLastCalledWith(
    `/theses/${thesisId}/revisions/${revision.id}/confirm`,
    "POST",
  );
  const status = renderHook(() => useChangeClaimStatus(thesisId, claim.id), { wrapper });
  const change = {
    to_status: "open" as const,
    expected_status: "open" as const,
    rationale: "Review",
    evidence: [],
  };
  vi.mocked(api.send).mockResolvedValue(claim);
  await act(() => status.result.current.mutateAsync(change));
  expect(api.send).toHaveBeenLastCalledWith(
    `/theses/${thesisId}/claims/${claim.id}/status`,
    "POST",
    change,
  );
  client.setQueryData(keys.thesis(thesisId), thesis);
  vi.mocked(api.send).mockRejectedValueOnce(new Error("conflict"));
  await act(async () => {
    await expect(status.result.current.mutateAsync(change)).rejects.toThrow("conflict");
  });
  expect(client.getQueryState(keys.thesis(thesisId))?.isInvalidated).toBe(true);
});
