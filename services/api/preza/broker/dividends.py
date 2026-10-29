"""Strict supported Flex XML contract, exercised with synthetic fixtures only.

IBKR field semantics: see ADR-0020. Unsupported/missing fields produce visible
coverage gaps. An absent section never proves zero dividends. No XML is archived.
"""

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import Element

from defusedxml import ElementTree

from preza.domain.dividends import Accrual, CashEvent, DividendStatement, ImportCoverage

SECTIONS = {
    "CashTransactions": "CashTransaction",
    "OpenDividendAccruals": "OpenDividendAccrual",
    "ChangeInDividendAccruals": "ChangeInDividendAccrual",
    "FinancialInstrumentInformation": "FinancialInstrumentInformation",
}
CASH_TYPES = {
    "dividends": "dividend",
    "payment in lieu of dividends": "payment_in_lieu",
    "payment in lieu": "payment_in_lieu",
    "withholding tax": "withholding",
}


def _day(value: str | None) -> date:
    if not value:
        raise ValueError("missing_date")
    raw = value.split(";")[0]
    return datetime.strptime(raw, "%Y%m%d" if "-" not in raw else "%Y-%m-%d").date()


def _decimal(value: str | None) -> Decimal | None:
    if value is None or value == "":
        return None
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("invalid_decimal")
    return result


def _optional_day(value: str | None) -> date | None:
    return _day(value) if value else None


def _common(row: Element, account: str, as_of: datetime) -> dict[str, object]:
    currency = row.get("currency", "").strip()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("missing_currency")
    return {
        "account_id": row.get("accountId") or account,
        "symbol": row.get("symbol") or None,
        "con_id": int(row.get("conid", "")) if row.get("conid") else None,
        "action_id": row.get("actionID") or None,
        "currency": currency.upper(),
        "fx_rate_to_base": _decimal(row.get("fxRateToBase")),
        "as_of": as_of,
    }


def parse_dividend_statement(xml: str) -> DividendStatement:
    root = ElementTree.fromstring(xml)
    result = DividendStatement()
    statements = list(root.iter("FlexStatement"))
    if not statements:
        raise ValueError("missing_statement")
    for statement in statements:
        account = statement.get("accountId", "").strip()
        if not account:
            raise ValueError("missing_account")
        end = _day(statement.get("toDate"))
        start = _day(statement.get("fromDate") or statement.get("toDate"))
        if start > end:
            raise ValueError("invalid_statement_period")
        # The reporting guide does not establish the timezone of whenGenerated.
        # Preserve a daily reporting boundary, never pretend a naive wall time is UTC.
        as_of = datetime.combine(end, datetime.min.time(), UTC)
        generated = statement.get("whenGenerated")
        if generated and ";" in generated:
            nominal = datetime.strptime(generated, "%Y%m%d;%H%M%S")
            snapshot_version = nominal.strftime("%Y%m%d%H%M%S")
        else:
            snapshot_version = (_day(generated) if generated else end).strftime("%Y%m%d") + "000000"
        for section_name, row_name in SECTIONS.items():
            section = statement.find(section_name)
            coverage = ImportCoverage(
                account_id=account,
                section=section_name,
                from_date=start,
                to_date=end,
                status="missing" if section is None else "complete",
                as_of=as_of,
                snapshot_version=snapshot_version,
            )
            result.coverage.append(coverage)
            if section is None:
                continue
            if section_name == "FinancialInstrumentInformation":
                # Instrument metadata is optional: it never supplies a guessed currency or DPS.
                if len(section):
                    coverage.status = "partial"
                    coverage.gaps.append("instrument_metadata_not_ingested")
                continue
            for row in section:
                if row.tag != row_name:
                    coverage.status = "partial"
                    coverage.gaps.append("unsupported_row_type")
                    continue
                try:
                    if section_name == "CashTransactions":
                        kind = CASH_TYPES.get(row.get("type", "").strip().lower())
                        if kind is None:
                            # Deposits/interest are outside this dividend ledger.
                            if any(
                                word in row.get("type", "").lower()
                                for word in ("dividend", "withholding", "lieu")
                            ):
                                raise ValueError("unsupported_cash_type")
                            continue
                        transaction_id = row.get("transactionID")
                        if not transaction_id:
                            raise ValueError("missing_transaction_id")
                        amount = _decimal(row.get("amount"))
                        if amount is None:
                            raise ValueError("missing_amount")
                        result.cash_events.append(
                            CashEvent.model_validate(
                                {
                                    **_common(row, account, as_of),
                                    "transaction_id": transaction_id,
                                    "kind": kind,
                                    "amount": amount,
                                    "booking_date": _day(
                                        row.get("dateTime") or row.get("reportDate")
                                    ),
                                    "settlement_date": _optional_day(row.get("settleDate")),
                                    "fx_basis": "statement_booking"
                                    if row.get("fxRateToBase")
                                    else None,
                                }
                            )
                        )
                    else:
                        common = _common(row, account, as_of)
                        if not common["con_id"] and not common["symbol"]:
                            raise ValueError("missing_instrument")
                        ex_date = _day(row.get("exDate"))
                        pay_date = _optional_day(row.get("payDate"))
                        action = row.get("actionID")
                        identity = action or (
                            f"{common['con_id'] or common['symbol']}:{ex_date}:{pay_date}:"
                            f"{common['currency']}"
                        )
                        status = (
                            "open"
                            if section_name == "OpenDividendAccruals"
                            else ("change:" + (row.get("code") or "unknown"))
                        )
                        result.accruals.append(
                            Accrual.model_validate(
                                {
                                    **common,
                                    "natural_key": (
                                        f"{section_name}:{identity}:{status}:{snapshot_version}"
                                    ),
                                    "snapshot_version": snapshot_version,
                                    "ex_date": ex_date,
                                    "pay_date": pay_date,
                                    "quantity": _decimal(row.get("quantity")),
                                    "gross_rate": _decimal(row.get("grossRate")),
                                    "gross_amount": _decimal(row.get("grossAmount")),
                                    "tax": _decimal(row.get("tax")),
                                    "net_amount": _decimal(row.get("netAmount")),
                                    "status": status,
                                }
                            )
                        )
                except (ValueError, InvalidOperation) as exc:
                    coverage.status = "partial"
                    # Stable codes only, never XML values or customer descriptions.
                    code = (
                        str(exc)
                        if str(exc)
                        in {
                            "missing_transaction_id",
                            "missing_amount",
                            "missing_currency",
                            "missing_instrument",
                            "unsupported_cash_type",
                            "invalid_decimal",
                        }
                        else "invalid_row"
                    )
                    if code not in coverage.gaps:
                        coverage.gaps.append(code)
            coverage.row_keys = [
                item.natural_key
                for item in result.accruals
                if item.account_id == account
                and item.snapshot_version == snapshot_version
                and item.natural_key.startswith(section_name + ":")
            ]
    return result
