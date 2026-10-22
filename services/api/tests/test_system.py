from fastapi.testclient import TestClient

from preza.config import Settings, get_settings
from preza.domain.system import ServiceId, ServiceState, ServiceStatus
from preza.main import create_app
from preza.system import checks


def test_health_reports_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_collect_status_runs_every_probe() -> None:
    async def up(settings: Settings) -> ServiceStatus:
        return ServiceStatus(id=ServiceId.REDIS, state=ServiceState.UP, latency_ms=1.0)

    async def down(settings: Settings) -> ServiceStatus:
        return ServiceStatus(id=ServiceId.OLLAMA, state=ServiceState.DOWN, detail="timeout")

    status = await checks.collect_status(Settings(), probes=(up, down))
    assert [s.id for s in status.services] == [ServiceId.REDIS, ServiceId.OLLAMA]
    assert status.overall == ServiceState.DEGRADED


async def test_unreachable_service_is_down_not_an_error() -> None:
    settings = Settings(ib_gateway_host="127.0.0.1", ib_gateway_port=9, status_timeout_s=0.5)
    status = await checks.probe_ib_gateway(settings)
    assert status.state == ServiceState.DOWN
    assert status.detail


async def test_slow_probe_times_out() -> None:
    import asyncio

    async def never() -> None:
        await asyncio.sleep(10)

    settings = Settings(status_timeout_s=0.05)
    status = await checks._timed(ServiceId.LITELLM, settings, never())
    assert status.state == ServiceState.DOWN
    assert status.detail == "timeout"


async def test_flex_and_telegram_report_unconfigured_without_secrets() -> None:
    settings = Settings(ibkr_flex_token=None, telegram_bot_token=None)
    assert (await checks.probe_flex(settings)).state == ServiceState.UNCONFIGURED
    assert (await checks.probe_telegram(settings)).state == ServiceState.UNCONFIGURED


def test_status_endpoint_uses_injected_settings(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_collect(settings: Settings) -> checks.SystemStatus:
        return await checks.collect_status(settings, probes=(checks.probe_flex,))

    monkeypatch.setattr("preza.routes.system.collect_status", fake_collect)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        ibkr_flex_token="t", ibkr_flex_query_id="q"
    )
    body = TestClient(app).get("/system/status").json()
    assert body["services"] == [
        {"id": "ibkr_flex", "state": "up", "latency_ms": None, "detail": "configured"}
    ]
