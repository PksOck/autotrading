import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { vi } from "vitest";
import { SessionGuard } from "./SessionGuard";

function Draft() {
  const [value, setValue] = useState("");
  return (
    <input aria-label="Draft" value={value} onChange={(event) => setValue(event.target.value)} />
  );
}

it("preserves unsaved drafts across backgrounding and conceals a late session check", async () => {
  let hidden = false;
  const property = vi.spyOn(document, "hidden", "get").mockImplementation(() => hidden);
  const fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify({ enabled: true, authenticated: true })));
  vi.stubGlobal("fetch", fetch);
  const view = render(
    <QueryClientProvider client={new QueryClient()}>
      <SessionGuard>
        <Draft />
      </SessionGuard>
    </QueryClientProvider>,
  );
  try {
    const draft = await screen.findByLabelText("Draft");
    fireEvent.change(draft, { target: { value: "unsaved thesis condition" } });
    hidden = true;
    fireEvent(document, new Event("visibilitychange"));
    expect(draft).not.toBeVisible();
    let resolve!: (response: Response) => void;
    fetch.mockImplementationOnce(
      () =>
        new Promise<Response>((done) => {
          resolve = done;
        }),
    );
    fireEvent(window, new Event("pageshow"));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    await act(async () =>
      resolve(new Response(JSON.stringify({ enabled: true, authenticated: true }))),
    );
    expect(draft).not.toBeVisible();
    fetch.mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify({ enabled: true, authenticated: true }))),
    );
    hidden = false;
    fireEvent(document, new Event("visibilitychange"));
    await waitFor(() => expect(draft).toBeVisible());
    expect(draft).toHaveValue("unsaved thesis condition");
  } finally {
    view.unmount();
    property.mockRestore();
    vi.unstubAllGlobals();
  }
});
