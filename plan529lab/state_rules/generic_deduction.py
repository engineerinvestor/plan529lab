"""Generic state rule for states offering an income tax deduction on 529 contributions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from plan529lab.tax.state_base import StateRule

if TYPE_CHECKING:
    from plan529lab.models.tax_profile import InvestorTaxProfile


class GenericDeductionStateRule(StateRule):
    """State rule for jurisdictions offering a deduction for 529 contributions.

    Benefit = contribution amount * state ordinary income rate.
    Recapture = recaptured base * state ordinary income rate.

    This is a generic model. It does not reflect any specific state's
    exact rules, caps, or conditions.
    """

    def __init__(self, state_code: str = "DEDUCTION") -> None:
        self.state_code = state_code

    def contribution_benefit(
        self,
        contribution_amount: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return contribution_amount * tax_profile.state_ordinary_rate

    def recapture_tax(
        self,
        recaptured_base: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return recaptured_base * tax_profile.state_ordinary_rate

    def validate(self, context: Any) -> list[str]:
        warnings: list[str] = []
        if hasattr(context, "tax_profile"):
            if context.tax_profile.state_ordinary_rate == 0.0:
                warnings.append(
                    f"State {self.state_code}: using generic deduction rule but "
                    "state_ordinary_rate is 0. No deduction benefit will be computed."
                )
        return warnings
