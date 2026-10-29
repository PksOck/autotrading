import pytest
from pydantic import BaseModel

from preza.services.table_sort import sort_rows
from tests.test_signal_expiry import seed_signals


class Row(BaseModel):
    id: int
    currency: str
    latest_close: str | None


def test_numeric_close_sort_preserves_currency_groups_and_nulls_last() -> None:
    rows = [
        Row(id=1, currency="USD", latest_close="20"),
        Row(id=2, currency="USD", latest_close="100"),
        Row(id=3, currency="EUR", latest_close="50"),
        Row(id=4, currency="EUR", latest_close=None),
    ]
    assert [row.id for row in sort_rows(rows, "latest_close", "desc")] == [3, 2, 1, 4]
    assert [row.id for row in sort_rows(rows, "latest_close", "asc")] == [3, 1, 2, 4]


@pytest.mark.db
async def test_overview_matches_normalized_inbox_instead_of_samples(api) -> None:
    client, _ = api
    expired, active = await seed_signals("new")
    data = (await client.get("/overview")).json()
    assert data["signal_counts"] == {"new": 1, "expired": 1}
    assert [row["id"] for row in data["signals"]] == [active]
    assert expired not in [row["id"] for row in data["signals"]]
    assert data["news_count"] == 0
    assert data["event_count"] == 0
