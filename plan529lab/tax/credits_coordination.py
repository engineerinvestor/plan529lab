"""Education credit coordination (AOTC/LLC) with 529 distributions.

In v1, AOTC/LLC coordination is handled through the AQEE reduction in the
education expense model. This module provides a named location for future
expansion of credit-specific logic.
"""


def compute_aotc_exception_amount(
    aotc_allocated_expense: float,
    earnings: float,
    distribution: float,
) -> float:
    """Compute the earnings portion made taxable only because of AOTC/LLC allocation.

    This amount is exempt from the 10% additional tax per IRS rules.
    Returns the exception amount to pass to compute_additional_tax().
    """
    if distribution <= 0.0:
        return 0.0
    # The portion of earnings attributable to the AOTC/LLC reduction
    earnings_ratio = earnings / distribution if distribution > 0 else 0.0
    return aotc_allocated_expense * earnings_ratio
