import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import messages from "@/messages/en.json";
import { useEmailPreferences, useSaveEmailPreferences } from "@/lib/api/email";
import { EmailSettings } from "./EmailSettings";

vi.mock("@/lib/api/email", () => ({
  useEmailPreferences: vi.fn(),
  useSaveEmailPreferences: vi.fn(),
}));

it("discloses email preferences, keeps unconfigured delivery off and saves multiple recipients without sending", () => {
  const mutate = vi.fn();
  vi.mocked(useEmailPreferences).mockReturnValue({
    data: { revision: 0, enabled: false, configured: false, recipients: [], kinds: ["signals"] },
    isPending: false,
    isError: false,
  } as unknown as ReturnType<typeof useEmailPreferences>);
  vi.mocked(useSaveEmailPreferences).mockReturnValue({
    mutate,
    isPending: false,
  } as unknown as ReturnType<typeof useSaveEmailPreferences>);
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <EmailSettings />
    </NextIntlClientProvider>,
  );
  const disclosure = screen.getByText("Email notifications").closest("details");
  expect(disclosure).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("Email notifications"));
  expect(screen.getByRole("checkbox", { name: "Enable email notifications" })).toBeDisabled();
  expect(mutate).not.toHaveBeenCalled();
  fireEvent.change(screen.getByRole("textbox", { name: /Recipients/ }), {
    target: { value: "one@example.org\ntwo@example.org" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save notifications" }));
  expect(mutate).toHaveBeenCalledWith({
    revision: 0,
    enabled: false,
    recipients: ["one@example.org", "two@example.org"],
    kinds: ["signals"],
  });
});
