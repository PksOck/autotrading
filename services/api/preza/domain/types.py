"""Shared field types for API models."""

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Money and prices are Decimal internally (AGENTS.md §4) and plain JSON numbers on the wire,
# so charts and tables do not have to parse strings.
Num = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
