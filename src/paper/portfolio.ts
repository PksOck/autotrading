import { checkOrder, type RiskLimits, type RiskState } from "./risk";
import type { PaperOrder } from "./orders";

export interface AuditEntry {
  seq: number;
  timestamp: string;
  kind: string;
  detail: string;
}

export interface FillCosts {
  commissionBps?: number;
  slippageBps?: number;
}

/**
 * Cash-and-shares paper portfolio. Market orders fill at the given bar
 * close; limit buys fill only when low <= limit, limit sells only when
 * high >= limit. No shorting, no leverage. Every state change is audited.
 */
export class PaperPortfolio {
  private cash: number;
  private readonly shares = new Map<string, number>();
  private readonly keys = new Set<string>();
  private ordersToday = 0;
  private readonly log: AuditEntry[] = [];
  private seq = 0;

  constructor(
    initialCash = 10_000,
    private readonly costs: FillCosts = {},
    private readonly limits: RiskLimits = { maxPositionPct: 1, maxOrdersPerDay: 50, killSwitch: false },
  ) {
    this.cash = initialCash;
    this.record("portfolio-open", `Paper portfolio opened with ${initialCash} cash`);
  }

  private record(kind: string, detail: string): void {
    this.seq += 1;
    this.log.push({ seq: this.seq, timestamp: new Date().toISOString(), kind, detail });
  }

  private state(): RiskState {
    return { ordersToday: this.ordersToday, idempotencyKeys: this.keys };
  }

  equity(price: number): number {
    let value = this.cash;
    for (const qty of this.shares.values()) value += qty * price;
    return value;
  }

  positions(): Map<string, number> {
    return new Map(this.shares);
  }

  positionShares(symbol: string): number {
    return this.shares.get(symbol) ?? 0;
  }

  auditLog(): AuditEntry[] {
    return [...this.log];
  }

  execute(order: PaperOrder, close: number, low?: number, high?: number): { ok: boolean; reasons: string[] } {
    const check = checkOrder(this.state(), order, this.equity(close), close, this.limits);
    if (!check.ok) {
      this.record("order-rejected", `${order.side} ${order.quantity} ${order.symbol}: ${check.reasons.join("; ")}`);
      return check;
    }

    if (order.limitPrice !== null) {
      const touched =
        order.side === "buy" ? (low ?? close) <= order.limitPrice : (high ?? close) >= order.limitPrice;
      if (!touched) {
        this.record("order-resting", `Limit ${order.side} ${order.quantity} ${order.symbol} @ ${order.limitPrice} rests`);
        return { ok: true, reasons: ["resting"] };
      }
    }

    if (order.side === "sell" && (this.shares.get(order.symbol) ?? 0) < order.quantity) {
      const reasons = ["Insufficient open position (no shorting in v1)"];
      this.record("order-rejected", `Sell ${order.quantity} ${order.symbol}: ${reasons[0]}`);
      return { ok: false, reasons };
    }

    const commission = (this.costs.commissionBps ?? 5) / 10_000;
    const slippage = (this.costs.slippageBps ?? 5) / 10_000;
    if (order.side === "buy") {
      const execPrice = close * (1 + slippage);
      const notional = order.quantity * execPrice;
      const fee = notional * commission;
      if (notional + fee > this.cash) {
        const reasons = ["Insufficient cash"];
        this.record("order-rejected", `Buy ${order.quantity} ${order.symbol}: ${reasons[0]}`);
        return { ok: false, reasons };
      }
      this.cash -= notional + fee;
      this.shares.set(order.symbol, (this.shares.get(order.symbol) ?? 0) + order.quantity);
    } else {
      const execPrice = close * (1 - slippage);
      const proceeds = order.quantity * execPrice * (1 - commission);
      this.cash += proceeds;
      this.shares.set(order.symbol, (this.shares.get(order.symbol) ?? 0) - order.quantity);
    }

    this.keys.add(order.idempotencyKey);
    this.ordersToday += 1;
    this.record("fill", `${order.side} ${order.quantity} ${order.symbol} @ ${close}`);
    return { ok: true, reasons: [] };
  }
}
