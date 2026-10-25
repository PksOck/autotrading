import { expect, test } from "@playwright/test";
import { asOf, claim, review, reviewProposal, revision, thesis } from "../test/thesis-fixtures";
import type { ClaimReviewProposalOut, ThesisOut } from "../lib/api/types";

function shellResponse(url: string) {
  const path = new URL(url).pathname;
  if (path === "/api/watchlist") return [];
  if (path === "/api/portfolio")
    return {
      as_of: asOf,
      base_currency: "EUR",
      total_value: null,
      positions: [],
      cash: [],
      last_sync: null,
    };
  if (path === "/api/signals") return [];
  return { services: [], as_of: asOf };
}

test("review proposals: actual status stays unchanged until explicit acceptance; dismissal needs a reason", async ({
  page,
  baseURL,
}) => {
  let detail: ThesisOut = thesis;
  let proposals: ClaimReviewProposalOut[] = [reviewProposal];
  let accepts = 0;
  let dismissals = 0;
  await page.context().addCookies([{ name: "locale", value: "en", url: baseURL! }]);
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith("/reviews")) await route.fulfill({ json: [review] });
    else if (path.endsWith("/review-proposals")) await route.fulfill({ json: proposals });
    else if (path.endsWith("/accept")) {
      accepts += 1;
      expect(request.postDataJSON()).toEqual({
        expected_status: "open",
        expected_last_event_id: null,
      });
      detail = {
        ...thesis,
        revisions: [{ ...revision, claims: [{ ...claim, status: "broken" }] }],
      };
      proposals = [
        {
          ...reviewProposal,
          id: "dismiss-me",
          suggested_status: null,
          assessment: "insufficient",
          evidence: [],
        },
      ];
      await route.fulfill({ json: { ...reviewProposal, state: "accepted" } });
    } else if (path.endsWith("/dismiss")) {
      dismissals += 1;
      expect(request.postDataJSON()).toEqual({ reason: "Await audited accounts" });
      proposals = [];
      await route.fulfill({ json: { ...reviewProposal, state: "dismissed" } });
    } else if (path === `/api/theses/${thesis.id}`) await route.fulfill({ json: detail });
    else await route.fulfill({ json: shellResponse(request.url()) });
  });
  await page.goto(`/theses/${thesis.id}`);
  const proposal = page.getByRole("region", { name: "Review proposal", exact: true });
  await expect(proposal.getByText("Possible thesis break", { exact: true })).toBeVisible();
  await expect(page.locator('[data-status="open"]')).toBeVisible();
  await expect(proposal.locator("[data-status]")).toHaveCount(0);
  await expect(proposal.getByText("Rumour, unconfirmed", { exact: true })).toBeVisible();
  await expect(proposal.getByRole("link")).toHaveAttribute("href", "https://www.sec.gov/filing/1");
  await expect(proposal.getByText("Omitted evidence items: 2", { exact: true })).toBeVisible();
  expect(accepts).toBe(0);
  await proposal.getByRole("button", { name: "Accept proposal", exact: true }).click();
  expect(accepts).toBe(0);
  await expect(page.locator('[data-status="open"]')).toBeVisible();
  await proposal.getByRole("button", { name: "Confirm acceptance", exact: true }).click();
  await expect(page.locator('[data-status="broken"]')).toBeVisible();
  await expect(
    proposal.getByText("Insufficient evidence to suggest a status.", { exact: true }),
  ).toBeVisible();
  await expect(proposal.getByRole("button", { name: "Accept proposal", exact: true })).toHaveCount(
    0,
  );
  const dismiss = proposal.getByRole("button", { name: "Dismiss proposal", exact: true });
  await expect(dismiss).toBeDisabled();
  await proposal.getByLabel("Reason for dismissal", { exact: true }).fill("   ");
  await expect(dismiss).toBeDisabled();
  expect(dismissals).toBe(0);
  await proposal.getByLabel("Reason for dismissal", { exact: true }).fill("Await audited accounts");
  await dismiss.click();
  await expect(proposal).toHaveCount(0);
  expect(accepts).toBe(1);
  expect(dismissals).toBe(1);
});

test("review conflicts offer a friendly refresh and stale revisions cannot be accepted", async ({
  page,
  baseURL,
}) => {
  let conflicted = false;
  await page.context().addCookies([{ name: "locale", value: "en", url: baseURL! }]);
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/reviews")) await route.fulfill({ json: [review] });
    else if (path.endsWith("/review-proposals")) await route.fulfill({ json: [reviewProposal] });
    else if (path.endsWith("/accept")) {
      conflicted = true;
      await route.fulfill({ status: 409, json: { detail: "claim_revision_raw_conflict" } });
    } else if (path === `/api/theses/${thesis.id}`)
      await route.fulfill({
        json: {
          ...thesis,
          revisions: [{ ...revision, status: conflicted ? "superseded" : "active" }],
        },
      });
    else await route.fulfill({ json: shellResponse(route.request().url()) });
  });
  await page.goto(`/theses/${thesis.id}`);
  const proposal = page.getByRole("region", { name: "Review proposal", exact: true });
  await proposal.getByRole("button", { name: "Accept proposal", exact: true }).click();
  await proposal.getByRole("button", { name: "Confirm acceptance", exact: true }).click();
  await expect(proposal.getByRole("alert")).toContainText("The claim or proposal changed");
  await expect(page.getByText(/claim_revision_raw_conflict|409/)).toHaveCount(0);
  await proposal.getByRole("button", { name: "Refresh reviews", exact: true }).click();
  await expect(proposal.getByText(/This review is outdated/)).toBeVisible();
  await expect(proposal.getByRole("button", { name: "Accept proposal", exact: true })).toHaveCount(
    0,
  );
});
