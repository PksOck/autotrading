import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { vi } from "vitest";
import { api, ApiError } from "./client";
import {
  keys,
  useThesisReviews,
  useThesisReviewProposals,
  useAcceptThesisReviewProposal,
  useDismissThesisReviewProposal,
} from "./hooks";
import { review, reviewProposal, thesisId } from "@/test/thesis-fixtures";

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

it("loads all review and pending-proposal pages for the detail view", async () => {
  const { wrapper } = setup();
  vi.mocked(api.get)
    .mockResolvedValueOnce([review, review])
    .mockResolvedValueOnce([{ ...review, id: "older-review" }]);
  const reviews = renderHook(() => useThesisReviews(thesisId, 2, 0, true), { wrapper });
  await waitFor(() => expect(reviews.result.current.data).toHaveLength(3));
  expect(api.get).toHaveBeenCalledWith(`/theses/${thesisId}/reviews?limit=2&offset=2`);
  vi.mocked(api.get)
    .mockResolvedValueOnce(
      Array.from({ length: 30 }, (_, index) => ({ ...reviewProposal, id: `proposal-${index}` })),
    )
    .mockResolvedValueOnce([{ ...reviewProposal, id: "older-proposal" }]);
  const proposals = renderHook(() => useThesisReviewProposals(thesisId), { wrapper });
  await waitFor(() => expect(proposals.result.current.data).toHaveLength(31));
  expect(api.get).toHaveBeenCalledWith(
    `/theses/${thesisId}/review-proposals?state=pending&limit=30&offset=30`,
  );
});

it("loads reviews with pagination and pending proposals using encoded thesis IDs", async () => {
  const { wrapper } = setup();
  vi.mocked(api.get).mockResolvedValueOnce([review]).mockResolvedValueOnce([reviewProposal]);
  const reviews = renderHook(() => useThesisReviews("a/b", 10, 20), { wrapper });
  await waitFor(() => expect(reviews.result.current.data).toEqual([review]));
  expect(api.get).toHaveBeenCalledWith("/theses/a%2Fb/reviews?limit=10&offset=20");
  const proposals = renderHook(() => useThesisReviewProposals("a/b"), { wrapper });
  await waitFor(() => expect(proposals.result.current.data).toEqual([reviewProposal]));
  expect(api.get).toHaveBeenCalledWith("/theses/a%2Fb/review-proposals?state=pending");
});

it.each(["accept", "dismiss"] as const)(
  "%s sends the exact contract and invalidates reviews, proposals, detail, lists and signals",
  async (action) => {
    const { client, wrapper } = setup();
    const queryKeys = [
      keys.thesisReviews(thesisId),
      keys.thesisReviews(thesisId, 10, 20),
      keys.thesisReviewProposals(thesisId),
      keys.thesis(thesisId),
      keys.theses(),
      keys.theses("MSFT"),
      keys.signals("all"),
      keys.signals("new"),
    ];
    for (const key of queryKeys) client.setQueryData(key, []);
    vi.mocked(api.send).mockResolvedValue(reviewProposal);
    const accept = renderHook(() => useAcceptThesisReviewProposal(thesisId, "p/id"), { wrapper });
    const dismiss = renderHook(() => useDismissThesisReviewProposal(thesisId, "p/id"), { wrapper });
    const acceptBody = {
      expected_status: reviewProposal.status_at_review,
      expected_last_event_id: null,
    };
    const dismissBody = { reason: "Await audited accounts" };
    await act(async () => {
      if (action === "accept") await accept.result.current.mutateAsync(acceptBody);
      else await dismiss.result.current.mutateAsync(dismissBody);
    });
    expect(api.send).toHaveBeenLastCalledWith(
      `/theses/${thesisId}/review-proposals/p%2Fid/${action}`,
      "POST",
      action === "accept" ? acceptBody : dismissBody,
    );
    for (const key of queryKeys) expect(client.getQueryState(key)?.isInvalidated).toBe(true);
  },
);

it("refreshes cached data on conflict and preserves a non-null expected event ID", async () => {
  const { client, wrapper } = setup();
  client.setQueryData(keys.thesisReviews(thesisId), [review]);
  client.setQueryData(keys.thesis(thesisId), {});
  vi.mocked(api.send).mockRejectedValueOnce(new ApiError(409, "claim_changed"));
  const accept = renderHook(() => useAcceptThesisReviewProposal(thesisId, reviewProposal.id), {
    wrapper,
  });
  const body = {
    expected_status: reviewProposal.status_at_review,
    expected_last_event_id: "event-id",
  };
  await act(async () => {
    await expect(accept.result.current.mutateAsync(body)).rejects.toMatchObject({ status: 409 });
  });
  expect(api.send).toHaveBeenLastCalledWith(
    `/theses/${thesisId}/review-proposals/${reviewProposal.id}/accept`,
    "POST",
    body,
  );
  expect(client.getQueryState(keys.thesisReviews(thesisId))?.isInvalidated).toBe(true);
  expect(client.getQueryState(keys.thesis(thesisId))?.isInvalidated).toBe(true);
});
