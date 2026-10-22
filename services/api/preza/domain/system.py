"""System status models shown in the UI header (CMP-02 SystemStatus)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ServiceState(StrEnum):
    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    UNCONFIGURED = "unconfigured"


class ServiceId(StrEnum):
    POSTGRES = "postgres"
    REDIS = "redis"
    LITELLM = "litellm"
    OLLAMA = "ollama"
    IB_GATEWAY = "ib_gateway"
    IBKR_FLEX = "ibkr_flex"
    TELEGRAM = "telegram"


class ServiceStatus(BaseModel):
    id: ServiceId
    state: ServiceState
    latency_ms: float | None = Field(default=None, ge=0)
    detail: str | None = None


class SystemStatus(BaseModel):
    as_of: datetime
    services: list[ServiceStatus]

    @property
    def overall(self) -> ServiceState:
        states = {s.state for s in self.services}
        if ServiceState.DOWN in states:
            return ServiceState.DEGRADED
        return ServiceState.UP
