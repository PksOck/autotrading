"""The explicit hypothesis check (BL-090)."""

import json

from preza_agents.hypothesis import HypothesisCheck, check_hypothesis, check_md
from tests.fake_role_llm import FakeRoleLlm


async def test_check_sees_hypothesis_and_reports() -> None:
    llm = FakeRoleLlm()
    reports = {"market_report": "x" * 10_000, "news_report": "", "final_trade_decision": "Hold"}
    check, model = await check_hypothesis(llm, "Cena bo rasla.", reports, "Hold", "sl")
    assert check.verdict == "partly" and model == "fake-cloud-deep"
    role, system, user = llm.calls[0]
    assert role == "cloud-deep" and "Slovenian" in system
    payload = json.loads(user)
    assert payload["hypothesis"] == "Cena bo rasla." and payload["rating"] == "Hold"
    assert len(payload["reports"]["market_report"]) == 6000
    assert "news_report" not in payload["reports"]  # empty reports are left out


def test_markdown_in_both_languages() -> None:
    check = HypothesisCheck(
        verdict="refuted", reasoning="Trend je navzdol.", evidence_against=["Pod SMA200."]
    )
    sl = check_md("Cena bo rasla.", check, "sl")
    assert "> Cena bo rasla." in sl and "ovržena" in sl and "**Proti**" in sl
    assert "**Za**" not in sl
    assert "refuted" in check_md("Price will rise.", check, "en")
