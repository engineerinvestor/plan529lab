"""Taxable brokerage account tax computation functions.

Implements formulas from SPEC Section 12.6–12.7.
"""


def compute_annual_dividend_tax(
    portfolio_value: float,
    dividend_yield: float,
    qualified_dividend_share: float,
    qualified_dividend_rate: float,
    ordinary_income_rate: float,
) -> float:
    """Compute annual tax on dividends from a taxable account.

    Splits dividends into qualified (taxed at QD rate) and ordinary
    (taxed at ordinary rate).
    """
    total_dividends = portfolio_value * dividend_yield
    qualified = total_dividends * qualified_dividend_share
    ordinary = total_dividends * (1.0 - qualified_dividend_share)
    return qualified * qualified_dividend_rate + ordinary * ordinary_income_rate


def compute_annual_realized_gain_tax(
    unrealized_gain: float,
    turnover_realization_rate: float,
    ltcg_rate: float,
) -> float:
    """Compute annual tax on realized capital gains from portfolio turnover."""
    realized = max(0.0, unrealized_gain) * turnover_realization_rate
    return realized * ltcg_rate


def compute_terminal_liquidation_tax(
    ending_value: float,
    tax_basis: float,
    ltcg_rate: float,
) -> float:
    """Compute tax on terminal liquidation of a taxable account."""
    gain = max(0.0, ending_value - tax_basis)
    return gain * ltcg_rate
