import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Loading from "./loading";
import InstrumentNotFound from "./not-found";

describe("instrument route boundaries", () => {
  it("uses instrument-neutral loading copy", () => {
    render(<Loading />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading instrument research…");
  });

  it("uses instrument-neutral not-found copy", () => {
    render(<InstrumentNotFound />);

    expect(screen.getByRole("heading", { name: "Instrument not found" })).toBeInTheDocument();
  });
});
