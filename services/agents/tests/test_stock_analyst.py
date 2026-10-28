"""Sequential stock pipeline with a deterministic role client, no external I/O."""

import json
import re
from datetime import date
from decimal import Decimal

import pytest

from preza_agents.budget import MAX_INPUT_TOKENS, WORK_INPUT_TOKENS
from preza_agents.deep_research.vendor_local import RUMOR_MARK
from preza_agents.stock_analyst.analyst import (
    AnalystNote,
    EvidencePoint,
    StockDecision,
    StockHypothesis,
    _gate,
    _supported,
    run_stock,
    sanitise,
    unverified_numbers,
)
from preza_agents.stock_analyst.digest import Digest, EvidenceItem, EvidenceRegister
from tests.conftest import make_snapshot
from tests.fake_role_llm import FakeRoleLlm


@pytest.mark.parametrize("compose_role", [None, "local-fast"])
async def test_run_stock(compose_role: str | None) -> None:
    llm = FakeRoleLlm()
    steps = []
    result = await run_stock(
        llm,
        make_snapshot(),
        "sl",
        steps.append,
        compose_role=compose_role,
        hypothesis="Rast naročil.",
        previous={"rating": "Buy", "decision": "Old decision"},
    )  # type: ignore[arg-type]
    agents = [json.loads(call[2]).get("agent", "compose") for call in llm.calls]
    assert agents == ["market", "fundamentals", "news", "bull", "bear", "decision"] + (
        ["compose"] if compose_role else []
    )
    assert all(size <= WORK_INPUT_TOKENS for size in llm.input_sizes)
    assert llm.output_caps == [6000] * 5 + [10_000] + ([2000] if compose_role else [])
    assert all(
        c["repair_input_estimate"] <= MAX_INPUT_TOKENS for c in result.models["usage"]["calls"]
    )
    registers = [json.loads(c[2])["evidence_register"] for c in llm.calls]
    assert all(r == registers[0] for r in registers)
    assert "### Sources" in result.decision and "[" in result.decision
    assert [s.agent for s in steps] == [
        "market",
        "fundamentals",
        "news",
        "bull",
        "bear",
        "portfolio_manager",
    ]
    assert [s.kind for s in steps] == ["report"] * 3 + ["debate"] * 2 + ["decision"]
    assert result.card_draft and result.card_draft.conviction == 6
    assert result.hypothesis_check and result.hypothesis_check.verdict == "partly"
    assert result.models["usage"]["prompt_tokens"] == sum(llm.input_sizes)
    assert result.models["usage"]["completion_tokens"] == 42 * len(llm.calls)
    assert [call[0] for call in llm.calls[:6]] == ["cloud-quick"] * 5 + ["cloud-deep"]
    assert not result.unverified_numbers
    assert json.loads(llm.calls[1][2])["earlier_notes"]["market"]
    assert set(json.loads(llm.calls[2][2])["earlier_notes"]) == {"market", "fundamentals"}
    assert json.loads(llm.calls[5][2])["previous"]["rating"] == "Buy"
    print(
        json.dumps(
            {
                "compose_role": compose_role,
                "per_call": [
                    {"agent": agent, "input_token_estimate": size, "max_output_tokens": cap}
                    for agent, size, cap in zip(
                        agents, llm.input_sizes, llm.output_caps, strict=True
                    )
                ],
            }
        )
    )


async def test_invented_number_and_compose_fallback() -> None:
    llm = FakeRoleLlm(compose_fails=True, invented_number=True)
    result = await run_stock(llm, make_snapshot(), "en", lambda _: None, compose_role="local-fast")
    assert "unverified_numbers" in result.caveats
    assert "987654.32" in result.unverified_numbers
    assert "987654.32" not in (result.decision or "")
    assert "[?]" in (result.decision or "")
    assert "compose_failed" in result.caveats
    assert result.summary == "Hold: Cena bo [?]."
    assert result.hypothesis_check is None and result.card_draft.delta_note is None
    assert len(result.models["usage"]["calls"]) == 7
    assert result.models["usage"]["calls"][-1]["status"] == "failed"


async def test_missing_hypothesis_and_large_optional_inputs() -> None:
    llm = FakeRoleLlm(check_fails=True)
    snapshot = make_snapshot()
    snapshot.fundamentals = None
    result = await run_stock(
        llm,
        snapshot,
        "en",
        lambda _: None,
        hypothesis="A claim",
        previous={"decision": "p" * 100_000},
        statements={"income": "revenue " * 100_000},
    )
    assert {"hypothesis_unchecked", "no_fundamentals"} <= set(result.caveats)
    assert all(n <= 16_000 for n in llm.input_sizes)


async def test_maximum_length_notes_remain_under_cap() -> None:
    class VerboseLlm(FakeRoleLlm):
        async def complete_json(self, role, system, user, schema, *, max_output_tokens=None):  # type: ignore[no-untyped-def]
            result = await super().complete_json(
                role, system, user, schema, max_output_tokens=max_output_tokens
            )
            if schema is AnalystNote:
                result.value = AnalystNote(
                    stance=0,
                    key_points=[EvidencePoint(text="p" * 300)] * 3,
                    risks=[EvidencePoint(text="r" * 300)] * 3,
                    what_to_watch=[EvidencePoint(text="w" * 300)] * 3,
                )
            return result

    llm = VerboseLlm()
    await run_stock(
        llm,
        make_snapshot(),
        "en",
        lambda _: None,
        hypothesis="A claim " * 1500,
        previous={"decision": "old " * 50_000},
    )
    assert len(llm.calls) == 6
    assert all(n <= WORK_INPUT_TOKENS for n in llm.input_sizes)


def test_number_formats_rounding_years_and_small_integers() -> None:
    digest = Digest(
        text="Price 1234.5",
        source="test",
        as_of=date(2026, 1, 1),
        numbers={"close": Decimal("1234.5")},
    )
    assert not unverified_numbers(["Price 1.234,5 or 1,234.50 or 1235."], [digest])
    assert unverified_numbers(["Up 1234.5%."], [digest]) == ["1234.5"]
    assert unverified_numbers(["Price 987654.32"], [digest]) == ["987654.32"]
    assert unverified_numbers(["In 2049, 3 risks. Price 1234.6."], [digest]) == [
        "1234.6",
        "2049",
        "3",
    ]
    assert unverified_numbers(["1. Another point\n12) Another risk"], [digest]) == ["1", "12"]
    assert unverified_numbers(["Target .98765 and 887766USD and 9e9."], [digest]) == [
        ".98765",
        "887766",
        "9e9",
    ]
    assert not unverified_numbers(["1\u202f234,50"], [digest])


async def test_unknown_evidence_is_dropped_and_recorded() -> None:
    llm = FakeRoleLlm(evidence_ids=["N999"])
    result = await run_stock(llm, make_snapshot(), "en", lambda _: None, hypothesis="An idea")
    assert "unknown_evidence" in result.caveats
    assert result.reports["unknown_evidence"] == "N999"
    assert "[N999]" not in result.decision
    assert all("N999" not in call[2] for call in llm.calls[1:])
    assert result.hypothesis_check and "N999" not in result.hypothesis_check.reasoning


@pytest.mark.parametrize("rating", ["Buy", "Overweight"])
async def test_rumor_support_cannot_buy_or_confirm_even_with_unrelated_official_news(
    rating: str,
) -> None:
    class RumorLlm(FakeRoleLlm):
        async def complete_json(self, role, system, user, schema, *, max_output_tokens=None):  # type: ignore[no-untyped-def]
            register = json.loads(user)["evidence_register"]
            line = next(line for line in register.splitlines() if RUMOR_MARK in line)
            self.evidence_ids = [re.match(r"\[([^]]+)\]", line).group(1)]
            result = await super().complete_json(
                role, system, user, schema, max_output_tokens=max_output_tokens
            )
            if json.loads(user).get("agent") == "decision":
                official = next(line for line in register.splitlines() if "press_release;" in line)
                result.value.risks[0].evidence_ids = [re.match(r"\[([^]]+)\]", official).group(1)]
            return result

    llm = RumorLlm(rating=rating, hypothesis_verdict="confirmed")
    result = await run_stock(llm, make_snapshot(), "en", lambda _: None, hypothesis="Acquisition")
    assert result.rating == "Hold" and "rumor_unconfirmed" in result.caveats
    assert result.hypothesis_check and result.hypothesis_check.verdict == "partly"
    assert "press_release" in result.decision


async def test_confirmed_cited_evidence_allows_buy() -> None:
    result = await run_stock(
        FakeRoleLlm(rating="Buy", hypothesis_verdict="confirmed"),
        make_snapshot(),
        "en",
        lambda _: None,
        hypothesis="Order",
    )
    assert result.rating == "Buy" and "rumor_unconfirmed" not in result.caveats
    assert result.hypothesis_check and result.hypothesis_check.verdict == "confirmed"


@pytest.mark.parametrize(
    "layer", ["market", "fundamentals", "news", "bull", "bear", "decision", "compose"]
)
async def test_numbers_redacted_before_next_layer_and_publishing(layer: str) -> None:
    class InventingLlm(FakeRoleLlm):
        async def complete_json(self, role, system, user, schema, *, max_output_tokens=None):  # type: ignore[no-untyped-def]
            result = await super().complete_json(
                role, system, user, schema, max_output_tokens=max_output_tokens
            )
            agent = json.loads(user).get("agent", "compose")
            if agent == layer:
                if schema is AnalystNote:
                    result.value.key_points[0].text = "Target 887766.55."
                elif agent == "decision":
                    result.value.rationale = "Target 887766.55."
                    result.value.upgrade_if[0].text = "Target 887766.55."
                    result.value.hypothesis.reasoning = "Target 887766.55."
                else:
                    result.value.summary = "Target 887766.55."
            return result

    llm = InventingLlm()
    steps = []
    result = await run_stock(
        llm, make_snapshot(), "en", steps.append, compose_role="local-fast", hypothesis="Order"
    )
    assert result.unverified_numbers == ["887766.55"]
    assert "unverified_numbers" in result.caveats
    index = [json.loads(c[2]).get("agent", "compose") for c in llm.calls].index(layer)
    assert all("887766.55" not in c[2] for c in llm.calls[index + 1 :])
    assert all("887766.55" not in s.content for s in steps)
    assert any("[?]" in s.content for s in steps)
    if layer == "decision":
        assert "[?]" in result.card_draft.upgrade_if[0]
        assert "[?]" in result.hypothesis_check.reasoning


async def test_unparseable_decision_fails_run_without_publishing_a_decision() -> None:
    steps = []
    with pytest.raises(RuntimeError, match="invalid structured output"):
        await run_stock(FakeRoleLlm(decision_fails=True), make_snapshot(), "en", steps.append)
    assert not any(step.kind == "decision" for step in steps)


def test_redaction_preserves_structural_citations_and_bounded_fields() -> None:
    register = EvidenceRegister(
        items=[
            EvidenceItem(
                id="N500",
                kind="news",
                source="test",
                as_of=date(2026, 1, 1),
                confirmed=True,
                text="Price 1234.5",
                numbers={"price": Decimal("1234.5")},
            )
        ]
    )
    bad: set[str] = set()
    unknown: set[str] = set()
    note = sanitise(
        AnalystNote(
            stance=2,
            key_points=[
                EvidencePoint(
                    text="Known 1.234,5 [N500], invented .98765USD [N999].",
                    evidence_ids=["N500", "N999"],
                )
            ],
            risks=[EvidencePoint(text="7 " * 150)],
        ),
        register,
        bad,
        unknown,
    )
    assert "[N500]" in note.key_points[0].text and "[N999]" not in note.key_points[0].text
    assert note.key_points[0].evidence_ids == ["N500"]
    assert "[?]USD" in note.key_points[0].text
    assert note.risks[0].text == "[?]"
    assert bad == {".98765", "7"} and unknown == {"N999"}
    assert note.stance == 2


def claim_register() -> EvidenceRegister:
    def item(identifier: str, **kwargs) -> EvidenceItem:  # type: ignore[no-untyped-def]
        return EvidenceItem(
            id=identifier, source="test", as_of=date(2026, 10, 20), text="Evidence", **kwargs
        )

    return EvidenceRegister(
        items=[
            item("N1", kind="news", confirmed=False),
            item("M1", kind="market", confirmed=True, numbers={"close": Decimal(100)}),
            item("N2", kind="news", confirmed=True, official=True),
            item("N3", kind="news", confirmed=True),
            item("F1", kind="fundamental", confirmed=True, official=True),
        ]
    )


@pytest.mark.parametrize("rating", ["Buy", "Overweight"])
@pytest.mark.parametrize(
    ("citations", "expected", "caveat"),
    [
        ([["N1"], ["M1"]], "Hold", "rumor_unconfirmed"),
        ([["N1", "M1"]], "Hold", "rumor_unconfirmed"),
        ([["N1", "N3"]], "Hold", "rumor_unconfirmed"),
        ([["N1", "F1"]], "Hold", "rumor_unconfirmed"),
        ([["N1", "N2"]], None, None),
        ([["M1"]], None, None),
        ([[]], "Hold", "unsupported_evidence"),
        ([], "Hold", "unsupported_evidence"),
    ],
)
def test_buy_gate_checks_each_reason(rating, citations, expected, caveat) -> None:  # type: ignore[no-untyped-def]
    value = StockDecision(
        rating=rating,
        rationale="Opinion",
        evidence_ids=["N2"],  # An unrelated rationale cannot rescue a reason.
        reasons=[EvidencePoint(text="Reason", evidence_ids=ids) for ids in citations],
        conviction=6,
    )
    found: list[str] = []
    _gate(value, claim_register(), found)
    assert value.rating == (expected or rating)
    assert found == ([caveat] if caveat else [])
    if caveat == "rumor_unconfirmed":
        assert any(p.render().startswith("[UNCONFIRMED]") for p in value.reasons)
        assert value.reasons[0].text == "Reason"
    else:
        assert not any("[UNCONFIRMED]" in p.render() for p in value.reasons)


@pytest.mark.parametrize("citations", [[["N1"], ["M1"]], [["N1", "M1"]], [[]]])
def test_hypothesis_gate_checks_each_supporting_claim(citations) -> None:  # type: ignore[no-untyped-def]
    value = StockDecision(
        rating="Hold",
        rationale="Opinion",
        conviction=5,
        hypothesis=StockHypothesis(
            verdict="confirmed",
            reasoning="Opinion",
            evidence_ids=["N2"],
            evidence_for=[EvidencePoint(text="Claim", evidence_ids=ids) for ids in citations],
        ),
    )
    found: list[str] = []
    _gate(value, claim_register(), found)
    assert value.hypothesis.verdict == "partly"
    assert found == (["rumor_unconfirmed"] if any(citations) else ["unsupported_evidence"])


@pytest.mark.parametrize("kind", ["news", "filing", "statement"])
def test_official_confirmation_must_be_cited_in_the_same_claim(kind: str) -> None:
    register = claim_register()
    register.items[2].kind = kind  # type: ignore[assignment]
    point = EvidencePoint(text="Confirmed claim", evidence_ids=["N1", "N2"])
    value = StockDecision(
        rating="Buy",
        rationale="Opinion",
        conviction=6,
        reasons=[point],
        hypothesis=StockHypothesis(
            verdict="confirmed",
            reasoning="Opinion",
            evidence_for=[point.model_copy()],
        ),
    )
    found: list[str] = []
    _gate(value, register, found)
    assert value.rating == "Buy" and value.hypothesis.verdict == "confirmed" and not found


@pytest.mark.parametrize(
    ("text", "bad"),
    [
        ("Target price 2026 USD", ["2026"]),
        ("50 % return", ["50"]),
        ("100 %", ["100"]),
        ("100pct", ["100"]),
        ("100 odstotkov", ["100"]),
        ("Price 1.234,5", []),
        ("Growth 12.5 % or 12,5pct or 12.5 odstotkov", []),
        ("Price 12.5", ["12.5"]),
    ],
)
def test_numbers_use_only_structured_facts_with_matching_units(text: str, bad: list[str]) -> None:
    register = claim_register()
    register.items[1].text = "SMA50: 100; return_3m: unavailable; as_of: 2026-10-20"
    register.items[1].numbers.update(
        {
            "sma50": Decimal(100),
            "price": Decimal("1234.5"),
            "growth_pct": Decimal("12.5"),
        }
    )
    assert unverified_numbers([text], register, "2026 50 100 %") == bad
    found: set[str] = set()
    clean = sanitise(
        AnalystNote(stance=2, key_points=[EvidencePoint(text=text)]), register, found, set()
    )
    assert found == set(bad)
    assert ("[?]" in clean.key_points[0].text) == bool(bad)
    assert clean.stance == 2


@pytest.mark.parametrize(
    "text",
    [
        "over 3 months",
        "50-day average",
        "SMA200",
        "EMA50",
        "RSI14",
        "ATR14",
        "v naslednjih 3 mesecih",
        "Q3",
        "50d",
        "3m",
        "400 days",
        "10 years",
        "2 tedna",
        "3 četrtletij",
        "2 leti",
        "200-dnevno SMA",
        "pod 12-mesečnim vrhom",
        "razmerje 20- in 50-dnevnega volumna",
        "20- oziroma 50-dnevnega",
        "52-tedenski razpon",
        "do 30. junija 2026",
        "as of June 30, 2026",
    ],
)
def test_periods_and_indicator_names_are_not_claimed_levels(text: str) -> None:
    register = EvidenceRegister()
    assert not unverified_numbers([text], register)
    bad: set[str] = set()
    clean = sanitise(
        AnalystNote(stance=-2, key_points=[EvidencePoint(text=text)]), register, bad, set()
    )
    assert not bad and clean.key_points[0].text == text and clean.stance == -2


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("RSI near 70", ["70"]),
        ("500 days", ["500"]),
        ("11 years", ["11"]),
        ("The scale is -2..+2", ["+2", "-2"]),
        ("Q5", ["5"]),
        ("500- in 20-dnevno", ["20", "500"]),
        ("12 % pod 12-mesečnim vrhom", ["12"]),
        ("5 majhnih podjetij", ["5"]),
    ],
)
def test_levels_and_unbounded_periods_are_still_checked(text: str, expected: list[str]) -> None:
    assert unverified_numbers([text], EvidenceRegister()) == expected


@pytest.mark.parametrize("fetch_fails", [False, True])
async def test_worker_fetch_is_injected_and_offloaded(fetch_fails: bool) -> None:
    import threading

    from preza.config import Settings
    from preza_agents.worker import _stock_work

    main_thread = threading.get_ident()

    def fetch(snapshot, settings):  # type: ignore[no-untyped-def]
        assert threading.get_ident() != main_thread
        if fetch_fails:
            raise RuntimeError("SEC unavailable")
        return {"income": ",2025-12-31,2026-03-31\nRevenue,100,120"}

    result = await _stock_work(
        {"statement_fetcher": fetch},
        Settings(_env_file=None),
        FakeRoleLlm(),
        make_snapshot(),
        "en",
        lambda _: None,
        None,
        None,
    )
    assert ("statements_unavailable" in result.caveats) is fetch_fails
    assert ("Revenue | 100 | 120" in result.reports["fundamentals_report"]) is not fetch_fails


async def test_default_sec_fetcher_uses_contact_cache_and_cutoff(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from tradingagents.dataflows.config import get_config
    from tradingagents.dataflows.vendors import sec_edgar

    from preza.config import Settings
    from preza_agents.worker import _stock_work

    calls = []

    def fetch(symbol, frequency, as_of):  # type: ignore[no-untyped-def]
        assert get_config()["data_cache_dir"] == str(tmp_path / "cache")
        calls.append((symbol, frequency, as_of))
        return ",2025-12-31,2026-03-31\nRevenue,100,120"

    for name in ("get_income_statement", "get_balance_sheet", "get_cashflow"):
        monkeypatch.setattr(sec_edgar, name, fetch)
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    settings = Settings(
        _env_file=None,
        agents_home=str(tmp_path),
        sec_edgar_user_agent="Preza unit test <unit@example.invalid>",
    )
    result = await _stock_work(
        {}, settings, FakeRoleLlm(), make_snapshot(), "en", lambda _: None, None, None
    )
    assert calls == [("ASML", "quarterly", "2026-10-20")] * 3
    assert "statements_unavailable" not in result.caveats


def test_sign_in_prose_matches_a_negative_fact() -> None:
    assert _supported("7,92", {Decimal("-7.92")})
    assert _supported("-5415", {Decimal("5415")})
    assert not _supported("7,9", {Decimal("-7.82")})
