"""Tests for deterministic tradeoff analysis."""

import datetime

import pytest

from plan529lab.core.deterministic import run_deterministic
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseItem, EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule


def _base_config(
    qualified_use_probability: float | None = None,
    aqee: float = 100000.0,
    tax_free_assistance: float = 0.0,
    aotc_allocated: float = 0.0,
) -> ScenarioConfig:
    """Build a standard test scenario config."""
    return ScenarioConfig(
        tax_profile=InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        ),
        qtp_contributions=ContributionSchedule(
            items=[
                Contribution(date=datetime.date(2025, 1, 1), amount=10000, account_type="qtp"),
            ]
        ),
        taxable_contributions=ContributionSchedule(
            items=[
                Contribution(
                    date=datetime.date(2025, 1, 1), amount=10000, account_type="taxable"
                ),
            ]
        ),
        portfolio_assumptions=PortfolioAssumptions(
            annual_return=0.07,
            dividend_yield=0.015,
            qualified_dividend_share=0.95,
            turnover_realization_rate=0.05,
        ),
        education_schedule=EducationExpenseSchedule(
            items=[
                EducationExpenseItem(
                    date=datetime.date(2043, 9, 1),
                    qualified_expense=aqee,
                    tax_free_assistance=tax_free_assistance,
                    aotc_or_llc_allocated_expense=aotc_allocated,
                ),
            ]
        ),
        qtp_assumptions=QTPAssumptions(),
        scenario_policy=ScenarioPolicy(
            qualified_use_probability=qualified_use_probability,
        ),
        horizon_years=18,
    )


class TestFullyQualified:
    def test_529_wins(self) -> None:
        """With full qualified use, 529 should beat taxable due to tax-free growth."""
        config = _base_config(qualified_use_probability=1.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())

        assert result.delta > 0, "529 should win with fully qualified use"
        assert result.qtp_taxable_earnings == pytest.approx(0.0)
        assert result.qtp_additional_tax == pytest.approx(0.0)

    def test_no_probability_assumes_qualified(self) -> None:
        """Without probability set and high AQEE, assumes fully qualified."""
        config = _base_config()
        result = run_deterministic(config, NoIncomeTaxStateRule())

        assert result.delta > 0


class TestNonqualified:
    def test_fully_nonqualified_still_returns_basis(self) -> None:
        """Even fully nonqualified, basis comes back tax-free."""
        config = _base_config(qualified_use_probability=0.0, aqee=0.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())

        # QTP value should still be positive (basis is tax-free)
        assert result.qtp_after_tax_value > 0
        assert result.qtp_taxable_earnings > 0
        assert result.qtp_additional_tax > 0

    def test_nonqualified_worse_than_qualified(self) -> None:
        """Nonqualified outcome should be worse than qualified."""
        config_qual = _base_config(qualified_use_probability=1.0)
        config_nonqual = _base_config(qualified_use_probability=0.0, aqee=0.0)

        result_qual = run_deterministic(config_qual, NoIncomeTaxStateRule())
        result_nonqual = run_deterministic(config_nonqual, NoIncomeTaxStateRule())

        assert result_qual.qtp_after_tax_value > result_nonqual.qtp_after_tax_value


class TestBreakEven:
    def test_break_even_exists(self) -> None:
        """Break-even probability should exist when QTP_A != QTP_B."""
        config = _base_config(qualified_use_probability=0.5, aqee=0.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())

        assert result.break_even_qualified_use_probability is not None
        assert 0.0 <= result.break_even_qualified_use_probability <= 1.0

    def test_break_even_clipped_to_zero(self) -> None:
        """When even nonqualified 529 beats taxable, break-even is 0."""
        # With high tax drag on taxable and low earnings on 529,
        # the 529 can win even nonqualified
        config = _base_config(qualified_use_probability=0.0, aqee=0.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())

        if result.delta > 0:
            # 529 wins even nonqualified -> break-even should be 0
            assert result.break_even_qualified_use_probability == pytest.approx(0.0)

    def test_fully_qualified_beats_taxable(self) -> None:
        """At p=1.0 (fully qualified), 529 should win."""
        config = _base_config(qualified_use_probability=1.0, aqee=100000.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())
        assert result.delta > 0


class TestAOTCCoordination:
    def test_aotc_reduces_aqee(self) -> None:
        """AOTC allocation should reduce AQEE and increase taxable earnings."""
        config_no_aotc = _base_config(qualified_use_probability=1.0, aqee=30000.0)
        config_with_aotc = _base_config(
            qualified_use_probability=1.0, aqee=30000.0, aotc_allocated=4000.0
        )

        result_no = run_deterministic(config_no_aotc, NoIncomeTaxStateRule())
        result_with = run_deterministic(config_with_aotc, NoIncomeTaxStateRule())

        # With AOTC, effective AQEE is lower, so 529 benefit is slightly less
        assert result_with.qtp_aqee < result_no.qtp_aqee


class TestScholarship:
    def test_scholarship_reduces_aqee(self) -> None:
        """Tax-free assistance should reduce AQEE."""
        config_no_schol = _base_config(qualified_use_probability=1.0, aqee=30000.0)
        config_with_schol = _base_config(
            qualified_use_probability=1.0, aqee=30000.0, tax_free_assistance=10000.0
        )

        result_no = run_deterministic(config_no_schol, NoIncomeTaxStateRule())
        result_with = run_deterministic(config_with_schol, NoIncomeTaxStateRule())

        assert result_with.qtp_aqee < result_no.qtp_aqee


class TestDriverDecomposition:
    def test_drivers_populated(self) -> None:
        config = _base_config(qualified_use_probability=0.75, aqee=0.0)
        result = run_deterministic(config, NoIncomeTaxStateRule())

        assert result.drivers.federal_tax_free_growth_benefit > 0
        assert result.drivers.taxable_dividend_drag_cost > 0
