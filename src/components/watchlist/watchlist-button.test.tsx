import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { WATCHLIST_STORAGE_KEY } from "@/lib/watchlist-storage";

import { WatchlistButton } from "./watchlist-button";

describe("WatchlistButton", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("offers to add an unwatched symbol", () => {
    render(<WatchlistButton symbol="AMZN" />);
    expect(screen.getByRole("button", { name: /add amzn to watchlist/i })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("toggles and persists across remounts", async () => {
    const user = userEvent.setup();
    const { unmount } = render(<WatchlistButton symbol="amzn" />);

    await user.click(screen.getByRole("button", { name: /add amzn to watchlist/i }));
    expect(screen.getByRole("button", { name: /remove amzn from watchlist/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(window.localStorage.getItem(WATCHLIST_STORAGE_KEY)).toContain("AMZN");

    unmount();
    render(<WatchlistButton symbol="AMZN" />);
    expect(screen.getByRole("button", { name: /remove amzn from watchlist/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /remove amzn from watchlist/i }));
    expect(screen.getByRole("button", { name: /add amzn to watchlist/i })).toBeInTheDocument();
    expect(window.localStorage.getItem(WATCHLIST_STORAGE_KEY)).not.toContain("AMZN");
  });
});
