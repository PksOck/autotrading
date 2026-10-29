import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, expect, it, vi } from "vitest";
import { useIdentityFacts, useEnrichIdentity } from "@/lib/api/identity";
import { InstrumentFacts } from "./InstrumentFacts";

vi.mock("@/lib/api/identity", () => ({ useIdentityFacts: vi.fn(), useEnrichIdentity: vi.fn() }));
const mutate = vi.fn();
const data = {
  instrument_id: 17,
  symbol: "SYNTH",
  kind: "unknown",
  name: null,
  exchange: null,
  currency: null,
  identity_source: "synthetic",
  identity_updated_at: "2026-10-29T08:00:00Z",
  identity_status: "unresolved",
  metrics: {
    pe: {
      value: "12.5",
      unit: "multiple",
      meta: {
        source: "synthetic",
        source_field: "peTTM",
        basis: "TTM",
        fetched_at: "2026-10-29T08:00:00Z",
        stale: true,
        availability: "partial",
        reason_code: "basis_unverified",
      },
    },
  },
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useIdentityFacts).mockReturnValue({
    data,
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useIdentityFacts>);
  vi.mocked(useEnrichIdentity).mockReturnValue({
    mutate,
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof useEnrichIdentity>);
});
function show() {
  return render(
    <NextIntlClientProvider
      locale="en"
      messages={{}}
      onError={() => {}}
      getMessageFallback={({ key }) => key}
    >
      <InstrumentFacts symbol="SYNTH" />
    </NextIntlClientProvider>,
  );
}
it("shows real metric provenance and gaps without guessing identity", () => {
  show();
  expect(screen.getByText("12.5 ×")).toBeVisible();
  expect(screen.getByText(/peTTM/)).toBeVisible();
  expect(screen.getByText("stale")).toBeVisible();
  expect(screen.getAllByText("unknown").length).toBeGreaterThan(0);
  expect(screen.queryByText("USD")).toBeNull();
  expect(mutate).not.toHaveBeenCalled();
});
it("only enriches on explicit action with the selected identity and version", () => {
  show();
  fireEvent.click(screen.getByRole("button", { name: "enrich" }));
  expect(mutate).toHaveBeenCalledWith({
    instrument_id: 17,
    expected_updated_at: data.identity_updated_at,
  });
});
it("does not display facts as empty during a request failure", () => {
  vi.mocked(useIdentityFacts).mockReturnValue({
    data: undefined,
    error: new Error("offline"),
    isLoading: false,
  } as unknown as ReturnType<typeof useIdentityFacts>);
  show();
  expect(screen.getByRole("alert")).toHaveTextContent("loadError");
  expect(screen.queryByRole("button", { name: "enrich" })).toBeNull();
});
