"""Email preferences contain recipients and notification choices, never credentials."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NotificationKind = Literal["signals", "daily_digest", "analysis_complete"]


class EmailPreferencesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(default=0, ge=0)
    enabled: bool = False
    recipients: list[str] = Field(default_factory=list, max_length=20)
    kinds: list[NotificationKind] = Field(default=["signals"])

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, values: list[str]) -> list[str]:
        result = []
        for raw in values:
            value = raw.strip()
            if len(value) > 254 or not re.fullmatch(
                r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}",
                value,
            ):
                raise ValueError("invalid_recipient")
            local, domain = value.rsplit("@", 1)
            if len(local) > 64 or local.startswith(".") or local.endswith(".") or ".." in value:
                raise ValueError("invalid_recipient")
            if any(
                not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                for label in domain.split(".")
            ):
                raise ValueError("invalid_recipient")
            normalized = local + "@" + domain.lower()
            if normalized not in result:
                result.append(normalized)
        return result

    @model_validator(mode="after")
    def enabled_requires_recipients(self) -> "EmailPreferencesInput":
        if self.enabled and (not self.recipients or not self.kinds):
            raise ValueError("recipients_and_kinds_required")
        return self


class EmailPreferencesOut(EmailPreferencesInput):
    configured: bool
    queued_deliveries: int = 0
    sent_deliveries: int = 0
    uncertain_deliveries: int = 0
