from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest

from preza.models import EtfProfile, Instrument
from preza.universe import loader
from preza_agents.etf_analyst.context import profile_dict
from preza_agents.etf_analyst.profile import profile_from_funds, store_profile

TODAY = date(2026, 10, 25)


@pytest.mark.parametrize("curated", [None, "0.0022", "bad"])
@pytest.mark.parametrize("yahoo", [None, 0.0035])
def test_cost_merge(monkeypatch, curated, yahoo) -> None:
    monkeypatch.setattr(
        loader,
        "read_ucits",
        lambda: [
            {
                "symbol": "X",
                "exchange": "LSEETF",
                "index": "Index",
                "ter": curated,
                "ter_source": "kid:issuer",
                "ter_as_of": "2026-09-01",
            }
        ],
    )
    facts = loader.ucits_facts("X", "LSEETF")
    ops = pd.DataFrame({"X": [yahoo]}, index=["Annual Report Expense Ratio"])
    profile = profile_from_funds(None, None, ops, {"categoryName": None}, None, TODAY, facts)
    valid = curated == "0.0022"
    expected = Decimal("0.0022") if valid else Decimal(str(yahoo)) if yahoo else None
    assert profile.ter == expected
    assert profile.ter_source == ("kid:issuer" if valid else "yahoo" if yahoo else None)
    assert profile.ter_as_of == (date(2026, 9, 1) if valid else TODAY if yahoo else None)
    assert profile.index_name == "Index"
    kept = profile_from_funds(None, None, ops, {"categoryName": "Yahoo"}, None, TODAY, facts)
    assert kept.index_name == "Yahoo"


async def test_store_and_context_provenance() -> None:
    facts = loader.UcitsFacts("Index", Decimal("0.0022"), "kid:issuer", date(2026, 9, 1))
    profile = profile_from_funds(None, None, None, None, None, TODAY, facts)
    instrument = Instrument(id=1, symbol="X")
    row = EtfProfile(instrument_id=1)
    session = Mock(get=AsyncMock(return_value=row))
    await store_profile(session, instrument, profile)
    context = profile_dict(row)
    assert context["ter_source"] == "kid:issuer"
    assert context["ter_as_of"] == "2026-09-01"
    assert row.ter == Decimal("0.0022")
