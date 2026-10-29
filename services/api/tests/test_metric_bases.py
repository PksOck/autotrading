from datetime import date

from preza.fundamentals.finnhub import parse_metric


def test_fallbacks_preserve_distinct_dividend_and_payout_bases() -> None:
    result = parse_metric(
        "TEST",
        {"metric": {"currentDividendYieldTTM": 0, "payoutRatioAnnual": 35, "peTTM": 20}},
        date(2026, 10, 29),
    )
    assert result.metrics["dividend_yield_pct"] == 0
    assert result.metadata["dividend_yield_pct"] == {
        "source_field": "currentDividendYieldTTM",
        "basis": "TTM",
        "period_end": None,
    }
    assert result.metadata["payout_ratio_pct"]["basis"] == "annual"
    assert result.metadata["pe"]["period_end"] is None
