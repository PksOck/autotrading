import { expect, test } from "@playwright/test";

for (const width of [1920, 2560]) {
  test(`analysis uses the available desktop width without a needless table scrollbar (${width})`, async ({
    page,
  }, info) => {
    test.skip(info.project.name === "phone", "desktop width contract");
    await page.setViewportSize({ width, height: 1440 });
    await page.goto("/analysis");
    await expect(page.getByTestId("analysis-table")).toBeVisible();
    const main = await page.locator("main").boundingBox();
    expect(main!.width).toBeGreaterThan(width - 300);
    const scrolling = page.getByTestId("analysis-table").locator("[tabindex='0']");
    const overflow = await scrolling.evaluate((node) => node.scrollWidth - node.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}
