import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import { useSignal } from "@/lib/api/hooks";
import { ApiError } from "@/lib/api/client";
import en from "@/messages/en.json";
import { signal, signalId } from "@/test/signal-fixtures";
import { SignalDetail } from "./SignalDetail";

vi.mock("@/lib/api/hooks", () => ({ useSignal: vi.fn() }));
const refetch = vi.fn();
function result(value: object = {}) {
  vi.mocked(useSignal).mockReturnValue({
    data: signal,
    isLoading: false,
    error: null,
    refetch,
    ...value,
  } as unknown as ReturnType<typeof useSignal>);
}
function show(id = signalId) {
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <SignalDetail signalId={id} />
    </NextIntlClientProvider>,
  );
}

describe("SignalDetail", () => {
  it("shows the exact signal, rumor, state and original evidence without mutation controls", () => {
    result();
    show();
    expect(useSignal).toHaveBeenCalledWith(signalId);
    expect(screen.getByRole("heading", { name: "MSFT" })).toBeVisible();
    expect(screen.getByText("Watching")).toBeVisible();
    expect(screen.getByText("Unconfirmed")).toBeVisible();
    expect(screen.getByText(signal.rationale)).toBeVisible();
    expect(screen.getByRole("link", { name: "Original source" })).toHaveAttribute(
      "href",
      "https://example.test/news",
    );
    expect(screen.getByRole("link", { name: "Open instrument" })).toHaveAttribute(
      "href",
      "/i/MSFT",
    );
    expect(screen.queryByRole("button", { name: "Accept" })).not.toBeInTheDocument();
  });
  it("distinguishes loading, missing, malformed and retryable transport failure", () => {
    result({ isLoading: true, data: undefined });
    const view = show();
    expect(screen.getByLabelText("Loading signal")).toHaveAttribute("aria-busy", "true");
    view.unmount();
    result({ error: new ApiError(404, "signal_not_found"), data: undefined });
    const missing = show();
    expect(screen.getByRole("alert")).toHaveTextContent("Signal not found");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    missing.unmount();
    result({ data: undefined });
    const malformed = show("not-a-uuid");
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid signal link");
    malformed.unmount();
    result({ error: new ApiError(503, "unavailable"), data: undefined });
    show();
    expect(screen.getByRole("alert")).toHaveTextContent("could not be loaded");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalledOnce();
  });
  it("does not silently relabel old data as another signal", () => {
    result();
    show("20000000-0000-4000-8000-000000000456");
    expect(screen.queryByRole("heading", { name: "MSFT" })).not.toBeInTheDocument();
  });
});
