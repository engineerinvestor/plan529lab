"""Tests for Roth rollover estimation."""

import pytest

from plan529lab.tax.roth_rollover import estimate_roth_rollover


class TestRothRolloverEligibility:
    def test_eligible_basic(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=18,
        )
        assert result.eligible is True
        assert result.amount_eligible == pytest.approx(30000.0)
        assert result.residual_balance == pytest.approx(20000.0)

    def test_ineligible_too_young(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=10,
        )
        assert result.eligible is False
        assert result.amount_eligible == 0.0
        assert "at least 15 years" in result.warnings[0]

    def test_exactly_15_years(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=15,
        )
        assert result.eligible is True

    def test_lookback_exclusion(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=18,
            contributions_within_lookback=10000,
        )
        # Eligible basis = 30000 - 10000 = 20000
        assert result.amount_eligible == pytest.approx(20000.0)
        assert result.amount_ineligible_recent == pytest.approx(10000.0)
        assert any("lookback" in w for w in result.warnings)

    def test_lifetime_cap(self) -> None:
        result = estimate_roth_rollover(
            account_balance=100000,
            total_contributions=80000,
            account_age_years=20,
        )
        # Capped at $35,000 lifetime
        assert result.amount_eligible == pytest.approx(35000.0)

    def test_lifetime_cap_partially_used(self) -> None:
        result = estimate_roth_rollover(
            account_balance=100000,
            total_contributions=80000,
            account_age_years=20,
            prior_rollovers=20000,
        )
        # Cap remaining = 35000 - 20000 = 15000
        assert result.amount_eligible == pytest.approx(15000.0)
        assert result.lifetime_cap_remaining == pytest.approx(15000.0)

    def test_lifetime_cap_exhausted(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=18,
            prior_rollovers=35000,
        )
        assert result.eligible is False
        assert result.amount_eligible == 0.0
        assert "exhausted" in result.warnings[0]


class TestRothRolloverYears:
    def test_years_to_complete(self) -> None:
        result = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=18,
        )
        # $30k eligible at $7k/year = ceil(30000/7000) = 5 years
        assert result.years_to_complete == 5

    def test_small_amount(self) -> None:
        result = estimate_roth_rollover(
            account_balance=10000,
            total_contributions=5000,
            account_age_years=18,
        )
        # $5k at $7k/year = 1 year
        assert result.years_to_complete == 1

    def test_balance_less_than_contributions(self) -> None:
        """If balance < contributions (e.g., losses), eligible is limited by balance."""
        result = estimate_roth_rollover(
            account_balance=20000,
            total_contributions=30000,
            account_age_years=18,
        )
        assert result.amount_eligible == pytest.approx(20000.0)
