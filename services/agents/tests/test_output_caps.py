"""Direct ETF/card/hypothesis callers cannot bypass budgets or output caps."""

import pytest

from preza_agents.budget import (
    MAX_INPUT_TOKENS,
    REPAIR_CONTENT_TOKENS,
    REPAIR_OVERHEAD_TOKENS,
)
from preza_agents.decision_card import draft_card
from preza_agents.etf_analyst.analyst import compute_facts, run_etf
from preza_agents.hypothesis import check_hypothesis
from tests.conftest import make_snapshot
from tests.fake_role_llm import FakeRoleLlm


async def test_raw_clients_receive_explicit_caps_and_schema_aware_budgets() -> None:
    raw = FakeRoleLlm()
    facts = compute_facts(make_snapshot(), None, 0, None, None)
    await run_etf(raw, facts, "en", lambda _: None)
    reports = {f"report_{i}": "Complete report line.\n" * 3000 for i in range(40)}
    await draft_card(raw, "Hold", "Decision", reports, None, "en")
    await check_hypothesis(raw, "Growth", reports, "Hold", "en")
    assert raw.output_caps == [6000, 10_000, 10_000, 10_000]
    for size, cap in zip(raw.input_sizes, raw.output_caps, strict=True):
        assert cap is not None
        assert size + min(cap, REPAIR_CONTENT_TOKENS) + REPAIR_OVERHEAD_TOKENS <= MAX_INPUT_TOKENS


@pytest.mark.parametrize("path", ["etf", "card", "hypothesis"])
async def test_direct_call_rejects_oversized_required_data_before_raw_client(path: str) -> None:
    raw = FakeRoleLlm()
    with pytest.raises(ValueError, match="input budget exceeded"):
        if path == "etf":
            facts = compute_facts(make_snapshot(), {"name": "x" * 40_000}, 0, None, None)
            await run_etf(raw, facts, "en", lambda _: None)
        elif path == "card":
            await draft_card(raw, "x" * 40_000, "Decision", {}, None, "en")
        else:
            await check_hypothesis(raw, "x" * 40_000, {}, "Hold", "en")
    assert not raw.calls
