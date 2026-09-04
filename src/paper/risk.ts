import type { PaperOrder } from "./orders";

export interface RiskLimits {
  maxPositionPct: number;
  maxOrdersPerDay: number;
  killSwitch: boolean;
}

export interface RiskState {
  ordersToday: number;
  idempotencyKeys: Set<string>;
  killSwitch?: boolean;
}

export interface RiskCheck {
  ok: boolean;
  reasons: string[];
}

/** Pre-trade gate: kill switch, idempotency, position cap, daily cap. */
export function checkOrder(
  state: RiskState,
  order: PaperOrder,
  equity: number,
  price: number,
  limits: RiskLimits,
): RiskCheck {
  const reasons: string[] = [];
  if (limits.killSwitch || state.killSwitch) reasons.push("Kill switch is engaged");
  if (state.idempotencyKeys.has(order.idempotencyKey)) reasons.push("Duplicate idempotency key");
  const notional = order.quantity * price;
  if (equity > 0 && notional / equity > limits.maxPositionPct) {
    reasons.push(`Order notional exceeds ${limits.maxPositionPct * 100}% of equity`);
  }
  if (state.ordersToday >= limits.maxOrdersPerDay) reasons.push("Daily order limit reached");
  return { ok: reasons.length === 0, reasons };
}
