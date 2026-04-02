"""Education expense models with AQEE computation."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class EducationExpenseItem(BaseModel, frozen=True):
    """A single period of qualified education expenses with adjustments."""

    date: datetime.date
    qualified_expense: float = Field(ge=0.0)
    tax_free_assistance: float = Field(default=0.0, ge=0.0)
    aotc_or_llc_allocated_expense: float = Field(default=0.0, ge=0.0)
    notes: str | None = None

    @property
    def aqee(self) -> float:
        """Adjusted Qualified Education Expenses (AQEE).

        AQEE = Qualified Expenses - Tax-Free Aid - AOTC/LLC Allocated Expenses,
        floored at zero.
        """
        return max(
            0.0,
            self.qualified_expense
            - self.tax_free_assistance
            - self.aotc_or_llc_allocated_expense,
        )


class EducationExpenseSchedule(BaseModel, frozen=True):
    """A schedule of education expenses over time."""

    items: list[EducationExpenseItem] = Field(default_factory=list)

    @property
    def total_aqee(self) -> float:
        """Sum of AQEE across all expense items."""
        return sum(item.aqee for item in self.items)

    @property
    def total_qualified_expense(self) -> float:
        """Sum of gross qualified expenses."""
        return sum(item.qualified_expense for item in self.items)

    @property
    def total_tax_free_assistance(self) -> float:
        """Sum of tax-free educational assistance."""
        return sum(item.tax_free_assistance for item in self.items)

    @property
    def total_aotc_llc_allocated(self) -> float:
        """Sum of expenses allocated to AOTC/LLC."""
        return sum(item.aotc_or_llc_allocated_expense for item in self.items)
