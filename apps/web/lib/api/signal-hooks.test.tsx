import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { vi } from "vitest";
import { api, ApiError } from "./client";
import { keys, useSignal, useSignalUpdate } from "./hooks";
import { signal, signalId } from "@/test/signal-fixtures";

vi.mock("./client", async (original) => ({
  ...(await original<typeof import("./client")>()),
  api: { get: vi.fn(), send: vi.fn() },
}));
function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper };
}
afterEach(() => vi.clearAllMocks());

it("disables malformed IDs and isolates detail from lists and another ID", async () => {
  const { wrapper } = setup();
  const detail = renderHook(({ id }) => useSignal(id), {
    wrapper,
    initialProps: { id: null as string | null },
  });
  detail.rerender({ id: "broken" });
  expect(api.get).not.toHaveBeenCalled();
  vi.mocked(api.get).mockResolvedValueOnce(signal);
  detail.rerender({ id: signalId });
  await waitFor(() => expect(detail.result.current.data).toEqual(signal));
  expect(api.get).toHaveBeenCalledWith(`/signals/${signalId}`);
  const second = "20000000-0000-4000-8000-000000000456";
  vi.mocked(api.get).mockImplementationOnce(() => new Promise(() => {}));
  detail.rerender({ id: second });
  expect(detail.result.current.data).toBeUndefined();
  expect(keys.signal(signalId)).not.toEqual(keys.signals("all"));
});

it.each([404, 422])("does not retry a permanent %s error", async (status) => {
  const { wrapper } = setup();
  vi.mocked(api.get).mockRejectedValue(new ApiError(status, "missing"));
  const detail = renderHook(() => useSignal(signalId), { wrapper });
  await waitFor(() => expect(detail.result.current.isError).toBe(true));
  expect(api.get).toHaveBeenCalledOnce();
});

it("invalidates every list and the changed detail after an explicit status mutation", async () => {
  const { client, wrapper } = setup();
  client.setQueryData(keys.signals("new"), [signal]);
  client.setQueryData(keys.signals("all"), [signal]);
  client.setQueryData(keys.signal(signalId), signal);
  vi.mocked(api.send).mockResolvedValue({ ...signal, status: "dismissed" });
  const mutation = renderHook(() => useSignalUpdate(), { wrapper });
  await act(() => mutation.result.current.mutateAsync({ id: signalId, status: "dismissed" }));
  expect(client.getQueryState(keys.signals("new"))?.isInvalidated).toBe(true);
  expect(client.getQueryState(keys.signals("all"))?.isInvalidated).toBe(true);
  expect(client.getQueryState(keys.signal(signalId))?.isInvalidated).toBe(true);
});
