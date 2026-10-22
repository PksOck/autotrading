from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from preza.broker.flex import FlexClient, FlexError, parse_send_request, parse_statement
from preza.domain.market import InstrumentKind

XML = (Path(__file__).parent / "fixtures" / "flex_statement.xml").read_text()
SEND_OK = (
    "<FlexStatementResponse><Status>Success</Status>"
    "<ReferenceCode>123</ReferenceCode></FlexStatementResponse>"
)
IN_PROGRESS = (
    "<FlexStatementResponse><Status>Warn</Status><ErrorCode>1019</ErrorCode>"
    "<ErrorMessage>Statement generation in progress.</ErrorMessage></FlexStatementResponse>"
)
BAD_TOKEN = (
    "<FlexStatementResponse><Status>Fail</Status><ErrorCode>1015</ErrorCode>"
    "<ErrorMessage>Token is invalid.</ErrorMessage></FlexStatementResponse>"
)


def test_statement_positions_trades_cash() -> None:
    statement = parse_statement(XML)
    assert [p.symbol for p in statement.positions] == ["MSFT", "VWRA"]  # LOT row skipped
    vwra = statement.positions[1]
    assert (
        vwra.kind == InstrumentKind.ETF
        and vwra.exchange == "LSEETF"
        and vwra.isin == "IE00BK5BQT80"
    )
    assert statement.positions[0].unrealized_pnl == Decimal("1845")
    assert [t.ib_trade_id for t in statement.trades] == ["7001"]  # options ignored for now
    assert {c.currency: c.amount for c in statement.cash} == {
        "USD": Decimal("1800.55"),
        "EUR": Decimal("640"),
    }


def test_send_request_errors_carry_ibkr_code() -> None:
    assert parse_send_request(SEND_OK) == "123"
    with pytest.raises(FlexError) as info:
        parse_send_request(BAD_TOKEN)
    assert info.value.code == "1015"


async def test_client_retries_while_statement_is_generated() -> None:
    responses = [SEND_OK, IN_PROGRESS, IN_PROGRESS, XML]
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["t"] == "secret"
        return httpx.Response(200, text=responses.pop(0))

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    client = FlexClient(
        "secret", "42", httpx.AsyncClient(transport=httpx.MockTransport(handler)), sleep=fake_sleep
    )
    statement = await client.fetch(first_wait=1)
    assert len(statement.positions) == 2
    assert waits == [1, 2, 4]


async def test_client_gives_up_on_real_errors() -> None:
    responses = [SEND_OK, BAD_TOKEN]
    client = FlexClient(
        "t",
        "q",
        httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, text=responses.pop(0)))
        ),
        sleep=lambda s: _noop(),
    )
    with pytest.raises(FlexError):
        await client.fetch()


async def _noop() -> None:
    return None
