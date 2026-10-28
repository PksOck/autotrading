import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { vi } from "vitest";
import { keys, usePortfolioImport } from "./hooks";

afterEach(() => vi.unstubAllGlobals());

function setup() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  client.setQueryData(keys.portfolio, {});
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper };
}

it("uploads raw XML and invalidates the portfolio", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ counts: { positions: 2, trades: 1, cash: 2 }, as_of: null }),
    });
  vi.stubGlobal("fetch", fetch);
  const { client, wrapper } = setup();
  const hook = renderHook(() => usePortfolioImport(), { wrapper });
  const file = new File(["<FlexQueryResponse/>"], "flex.xml");
  Object.defineProperty(file, "text", { value: async () => "<FlexQueryResponse/>" });
  await act(() => hook.result.current.mutateAsync(file));
  expect(fetch).toHaveBeenCalledWith(
    "/api/portfolio/import",
    expect.objectContaining({
      method: "POST",
      headers: { "content-type": "application/xml" },
      body: "<FlexQueryResponse/>",
    }),
  );
  expect(client.getQueryState(keys.portfolio)?.isInvalidated).toBe(true);
});

it("rejects oversized files without sending them", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const { wrapper } = setup();
  const hook = renderHook(() => usePortfolioImport(), { wrapper });
  const file = new File([], "large.xml");
  Object.defineProperty(file, "size", { value: 10 * 1024 * 1024 + 1 });
  await act(async () => {
    await expect(hook.result.current.mutateAsync(file)).rejects.toThrow("flex_too_large");
  });
  expect(fetch).not.toHaveBeenCalled();
});

it("preserves safe server errors and leaves cached portfolio unchanged", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: "flex_invalid" }),
      }),
  );
  const { client, wrapper } = setup();
  const hook = renderHook(() => usePortfolioImport(), { wrapper });
  const file = new File([], "invalid.xml");
  Object.defineProperty(file, "text", { value: async () => "invalid" });
  await act(async () => {
    await expect(hook.result.current.mutateAsync(file)).rejects.toThrow("flex_invalid");
  });
  expect(client.getQueryState(keys.portfolio)?.isInvalidated).toBe(false);
});
