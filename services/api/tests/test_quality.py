from preza.domain.quality import quality_parts, quality_score


def test_strong_and_weak_companies() -> None:
    strong = {
        "roe_pct": 32.0,
        "net_margin_pct": 24.0,
        "revenue_growth_pct": 15.0,
        "debt_to_equity": 0.3,
    }
    assert quality_score(strong) == 1.0
    weak = {
        "roe_pct": -4.0,
        "net_margin_pct": -10.0,
        "revenue_growth_pct": -8.0,
        "debt_to_equity": 3.5,
    }
    assert quality_score(weak) == -1.0
    middling = {"roe_pct": 12.0, "net_margin_pct": 3.0}
    assert quality_score(middling) == 0.25


def test_too_little_data_and_negative_equity() -> None:
    assert quality_score({"roe_pct": 25.0}) is None
    assert quality_score({"roe_pct": None, "net_margin_pct": "n/a"}) is None
    assert quality_parts({"debt_to_equity": -0.4})["debt_to_equity"] == -1.0


def test_debt_is_not_scored_for_banks() -> None:
    bank = {"roe_pct": 12.0, "net_margin_pct": 25.0, "debt_to_equity": 6.0}
    assert "debt_to_equity" not in quality_parts(bank, "Financials")
    assert quality_parts(bank)["debt_to_equity"] == -1.0
