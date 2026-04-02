"""Abstract base class for state-specific 529 tax treatment."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plan529lab.models.tax_profile import InvestorTaxProfile


class StateRule(ABC):
    """Abstract interface for state-specific 529 tax treatment.

    Subclasses implement contribution benefits, recapture logic, and validation.
    """

    state_code: str

    @abstractmethod
    def contribution_benefit(
        self,
        contribution_amount: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        """Compute the tax benefit from 529 contributions (deduction or credit value)."""
        ...

    @abstractmethod
    def recapture_tax(
        self,
        recaptured_base: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        """Compute recapture tax if state benefit conditions are violated."""
        ...

    @abstractmethod
    def validate(self, context: Any) -> list[str]:
        """Validate assumptions and return warnings."""
        ...

    def metadata(self) -> dict[str, Any]:
        """Return metadata about this state rule."""
        return {
            "state_code": self.state_code,
            "class": type(self).__name__,
        }
