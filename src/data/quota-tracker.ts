export type QuotaKey = string;

/**
 * Daily quota guard per upstream vendor.
 * Limits are calendar-day UTC budgets (e.g. FMP=10, AlphaVantage=25).
 * Unknown keys are treated as unlimited (e.g. FRED 120/min is enforced
 * upstream, not here). Day rollover resets lazily on read.
 */
export class QuotaTracker {
  private static sharedDay: string | null = null;

  private readonly used = new Map<QuotaKey, { day: string; count: number }>();

  constructor(
    private readonly limits: Record<QuotaKey, number>,
    private readonly now: () => Date = () => new Date(),
  ) {}

  private dayKey(): string {
    return this.now().toISOString().slice(0, 10);
  }

  canConsume(key: QuotaKey): boolean {
    const limit = this.limits[key];
    if (limit === undefined) return true;
    const entry = this.used.get(key);
    const today = this.dayKey();
    const count = entry && entry.day === today ? entry.count : 0;
    return count < limit;
  }

  consume(key: QuotaKey): boolean {
    if (!this.canConsume(key)) return false;
    if (this.limits[key] === undefined) return true;
    const today = this.dayKey();
    const entry = this.used.get(key);
    const count = entry && entry.day === today ? entry.count : 0;
    this.used.set(key, { day: today, count: count + 1 });
    return true;
  }

  remaining(key: QuotaKey): number {
    const limit = this.limits[key];
    if (limit === undefined) return Number.POSITIVE_INFINITY;
    const entry = this.used.get(key);
    const today = this.dayKey();
    const count = entry && entry.day === today ? entry.count : 0;
    return Math.max(0, limit - count);
  }

  /** Test-only reset for module-level shared state, if ever added. */
  static resetAllForTests(): void {
    QuotaTracker.sharedDay = null;
  }
}
