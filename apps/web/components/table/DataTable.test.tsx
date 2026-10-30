import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import messages from "@/messages/en.json";
import { DataTable } from "./DataTable";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/portfolio",
  useRouter: () => ({ replace: vi.fn() }),
}));

it("always exposes standard after profiles and restores default columns and order", () => {
  localStorage.clear();
  localStorage.setItem(
    "preza.view.test.v1",
    JSON.stringify({
      version: 1,
      columns: ["symbol", "pe", "actions"],
      column_order: ["actions", "pe", "quantity", "symbol"],
    }),
  );
  render(
    <NextIntlClientProvider
      locale="en"
      messages={{ ...messages, table: { ...messages.table, standard: "Standard" } }}
    >
      <DataTable
        module="test"
        label="Positions"
        rows={[{}]}
        rowKey={() => "one"}
        columns={[
          { id: "symbol", label: "Identity", required: true, render: () => "ABC" },
          { id: "quantity", label: "Quantity", render: () => "10" },
          { id: "pe", label: "P/E", defaultVisible: false, render: () => "20" },
          { id: "actions", label: "Actions", required: true, render: () => "Open" },
        ]}
        profiles={[
          { label: "Valuation", columns: ["symbol", "pe", "actions"] },
          { label: "Dividends", columns: ["symbol", "actions"] },
        ]}
      />
    </NextIntlClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Valuation" }));
  expect(screen.queryByRole("columnheader", { name: "Quantity" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Standard" }));
  expect(screen.getAllByRole("columnheader").map((cell) => cell.textContent)).toEqual([
    "Identity",
    "Quantity",
    "Actions",
  ]);
  expect(screen.queryByRole("columnheader", { name: "P/E" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Dividends" }));
  expect(screen.queryByRole("columnheader", { name: "Quantity" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Standard" }));
  expect(screen.getAllByRole("columnheader").map((cell) => cell.textContent)).toEqual([
    "Identity",
    "Quantity",
    "Actions",
  ]);
  const buttons = screen.getAllByRole("button");
  expect(buttons.findIndex((b) => b.textContent === "Standard")).toBeGreaterThan(
    buttons.findIndex((b) => b.textContent === "Dividends"),
  );
});
