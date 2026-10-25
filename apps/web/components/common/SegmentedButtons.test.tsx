import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { SegmentedButtons } from "./SegmentedButtons";

const options = [
  { value: "a", label: "Alpha", testId: "alpha" },
  { value: "b", label: "Beta" },
];
function Group({ semantics = "radio" }: { semantics?: "radio" | "pressed" }) {
  const [value, setValue] = useState("a");
  return (
    <SegmentedButtons
      label="Choice"
      name="choice"
      options={options}
      value={value}
      onChange={setValue}
      semantics={semantics}
    />
  );
}

describe("SegmentedButtons", () => {
  it("selects native radios by click and keeps form names and test ids", async () => {
    const user = userEvent.setup();
    render(<Group />);
    expect(screen.getByRole("radiogroup", { name: "Choice" })).toBeVisible();
    expect(screen.getByTestId("alpha")).toBeChecked();
    expect(screen.getByTestId("alpha")).toHaveAttribute("name", "choice");
    await user.click(screen.getByLabelText("Beta"));
    expect(screen.getByLabelText("Beta")).toBeChecked();
    expect(screen.getByLabelText("Alpha")).not.toBeChecked();
  });

  it("supports tab entry and native arrow-key selection", async () => {
    const user = userEvent.setup();
    render(<Group />);
    await user.tab();
    expect(screen.getByLabelText("Alpha")).toHaveFocus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByLabelText("Beta")).toHaveFocus();
    expect(screen.getByLabelText("Beta")).toBeChecked();
  });

  it("retains pressed-button semantics where the original control used them", async () => {
    const user = userEvent.setup();
    render(<Group semantics="pressed" />);
    expect(screen.getByRole("button", { name: "Alpha" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Beta" }));
    expect(screen.getByRole("button", { name: "Beta" })).toHaveAttribute("aria-pressed", "true");
  });
});
