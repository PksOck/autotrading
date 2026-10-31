import { expect, test } from "@playwright/test";

for (const tab of ["positions", "watchlist"] as const) {
  test(`${tab}: compact trend sits beside identity and preserves accessible provenance`, async ({
    page,
  }, info) => {
    await page.goto(tab === "positions" ? "/portfolio" : "/portfolio?tab=watchlist");
    const row = page.locator("tbody tr").first();
    await expect(row).toBeVisible();
    const cell = row.locator("td").first();
    await expect(cell.locator("svg")).toBeVisible();
    if (info.project.name !== "phone") {
      await expect
        .poll(async () => (await row.boundingBox())?.height ?? Number.POSITIVE_INFINITY)
        .toBeLessThanOrEqual(130);
    }
    const identity = (await cell.locator("a").first().boundingBox())!;
    const graph = (await cell.locator("svg").boundingBox())!;
    expect(graph.x).toBeGreaterThan(identity.x + identity.width);
    await expect(cell.getByText(/\d{4}-\d{2}-\d{2} – \d{4}-\d{2}-\d{2}/)).toBeVisible();
    const disclosure = cell.locator("details");
    await disclosure.locator("summary").press("Enter");
    await expect(disclosure).toHaveAttribute("open", "");
    await expect(disclosure.getByText("demo", { exact: true })).toBeVisible();
    await expect(disclosure.getByText(/^\d{4}-\d{2}-\d{2}/)).toBeVisible();
    await disclosure.locator("summary").press("Enter");
    await expect(disclosure).not.toHaveAttribute("open");
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
}
