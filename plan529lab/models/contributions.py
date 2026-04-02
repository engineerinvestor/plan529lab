"""Contribution and contribution schedule models."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Contribution(BaseModel, frozen=True):
    """A single dated contribution to a 529 or taxable account."""

    date: datetime.date
    amount: float = Field(gt=0.0)
    account_type: Literal["qtp", "taxable"]
    source: str | None = None


class ContributionSchedule(BaseModel, frozen=True):
    """An ordered list of contributions."""

    items: list[Contribution] = Field(default_factory=list)

    @property
    def total_amount(self) -> float:
        """Sum of all contribution amounts."""
        return sum(c.amount for c in self.items)

    @property
    def first_date(self) -> datetime.date | None:
        """Earliest contribution date, or None if empty."""
        if not self.items:
            return None
        return min(c.date for c in self.items)

    @property
    def last_date(self) -> datetime.date | None:
        """Latest contribution date, or None if empty."""
        if not self.items:
            return None
        return max(c.date for c in self.items)

    def contributions_for_year(self, year: int) -> list[Contribution]:
        """Return contributions made in a given calendar year."""
        return [c for c in self.items if c.date.year == year]

    def total_for_year(self, year: int) -> float:
        """Sum of contributions in a given calendar year."""
        return sum(c.amount for c in self.contributions_for_year(year))
