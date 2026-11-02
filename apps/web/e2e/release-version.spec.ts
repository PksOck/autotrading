import { expect, test } from "@playwright/test";
import manifest from "../package.json" with { type: "json" };

const { version } = manifest;

for (const locale of ["sl", "en"]) {
  test(`public login exposes the deployed release and supporting pages (${locale})`, async ({
    page,
    context,
    baseURL,
  }) => {
    await context.addCookies([{ name: "locale", value: locale, url: baseURL! }]);
    await page.goto("/login");
    const release = page.getByRole("link", {
      name: new RegExp(`${locale === "sl" ? "Različica" : "Version"} ${version}`),
    });
    await expect(release).toBeVisible();
    await expect(release).toHaveAttribute(
      "href",
      `https://github.com/PksOck/autotrading/releases/tag/v${version}`,
    );
    await expect(page.locator("header")).toHaveCount(0);
    for (const path of ["about", "privacy", "terms", "security"]) {
      const response = await page.request.get(`/${path}`);
      expect(response.ok()).toBeTruthy();
    }
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth - innerWidth),
    ).toBeLessThanOrEqual(1);
  });
}
