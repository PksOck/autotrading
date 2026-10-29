"""IBKR portfolio: Flex sync into snapshots and the portfolio view (BL-022, BL-028)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, func, select, union_all
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from preza.domain.market import InstrumentKind
from preza.domain.metadata import DataMeta
from preza.domain.portfolio import CashIn, FlexStatement, PortfolioOut, PositionOut, SyncInfo
from preza.models import AccountSnapshot, Bar, CashBalance, Position, SyncRun, Trade
from preza.services.instruments import get_or_create
from preza.services.market_context import identity_status, market_context


async def store_statement(
    session: AsyncSession, statement: FlexStatement, source: str = "ibkr_flex"
) -> dict[str, int]:
    """Idempotent: re-running the same statement replaces the snapshot and skips known trades."""
    snapshots = {(p.account_id, p.report_date) for p in statement.positions}
    snapshots.update(
        (s.account_id, s.report_date) for s in statement.snapshots if s.positions_complete
    )
    for snapshot in statement.snapshots:
        key = (snapshot.account_id, snapshot.report_date)
        row = await session.get(AccountSnapshot, key)
        if row is None:
            row = AccountSnapshot(
                account_id=key[0],
                report_date=key[1],
                source=source,
                positions_complete=False,
                cash_complete=False,
            )
            session.add(row)
        row.positions_complete = row.positions_complete or snapshot.positions_complete
        row.cash_complete = row.cash_complete or snapshot.cash_complete
        row.fetched_at = datetime.now(UTC)
        if snapshot.cash_complete:
            await session.execute(
                delete(CashBalance).where(
                    CashBalance.account_id == key[0], CashBalance.report_date == key[1]
                )
            )
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
    counts = {
        "positions": len(statement.positions),
        "trades": new_trades,
        "cash": len(statement.cash),
    }
    if statement.dividends is not None:
        from preza.services.dividends import store_dividend_data

        counts.update(await store_dividend_data(session, statement.dividends))
    return counts


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


def latest_account_dates(model: type[Position] | type[CashBalance], section: str):  # type: ignore[no-untyped-def]
    declared = (
        AccountSnapshot.positions_complete
        if section == "positions"
        else AccountSnapshot.cash_complete
    )
    dates = union_all(
        select(model.account_id, model.report_date),
        select(AccountSnapshot.account_id, AccountSnapshot.report_date).where(declared),
    ).subquery()
    return (
        select(dates.c.account_id, func.max(dates.c.report_date).label("report_date"))
        .group_by(dates.c.account_id)
        .subquery()
    )


async def latest_positions(session: AsyncSession, account_id: str | None = None) -> list[Position]:
    dates = latest_account_dates(Position, "positions")
    query = (
        select(Position)
        .join(
            dates,
            (Position.account_id == dates.c.account_id)
            & (Position.report_date == dates.c.report_date),
        )
        .where(Position.quantity != 0)
    )
    if account_id:
        query = query.where(Position.account_id == account_id)
    return list(await session.scalars(query))


async def get_portfolio(
    session: AsyncSession, base_currency: str, account_id: str | None = None
) -> PortfolioOut:
    accounts = sorted(
        set(await session.scalars(select(Position.account_id)))
        | set(await session.scalars(select(AccountSnapshot.account_id)))
        | set(await session.scalars(select(CashBalance.account_id)))
    )
    positions = await latest_positions(session, account_id)
    cash_dates = latest_account_dates(CashBalance, "cash")
    cash_query = select(CashBalance).join(
        cash_dates,
        (CashBalance.account_id == cash_dates.c.account_id)
        & (CashBalance.report_date == cash_dates.c.report_date),
    )
    if account_id:
        cash_query = cash_query.where(CashBalance.account_id == account_id)
    cash_rows = list(await session.scalars(cash_query))
    snapshot_query = select(AccountSnapshot.report_date)
    if account_id:
        snapshot_query = snapshot_query.where(AccountSnapshot.account_id == account_id)
    all_dates = (
        [p.report_date for p in positions]
        + [c.report_date for c in cash_rows]
        + list(await session.scalars(snapshot_query))
    )
    latest = max(all_dates, default=None)
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
            accounts=accounts,
            selected_account=account_id,
        )

    values = {p.id: _value_in_base(p, base_currency) for p in positions}
    currencies = {p.currency for p in positions}
    if (
        None in values.values()
        and len(currencies) == 1
        and all(c.currency in currencies for c in cash_rows)
    ):
        # No FX rate from IBKR but a single currency: weights are still exact in that currency.
        base_currency = currencies.pop()
        values = {p.id: p.market_value for p in positions}
    known = [v for v in values.values() if v is not None]
    cash_base = sum((c.amount for c in cash_rows if c.currency == base_currency), Decimal(0))
    missing_fx = None in values.values() or any(c.currency != base_currency for c in cash_rows)
    total = None if missing_fx else sum(known, Decimal(0)) + cash_base
    contexts = await market_context(session, [p.instrument_id for p in positions])

    out = []
    for p in sorted(positions, key=lambda p: values[p.id] or Decimal(0), reverse=True):
        value = values[p.id]
        out.append(
            PositionOut(
                instrument_id=p.instrument_id,
                account_id=p.account_id,
                report_date=p.report_date,
                exchange=p.instrument.exchange,
                identity_status=identity_status(p.instrument),
                **contexts[p.instrument_id],
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
        accounts=accounts,
        selected_account=account_id,
        valuation_meta=DataMeta(
            source=positions[0].source if positions else "ibkr_flex",
            market_date=latest,
            availability="partial" if missing_fx else "available",
            reason_code="missing_fx" if missing_fx else None,
            basis="latest_snapshot_per_account",
        ),
    )
