import { render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import { useRadarEvents } from "@/lib/api/hooks";
import { useRadarEvent } from "@/lib/api/research";
import { ApiError } from "@/lib/api/client";
import en from "@/messages/en.json";
import { RadarView } from "./RadarView";

vi.mock("@/lib/api/hooks", () => ({ useRadarEvents: vi.fn() }));
vi.mock("@/lib/api/research", () => ({ useRadarEvent: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/radar",
  useSearchParams: () => new URLSearchParams("event=42"),
}));
vi.mock("@/components/common/EntityLink", () => ({
  EntityLink: ({ entity }: { entity: { id: string } }) => <span>{entity.id}</span>,
}));
const event = {
  id: 1,
  symbols: ["ASML"],
  title: "First list item",
  summary: null,
  event_type: "earnings",
  is_rumor: false,
  last_seen_at: "2026-10-28T12:00:00Z",
  sources: [
    {
      kind: "news",
      source: "news",
      url: "https://example.test",
      title: "Source",
      published_at: "2026-10-28T12:00:00Z",
    },
  ],
};
function show(result: object) {
  vi.mocked(useRadarEvents).mockReturnValue({
    data: [event],
    error: null,
    isLoading: false,
  } as unknown as ReturnType<typeof useRadarEvents>);
  vi.mocked(useRadarEvent).mockReturnValue({
    error: null,
    isLoading: false,
    ...result,
  } as unknown as ReturnType<typeof useRadarEvent>);
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <RadarView />
    </NextIntlClientProvider>,
  );
}
it("loads exact hidden selection rather than opening the first filtered item", async () => {
  show({ data: { ...event, id: 42, title: "Exact selected event" } });
  expect(useRadarEvent).toHaveBeenCalledWith(42);
  await waitFor(() =>
    expect(screen.getByRole("heading", { name: "Exact selected event" })).toBeVisible(),
  );
  expect(screen.queryByRole("heading", { name: "First list item" })).not.toBeInTheDocument();
  expect(screen.getAllByText("No official confirmation")).toHaveLength(2);
});
it("shows a missing selection without silently using a different event", () => {
  show({ error: new ApiError(404, "event_not_found") });
  expect(screen.getByRole("alert")).toHaveTextContent("selected item was not found");
  expect(screen.queryByRole("heading", { name: "First list item" })).not.toBeInTheDocument();
});
