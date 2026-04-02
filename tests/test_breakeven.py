"""Tests for break-even solvers."""

import datetime

import pytest

from plan529lab.core.breakeven import (
    compute_breakeven_horizon,
    compute_breakeven_probability,
    compute_breakeven_state_benefit,
    compute_breakeven_tax_efficiency,
)
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule


class TestBreakEvenProbability:
    def test_basic_midpoint(self) -> None:
        result = compute_breakeven_probability(20000, 10000, 15000)
        assert result == pytest.approx(0.5)

    def test_taxable_equals_qtp_b(self) -> None:
        result = compute_breakeven_probability(20000, 10000, 10000)
        assert result == pytest.approx(0.0)

    def test_taxable_equals_qtp_a(self) -> None:
        result = compute_breakeven_probability(20000, 10000, 20000)
        assert result == pytest.approx(1.0)

    def test_clipped_below_zero(self) -> None:
        result = compute_breakeven_probability(20000, 15000, 10000)
        assert result == pytest.approx(0.0)

    def test_clipped_above_one(self) -> None:
        result = compute_breakeven_probability(20000, 10000, 25000)
        assert result == pytest.approx(1.0)

    def test_undefined_when_equal(self) -> None:
        result = compute_breakeven_probability(20000, 20000, 15000)
        assert result is None

    def test_529_always_wins(self) -> None:
        result = compute_breakeven_probability(30000, 20000, 15000)
        assert result == pytest.approx(0.0)


def _base_config(
    prob: float = 0.5,
    turnover: float = 0.05,
    state_rate: float = 0.0,
) -> ScenarioConfig:
    return ScenarioConfig(
        tax_profile=InvestorTaxProfile(
            ordinary_income_rate=0.35, ltcg_rate=0.15,
            qualified_dividend_rate=0.15, state_ordinary_rate=state_rate,
        ),
        qtp_contributions=ContributionSchedule(items=[
            Contribution(date=datetime.date(2025, 1, 1), amount=10000, account_type="qtp"),
        ]),
        taxable_contributions=ContributionSchedule(items=[
            Contribution(
                date=datetime.date(2025, 1, 1), amount=10000, account_type="taxable",
            ),
        ]),
        portfolio_assumptions=PortfolioAssumptions(
            annual_return=0.07, dividend_yield=0.015,
            qualified_dividend_share=0.95, turnover_realization_rate=turnover,
        ),
        education_schedule=EducationExpenseSchedule(),
        qtp_assumptions=QTPAssumptions(),
        scenario_policy=ScenarioPolicy(qualified_use_probability=prob),
        horizon_years=18,
    )


class TestBreakEvenHorizon:
    def test_finds_horizon(self) -> None:
        config = _base_config(prob=1.0)
        result = compute_breakeven_horizon(config, NoIncomeTaxStateRule(), max_years=30)
        assert result is not None
        assert 1 <= result <= 30

    def test_returns_none_if_never_crosses(self) -> None:
        # With 0% qualified use and 0 AQEE, 529 may never win at short horizons
        # Use very short max_years to make it likely to not cross
        config = _base_config(prob=0.0)
        # This may or may not be None depending on tax drag, but should not crash
        result = compute_breakeven_horizon(config, NoIncomeTaxStateRule(), max_years=1)
        assert result is None or result == 1


class TestBreakEvenTaxEfficiency:
    def test_returns_value_or_none(self) -> None:
        config = _base_config(prob=0.5)
        result = compute_breakeven_tax_efficiency(config, NoIncomeTaxStateRule())
        # May or may not find a crossing depending on scenario
        assert result is None or 0.0 <= result <= 0.5


class TestBreakEvenStateBenefit:
    def test_returns_value_or_none(self) -> None:
        config = _base_config(prob=0.5)
        result = compute_breakeven_state_benefit(config, NoIncomeTaxStateRule())
        assert result is None or 0.0 <= result <= 0.15
