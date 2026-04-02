"""Smoke tests for plotting functions."""

import datetime

import matplotlib
import matplotlib.pyplot as plt
import pytest

from plan529lab.api import run_monte_carlo, run_sensitivity, run_two_way_sensitivity
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.monte_carlo import MonteCarloConfig, StochasticAssumptions
from plan529lab.models.results import DriverDecomposition, TradeoffResult
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.outputs.plots import (
    plot_delta_vs_probability,
    plot_delta_vs_years,
    plot_heatmap,
    plot_mc_histogram,
    plot_waterfall,
)

matplotlib.use("Agg")  # non-interactive backend for tests


def _base_config() -> ScenarioConfig:
    return ScenarioConfig(
        tax_profile=InvestorTaxProfile(
            ordinary_income_rate=0.35, ltcg_rate=0.15, qualified_dividend_rate=0.15,
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


@pytest.fixture(autouse=True)
def _close_plots() -> None:  # type: ignore[misc]
    yield
    plt.close("all")


class TestPlotDeltaVsProbability:
    def test_returns_figure(self) -> None:
        result = run_sensitivity(
            _base_config(), "qualified_use_probability", [0.0, 0.25, 0.5, 0.75, 1.0],
        )
        fig = plot_delta_vs_probability(result)
        assert isinstance(fig, matplotlib.figure.Figure)


class TestPlotDeltaVsYears:
    def test_returns_figure(self) -> None:
        result = run_sensitivity(
            _base_config(), "horizon_years", [5.0, 10.0, 15.0, 20.0],
        )
        fig = plot_delta_vs_years(result)
        assert isinstance(fig, matplotlib.figure.Figure)


class TestPlotHeatmap:
    def test_returns_figure(self) -> None:
        result = run_two_way_sensitivity(
            _base_config(),
            "annual_return", [0.04, 0.07, 0.10],
            "qualified_use_probability", [0.0, 0.5, 1.0],
        )
        fig = plot_heatmap(result)
        assert isinstance(fig, matplotlib.figure.Figure)


class TestPlotWaterfall:
    def test_returns_figure(self) -> None:
        result = TradeoffResult(
            qtp_after_tax_value=50000, taxable_after_tax_value=45000, delta=5000,
            qtp_ending_value=50000, qtp_basis=30000, qtp_earnings=20000,
            qtp_aqee=50000, qtp_taxable_earnings=0, qtp_income_tax=0,
            qtp_additional_tax=0, qtp_state_recapture_tax=0, qtp_state_benefit=0,
            taxable_ending_value_pre_liquidation=48000, taxable_basis=30000,
            taxable_unrealized_gain=18000, taxable_dividend_tax_drag=1500,
            taxable_realized_gain_tax_drag=800, taxable_terminal_liquidation_tax=700,
            drivers=DriverDecomposition(
                federal_tax_free_growth_benefit=3000,
                taxable_dividend_drag_cost=1500,
                taxable_realization_drag_cost=800,
            ),
        )
        fig = plot_waterfall(result)
        assert isinstance(fig, matplotlib.figure.Figure)


class TestPlotMCHistogram:
    def test_returns_figure(self) -> None:
        mc_config = MonteCarloConfig(
            n_paths=100, seed=42,
            stochastic=StochasticAssumptions(return_std=0.15),
        )
        mc_result = run_monte_carlo(_base_config(), mc_config)
        fig = plot_mc_histogram(mc_result)
        assert isinstance(fig, matplotlib.figure.Figure)
