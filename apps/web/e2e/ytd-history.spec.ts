import { expect, test } from "@playwright/test";

test("portfolio shows numeric synthetic YTD with archived source evidence", async ({
  page,
  request,
}) => {
  const response = await request.get("/api/portfolio");
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  const rows = body.ytd_native.filter((row: { amount: unknown }) => row.amount !== null);
  // No completed current-year session exists on Jan1; this is an explicit valid unavailable case.
  const today = new Date();
  if (today.getUTCMonth() === 0 && today.getUTCDate() <= 3 && !rows.length) {
    expect(
      body.ytd_native.every((row: { reason: string }) => row.reason === "missing_year_history"),
    ).toBe(true);
    return;
  }
  expect(rows.length).toBeGreaterThan(0);
  for (const row of rows) {
    expect(row.sources).toEqual(["demo"]);
    expect(row.capture_ids.length).toBeGreaterThan(0);
    expect(row.adjustment_bases).toEqual(["demo-split-only-v1"]);
    expect(row.percent).not.toBeNull();
  }
  await page.goto("/portfolio");
  const summary = page.getByRole("region", { name: "Cenovni premik pozicij", exact: true });
  await summary.getByLabel("Obdobje premika", { exact: true }).selectOption("ytd");
  await expect(summary.getByText("Ločeno po izvornih valutah", { exact: true })).toBeVisible();
  await expect(summary.getByText(/▲|▼/).first()).toBeVisible();
});
