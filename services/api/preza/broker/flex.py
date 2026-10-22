"""IBKR Flex Web Service: read-only portfolio, trades and cash (BL-022).

Flow: SendRequest(token, query) → reference code → GetStatement(reference) → XML.
While IBKR is still generating the statement it answers with error 1019; we retry.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import Element

import httpx
from defusedxml import ElementTree

from preza.domain.market import InstrumentKind
from preza.domain.portfolio import CashIn, FlexStatement, PositionIn, TradeIn

BASE_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
IN_PROGRESS_CODES = {"1019"}  # "Statement generation in progress. Please try again shortly."


class FlexError(Exception):
    def __init__(self, code: str | None, message: str):
        super().__init__(f"{code}: {message}" if code else message)
        self.code = code


def _dec(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _date(value: str | None) -> date:
    if not value:
        raise ValueError("missing date")
    value = value.split(";")[0].split(",")[0]
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"bad date {value}")


def _kind(asset_category: str | None, sub_category: str | None) -> InstrumentKind:
    if (sub_category or "").upper() == "ETF":
        return InstrumentKind.ETF
    if (asset_category or "").upper() == "STK":
        return InstrumentKind.STOCK
    return InstrumentKind.UNKNOWN


def _response_status(root: Element) -> tuple[str | None, str | None, str | None]:
    status = root.findtext("Status")
    code = root.findtext("ErrorCode")
    message = root.findtext("ErrorMessage")
    return status, code, message


def parse_send_request(xml: str) -> str:
    root = ElementTree.fromstring(xml)
    status, code, message = _response_status(root)
    if status != "Success":
        raise FlexError(code, message or "SendRequest failed")
    reference = root.findtext("ReferenceCode")
    if not reference:
        raise FlexError(None, "no reference code")
    return reference


def parse_statement(xml: str) -> FlexStatement:
    """Parses OpenPositions, Trades and CashReport from one or more FlexStatement elements."""
    root = ElementTree.fromstring(xml)
    if root.tag == "FlexStatementResponse":
        _, code, message = _response_status(root)
        raise FlexError(code, message or "statement not ready")

    positions: list[PositionIn] = []
    trades: list[TradeIn] = []
    cash: list[CashIn] = []
    for statement in root.iter("FlexStatement"):
        account = statement.get("accountId", "")
        statement_date = _date(statement.get("toDate") or statement.get("whenGenerated"))

        for p in statement.iter("OpenPosition"):
            if (p.get("levelOfDetail") or "SUMMARY").upper() not in ("SUMMARY", ""):
                continue  # skip LOT rows when the query includes lot detail
            quantity = _dec(p.get("position"))
            if quantity is None:
                continue
            positions.append(
                PositionIn(
                    account_id=p.get("accountId") or account,
                    symbol=p.get("symbol", "").strip(),
                    con_id=int(p.get("conid", "")) if p.get("conid") else None,
                    name=p.get("description"),
                    kind=_kind(p.get("assetCategory"), p.get("subCategory")),
                    exchange=p.get("listingExchange") or None,
                    currency=p.get("currency", "USD"),
                    isin=p.get("isin") or None,
                    quantity=quantity,
                    avg_cost=_dec(p.get("costBasisPrice")),
                    market_price=_dec(p.get("markPrice")),
                    market_value=_dec(p.get("positionValue")),
                    unrealized_pnl=_dec(p.get("fifoPnlUnrealized")),
                    fx_rate_to_base=_dec(p.get("fxRateToBase")),
                    report_date=_date(p.get("reportDate"))
                    if p.get("reportDate")
                    else statement_date,
                )
            )

        for t in statement.iter("Trade"):
            if not t.get("tradeID") or (t.get("assetCategory") or "STK") not in ("STK", "ETF"):
                continue
            quantity = _dec(t.get("quantity"))
            price = _dec(t.get("tradePrice"))
            if quantity is None or price is None:
                continue
            trades.append(
                TradeIn(
                    account_id=t.get("accountId") or account,
                    ib_trade_id=t.get("tradeID", ""),
                    symbol=t.get("symbol", "").strip(),
                    con_id=int(t.get("conid", "")) if t.get("conid") else None,
                    trade_date=_date(t.get("tradeDate")),
                    side=(t.get("buySell") or ("BUY" if quantity > 0 else "SELL")).upper(),
                    quantity=abs(quantity),
                    price=price,
                    currency=t.get("currency", "USD"),
                    commission=_dec(t.get("ibCommission")),
                )
            )

        for c in statement.iter("CashReportCurrency"):
            currency = c.get("currency")
            amount = _dec(c.get("endingCash"))
            if not currency or currency == "BASE_SUMMARY" or amount is None:
                continue
            cash.append(
                CashIn(
                    account_id=c.get("accountId") or account,
                    currency=currency,
                    amount=amount,
                    report_date=statement_date,
                )
            )

    return FlexStatement(positions=positions, trades=trades, cash=cash)


class FlexClient:
    def __init__(
        self,
        token: str,
        query_id: str,
        client: httpx.AsyncClient | None = None,
        base_url: str = BASE_URL,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self._token = token
        self._query_id = query_id
        self._client = client or httpx.AsyncClient(timeout=30, headers={"User-Agent": "Preza/0.1"})
        self._base_url = base_url
        self._sleep = sleep

    async def fetch(self, attempts: int = 8, first_wait: float = 5.0) -> FlexStatement:
        response = await self._client.get(
            f"{self._base_url}/SendRequest",
            params={"t": self._token, "q": self._query_id, "v": "3"},
        )
        response.raise_for_status()
        reference = parse_send_request(response.text)

        wait = first_wait
        for _ in range(attempts):
            await self._sleep(wait)
            response = await self._client.get(
                f"{self._base_url}/GetStatement",
                params={"t": self._token, "q": reference, "v": "3"},
            )
            response.raise_for_status()
            try:
                return parse_statement(response.text)
            except FlexError as exc:
                if exc.code not in IN_PROGRESS_CODES:
                    raise
            wait = min(wait * 2, 60)
        raise FlexError("1019", "statement still in progress after retries")
