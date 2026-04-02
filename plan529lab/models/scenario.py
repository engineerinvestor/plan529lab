"""Scenario policy model for leftover-funds resolution."""

from typing import Literal

from pydantic import BaseModel, Field

LeftoverResolution = Literal[
    "withdraw_nonqualified",
    "change_beneficiary",
    "hold_for_future_education",
    "roth_rollover",
    "mixed",
]


class ScenarioPolicy(BaseModel, frozen=True):
    """How leftover 529 funds are resolved when not fully used for education."""

    leftover_resolution: LeftoverResolution = "withdraw_nonqualified"
    qualified_use_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    scholarship_exception_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    roth_rollover_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
