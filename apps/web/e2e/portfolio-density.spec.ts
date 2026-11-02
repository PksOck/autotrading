import { expect, test } from "@playwright/test";

for (const tab of ["positions", "watchlist"] as const) {
  test(`${tab}: compact trend sits beside identity and preserves accessible provenance`, async ({
    page,
  }, info) => {
    if (info.project.name === "desktop") await page.setViewportSize({ width: 1920, height: 1100 });
    await page.goto(tab === "positions" ? "/portfolio" : "/portfolio?tab=watchlist");
    const row = page.locator("tbody tr").first();
    await expect(row).toBeVisible();
    const cell = row.locator("td").first();
    await expect(cell.locator("svg").first()).toBeVisible();
    if (info.project.name !== "phone") {
      await expect
        .poll(async () => (await row.boundingBox())?.height ?? Number.POSITIVE_INFINITY)
        .toBeLessThanOrEqual(105);
    }
    const identity = (await cell.locator("a").first().boundingBox())!;
    const graph = (await cell.locator("svg").first().boundingBox())!;
    expect(graph.x).toBeGreaterThan(identity.x + identity.width);
    const period = (await cell.getByText(/\d{4}-\d{2}-\d{2} – \d{4}-\d{2}-\d{2}/).boundingBox())!;
    expect(period.y - graph.y - graph.height).toBeLessThanOrEqual(18);
    await expect(row.locator("td").nth(1)).toHaveCSS("vertical-align", "middle");
    await expect(cell.getByText(/\d{4}-\d{2}-\d{2} – \d{4}-\d{2}-\d{2}/)).toBeVisible();
    const disclosure = cell.locator("details");
    await disclosure.locator("summary").press("Enter");
    await expect(disclosure).toHaveAttribute("open", "");
    await expect(disclosure.getByText("demo", { exact: true })).toBeVisible();
    await expect(disclosure.getByText(/^\d{4}-\d{2}-\d{2}$/)).toBeVisible();
    await disclosure.locator("summary").press("Enter");
    await expect(disclosure).not.toHaveAttribute("open");
    const last = page
      .locator("table")
      .first()
      .locator("tbody tr")
      .last()
      .locator("td")
      .first()
      .locator("details");
    await last.locator("summary").press("Enter");
    await expect(last).toHaveAttribute("open", "");
    expect(
      await last.evaluate((node) => {
        const scroller = node.closest("[tabindex='0']")!;
        return (
          node.lastElementChild!.getBoundingClientRect().bottom -
          scroller.getBoundingClientRect().top -
          scroller.clientHeight
        );
      }),
    ).toBeLessThanOrEqual(1);
    await last.locator("summary").press("Enter");
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    if (process.env.SHOTS_DIR)
      await page.screenshot({ path: `${process.env.SHOTS_DIR}/${info.project.name}-${tab}.png` });
  });
}
