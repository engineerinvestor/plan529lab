"""Federal 529/QTP tax computation functions.

All functions take plain floats and return plain floats for testability.
Implements formulas from SPEC Section 12.2–12.5.
"""

from plan529lab.constants import FEDERAL_ADDITIONAL_TAX_RATE


def compute_aqee(
    qualified_expenses: float,
    tax_free_assistance: float,
    aotc_llc_allocated: float,
) -> float:
    """Compute Adjusted Qualified Education Expenses (AQEE).

    AQEE = Qualified Expenses - Tax-Free Aid - AOTC/LLC Allocated, floored at 0.
    """
    return max(0.0, qualified_expenses - tax_free_assistance - aotc_llc_allocated)


def compute_taxable_earnings(
    earnings: float,
    aqee: float,
    distribution: float,
) -> float:
    """Compute the taxable portion of 529 distributed earnings.

    If AQEE >= distribution, all earnings are tax-free.
    Otherwise: Taxable Earnings = E * (1 - min(Q, D) / D)
    """
    if distribution <= 0.0:
        return 0.0
    if aqee >= distribution:
        return 0.0
    return max(0.0, earnings * (1.0 - min(aqee, distribution) / distribution))


def compute_additional_tax(
    taxable_earnings: float,
    exception_amount: float = 0.0,
    rate: float = FEDERAL_ADDITIONAL_TAX_RATE,
) -> float:
    """Compute the 10% additional tax on taxable 529 earnings.

    The additional tax applies to taxable earnings minus any exception amount
    (e.g., scholarship exception, AOTC/LLC-only taxable portion).
    """
    return rate * max(0.0, taxable_earnings - exception_amount)


def compute_qtp_after_tax(
    distribution: float,
    taxable_earnings: float,
    ordinary_rate: float,
    additional_tax: float,
    state_recapture: float = 0.0,
    state_benefit: float = 0.0,
) -> float:
    """Compute after-tax value of a 529 distribution.

    QTP After-Tax = Distribution - (Taxable Earnings * T_ord) - Additional Tax
                    - State Recapture + State Benefit
    """
    income_tax = taxable_earnings * ordinary_rate
    return distribution - income_tax - additional_tax - state_recapture + state_benefit
