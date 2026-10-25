import { render, screen, fireEvent } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { vi } from "vitest";
import en from "@/messages/en.json";
import { summary } from "@/test/thesis-fixtures";
import { useTheses } from "@/lib/api/hooks";
import { ThesisList } from "./ThesisList";

vi.mock("@/lib/api/hooks", () => ({ useTheses: vi.fn() }));
const useList = vi.mocked(useTheses);
const refetch = vi.fn();
function renderList() {
  return render(
    <NextIntlClientProvider locale="en" messages={en} timeZone="UTC">
      <ThesisList />
    </NextIntlClientProvider>,
  );
}
function result(value: object) {
  useList.mockReturnValue({
    isLoading: false,
    data: [],
    error: null,
    refetch,
    ...value,
  } as unknown as ReturnType<typeof useTheses>);
}

describe("ThesisList", () => {
  it("shows symbols, names, active versions, status counts, drafts and local update times", () => {
    result({ data: [{ ...summary, latest_draft_id: "draft" }] });
    renderList();
    expect(
      screen.getByRole("link", { name: /MSFT Microsoft Active version 1 Draft/ }),
    ).toHaveAttribute("href", `/theses/${summary.id}`);
    expect(screen.getByText("Open")).toBeVisible();
    expect(screen.getByText("1", { selector: "dd" })).toBeVisible();
    expect(document.querySelector("time")).toHaveAttribute("datetime", summary.updated_at);
    expect(document.querySelector("time")?.textContent).not.toBe("Loading theses");
    fireEvent.change(screen.getByLabelText("Filter by symbol"), { target: { value: "MSFT" } });
    expect(useList).toHaveBeenLastCalledWith("MSFT", 30, 0);
  });
  it("shows an empty state with an action", () => {
    result({});
    renderList();
    expect(screen.getByRole("link", { name: "Open analyses" })).toHaveAttribute(
      "href",
      "/analysis",
    );
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
  it("shows loading and recoverable errors", () => {
    result({ isLoading: true });
    const view = renderList();
    expect(screen.getByLabelText("Loading theses")).toHaveAttribute("aria-busy", "true");
    result({ error: new Error("offline") });
    view.rerender(
      <NextIntlClientProvider locale="en" messages={en}>
        <ThesisList />
      </NextIntlClientProvider>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("could not be loaded");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalled();
  });
  it("supports paged results and resets the page on filter changes", () => {
    result({ data: Array.from({ length: 30 }, (_, i) => ({ ...summary, id: String(i) })) });
    renderList();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(useList).toHaveBeenLastCalledWith(undefined, 30, 30);
    fireEvent.change(screen.getByLabelText("Filter by symbol"), { target: { value: "A" } });
    expect(useList).toHaveBeenLastCalledWith("A", 30, 0);
  });
});
