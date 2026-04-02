"""Generic state rule for states offering a tax credit on 529 contributions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from plan529lab.tax.state_base import StateRule

if TYPE_CHECKING:
    from plan529lab.models.tax_profile import InvestorTaxProfile


class GenericCreditStateRule(StateRule):
    """State rule for jurisdictions offering a credit for 529 contributions.

    Benefit = contribution amount * credit rate (from QTP assumptions).
    Recapture = recaptured base * credit rate.

    This is a generic model. It does not reflect any specific state's
    exact rules, caps, or conditions.
    """

    def __init__(self, state_code: str = "CREDIT", credit_rate: float = 0.0) -> None:
        self.state_code = state_code
        self.credit_rate = credit_rate

    def contribution_benefit(
        self,
        contribution_amount: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return contribution_amount * self.credit_rate

    def recapture_tax(
        self,
        recaptured_base: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return recaptured_base * self.credit_rate

    def validate(self, context: Any) -> list[str]:
        warnings: list[str] = []
        if self.credit_rate == 0.0:
            warnings.append(
                f"State {self.state_code}: using generic credit rule but "
                "credit_rate is 0. No credit benefit will be computed."
            )
        return warnings
