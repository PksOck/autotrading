import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { WATCHLIST_STORAGE_KEY } from "@/lib/watchlist-storage";

import WatchlistPage from "./page";

describe("WatchlistPage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("explains an empty watchlist", async () => {
    render(<WatchlistPage />);
    expect(await screen.findByText(/your watchlist is empty/i)).toBeInTheDocument();
  });

  it("lists stored symbols with canonical links and removes them", async () => {
    window.localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(["AMZN", "NOPE"]));
    const user = userEvent.setup();
    render(<WatchlistPage />);

    expect(await screen.findByRole("link", { name: /amazon\.com/i })).toHaveAttribute(
      "href",
      "/instruments/AMZN",
    );
    expect(screen.getByText("Detail not available for this symbol")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /remove amzn from watchlist/i }));
    expect(screen.queryByRole("link", { name: /amazon\.com/i })).not.toBeInTheDocument();
    expect(window.localStorage.getItem(WATCHLIST_STORAGE_KEY)).not.toContain("AMZN");
  });
});
