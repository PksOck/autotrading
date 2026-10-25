from datetime import date
from decimal import Decimal

import pytest

from preza.universe import loader


def test_curated_indices() -> None:
    rows = loader.read_ucits()
    assert len(rows) == 10
    assert all(row.get("index") for row in rows)
    assert loader.ucits_facts("VWRA", "LSEETF").index == "FTSE All-World"
    assert loader.ucits_facts("other", None, isin="IE00BK5BQT80").index == "FTSE All-World"
    assert loader.ucits_facts("VWRA", "wrong") is None
    assert loader.ucits_facts("VWRA", "LSEETF", isin="unknown") is None


@pytest.mark.parametrize(
    "ter,source,as_of",
    [
        (0.0022, "kid:vanguard", "2026-10-25"),
        ("0", "kid:vanguard", "2026-10-25"),
        ("0.05", "kid:vanguard", "2026-10-25"),
        ("-0.001", "kid:vanguard", "2026-10-25"),
        ("NaN", "kid:vanguard", "2026-10-25"),
        ("Infinity", "kid:vanguard", "2026-10-25"),
        ("bad", "kid:vanguard", "2026-10-25"),
        ("0.0022", None, "2026-10-25"),
        ("0.0022", "", "2026-10-25"),
        ("0.0022", "kid:vanguard", None),
        ("0.0022", "kid:vanguard", "bad"),
    ],
)
def test_invalid_cost_keeps_index(monkeypatch, caplog, ter, source, as_of) -> None:
    monkeypatch.setattr(
        loader,
        "read_ucits",
        lambda: [
            {
                "symbol": "X",
                "exchange": "LSEETF",
                "index": "Index",
                "ter": ter,
                "ter_source": source,
                "ter_as_of": as_of,
            }
        ],
    )
    facts = loader.ucits_facts("X", "LSEETF")
    assert facts == loader.UcitsFacts(index="Index")
    assert "Ignoring curated TER" in caplog.text


@pytest.mark.parametrize("as_of", ["2026-10-25", date(2026, 10, 25)])
def test_valid_cost(monkeypatch, as_of) -> None:
    monkeypatch.setattr(
        loader,
        "read_ucits",
        lambda: [
            {
                "isin": "ISIN",
                "index": "Index",
                "ter": "0.0022",
                "ter_source": "kid:vanguard",
                "ter_as_of": as_of,
            }
        ],
    )
    assert loader.ucits_facts("X", None, isin="ISIN") == loader.UcitsFacts(
        index="Index",
        ter=Decimal("0.0022"),
        ter_source="kid:vanguard",
        ter_as_of=date(2026, 10, 25),
    )
