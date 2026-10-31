import { act, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { renderToString } from "react-dom/server";
import { LocalDate } from "./LocalDate";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

const element = () => (
  <NextIntlClientProvider locale="en" messages={{ pageHelp: { today: "Today" } }}>
    <LocalDate />
  </NextIntlClientProvider>
);

it("does not embed a server-local date in the initial HTML", () => {
  vi.setSystemTime(new Date(2026, 9, 30, 10, 0));
  expect(renderToString(element())).not.toContain("2026-10-30");
});

it("updates the browser-local calendar date at midnight and removes timers on unmount", () => {
  vi.setSystemTime(new Date(2026, 9, 30, 23, 59, 59));
  const { unmount } = render(element());
  expect(screen.getByLabelText("Today")).toHaveAttribute("datetime", "2026-10-30");
  act(() => vi.advanceTimersByTime(1500));
  expect(screen.getByLabelText("Today")).toHaveAttribute("datetime", "2026-10-31");
  unmount();
  expect(vi.getTimerCount()).toBe(0);
});

it.each([2, 9])("uses calendar midnight across the local DST boundary in month %s", (month) => {
  const day = month === 2 ? 29 : 25;
  const start = new Date(2026, month, day, 0, 30);
  const beforeMidnight = new Date(2026, month, day, 23, 59, 59);
  vi.setSystemTime(start);
  const { unmount } = render(element());
  const expected = `2026-${String(month + 1).padStart(2, "0")}-${day}`;
  act(() => vi.advanceTimersByTime(beforeMidnight.getTime() - start.getTime()));
  expect(screen.getByLabelText("Today")).toHaveAttribute("datetime", expected);
  act(() => vi.advanceTimersByTime(1500));
  expect(screen.getByLabelText("Today")).not.toHaveAttribute("datetime", expected);
  unmount();
});
