"""Tests for account growth models."""

import datetime

import pytest

from plan529lab.core.growth import grow_qtp_account, grow_taxable_account
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.tax_profile import InvestorTaxProfile


def _lump_sum_schedule(amount: float, year: int, account_type: str) -> ContributionSchedule:
    return ContributionSchedule(
        items=[
            Contribution(
                date=datetime.date(year, 1, 1),
                amount=amount,
                account_type=account_type,
            )
        ]
    )


def _base_portfolio() -> PortfolioAssumptions:
    return PortfolioAssumptions(
        annual_return=0.07,
        dividend_yield=0.0,
        qualified_dividend_share=0.0,
        turnover_realization_rate=0.0,
    )


class TestGrowQTPAccount:
    def test_lump_sum_growth(self) -> None:
        """$10k at 7% for 10 years = 10000 * 1.07^10 ≈ 19671.51"""
        result = grow_qtp_account(
            contributions=_lump_sum_schedule(10000, 2025, "qtp"),
            portfolio=_base_portfolio(),
            qtp=QTPAssumptions(),
            horizon_years=10,
            start_year=2025,
        )
        assert result.ending_value == pytest.approx(10000 * 1.07**10, rel=1e-6)
        assert result.total_contributions == pytest.approx(10000.0)
        assert result.total_earnings == pytest.approx(result.ending_value - 10000.0)

    def test_with_fees(self) -> None:
        """Plan fees reduce net return."""
        result = grow_qtp_account(
            contributions=_lump_sum_schedule(10000, 2025, "qtp"),
            portfolio=_base_portfolio(),
            qtp=QTPAssumptions(plan_fee_drag=0.005),
            horizon_years=10,
            start_year=2025,
        )
        expected = 10000 * (1.07 - 0.005) ** 10
        assert result.ending_value == pytest.approx(expected, rel=1e-6)

    def test_multi_year_contributions(self) -> None:
        """$5k per year for 3 years at 7%."""
        schedule = ContributionSchedule(
            items=[
                Contribution(date=datetime.date(2025, 1, 1), amount=5000, account_type="qtp"),
                Contribution(date=datetime.date(2026, 1, 1), amount=5000, account_type="qtp"),
                Contribution(date=datetime.date(2027, 1, 1), amount=5000, account_type="qtp"),
            ]
        )
        result = grow_qtp_account(
            contributions=schedule,
            portfolio=_base_portfolio(),
            qtp=QTPAssumptions(),
            horizon_years=3,
            start_year=2025,
        )
        # Year 0: (0 + 5000) * 1.07 = 5350
        # Year 1: (5350 + 5000) * 1.07 = 11074.5
        # Year 2: (11074.5 + 5000) * 1.07 = 17199.715
        assert result.ending_value == pytest.approx(17199.715, rel=1e-4)
        assert result.total_contributions == pytest.approx(15000.0)

    def test_zero_horizon(self) -> None:
        result = grow_qtp_account(
            contributions=_lump_sum_schedule(10000, 2025, "qtp"),
            portfolio=_base_portfolio(),
            qtp=QTPAssumptions(),
            horizon_years=0,
            start_year=2025,
        )
        assert result.ending_value == 0.0
        assert result.total_contributions == 0.0


class TestGrowTaxableAccount:
    def test_no_tax_drag_matches_qtp(self) -> None:
        """With zero dividends and turnover, taxable should match QTP pre-liquidation."""
        portfolio = _base_portfolio()
        schedule = _lump_sum_schedule(10000, 2025, "taxable")
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )

        result = grow_taxable_account(
            contributions=schedule,
            portfolio=portfolio,
            tax_profile=profile,
            horizon_years=10,
            start_year=2025,
            liquidate=False,
        )

        expected_value = 10000 * 1.07**10
        assert result.ending_value_pre_liquidation == pytest.approx(expected_value, rel=1e-6)
        assert result.cumulative_dividend_tax == pytest.approx(0.0)
        assert result.cumulative_realized_gain_tax == pytest.approx(0.0)

    def test_dividends_create_drag(self) -> None:
        """Dividends should reduce ending value compared to no-dividend case."""
        schedule = _lump_sum_schedule(10000, 2025, "taxable")
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )
        portfolio_no_div = _base_portfolio()
        portfolio_with_div = PortfolioAssumptions(
            annual_return=0.07,
            dividend_yield=0.02,
            qualified_dividend_share=0.95,
            turnover_realization_rate=0.0,
        )

        no_div = grow_taxable_account(
            contributions=schedule,
            portfolio=portfolio_no_div,
            tax_profile=profile,
            horizon_years=10,
            start_year=2025,
            liquidate=False,
        )

        with_div = grow_taxable_account(
            contributions=schedule,
            portfolio=portfolio_with_div,
            tax_profile=profile,
            horizon_years=10,
            start_year=2025,
            liquidate=False,
        )

        assert with_div.ending_value_pre_liquidation < no_div.ending_value_pre_liquidation
        assert with_div.cumulative_dividend_tax > 0

    def test_terminal_liquidation(self) -> None:
        """Liquidation tax should reduce ending value."""
        schedule = _lump_sum_schedule(10000, 2025, "taxable")
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )

        result = grow_taxable_account(
            contributions=schedule,
            portfolio=_base_portfolio(),
            tax_profile=profile,
            horizon_years=10,
            start_year=2025,
            liquidate=True,
        )

        assert result.terminal_liquidation_tax > 0
        assert result.ending_value_after_tax < result.ending_value_pre_liquidation

    def test_after_tax_never_exceeds_pre_tax(self) -> None:
        schedule = _lump_sum_schedule(10000, 2025, "taxable")
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )
        portfolio = PortfolioAssumptions(
            annual_return=0.07,
            dividend_yield=0.015,
            qualified_dividend_share=0.95,
            turnover_realization_rate=0.05,
        )

        result = grow_taxable_account(
            contributions=schedule,
            portfolio=portfolio,
            tax_profile=profile,
            horizon_years=18,
            start_year=2025,
            liquidate=True,
        )

        assert result.ending_value_after_tax <= result.ending_value_pre_liquidation
