import { act, renderHook, waitFor } from "@testing-library/react";
import { StrictMode, type ReactNode } from "react";
import { useBackToClose } from "./useBackToClose";

describe("useBackToClose", () => {
  beforeEach(() => {
    window.history.replaceState({ __NA: true, tree: "router" }, "", "/?filter=kept");
  });

  it("pushes the same URL, preserves router state, and closes on popstate", () => {
    const onClose = vi.fn();
    const previous = window.history.state;
    const url = window.location.href;
    const { unmount } = renderHook(() => useBackToClose(true, onClose));
    expect(window.location.href).toBe(url);
    expect(window.history.state).toMatchObject(previous);
    expect(window.history.state.prezaOverlays).toHaveLength(1);
    act(() => {
      window.history.replaceState(previous, "", url);
      window.dispatchEvent(new PopStateEvent("popstate", { state: previous }));
    });
    expect(onClose).toHaveBeenCalledOnce();
    unmount();
  });

  it("UI close pops its entry before running navigation actions, only once", async () => {
    const onClose = vi.fn();
    const after = vi.fn();
    const { result, unmount } = renderHook(() => useBackToClose(true, onClose));
    act(() => {
      result.current(after);
      result.current(after);
    });
    await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
    expect(after).toHaveBeenCalledOnce();
    expect(window.history.state.prezaOverlays).toBeUndefined();
    expect(window.location.search).toBe("?filter=kept");
    unmount();
  });

  it("does not push twice under StrictMode effect replay", () => {
    const push = vi.spyOn(window.history, "pushState");
    const wrapper = ({ children }: { children: ReactNode }) => <StrictMode>{children}</StrictMode>;
    const { unmount } = renderHook(() => useBackToClose(true, vi.fn()), { wrapper });
    expect(push).toHaveBeenCalledOnce();
    unmount();
    push.mockRestore();
  });

  it("closes only the top overlay when nested", async () => {
    const lowerClose = vi.fn();
    const upperClose = vi.fn();
    const { result, unmount } = renderHook(() => {
      useBackToClose(true, lowerClose);
      return useBackToClose(true, upperClose);
    });
    act(() => result.current());
    await waitFor(() => expect(upperClose).toHaveBeenCalledOnce());
    expect(lowerClose).not.toHaveBeenCalled();
    unmount();
  });

  it("uses a new token on reopen even if Forward restored an old marker", async () => {
    const onClose = vi.fn();
    const { result, rerender, unmount } = renderHook(({ open }) => useBackToClose(open, onClose), {
      initialProps: { open: true },
    });
    const oldState = window.history.state;
    act(() => result.current());
    await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
    rerender({ open: false });
    window.history.replaceState(oldState, "");
    rerender({ open: true });
    expect(window.history.state.prezaOverlays.at(-1)).not.toBe(oldState.prezaOverlays.at(-1));
    act(() => result.current());
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(2));
    unmount();
  });
});
