import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from preza.ingest.base import SourceUnavailableError
from preza.ingest.edgar import EdgarSource, parse_company_tickers, parse_edgar_atom
from preza.ingest.finnhub import FinnhubSource, parse_company_news
from preza.ingest.rss import DEFAULT_FEEDS, RssSource, extract_tickers, parse_rss

FIXTURES = Path(__file__).parent.parent / "fixtures" / "news"
LONG_AGO = datetime(2020, 1, 1, tzinfo=UTC)


def read(name: str) -> str:
    return (FIXTURES / name).read_text()


def client_returning(
    status: int, body: str | bytes = b"", seen: list[httpx.Request] | None = None
) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- RSS / Atom ---------------------------------------------------------------------------


def test_rss_parses_items_and_skips_incomplete() -> None:
    items = parse_rss(read("press_release.rss"), "rss:test", "press_release")
    assert [i.external_id for i in items] == ["pr-20261021-0001", "pr-20261020-0042"]
    first, second = items
    assert first.published_at == datetime(2026, 10, 21, 12, 30, tzinfo=UTC)
    assert second.published_at == datetime(2026, 10, 20, 12, 0, tzinfo=UTC)  # -0400 → UTC
    assert first.kind == "press_release" and first.source == "rss:test"
    assert second.title == "Northwind Mining Files Technical Report & Updates Outlook"


def test_rss_strips_html_and_collapses_whitespace() -> None:
    first, second = parse_rss(read("press_release.rss"), "rss:test", "press_release")
    assert first.summary is not None
    assert "<" not in first.summary and "  " not in first.summary and "\n" not in first.summary
    assert "reported record revenue." in first.summary
    assert second.summary == "Northwind Mining (NYSE American: NWM) said & confirmed guidance."


def test_rss_extracts_tickers_deduped_uppercase() -> None:
    first, second = parse_rss(read("press_release.rss"), "rss:test", "press_release")
    assert first.symbols == ["CTSO", "FBK"]
    assert second.symbols == ["NWM"]


def test_extract_tickers_patterns() -> None:
    text = "(NASDAQ: MSFT) (NYSE:V) NYSE American: XYZ Nasdaq: ABC and BRK.B via (NYSE: BRK.B)"
    assert extract_tickers(text) == ["MSFT", "V", "XYZ", "ABC", "BRK.B"]
    assert extract_tickers("The NASDAQ: is closed, nyse: lower") == []


def test_summary_is_capped() -> None:
    xml = (
        "<rss><channel><item><title>T</title><link>https://x/1</link>"
        f"<pubDate>Wed, 21 Oct 2026 12:30:00 GMT</pubDate><description>{'a ' * 2000}</description>"
        "</item></channel></rss>"
    )
    (item,) = parse_rss(xml, "rss:test", "news")
    assert item.summary is not None and len(item.summary) == 1000


def test_atom_parses_entries() -> None:
    posted, older = parse_rss(read("blog.atom"), "rss:blog", "news")
    assert posted.url == "https://blog.example.com/adatum-launch"
    assert posted.external_id == "urn:example:blog:101"
    assert posted.published_at == datetime(2026, 10, 21, 9, 15, tzinfo=UTC)
    assert posted.summary == "Adatum (NYSE: ADT) unveiled a new line. Shipping next month."
    assert posted.symbols == ["ADT"]
    assert older.published_at == datetime(2026, 10, 1, 7, 0, tzinfo=UTC)
    assert older.summary == "Nothing to see."
    assert older.kind == "news"


def test_rss_rejects_garbage_and_entities() -> None:
    with pytest.raises(ValueError):
        parse_rss("<rss><unclosed>", "x", "news")
    bomb = '<?xml version="1.0"?><!DOCTYPE a [<!ENTITY e "x">]><rss><channel>&e;</channel></rss>'
    with pytest.raises(ValueError):
        parse_rss(bomb, "x", "news")


def test_default_feeds_shape() -> None:
    assert len(DEFAULT_FEEDS) == 3
    assert all(url.startswith("https://") for _, url in DEFAULT_FEEDS)


async def test_rss_source_filters_by_since() -> None:
    source = RssSource(
        "test",
        "https://feed.example.com/x.rss",
        client=client_returning(200, read("press_release.rss")),
    )
    assert source.name == "rss:test"
    everything = await source.fetch(LONG_AGO)
    assert len(everything) == 2
    recent = await source.fetch(datetime(2026, 10, 21, tzinfo=UTC))
    assert [i.external_id for i in recent] == ["pr-20261021-0001"]
    naive = await source.fetch(datetime(2026, 10, 21))
    assert len(naive) == 1


async def test_rss_source_errors() -> None:
    with pytest.raises(SourceUnavailableError):
        await RssSource("t", "https://x", client=client_returning(503)).fetch(LONG_AGO)
    with pytest.raises(SourceUnavailableError, match="quota"):
        await RssSource("t", "https://x", client=client_returning(429)).fetch(LONG_AGO)
    with pytest.raises(SourceUnavailableError):
        await RssSource("t", "https://x", client=client_returning(200, "<html")).fetch(LONG_AGO)


async def test_rss_source_network_error() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client = httpx.AsyncClient(transport=httpx.MockTransport(boom))
    with pytest.raises(SourceUnavailableError):
        await RssSource("t", "https://x", client=client).fetch(LONG_AGO)


# --- Finnhub ------------------------------------------------------------------------------


def test_finnhub_parse_company_news() -> None:
    payload = json.loads(read("finnhub_company_news.json"))
    first, second, third = parse_company_news(payload, "CTSO")
    assert first.source == "finnhub" and first.external_id == "900001"
    assert first.published_at == datetime.fromtimestamp(1792576800, tz=UTC)
    assert first.symbols == ["CTSO"] and first.summary is not None
    assert second.symbols == ["FBK", "CTSO"] and second.summary is None
    assert third.symbols == ["CTSO"]  # fallback
    assert parse_company_news(payload, None)[2].symbols == []


def test_finnhub_skips_incomplete_rows() -> None:
    rows = [{"headline": "", "url": "u", "datetime": 1}, {"headline": "h", "url": "u"}]
    assert parse_company_news(rows, None) == []


async def test_finnhub_fetch_per_symbol_and_general() -> None:
    company = read("finnhub_company_news.json")
    general = json.dumps(
        [
            {
                "id": 1,
                "headline": "Markets open",
                "url": "https://n/1",
                "datetime": 1792576000,
                "related": "",
            }
        ]
    )
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/company-news"):
            if request.url.params["symbol"] == "BAD":
                return httpx.Response(422, content=b"{}")
            return httpx.Response(200, content=company)
        return httpx.Response(200, content=general)

    source = FinnhubSource(
        "KEY",
        ["CTSO", "BAD", "FBK"],
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    items = await source.fetch(datetime(2026, 10, 19, tzinfo=UTC))
    assert [r.url.params.get("symbol") for r in seen] == ["CTSO", "BAD", "FBK", None]
    assert seen[0].url.params["token"] == "KEY"
    assert seen[0].url.params["from"] == "2026-10-19"
    assert seen[-1].url.params["category"] == "general"
    by_id = {i.external_id: i for i in items}
    assert set(by_id) == {"900001", "900002", "1"}  # 900003 is older than since
    assert by_id["900001"].symbols == ["CTSO"]  # deduped across symbols
    assert by_id["900002"].symbols == ["FBK", "CTSO"]


@pytest.mark.parametrize(
    ("status", "message"), [(429, "quota"), (401, "unauthorized"), (503, "503")]
)
async def test_finnhub_errors(status: int, message: str) -> None:
    source = FinnhubSource("SECRET", ["MSFT"], client=client_returning(status, b"[]"))
    with pytest.raises(SourceUnavailableError, match=message) as info:
        await source.fetch(LONG_AGO)
    assert "SECRET" not in str(info.value)


async def test_finnhub_network_error_hides_token() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(boom))
    with pytest.raises(SourceUnavailableError) as info:
        await FinnhubSource("SECRET", ["MSFT"], client=client).fetch(LONG_AGO)
    assert "SECRET" not in str(info.value)


# --- EDGAR --------------------------------------------------------------------------------


def test_edgar_parse_atom() -> None:
    filing, insider = parse_edgar_atom(read("edgar_current.atom"))
    assert filing.source == "edgar" and filing.kind == "filing" and filing.filing_form == "8-K"
    assert filing.external_id == "0000950170-26-000123"
    assert filing.title == "8-K · CONTOSO CORP"
    assert filing.summary is not None and filing.summary.startswith("CIK 0000123456")
    assert "Item 2.02" in filing.summary and "<" not in filing.summary
    assert filing.symbols == []
    assert filing.published_at == datetime(2026, 10, 21, 20, 32, 11, tzinfo=UTC)
    assert insider.filing_form == "4" and insider.title == "4 · DOE JANE"
    assert insider.summary == "CIK 0001999888"


def test_edgar_company_tickers() -> None:
    mapping = parse_company_tickers(json.loads(read("company_tickers.json")))
    assert mapping == {"0000123456": "CTSO", "0000789019": "MSFT", "0001045810": "NVDA"}
    assert parse_company_tickers({"0": {"cik_str": "bad", "ticker": "X"}, "1": 5}) == {}


async def test_edgar_fetch_sends_user_agent_and_maps_ciks() -> None:
    seen: list[httpx.Request] = []
    source = EdgarSource(
        "Preza test@example.com",
        cik_to_ticker=parse_company_tickers(json.loads(read("company_tickers.json"))),
        client=client_returning(200, read("edgar_current.atom"), seen),
    )
    items = await source.fetch(LONG_AGO)
    assert [r.url.params["type"] for r in seen] == ["8-K", "4", "SC 13D"]
    assert all(r.headers["User-Agent"] == "Preza test@example.com" for r in seen)
    assert seen[0].url.params["output"] == "atom"
    assert len(items) == 2  # same entries on every form feed are deduped by url
    assert items[0].symbols == ["CTSO"]
    assert items[1].symbols == []  # reporting person CIK is not in the ticker file


async def test_edgar_since_and_no_mapping() -> None:
    source = EdgarSource(
        "UA", forms=("8-K",), client=client_returning(200, read("edgar_current.atom"))
    )
    items = await source.fetch(datetime(2026, 10, 21, 20, 0, tzinfo=UTC))
    assert [i.filing_form for i in items] == ["8-K"]
    assert items[0].symbols == []


@pytest.mark.parametrize(("status", "message"), [(403, "forbidden"), (429, "quota"), (503, "503")])
async def test_edgar_errors(status: int, message: str) -> None:
    with pytest.raises(SourceUnavailableError, match=message):
        await EdgarSource("UA", client=client_returning(status)).fetch(LONG_AGO)
