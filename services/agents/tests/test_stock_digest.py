"""Stock digests are bounded, sourced and deterministic, without network."""

from datetime import timedelta
from decimal import Decimal

import pytest

from preza_agents.deep_research.vendor_local import RUMOR_MARK
from preza_agents.stock_analyst.digest import (
    MAX_MACRO_ITEMS,
    evidence_register,
    fundamentals_digest,
    market_digest,
    news_digest,
    statement_lines,
)
from tests.conftest import make_snapshot


@pytest.mark.parametrize("locale", ["sl", "en"])
def test_digests(locale: str) -> None:
    snapshot = make_snapshot()
    market = market_digest(snapshot, locale)
    assert market.numbers["close"] == snapshot.bars[-2].close
    assert {
        "return_1w_pct",
        "return_1m_pct",
        "return_3m_pct",
        "return_6m_pct",
        "return_1y_pct",
        "sma50",
        "sma200",
        "rsi14",
        "atr_pct",
        "high_52w",
        "low_52w",
        "avg_volume_20d",
        "avg_volume_90d",
    } <= market.numbers.keys()
    news = news_digest(snapshot, locale)
    assert RUMOR_MARK in news.text
    assert news.numbers["form4_count"] == 1
    assert "CFO buys" not in news.text
    assert "Fed holds rates" in news.text
    assert news.text.index("wins a large order") < news.text.index("may be acquired")
    for digest in (market, fundamentals_digest(snapshot, locale), news):
        assert len(digest.text) <= 3000
        assert digest.source and digest.as_of.isoformat() in digest.text


def test_fundamentals_and_statements() -> None:
    snapshot = make_snapshot()
    snapshot.fundamentals = {"pe": 20.0, "roe_pct": 22.0, "net_margin_pct": 16.0, "unknown": 9999}
    snapshot.fundamentals_history = {
        "pe": [(snapshot.as_of - timedelta(days=i), float(i + 10)) for i in range(1, 12)]
    }
    digest = fundamentals_digest(
        snapshot,
        statements={"income": ",2022,2023,2024,2025,2026\nRevenue,60,70,80,90,100"},
    )
    assert digest.numbers["pe"] == 20
    assert "quality_score" in digest.numbers and "pe_percentile" in digest.numbers
    assert "unknown" not in digest.text and "sec_edgar" in digest.text
    assert "2022" not in digest.text
    snapshot.fundamentals = None
    assert "No fundamentals" in fundamentals_digest(snapshot).text


def test_statement_csv_keeps_aligned_latest_periods() -> None:
    rows = statement_lines(
        {
            "income": (
                "# Income statement, USD millions\n# Filed on or before analysis date\n\n"
                ",2024-03-31,2024-06-30 (6 months),2024-09-30 (9 months),"
                "2024-12-31,2025-03-31,2025-06-30 (6 months)\n"
                "Revenue,10,20,30,40,50,60\nDiluted EPS (USD/shares),1,2,3,4,5,6\n"
                "Net Income,,,,,,unavailable (not tagged by this filer)"
            )
        }
    )
    assert rows[1] == " | 2024-09-30 (9 months) | 2024-12-31 | 2025-03-31 | 2025-06-30 (6 months)"
    assert rows[2] == "Revenue | 30 | 40 | 50 | 60"
    assert rows[3] == "Diluted EPS (USD/shares) | 3 | 4 | 5 | 6"
    assert "unavailable" in rows[4] and "millions" in rows[0]


def test_extreme_news_and_deduplication() -> None:
    snapshot = make_snapshot()
    duplicate = snapshot.news[0].model_copy(update={"title": "ASML WINS a large order!!!"})
    snapshot.news += [duplicate]
    assert news_digest(snapshot).text.lower().count("wins a large order") == 1
    snapshot.news *= 100
    for item in snapshot.news:
        item.summary = "long summary " * 1000
    assert len(news_digest(snapshot).text) <= 3000
    assert RUMOR_MARK in news_digest(snapshot).text


def test_empty_future_and_zero_data() -> None:
    snapshot = make_snapshot(days=0)
    snapshot.fundamentals_as_of = snapshot.as_of + timedelta(days=1)
    assert not market_digest(snapshot).numbers
    assert not fundamentals_digest(snapshot).numbers
    snapshot = make_snapshot(days=3)
    for bar in snapshot.bars:
        bar.close = Decimal(0)
    assert "return_1w_pct" not in market_digest(snapshot).numbers


def test_evidence_ids_stable_and_trimming_keeps_complete_items() -> None:
    snapshot = make_snapshot()
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    full = evidence_register(snapshot, digests, max_chars=100_000)
    snapshot.news.reverse()
    snapshot.global_news.reverse()
    assert evidence_register(snapshot, digests, max_chars=100_000) == full
    trimmed = evidence_register(snapshot, digests, max_chars=900)
    assert len(trimmed.render()) <= 900 and trimmed.items
    originals = {item.id: item for item in full.items}
    assert all(originals[item.id] == item for item in trimmed.items)
    assert trimmed.render().splitlines() == [item.render() for item in trimmed.items]
    assert len(originals) == len(full.items)
    assert any(item.numbers.get("close") == snapshot.bars[-2].close for item in full.items)
    assert all(item.source and item.as_of for item in full.items)


def test_rumor_flag_and_mark_both_make_evidence_unconfirmed() -> None:
    snapshot = make_snapshot()
    snapshot.global_news[0].title += f" {RUMOR_MARK}"
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    register = evidence_register(snapshot, digests)
    rumor = next(item for item in register.items if "may be acquired" in item.text)
    marked = next(item for item in register.items if "Fed holds rates" in item.text)
    official = next(item for item in register.items if "wins a large order" in item.text)
    assert not rumor.confirmed and not marked.confirmed and official.confirmed
    assert register.items.index(official) < register.items.index(rumor)
    assert rumor.url == "https://example.com/b"


def test_no_mid_sentence_trimming_or_oversized_fragment() -> None:
    snapshot = make_snapshot()
    snapshot.news[0].summary = "A complete sentence. " + "unfinished " * 1000
    snapshot.news[1].summary = "unsplittable " * 1000
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    register = evidence_register(snapshot, digests)
    official = next(item for item in register.items if "wins a large order" in item.text)
    assert official.text.endswith("A complete sentence.")
    assert "unfinished" not in register.render() and "unsplittable" not in register.render()
    assert "unfinished" not in digests[2].text


def test_duplicate_prefers_official_confirmation_and_recent_items() -> None:
    snapshot = make_snapshot()
    old_rumor = snapshot.news[0].model_copy(
        update={
            "is_rumor": True,
            "source": "reddit",
            "kind": "social",
            "published_at": snapshot.news[0].published_at - timedelta(days=1),
        }
    )
    snapshot.news.append(old_rumor)
    register = evidence_register(
        snapshot, [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    )
    order = [item for item in register.items if "wins a large order" in item.text]
    assert len(order) == 1 and order[0].confirmed and order[0].official
    assert order[0].source == "press_release"
    # Structured instrument facts come first, official news before other news, macro last.
    position = register.items.index(order[0])
    kinds = [item.kind for item in register.items]
    assert all(
        kind in ("market", "fundamental", "insider") for kind in kinds[: kinds.index("news")]
    )
    assert all(not item.official for item in register.items[position + 1 :])
    assert kinds[-1] == "macro"


def test_macro_news_is_capped_never_official_and_last() -> None:
    snapshot = make_snapshot()
    template = snapshot.global_news[0]
    snapshot.global_news = [
        template.model_copy(
            update={"title": f"Unrelated issuer {i} reports results", "kind": "press_release"}
        )
        for i in range(12)
    ]
    register = evidence_register(
        snapshot, [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    )
    macro = [item for item in register.items if item.kind == "macro"]
    assert len(macro) == MAX_MACRO_ITEMS
    assert not any(item.official for item in macro)
    assert all(item.id.startswith("G") for item in macro)
    assert any(item.kind == "market" for item in register.items)


def test_statement_fact_keeps_units_and_periods_when_other_items_are_trimmed() -> None:
    snapshot = make_snapshot()
    statements = {"income": ",2025,2026\nRevenue,1234.5,1500"}
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    register = evidence_register(snapshot, digests, statements, max_chars=1800)
    item = next(item for item in register.items if item.kind == "statement")
    assert "USD millions" in item.text and "2025" in item.text and "2026" in item.text
    assert "Revenue | 1234.5 | 1500" in item.text
    assert set(item.numbers.values()) == {Decimal("1234.5"), Decimal(1500)}


def test_statement_percent_units_do_not_allow_plain_claims() -> None:
    from preza_agents.stock_analyst.analyst import unverified_numbers

    snapshot = make_snapshot(days=0)
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    register = evidence_register(
        snapshot, digests, {"income": ",2025,2026\nRevenue growth (%),21.5,22.5"}
    )
    item = next(item for item in register.items if item.kind == "statement")
    assert set(item.numbers.values()) == {Decimal("21.5"), Decimal("22.5")}
    assert all(key.endswith("_pct") for key in item.numbers)
    assert not unverified_numbers(["Growth 22.5 %"], register)
    assert unverified_numbers(["Price 22.5 USD"], register) == ["22.5"]


def test_news_numbers_exclude_metadata_and_metric_names() -> None:
    from preza_agents.stock_analyst.analyst import unverified_numbers
    from preza_agents.stock_analyst.numbers import fact_unit

    snapshot = make_snapshot(days=0)
    snapshot.news = [
        snapshot.news[0].model_copy(
            update={
                "title": "Revenue 4321.5 USD and growth 17 %.",
                "summary": (
                    "As of 2026-10-20; SMA50; return_3m; ID N88; accession 0000320193-26-000123; "
                    "https://example.com/654321. ID: 876543; CIK 543210. Over 3 months, next Q3."
                ),
            }
        )
    ]
    snapshot.global_news = []
    register = evidence_register(
        snapshot, [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    )
    item = next(item for item in register.items if item.kind == "news")
    assert set(item.numbers.values()) == {Decimal("4321.5"), Decimal(17)}
    assert {fact_unit(k) for k in item.numbers} == {"plain", "percent"}
    assert not unverified_numbers(["Revenue 4.321,5 USD, up 17 odstotkov"], register)
    assert unverified_numbers(["Price 2026 and return 50 %"], register) == ["2026", "50"]


def test_register_prioritises_intraday_recency_and_handles_many_sources() -> None:
    snapshot = make_snapshot()
    newer = snapshot.news[0].model_copy(
        update={
            "title": "Later official update",
            "published_at": snapshot.news[0].published_at + timedelta(hours=2),
        }
    )
    snapshot.news += [newer] + [
        snapshot.news[0].model_copy(
            update={
                "title": f"Different complete headline {i}.",
                "source": f"source_{i}_" + "x" * 80,
                "kind": "news",
            }
        )
        for i in range(100)
    ]
    digests = [market_digest(snapshot), fundamentals_digest(snapshot), news_digest(snapshot)]
    register = evidence_register(snapshot, digests)
    newer_item = next(item for item in register.items if item.text == "Later official update")
    older_item = next(item for item in register.items if "wins a large order" in item.text)
    assert register.items.index(newer_item) < register.items.index(older_item)
    assert newer_item.as_of == newer.published_at
    assert len(digests[2].text) <= 3000 and len(register.render()) <= 6500
