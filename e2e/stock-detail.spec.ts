import { expect, test, type Locator, type Page } from "@playwright/test";

const minimumNormalTextContrast = 4.5;

function parseRgb(color: string): [number, number, number] {
  const channels = color.match(/[\d.]+/g)?.slice(0, 3).map(Number);
  if (!channels || channels.length !== 3) throw new Error(`Unsupported computed color: ${color}`);
  return channels as [number, number, number];
}

function relativeLuminance(color: string): number {
  const channels = parseRgb(color).map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });

  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

async function expectNormalTextContrast(locator: Locator, label: string) {
  await expect(locator).toBeVisible();
  const colors = await locator.evaluate((element) => {
    let ancestor: Element | null = element;

    while (ancestor) {
      const background = getComputedStyle(ancestor).backgroundColor;
      const components = background.match(/[\d.]+/g)?.map(Number) ?? [];
      const alpha = components.length === 4 ? components[3] : 1;
      if (alpha === 1) {
        return { background, foreground: getComputedStyle(element).color };
      }
      ancestor = ancestor.parentElement;
    }

    throw new Error("No opaque rendered background found");
  });
  const ratio = contrastRatio(colors.foreground, colors.background);

  expect.soft(
    ratio,
    `${label} uses ${colors.foreground} on ${colors.background} (${ratio.toFixed(2)}:1)`,
  ).toBeGreaterThanOrEqual(minimumNormalTextContrast);
}

async function expectChartAndFreshnessContrast(page: Page, freshnessText: string, theme: string) {
  await expectNormalTextContrast(page.locator(".chart-provenance"), `${theme} chart provenance`);
  await expectNormalTextContrast(page.locator(".chart-volume"), `${theme} chart volume`);
  await expectNormalTextContrast(page.getByText(freshnessText, { exact: true }), `${theme} freshness`);
}

test("legacy stock URLs redirect to the canonical instrument URL", async ({ page }) => {
  await page.goto("/stocks/AMZN");
  await expect(page).toHaveURL(/\/instruments\/AMZN$/);
});

test("instrument charts expose ranges, summaries, theme support, and responsive layout", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-23T20:05:00Z") });
  await page.goto("/instruments/AMZN");
  await expect(page.getByText("$217.35", { exact: true })).toBeVisible();
  await expect(page.getByText("AMZN · NASDAQ · USD", { exact: true })).toBeVisible();
  await expect(page.getByText("Fixture current", { exact: true })).toBeVisible();

  const provenance = page.getByRole("complementary", { name: "Data provenance" });
  await expect(provenance.getByText("Source: Illustrative fixture data", { exact: true })).toBeVisible();
  await expect(provenance.locator('time[datetime="2026-07-22T20:05:00Z"]')).toHaveText(
    "7/22/2026, 8:05:00 PM UTC",
  );

  await expect(page.getByRole("heading", { name: "Price history" })).toBeVisible();
  await expect(page.getByText(/1Y · .* observations:.*Change:.*\(.*%\)/)).toBeVisible();
  await expect(page.getByText("Volume shown below price")).toBeVisible();

  const chartFrame = page.getByTestId("price-volume-chart-frame");
  await expect(chartFrame).toBeVisible();
  await expect(chartFrame).toHaveAttribute("data-range", "1Y");
  await expect(chartFrame).toHaveAttribute("data-volume", "shown");

  const annualFinancials = page.getByRole("heading", { name: "Annual financials" }).locator("xpath=ancestor::section");
  await expect(annualFinancials.getByText("USD millions", { exact: true })).toBeVisible();
  await expect(annualFinancials.getByRole("img", { name: "Revenue trend in USD millions" })).toBeVisible();

  for (const range of ["1M", "6M", "1Y", "5Y", "MAX"]) {
    const button = page.getByRole("button", { name: range, exact: true });
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(chartFrame).toBeVisible();
    await expect(chartFrame).toHaveAttribute("data-range", range);
    await expect(page.getByText(new RegExp(`^${range} · .* observations:.*Change:.*\\(.*%\\)\\.$`))).toBeVisible();
  }

  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.getByRole("button", { name: "Use light theme" })).toBeVisible();

  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
});

test("freshness is derived from the browser clock rather than build time", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-24T20:05:00.001Z") });

  await page.goto("/instruments/AMZN");

  await expect(page.getByText("Stale fixture data", { exact: true })).toBeVisible();
});

test("key normal text meets WCAG AA contrast in light and dark themes", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-23T20:05:00Z") });
  await page.goto("/instruments/AMZN");

  await expectChartAndFreshnessContrast(page, "Fixture current", "light");
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expectChartAndFreshnessContrast(page, "Fixture current", "dark");

  await page.clock.setFixedTime(new Date("2026-07-24T20:05:00.001Z"));
  await page.reload();
  await expectChartAndFreshnessContrast(page, "Stale fixture data", "light");
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expectChartAndFreshnessContrast(page, "Stale fixture data", "dark");
});
