import uuid

from preza.routes import analyses


async def test_revoked_stream_stops_before_reading_private_rows(monkeypatch):
    async def revoked():
        return False

    def forbidden_db():
        raise AssertionError("revoked stream must not query private data")

    monkeypatch.setattr(analyses, "get_sessionmaker", forbidden_db)
    assert [event async for event in analyses.run_events(uuid.uuid4(), 0, authorized=revoked)] == []
