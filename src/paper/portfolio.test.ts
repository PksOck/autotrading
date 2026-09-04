import { describe, expect, it } from "vitest";

import { parsePaperOrder } from "./orders";
import { PaperPortfolio } from "./portfolio";
import { checkOrder, type RiskState } from "./risk";

const limits = { maxPositionPct: 1, maxOrdersPerDay: 10, killSwitch: false };
const state: RiskState = { ordersToday: 0, idempotencyKeys: new Set() };

describe("paper domain", () => {
  it("rejects invalid orders", () => {
    expect(() => parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 0 })).toThrow();
    expect(() => parsePaperOrder({ symbol: "", side: "buy", quantity: 1 })).toThrow();
    expect(() =>
      parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 1, idempotencyKey: "" }),
    ).toThrow();
  });

  it("rejects duplicate idempotency keys", () => {
    const portfolio = new PaperPortfolio(10_000);
    const order = parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 10, idempotencyKey: "k1" });

    expect(portfolio.execute(order, 100).ok).toBe(true);
    expect(portfolio.execute(order, 100).ok).toBe(false);
  });

  it("refuses orders under kill switch, position cap, and daily cap", () => {
    const order = parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 1000 });
    expect(checkOrder({ ...state, killSwitch: true }, order, 10_000, 100, limits).ok).toBe(false);
    expect(
      checkOrder(state, order, 10_000, 100, { ...limits, maxPositionPct: 0.01 }).ok,
    ).toBe(false);
    expect(
      checkOrder({ ...state, ordersToday: 10 }, order, 10_000, 100, limits).ok,
    ).toBe(false);
  });

  it("fills market orders at bar close with costs and sequences audit", () => {
    const portfolio = new PaperPortfolio(10_000, { commissionBps: 0, slippageBps: 0 });
    const buy = parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 10 });
    const sell = parsePaperOrder({ symbol: "AMZN", side: "sell", quantity: 10 });

    expect(portfolio.execute(buy, 100).ok).toBe(true);
    expect(portfolio.equity(100)).toBeCloseTo(10_000, 6);
    expect(portfolio.execute(sell, 110).ok).toBe(true);
    expect(portfolio.equity(110)).toBeCloseTo(10_100, 6);

    const audit = portfolio.auditLog();
    expect(audit.map((entry) => entry.seq)).toEqual([1, 2, 3]);
    expect(audit[0].kind).toBe("portfolio-open");
  });

  it("fills limit buys only when touched", () => {
    const portfolio = new PaperPortfolio(10_000, { commissionBps: 0, slippageBps: 0 });
    const limit = parsePaperOrder({ symbol: "AMZN", side: "buy", quantity: 10, limitPrice: 90 });

    const resting = portfolio.execute(limit, 100, 95);
    expect(resting.ok).toBe(true);
    expect(resting.reasons).toEqual(["resting"]);
    expect(portfolio.positionShares("AMZN")).toBe(0);
  });
});
