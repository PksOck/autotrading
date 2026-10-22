"""ETF analyst: profile parsing, look-through overlap and the pipeline (BL-083)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from preza_agents.deep_research.snapshot import DataSnapshot
from preza_agents.deep_research.timeline import Step
from preza_agents.etf_analyst import analyst
from preza_agents.etf_analyst.exposure import Holding, look_through, overlap
from preza_agents.etf_analyst.profile import distribution_from_name, profile_from_funds
from tests.fake_role_llm import FakeRoleLlm

HOLDINGS = [
    {"symbol": "NVDA", "name": "NVIDIA", "weight": 0.20},
    {"symbol": "ASML.AS", "name": "ASML", "weight": 0.12},
    {"symbol": "TSM", "name": "TSMC", "weight": 0.10},
]


def test_profile_from_yahoo_frames() -> None:
    top = pd.DataFrame(
        {"Name": ["NVIDIA", "ASML", "Bad"], "Holding Percent": [0.2, 0.12, None]},
        index=pd.Index(["NVDA", "ASML.AS", "X"], name="Symbol"),
    )
    ops = pd.DataFrame(
        {"SMH.L": [0.0035, None, 1.2e9]},
        index=pd.Index(
            ["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"]
        ),
    )
    profile = profile_from_funds(
        top,
        {"technology": 0.9, "industrials": 0.0},
        ops,
        {"categoryName": "Sector Equity Technology"},
        "VanEck Semiconductor UCITS ETF (Acc)",
        date(2026, 10, 20),
    )
    assert [h["symbol"] for h in profile.holdings] == ["NVDA", "ASML.AS"]
    assert profile.coverage == Decimal("0.32")
    assert profile.ter == Decimal("0.0035")
    assert profile.sectors == {"technology": 0.9}
    assert profile.distribution == "acc"
    assert profile.index_name == "Sector Equity Technology"


def test_ter_in_percent_units_is_rejected() -> None:
    ops = pd.DataFrame({"X": [0.35]}, index=pd.Index(["Annual Report Expense Ratio"]))
    assert profile_from_funds(None, None, ops, None, None, date(2026, 1, 1)).ter is None
    assert distribution_from_name("Invesco EQQQ Nasdaq-100 UCITS ETF (Dist)") == "dist"
    assert distribution_from_name("Some fund") is None


def test_look_through_and_overlap() -> None:
    portfolio = [
        Holding("NVDA", "stock", 0.05),
        Holding("VWRA", "etf", 0.50),
        Holding("EQQQ", "etf", 0.10),  # no profile: all unexplained
    ]
    profiles = {
        "VWRA": [
            {"symbol": "NVDA", "name": "NVIDIA", "weight": 0.04},
            {"symbol": "ASML", "name": "ASML", "weight": 0.01},
        ]
    }
    exposure = look_through(portfolio, profiles)
    assert exposure.by_symbol["NVDA"] == pytest.approx(0.05 + 0.02)
    assert exposure.by_symbol["ASML"] == pytest.approx(0.005)
    assert exposure.unexplained == pytest.approx(0.50 * 0.95 + 0.10)

    result = overlap(HOLDINGS, exposure)
    assert result.coverage == pytest.approx(0.42)
    assert result.shared_weight == pytest.approx(0.32 / 0.42)  # NVDA and ASML(.AS) owned
    assert [r.symbol for r in result.rows if r.portfolio_exposure == 0] == ["TSM"]


async def test_pipeline_steps_and_facts(snapshot: DataSnapshot) -> None:
    profile = {
        "as_of": "2026-10-19",
        "ter": 0.0035,
        "index_name": "Semis",
        "distribution": "acc",
        "holdings": HOLDINGS,
        "sectors": {"technology": 0.95},
        "source": "yahoo",
    }
    exposure = look_through([Holding("NVDA", "stock", 0.08)], {})
    facts = analyst.compute_facts(snapshot, profile, 0.0, overlap(HOLDINGS, exposure), None)
    assert facts.price == float(snapshot.bars[-2].close)  # the bar after the run date is cut
    assert facts.sma200 is not None and facts.rsi14 is not None

    llm = FakeRoleLlm(rating="Overweight")
    steps: list[Step] = []
    result = await analyst.run_etf(llm, facts, "sl", steps.append)

    assert result.rating == "Overweight"
    assert [s.agent for s in steps] == [
        "profile",
        "exposure",
        "market",
        "news",
        "portfolio_manager",
    ]
    assert "0,35 %" in steps[0].content  # TER rendered by code, Slovenian format
    assert "NVDA: 20,0 % sklada, v portfelju 8,0 %" in steps[1].content
    assert [c[0] for c in llm.calls] == ["cloud-quick", "cloud-deep"]
    sent = json.loads(llm.calls[0][2])
    assert sent["profile"]["ter"] == 0.0035 and "Slovenian" in llm.calls[0][1]
    assert "**Rating**: Overweight" in (result.decision or "")
