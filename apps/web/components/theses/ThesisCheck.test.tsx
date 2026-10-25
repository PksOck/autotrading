import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import sl from "@/messages/sl.json";
import { ThesisCheck } from "./ThesisCheck";
import type { ClaimStatus } from "@/lib/api/types";

describe("ThesisCheck", () => {
  it.each([
    ["open", "Open", "○"],
    ["confirmed", "Holds", "✓"],
    ["weakening", "Weakening", "!"],
    ["broken", "Broken", "✕"],
    ["expired", "Expired", "◷"],
  ] as [ClaimStatus, string, string][])(
    "shows %s with a text label and icon",
    (status, label, icon) => {
      render(
        <NextIntlClientProvider locale="en" messages={en}>
          <ThesisCheck status={status} />
        </NextIntlClientProvider>,
      );
      expect(screen.getByText(label)).toBeVisible();
      expect(screen.getByText(icon)).toHaveAttribute("aria-hidden", "true");
    },
  );

  it("translates the confirmed state to Slovenian", () => {
    render(
      <NextIntlClientProvider locale="sl" messages={sl}>
        <ThesisCheck status="confirmed" />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Drži")).toBeVisible();
  });
});
