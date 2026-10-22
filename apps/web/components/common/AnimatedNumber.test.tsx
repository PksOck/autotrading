import { render, screen } from "@testing-library/react";
import { AnimatedNumber } from "./AnimatedNumber";

describe("AnimatedNumber", () => {
  it("exposes the final formatted value to assistive technology", () => {
    const { rerender } = render(<AnimatedNumber value={10} format={(v) => `${v.toFixed(1)} $`} />);
    expect(screen.getByText("10.0 $", { selector: ".sr-only" })).toBeInTheDocument();
    rerender(<AnimatedNumber value={12.5} format={(v) => `${v.toFixed(1)} $`} />);
    expect(screen.getByText("12.5 $", { selector: ".sr-only" })).toBeInTheDocument();
  });
});
