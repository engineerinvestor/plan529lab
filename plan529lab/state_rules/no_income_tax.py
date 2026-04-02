"""State rule for states with no personal income tax (e.g., WA, TX, FL)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from plan529lab.tax.state_base import StateRule

if TYPE_CHECKING:
    from plan529lab.models.tax_profile import InvestorTaxProfile


class NoIncomeTaxStateRule(StateRule):
    """State rule for jurisdictions with no personal income tax.

    Returns zero for both contribution benefit and recapture.
    """

    def __init__(self, state_code: str = "WA") -> None:
        self.state_code = state_code

    def contribution_benefit(
        self,
        contribution_amount: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return 0.0

    def recapture_tax(
        self,
        recaptured_base: float,
        tax_profile: InvestorTaxProfile,
        year: int,
    ) -> float:
        return 0.0

    def validate(self, context: Any) -> list[str]:
        warnings: list[str] = []
        if hasattr(context, "qtp_assumptions"):
            qtp = context.qtp_assumptions
            if qtp.state_tax_deduction_rate > 0 or qtp.state_tax_credit_rate > 0:
                warnings.append(
                    f"State {self.state_code} has no income tax, but QTP assumptions "
                    "include a state deduction/credit rate > 0."
                )
        return warnings
