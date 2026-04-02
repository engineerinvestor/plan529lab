"""Tests for tax computation modules."""

import pytest

from plan529lab.tax.credits_coordination import compute_aotc_exception_amount
from plan529lab.tax.federal_qtp import (
    compute_additional_tax,
    compute_aqee,
    compute_qtp_after_tax,
    compute_taxable_earnings,
)
from plan529lab.tax.taxable_account import (
    compute_annual_dividend_tax,
    compute_annual_realized_gain_tax,
    compute_terminal_liquidation_tax,
)


class TestComputeAQEE:
    def test_basic(self) -> None:
        assert compute_aqee(30000, 5000, 4000) == pytest.approx(21000.0)

    def test_no_adjustments(self) -> None:
        assert compute_aqee(30000, 0, 0) == pytest.approx(30000.0)

    def test_floors_at_zero(self) -> None:
        assert compute_aqee(5000, 10000, 0) == 0.0

    def test_all_adjustments_exceed(self) -> None:
        assert compute_aqee(10000, 6000, 6000) == 0.0


class TestComputeTaxableEarnings:
    def test_fully_qualified(self) -> None:
        # AQEE covers the full distribution
        result = compute_taxable_earnings(earnings=5000, aqee=25000, distribution=25000)
        assert result == pytest.approx(0.0)

    def test_aqee_exceeds_distribution(self) -> None:
        result = compute_taxable_earnings(earnings=5000, aqee=30000, distribution=25000)
        assert result == pytest.approx(0.0)

    def test_partially_qualified(self) -> None:
        # E=5000, Q=21000, D=25000
        # Taxable = 5000 * (1 - 21000/25000) = 5000 * 0.16 = 800
        result = compute_taxable_earnings(earnings=5000, aqee=21000, distribution=25000)
        assert result == pytest.approx(800.0)

    def test_fully_nonqualified(self) -> None:
        # No AQEE at all
        result = compute_taxable_earnings(earnings=5000, aqee=0, distribution=25000)
        assert result == pytest.approx(5000.0)

    def test_zero_distribution(self) -> None:
        result = compute_taxable_earnings(earnings=0, aqee=0, distribution=0)
        assert result == 0.0

    def test_never_negative(self) -> None:
        # Even with weird inputs, should never go negative
        result = compute_taxable_earnings(earnings=100, aqee=50, distribution=200)
        assert result >= 0.0

    def test_never_exceeds_earnings(self) -> None:
        result = compute_taxable_earnings(earnings=5000, aqee=0, distribution=25000)
        assert result <= 5000.0


class TestComputeAdditionalTax:
    def test_basic(self) -> None:
        # 10% of 800
        assert compute_additional_tax(800) == pytest.approx(80.0)

    def test_with_exception(self) -> None:
        # 10% of (800 - 200) = 60
        assert compute_additional_tax(800, exception_amount=200) == pytest.approx(60.0)

    def test_exception_exceeds_taxable(self) -> None:
        assert compute_additional_tax(800, exception_amount=1000) == pytest.approx(0.0)

    def test_zero_taxable(self) -> None:
        assert compute_additional_tax(0) == 0.0

    def test_custom_rate(self) -> None:
        assert compute_additional_tax(1000, rate=0.05) == pytest.approx(50.0)


class TestComputeQTPAfterTax:
    def test_fully_qualified(self) -> None:
        # No taxable earnings -> after-tax == distribution
        result = compute_qtp_after_tax(
            distribution=25000,
            taxable_earnings=0,
            ordinary_rate=0.35,
            additional_tax=0,
        )
        assert result == pytest.approx(25000.0)

    def test_nonqualified_with_penalty(self) -> None:
        # D=25000, TE=800, T_ord=0.35, AT=80
        # After-tax = 25000 - 800*0.35 - 80 = 25000 - 280 - 80 = 24640
        result = compute_qtp_after_tax(
            distribution=25000,
            taxable_earnings=800,
            ordinary_rate=0.35,
            additional_tax=80,
        )
        assert result == pytest.approx(24640.0)

    def test_with_state_effects(self) -> None:
        result = compute_qtp_after_tax(
            distribution=25000,
            taxable_earnings=0,
            ordinary_rate=0.35,
            additional_tax=0,
            state_recapture=500,
            state_benefit=1000,
        )
        assert result == pytest.approx(25500.0)


class TestAnnualDividendTax:
    def test_mixed_dividends(self) -> None:
        # $100k portfolio, 1.5% yield, 95% qualified
        # Total div = 1500
        # Qualified = 1425 * 0.15 = 213.75
        # Ordinary = 75 * 0.35 = 26.25
        # Total = 240.0
        result = compute_annual_dividend_tax(
            portfolio_value=100000,
            dividend_yield=0.015,
            qualified_dividend_share=0.95,
            qualified_dividend_rate=0.15,
            ordinary_income_rate=0.35,
        )
        assert result == pytest.approx(240.0)

    def test_zero_yield(self) -> None:
        result = compute_annual_dividend_tax(100000, 0.0, 0.95, 0.15, 0.35)
        assert result == 0.0


class TestAnnualRealizedGainTax:
    def test_basic(self) -> None:
        # $20k unrealized gain, 5% turnover, 15% LTCG
        # Realized = 1000, Tax = 150
        result = compute_annual_realized_gain_tax(20000, 0.05, 0.15)
        assert result == pytest.approx(150.0)

    def test_no_gain(self) -> None:
        result = compute_annual_realized_gain_tax(0, 0.05, 0.15)
        assert result == 0.0

    def test_negative_gain_ignored(self) -> None:
        result = compute_annual_realized_gain_tax(-5000, 0.05, 0.15)
        assert result == 0.0


class TestTerminalLiquidationTax:
    def test_basic(self) -> None:
        # $50k value, $30k basis, 15% LTCG -> tax = $3000
        result = compute_terminal_liquidation_tax(50000, 30000, 0.15)
        assert result == pytest.approx(3000.0)

    def test_no_gain(self) -> None:
        result = compute_terminal_liquidation_tax(30000, 30000, 0.15)
        assert result == 0.0

    def test_loss(self) -> None:
        result = compute_terminal_liquidation_tax(25000, 30000, 0.15)
        assert result == 0.0


class TestAOTCExceptionAmount:
    def test_basic(self) -> None:
        # $4000 AOTC allocated, E=5000, D=25000
        # earnings_ratio = 5000/25000 = 0.2
        # exception = 4000 * 0.2 = 800
        result = compute_aotc_exception_amount(4000, 5000, 25000)
        assert result == pytest.approx(800.0)

    def test_zero_distribution(self) -> None:
        result = compute_aotc_exception_amount(4000, 5000, 0)
        assert result == 0.0
