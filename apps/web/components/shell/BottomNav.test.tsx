import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import sl from "@/messages/sl.json";
import { BottomNav } from "./BottomNav";

const state = vi.hoisted(() => ({ pathname: "/", open: vi.fn() }));
vi.mock("next/navigation", () => ({ usePathname: () => state.pathname }));
vi.mock("./CommandPalette", () => ({ openCommandPalette: state.open }));

const setup = (pathname: string) => {
  state.pathname = pathname;
  return render(
    <NextIntlClientProvider locale="sl" messages={sl}>
      <BottomNav />
    </NextIntlClientProvider>,
  );
};

describe("BottomNav", () => {
  it("has exactly four main links plus More, with the current page marked", () => {
    setup("/radar");
    const nav = screen.getByRole("navigation");
    expect(
      within(nav)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Pregled", "Radar", "Signali", "Portfelj"]);
    expect(within(nav).getAllByRole("button")).toHaveLength(1);
    expect(within(nav).queryByRole("link", { name: "Vstopi" })).not.toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "Radar" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(nav.querySelectorAll('[aria-current="page"]')).toHaveLength(1);
  });

  it("marks More for secondary destinations and opens the palette", async () => {
    setup("/entries");
    const more = screen.getByRole("button", { name: "Več" });
    expect(more).toHaveAttribute("aria-current", "page");
    await userEvent.setup().click(more);
    expect(state.open).toHaveBeenCalled();
  });
});
