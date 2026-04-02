"""Year-by-year account growth models for 529/QTP and taxable accounts."""

from __future__ import annotations

from collections.abc import Sequence

from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.contributions import ContributionSchedule
from plan529lab.models.results import QTPGrowthResult, TaxableGrowthResult
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.tax.taxable_account import (
    compute_annual_dividend_tax,
    compute_annual_realized_gain_tax,
    compute_terminal_liquidation_tax,
)


def grow_qtp_account(
    contributions: ContributionSchedule,
    portfolio: PortfolioAssumptions,
    qtp: QTPAssumptions,
    horizon_years: int,
    start_year: int = 0,
    annual_returns: Sequence[float] | None = None,
) -> QTPGrowthResult:
    """Grow a 529/QTP account over the given horizon.

    Contributions are applied at the start of each year. Growth is net of
    expense ratio and plan fee drag.

    If annual_returns is provided, uses per-year returns instead of the
    fixed portfolio.annual_return (for Monte Carlo simulation).
    """
    value = 0.0
    total_contributions = 0.0
    fee_drag = portfolio.expense_ratio + qtp.plan_fee_drag

    for year in range(horizon_years):
        # Add contributions for this year
        year_contrib = contributions.total_for_year(start_year + year)
        value += year_contrib
        total_contributions += year_contrib

        # Apply net growth
        if annual_returns is not None:
            base_return = annual_returns[year]
        else:
            base_return = portfolio.annual_return
        value *= 1.0 + base_return - fee_drag

    total_earnings = value - total_contributions

    return QTPGrowthResult(
        ending_value=value,
        total_contributions=total_contributions,
        total_earnings=total_earnings,
    )


def grow_taxable_account(
    contributions: ContributionSchedule,
    portfolio: PortfolioAssumptions,
    tax_profile: InvestorTaxProfile,
    horizon_years: int,
    start_year: int = 0,
    liquidate: bool = True,
    annual_returns: Sequence[float] | None = None,
) -> TaxableGrowthResult:
    """Grow a taxable brokerage account over the given horizon.

    Each year:
    1. Add contributions (increases value and basis)
    2. Compute and pay dividend taxes (reduces value, dividends reinvested pre-tax)
    3. Compute and pay realized gain taxes from turnover (reduces value, adjusts basis up)
    4. Apply remaining price appreciation

    Basis tracking: basis increases by new contributions. When gains are realized
    from turnover, basis increases proportionally (the realized portion is re-invested
    at the new cost basis).
    """
    value = 0.0
    basis = 0.0
    cumulative_dividend_tax = 0.0
    cumulative_realized_gain_tax = 0.0

    for year in range(horizon_years):
        base_return = (
            annual_returns[year] if annual_returns is not None else portfolio.annual_return
        )
        net_return = base_return - portfolio.expense_ratio

        # 1. Add contributions
        year_contrib = contributions.total_for_year(start_year + year)
        value += year_contrib
        basis += year_contrib

        # 2. Dividend taxes
        div_tax = compute_annual_dividend_tax(
            portfolio_value=value,
            dividend_yield=portfolio.dividend_yield,
            qualified_dividend_share=portfolio.qualified_dividend_share,
            qualified_dividend_rate=tax_profile.combined_qualified_dividend_rate,
            ordinary_income_rate=tax_profile.combined_ordinary_rate,
        )
        value -= div_tax
        cumulative_dividend_tax += div_tax

        # 3. Realized gain taxes from turnover
        unrealized_gain = max(0.0, value - basis)
        realized_gain_tax = compute_annual_realized_gain_tax(
            unrealized_gain=unrealized_gain,
            turnover_realization_rate=portfolio.turnover_realization_rate,
            ltcg_rate=tax_profile.combined_ltcg_rate,
        )
        # When gains are realized and taxed, basis adjusts upward for the realized portion
        realized_amount = unrealized_gain * portfolio.turnover_realization_rate
        basis += realized_amount  # re-invested at new cost basis
        value -= realized_gain_tax
        cumulative_realized_gain_tax += realized_gain_tax

        # 4. Apply price appreciation (net of dividends already distributed)
        price_return = net_return - portfolio.dividend_yield
        value *= 1.0 + price_return

    # Terminal state
    unrealized_gain = max(0.0, value - basis)

    if liquidate:
        liquidation_tax = compute_terminal_liquidation_tax(
            ending_value=value,
            tax_basis=basis,
            ltcg_rate=tax_profile.combined_ltcg_rate,
        )
    else:
        liquidation_tax = 0.0

    return TaxableGrowthResult(
        ending_value_pre_liquidation=value,
        tax_basis=basis,
        unrealized_gain=unrealized_gain,
        cumulative_dividend_tax=cumulative_dividend_tax,
        cumulative_realized_gain_tax=cumulative_realized_gain_tax,
        terminal_liquidation_tax=liquidation_tax,
        ending_value_after_tax=value - liquidation_tax,
    )
