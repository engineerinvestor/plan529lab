"""Property-based tests using hypothesis."""

from hypothesis import given, settings
from hypothesis import strategies as st

from plan529lab.core.breakeven import compute_breakeven_probability
from plan529lab.tax.federal_qtp import (
    compute_additional_tax,
    compute_aqee,
    compute_taxable_earnings,
)
from plan529lab.tax.taxable_account import compute_terminal_liquidation_tax

# Reasonable financial ranges
rate = st.floats(min_value=0.0, max_value=1.0)
money = st.floats(min_value=0.0, max_value=1_000_000.0)
pos_money = st.floats(min_value=0.01, max_value=1_000_000.0)


class TestTaxableEarningsProperties:
    @given(earnings=money, aqee=money, distribution=pos_money)
    @settings(max_examples=200)
    def test_never_negative(
        self, earnings: float, aqee: float, distribution: float
    ) -> None:
        result = compute_taxable_earnings(earnings, aqee, distribution)
        assert result >= 0.0

    @given(earnings=money, aqee=money, distribution=pos_money)
    @settings(max_examples=200)
    def test_never_exceeds_earnings(
        self, earnings: float, aqee: float, distribution: float
    ) -> None:
        result = compute_taxable_earnings(earnings, aqee, distribution)
        assert result <= earnings + 1e-10  # small tolerance for floating point

    @given(earnings=money, distribution=pos_money)
    @settings(max_examples=100)
    def test_zero_aqee_means_all_earnings_taxable(
        self, earnings: float, distribution: float
    ) -> None:
        result = compute_taxable_earnings(earnings, 0.0, distribution)
        assert abs(result - earnings) < 1e-10


class TestAQEEProperties:
    @given(qualified=money, aid=money, aotc=money)
    @settings(max_examples=200)
    def test_never_negative(self, qualified: float, aid: float, aotc: float) -> None:
        result = compute_aqee(qualified, aid, aotc)
        assert result >= 0.0

    @given(qualified=money, aid=money, aotc=money)
    @settings(max_examples=200)
    def test_never_exceeds_qualified(
        self, qualified: float, aid: float, aotc: float
    ) -> None:
        result = compute_aqee(qualified, aid, aotc)
        assert result <= qualified + 1e-10


class TestAdditionalTaxProperties:
    @given(taxable_earnings=money, exception=money)
    @settings(max_examples=200)
    def test_never_negative(self, taxable_earnings: float, exception: float) -> None:
        result = compute_additional_tax(taxable_earnings, exception)
        assert result >= 0.0


class TestTerminalLiquidationProperties:
    @given(ending=money, basis=money, ltcg=rate)
    @settings(max_examples=200)
    def test_never_negative(
        self, ending: float, basis: float, ltcg: float
    ) -> None:
        result = compute_terminal_liquidation_tax(ending, basis, ltcg)
        assert result >= 0.0

    @given(ending=money, basis=money, ltcg=rate)
    @settings(max_examples=200)
    def test_never_exceeds_gain(
        self, ending: float, basis: float, ltcg: float
    ) -> None:
        result = compute_terminal_liquidation_tax(ending, basis, ltcg)
        gain = max(0.0, ending - basis)
        assert result <= gain + 1e-10


class TestBreakEvenProperties:
    @given(qtp_a=pos_money, qtp_b=money, taxable=money)
    @settings(max_examples=200)
    def test_in_range_or_none(
        self, qtp_a: float, qtp_b: float, taxable: float
    ) -> None:
        result = compute_breakeven_probability(qtp_a, qtp_b, taxable)
        if result is not None:
            assert 0.0 <= result <= 1.0
