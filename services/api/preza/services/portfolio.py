"""IBKR portfolio: Flex sync into snapshots and the portfolio view (BL-022, BL-028)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.domain.portfolio import CashIn, FlexStatement, PortfolioOut, PositionOut, SyncInfo
from preza.models import Bar, CashBalance, Position, SyncRun, Trade
from preza.services.instruments import get_or_create


async def store_statement(
    session: AsyncSession, statement: FlexStatement, source: str = "ibkr_flex"
) -> dict[str, int]:
    """Idempotent: re-running the same statement replaces the snapshot and skips known trades."""
    snapshots = {(p.account_id, p.report_date) for p in statement.positions}
    for account_id, report_date in snapshots:
        await session.execute(
            delete(Position).where(
                Position.account_id == account_id, Position.report_date == report_date
            )
        )

    for p in statement.positions:
        instrument = await get_or_create(
            session,
            symbol=p.symbol,
            source=source,
            exchange=p.exchange,
            con_id=p.con_id,
            name=p.name,
            kind=p.kind,
            currency=p.currency,
            isin=p.isin,
        )
        session.add(
            Position(
                account_id=p.account_id,
                instrument_id=instrument.id,
                report_date=p.report_date,
                quantity=p.quantity,
                avg_cost=p.avg_cost,
                market_price=p.market_price,
                market_value=p.market_value,
                unrealized_pnl=p.unrealized_pnl,
                fx_rate_to_base=p.fx_rate_to_base,
                currency=p.currency,
                source=source,
            )
        )

    new_trades = 0
    for t in statement.trades:
        instrument = await get_or_create(
            session, symbol=t.symbol, source=source, con_id=t.con_id, currency=t.currency
        )
        result = await session.execute(
            insert(Trade)
            .values(
                account_id=t.account_id,
                ib_trade_id=t.ib_trade_id,
                instrument_id=instrument.id,
                trade_date=t.trade_date,
                side=t.side,
                quantity=t.quantity,
                price=t.price,
                currency=t.currency,
                commission=t.commission,
                source=source,
            )
            .on_conflict_do_nothing(index_elements=["ib_trade_id"])
        )
        new_trades += result.rowcount or 0  # type: ignore[attr-defined]

    for c in statement.cash:
        stmt = insert(CashBalance).values(
            account_id=c.account_id,
            currency=c.currency,
            report_date=c.report_date,
            amount=c.amount,
            source=source,
        )
        await session.execute(
            stmt.on_conflict_do_update(
                index_elements=["account_id", "currency", "report_date"],
                set_={"amount": stmt.excluded.amount},
            )
        )
    await session.flush()
    return {
        "positions": len(statement.positions),
        "trades": new_trades,
        "cash": len(statement.cash),
    }


async def record_sync(session: AsyncSession, kind: str, status: str, detail: str | None) -> None:
    now = datetime.now(UTC)
    session.add(SyncRun(kind=kind, status=status, started_at=now, finished_at=now, detail=detail))


def _value_in_base(position: Position, base: str) -> Decimal | None:
    if position.market_value is None:
        return None
    if position.currency == base:
        return position.market_value
    if position.fx_rate_to_base is not None:
        return position.market_value * position.fx_rate_to_base
    return None


async def daily_change(session: AsyncSession, instrument_id: int) -> Decimal | None:
    closes = list(
        await session.scalars(
            select(Bar.close)
            .where(Bar.instrument_id == instrument_id)
            .order_by(Bar.day.desc())
            .limit(2)
        )
    )
    if len(closes) < 2 or not closes[1]:
        return None
    return (closes[0] / closes[1] - 1) * 100


async def get_portfolio(session: AsyncSession, base_currency: str) -> PortfolioOut:
    latest = await session.scalar(select(func.max(Position.report_date)))
    last_sync_row = await session.scalar(
        select(SyncRun).where(SyncRun.kind == "flex").order_by(SyncRun.started_at.desc()).limit(1)
    )
    last_sync = (
        SyncInfo(
            kind=last_sync_row.kind,
            status=last_sync_row.status,
            finished_at=last_sync_row.finished_at,
            detail=last_sync_row.detail,
        )
        if last_sync_row
        else None
    )
    if latest is None:
        return PortfolioOut(
            as_of=None,
            base_currency=base_currency,
            total_value=None,
            positions=[],
            cash=[],
            last_sync=last_sync,
            source=None,
        )

    positions = list(await session.scalars(select(Position).where(Position.report_date == latest)))
    cash_rows = list(
        await session.scalars(select(CashBalance).where(CashBalance.report_date == latest))
    )
    values = {p.id: _value_in_base(p, base_currency) for p in positions}
    currencies = {p.currency for p in positions}
    if None in values.values() and len(currencies) == 1:
        # No FX rate from IBKR but a single currency: weights are still exact in that currency.
        base_currency = currencies.pop()
        values = {p.id: p.market_value for p in positions}
    known = [v for v in values.values() if v is not None]
    cash_base = sum((c.amount for c in cash_rows if c.currency == base_currency), Decimal(0))
    total = sum(known, Decimal(0)) + cash_base if known else None

    out = []
    for p in sorted(positions, key=lambda p: values[p.id] or Decimal(0), reverse=True):
        value = values[p.id]
        out.append(
            PositionOut(
                symbol=p.instrument.symbol,
                name=p.instrument.name,
                kind=InstrumentKind(p.instrument.kind),
                currency=p.currency,
                quantity=p.quantity,
                avg_cost=p.avg_cost,
                market_price=p.market_price,
                market_value=p.market_value,
                unrealized_pnl=p.unrealized_pnl,
                weight_pct=(value / total * 100) if value is not None and total else None,
                change_pct=await daily_change(session, p.instrument_id),
            )
        )
    return PortfolioOut(
        as_of=latest,
        base_currency=base_currency,
        total_value=total,
        positions=out,
        cash=[
            CashIn(
                account_id=c.account_id,
                currency=c.currency,
                amount=c.amount,
                report_date=c.report_date,
            )
            for c in cash_rows
        ],
        last_sync=last_sync,
        source=positions[0].source if positions else None,
    )
