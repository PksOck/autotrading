import { act, renderHook } from "@testing-library/react";
import { vi } from "vitest";
import { usePeek } from "./use-peek";

const nav = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  params: "status=watching&peek=signal%3Aid&filter=keep",
}));
vi.mock("next/navigation", () => ({
  useRouter: () => nav,
  usePathname: () => "/signals",
  useSearchParams: () => new URLSearchParams(nav.params),
}));

describe("usePeek", () => {
  it("closes a direct link in place without adding a history entry or losing filters", () => {
    const { result } = renderHook(() => usePeek());
    act(() => result.current.close());
    expect(nav.replace).toHaveBeenCalledWith("/signals?status=watching&filter=keep", {
      scroll: false,
    });
    expect(nav.push).not.toHaveBeenCalled();
  });
});
