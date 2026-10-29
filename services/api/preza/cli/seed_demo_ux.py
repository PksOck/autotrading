"""Explicit synthetic UX scenarios; only invoked by the guarded isolated demo seed."""

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy import select

from preza.db import get_sessionmaker
from preza.domain.dividends import ProjectionBasis
from preza.domain.portfolio import FlexStatement, PositionIn
from preza.models import EtfProfile, Fundamentals, Instrument, Proposal, WatchlistItem
from preza.models_dividends import DividendProjectionBasis
from preza.services.dividends import import_dividend_statement
from preza.services.portfolio import store_statement


async def seed_ux_scenarios() -> None:
    today = date.today()
    now = datetime.now(UTC)
    async with get_sessionmaker()() as session:
        instruments = list(await session.scalars(select(Instrument)))
        for index, instrument in enumerate(instruments):
            if instrument.kind == "stock":
                fund = await session.get(Fundamentals, instrument.id)
                if fund is None:
                    continue
                fund.metrics = {
                    **fund.metrics,
                    "roe_pct": 22 + index,
                    "gross_margin_pct": 48,
                    "net_margin_pct": 21,
                    "revenue_growth_pct": 8,
                    "debt_to_equity": 0.4,
                    "dividend_yield_pct": 1.2 if index % 2 else 0,
                    "payout_ratio_pct": 30 if index % 2 else 0,
                }
                fund.metrics_meta = {
                    key: {
                        "source_field": f"synthetic.{key}",
                        "basis": "synthetic_TTM",
                        "period_end": None,
                    }
                    for key in fund.metrics
                }
                fund.fetched_at = now - timedelta(days=20) if instrument.symbol == "ORCL" else now
                fund.source = "demo"
            elif instrument.kind == "etf":
                profile = await session.get(EtfProfile, instrument.id)
                if profile is None:
                    profile = EtfProfile(instrument_id=instrument.id, as_of=today, source="demo")
                    session.add(profile)
                profile.ter = Decimal("0.0020")
                profile.ter_source, profile.ter_as_of = "demo:synthetic_issuer", today
                profile.index_name, profile.distribution = "Synthetic demo index", "acc"
                basis = ProjectionBasis(
                    symbol=instrument.symbol,
                    currency=instrument.currency or "EUR",
                    basis="accumulating_share_class",
                    source="demo:synthetic_issuer",
                    as_of=now,
                )
                row = await session.scalar(
                    select(DividendProjectionBasis).where(
                        DividendProjectionBasis.symbol == basis.symbol,
                        DividendProjectionBasis.currency == basis.currency,
                    )
                )
                if row is None:
                    session.add(
                        DividendProjectionBasis(
                            symbol=basis.symbol,
                            currency=basis.currency,
                            annual_per_share=None,
                            payload=basis.model_dump(mode="json"),
                        )
                    )
        msft = next((instrument for instrument in instruments if instrument.symbol == "MSFT"), None)
        if msft:
            await store_statement(
                session,
                FlexStatement(
                    positions=[
                        PositionIn(
                            account_id="DEMO-SECOND",
                            symbol="MSFT",
                            exchange=msft.exchange,
                            kind="stock",
                            currency="USD",
                            quantity=Decimal("0.125"),
                            market_price=Decimal("400"),
                            market_value=Decimal("50"),
                            fx_rate_to_base=Decimal("0.92"),
                            report_date=today - timedelta(days=1),
                        )
                    ],
                    trades=[],
                    cash=[],
                ),
                source="demo",
            )
            basis = ProjectionBasis(
                symbol="MSFT",
                currency="USD",
                annual_per_share=Decimal("3.00"),
                basis="indicated_annual",
                source="demo:synthetic_issuer",
                as_of=now,
            )
            row = await session.scalar(
                select(DividendProjectionBasis).where(
                    DividendProjectionBasis.symbol == "MSFT",
                    DividendProjectionBasis.currency == "USD",
                )
            )
            if row is None:
                session.add(
                    DividendProjectionBasis(
                        symbol="MSFT",
                        currency="USD",
                        annual_per_share=basis.annual_per_share,
                        payload=basis.model_dump(mode="json"),
                    )
                )
        unknown = await session.scalar(
            select(Instrument).where(Instrument.symbol == "SYNTH-UNKNOWN")
        )
        if unknown is None:
            unknown = Instrument(symbol="SYNTH-UNKNOWN", source="demo", kind="unknown")
            session.add(unknown)
            await session.flush()
            session.add(
                WatchlistItem(
                    instrument_id=unknown.id,
                    tier="reserve",
                    source="demo",
                    note="Synthetic missing identity scenario.",
                )
            )
        for status in ("done", "failed"):
            proposal_id = uuid.uuid5(uuid.NAMESPACE_URL, f"preza-demo-ux-proposal-{status}")
            proposal = await session.get(Proposal, proposal_id)
            if proposal is None:
                proposal = Proposal(
                    id=proposal_id,
                    symbols=["MSFT"],
                    hypothesis="Synthetic demo: verify evidence after an earnings move.",
                    direction="up",
                    horizon="months",
                    depth="quick",
                    save_to="once",
                    source_text="Demo fixture",
                    status=status,
                )
                session.add(proposal)
            proposal.verdict = (
                json.dumps(
                    {
                        "verdict": "supports",
                        "summary": "Synthetic review with explicit supporting evidence and risks.",
                        "direction": "up",
                        "horizon": "months",
                        "strength": 0.6,
                    }
                )
                if status == "done"
                else json.dumps({"summary": "llm_unavailable: synthetic invalid structured output"})
            )
            proposal.finished_at = now
        report = today.strftime("%Y%m%d")
        ex_date = (today - timedelta(days=5)).strftime("%Y%m%d")
        pay_date = (today + timedelta(days=14)).strftime("%Y%m%d")
        generated = now.strftime("%Y%m%d;%H%M%S")
        root = Element("FlexQueryResponse")
        statements = SubElement(root, "FlexStatements")
        statement = SubElement(
            statements,
            "FlexStatement",
            accountId="DEMO-SECOND",
            fromDate=f"{today.year}0101",
            toDate=report,
            whenGenerated=generated,
        )
        cash = SubElement(statement, "CashTransactions")
        for transaction_id, kind, amount in [
            ("DEMO-DIV-1", "Dividends", "25"),
            ("DEMO-TAX-1", "Withholding Tax", "-3.75"),
        ]:
            SubElement(
                cash,
                "CashTransaction",
                transactionID=transaction_id,
                type=kind,
                amount=amount,
                currency="USD",
                dateTime=f"{ex_date};120000",
                symbol="MSFT",
                conid="999001",
                actionID="DEMO-A1",
            )
        accruals = SubElement(statement, "OpenDividendAccruals")
        SubElement(
            accruals,
            "OpenDividendAccrual",
            conid="999001",
            symbol="MSFT",
            currency="USD",
            exDate=ex_date,
            payDate=pay_date,
            grossAmount="5",
            tax="0.75",
            netAmount="4.25",
            quantity="2",
            grossRate="2.5",
        )
        xml = tostring(root, encoding="unicode")
        await import_dividend_statement(session, xml)
        await session.commit()
    print(
        "demo UX: metric bases, stale/missing observations, fractional second account, "
        "safe proposal outcomes, synthetic dividend ledger"
    )
