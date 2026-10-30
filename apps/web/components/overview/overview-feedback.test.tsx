import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import feedback from "@/messages/en.json";
import { PulseTimeline } from "./PulseTimeline";
import { PortfolioTreemapCard } from "./PortfolioTreemapCard";
import { Treemap } from "./Treemap";

const { open, portfolio } = vi.hoisted(() => ({ open: vi.fn(), portfolio: vi.fn() }));
vi.mock("@/lib/use-peek", () => ({ usePeek: () => ({ open }) }));
vi.mock("@/lib/api/hooks", () => ({ usePortfolio: portfolio }));
vi.mock("@/lib/use-element-size", () => ({
  useElementSize: () => [null, { width: 800, height: 280 }],
}));
const wrap = (node: React.ReactNode) =>
  render(
    <NextIntlClientProvider locale="en" messages={{ ...en, ...feedback }} timeZone="UTC">
      {node}
    </NextIntlClientProvider>,
  );

it("opens the actual radar event, including with the keyboard", () => {
  wrap(
    <PulseTimeline
      events={[{ id: "17", symbol: "MSFT", hoursAgo: 24, score: 0.7, type: "rumor" }]}
    />,
  );
  fireEvent.click(screen.getByRole("button"));
  expect(open).toHaveBeenLastCalledWith({ kind: "event", id: "17" });
  fireEvent.keyDown(screen.getByRole("button"), { key: " " });
  expect(open).toHaveBeenLastCalledWith({ kind: "event", id: "17" });
});

it("never substitutes sample positions when portfolio is unavailable", () => {
  portfolio.mockReturnValue({ data: undefined, error: new Error("offline"), isLoading: false });
  wrap(<PortfolioTreemapCard />);
  expect(screen.getByText(en.table.loadFailed)).toBeInTheDocument();
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("shows unknown daily change as missing rather than a green zero", () => {
  wrap(<Treemap items={[{ symbol: "MSFT", weight: 100, change: null, thesis: "none" }]} />);
  const tile = screen.getByRole("button", { name: /MSFT/ });
  expect(tile).toHaveAccessibleName(`MSFT, ${feedback.overviewFeedback.notAvailable}`);
  expect(tile.style.background).not.toContain("--pos");
});
