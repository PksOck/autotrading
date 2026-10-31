import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import en from "@/messages/en.json";
import { PageHelp } from "./PageHelp";
import { Dialog } from "radix-ui";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
const messages = {
  ...en,
  pageHelp: {
    open: "Help for {page}",
    title: "About {page}",
    close: "Close help",
    actions: "What can I do?",
    data: "Where do the data come from?",
    limits: "What should I know?",
    links: "Related pages",
    pages: {
      signals: {
        purpose: "Saved signals and their current states.",
        actions: "Open a signal to inspect its evidence.",
        data: "Each signal has its own source and time.",
        limits: "A rumor needs official confirmation.",
      },
    },
  },
};

beforeEach(() => {
  window.history.replaceState({ keep: "router" }, "", "/signals?kind=entry");
  push.mockClear();
});

function show() {
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <PageHelp pageKey="signals" title="Signals" />
    </NextIntlClientProvider>,
  );
}

it("opens editorial help without requesting data and restores focus on Escape", async () => {
  const fetchSpy = vi.spyOn(globalThis, "fetch");
  show();
  const trigger = screen.getByRole("button", { name: "Help for Signals" });
  trigger.focus();
  fireEvent.click(trigger);
  const dialog = screen.getByRole("dialog", { name: "About Signals" });
  expect(dialog).toHaveTextContent("Each signal has its own source and time.");
  expect(dialog).toHaveTextContent("A rumor needs official confirmation.");
  expect(fetchSpy).not.toHaveBeenCalled();
  fireEvent.keyDown(dialog, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  await waitFor(() => expect(trigger).toHaveFocus());
  expect(window.location.pathname + window.location.search).toBe("/signals?kind=entry");
  expect(window.history.state).toMatchObject({ keep: "router" });
  fetchSpy.mockRestore();
});

it("Back closes help while preserving the current page filters", async () => {
  show();
  fireEvent.click(screen.getByRole("button", { name: "Help for Signals" }));
  expect(screen.getByRole("dialog")).toBeVisible();
  act(() => window.history.back());
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  expect(window.location.pathname + window.location.search).toBe("/signals?kind=entry");
});

it("Escape closes only help when opened inside a nonmodal preview", async () => {
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <Dialog.Root defaultOpen modal={false}>
        <Dialog.Content aria-describedby={undefined}>
          <Dialog.Title>Instrument preview</Dialog.Title>
          <PageHelp pageKey="signals" title="Signals" />
        </Dialog.Content>
      </Dialog.Root>
    </NextIntlClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Help for Signals" }));
  fireEvent.keyDown(screen.getByRole("dialog", { name: "About Signals" }), { key: "Escape" });
  await waitFor(() =>
    expect(screen.queryByRole("dialog", { name: "About Signals" })).not.toBeInTheDocument(),
  );
  expect(screen.getByRole("dialog", { name: "Instrument preview" })).toBeVisible();
});
