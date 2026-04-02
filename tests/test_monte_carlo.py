"""Tests for Monte Carlo simulation."""

import datetime

import pytest

from plan529lab.api import analyze_tradeoff, run_monte_carlo
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.monte_carlo import MonteCarloConfig, StochasticAssumptions
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule


def _base_config() -> ScenarioConfig:
    return ScenarioConfig(
        tax_profile=InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
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
            qualified_dividend_share=0.95, turnover_realization_rate=0.05,
        ),
        education_schedule=EducationExpenseSchedule(),
        qtp_assumptions=QTPAssumptions(),
        scenario_policy=ScenarioPolicy(qualified_use_probability=0.75),
        horizon_years=18,
    )


class TestMonteCarloBasic:
    def test_n_paths_matches(self) -> None:
        mc_config = MonteCarloConfig(n_paths=100, seed=42)
        result = run_monte_carlo(_base_config(), mc_config)
        assert result.n_paths == 100
        assert len(result.deltas) == 100

    def test_seed_reproducibility(self) -> None:
        mc_config = MonteCarloConfig(
            n_paths=50, seed=42,
            stochastic=StochasticAssumptions(return_std=0.15),
        )
        result1 = run_monte_carlo(_base_config(), mc_config)
        result2 = run_monte_carlo(_base_config(), mc_config)
        assert result1.deltas == result2.deltas
        assert result1.mean_delta == result2.mean_delta

    def test_prob_qtp_wins_in_range(self) -> None:
        mc_config = MonteCarloConfig(
            n_paths=100, seed=42,
            stochastic=StochasticAssumptions(return_std=0.15),
        )
        result = run_monte_carlo(_base_config(), mc_config)
        assert 0.0 <= result.prob_qtp_wins <= 1.0


class TestZeroVarianceBridge:
    def test_matches_deterministic(self) -> None:
        """With zero stochastic variance, MC should exactly match deterministic."""
        config = _base_config()
        mc_config = MonteCarloConfig(
            n_paths=5, seed=42,
            stochastic=StochasticAssumptions(),  # all stds = 0
        )
        det_result = analyze_tradeoff(config, NoIncomeTaxStateRule())
        mc_result = run_monte_carlo(config, mc_config, NoIncomeTaxStateRule())

        # All paths should produce the same delta as deterministic
        for d in mc_result.deltas:
            assert d == pytest.approx(det_result.delta, rel=1e-10)

        assert mc_result.mean_delta == pytest.approx(det_result.delta, rel=1e-10)
        assert mc_result.std_delta == pytest.approx(0.0, abs=1e-10)


class TestStochasticReturns:
    def test_variance_increases_spread(self) -> None:
        """Higher return volatility should increase the spread of deltas."""
        config = _base_config()
        mc_low = MonteCarloConfig(
            n_paths=500, seed=42,
            stochastic=StochasticAssumptions(return_std=0.05),
        )
        mc_high = MonteCarloConfig(
            n_paths=500, seed=42,
            stochastic=StochasticAssumptions(return_std=0.20),
        )
        result_low = run_monte_carlo(config, mc_low)
        result_high = run_monte_carlo(config, mc_high)

        assert result_high.std_delta > result_low.std_delta

    def test_percentiles_ordered(self) -> None:
        mc_config = MonteCarloConfig(
            n_paths=200, seed=42,
            stochastic=StochasticAssumptions(return_std=0.15),
        )
        result = run_monte_carlo(_base_config(), mc_config)
        p5 = result.percentile_values["5.0"]
        p50 = result.percentile_values["50.0"]
        p95 = result.percentile_values["95.0"]
        assert p5 <= p50 <= p95


class TestPublicAPI:
    def test_api_run_monte_carlo(self) -> None:
        mc_config = MonteCarloConfig(n_paths=10, seed=1)
        result = run_monte_carlo(_base_config(), mc_config)
        assert result.n_paths == 10
        assert result.seed == 1
