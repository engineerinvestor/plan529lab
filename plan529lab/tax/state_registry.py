"""Registry mapping state codes to StateRule classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plan529lab.state_rules.generic_credit import GenericCreditStateRule
from plan529lab.state_rules.generic_deduction import GenericDeductionStateRule
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule

if TYPE_CHECKING:
    from plan529lab.tax.state_base import StateRule

# States with no personal income tax
_NO_INCOME_TAX_STATES = {"WA", "TX", "FL", "NV", "SD", "WY", "AK", "TN", "NH"}

STATE_RULE_REGISTRY: dict[str, type[StateRule]] = {
    "NONE": NoIncomeTaxStateRule,
    "DEDUCTION": GenericDeductionStateRule,
    "CREDIT": GenericCreditStateRule,
}

# Register no-income-tax states
for _code in _NO_INCOME_TAX_STATES:
    STATE_RULE_REGISTRY[_code] = NoIncomeTaxStateRule


def get_state_rule(state_code: str, **kwargs: object) -> StateRule:
    """Look up and instantiate a state rule by state code.

    Raises KeyError if the state code is not registered.
    """
    state_code = state_code.upper()
    if state_code not in STATE_RULE_REGISTRY:
        available = sorted(STATE_RULE_REGISTRY.keys())
        msg = f"Unknown state code '{state_code}'. Available: {available}"
        raise KeyError(msg)
    rule_class = STATE_RULE_REGISTRY[state_code]
    return rule_class(state_code=state_code, **kwargs)  # type: ignore[call-arg]
