"""Tests for sensitivity analysis."""

import datetime

import pytest

from plan529lab.api import run_sensitivity, run_two_way_sensitivity
from plan529lab.core.sensitivity import SWEEPABLE_PARAMS, _set_nested_param
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile


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


class TestOneWaySensitivity:
    def test_correct_count(self) -> None:
        values = [0.04, 0.06, 0.08, 0.10]
        result = run_sensitivity(_base_config(), "annual_return", values)
        assert len(result.deltas) == 4
        assert len(result.param_values) == 4
        assert result.param_name == "annual_return"

    def test_monotonic_annual_return(self) -> None:
        """Higher returns should increase delta (more tax-free growth benefit)."""
        values = [0.03, 0.05, 0.07, 0.09, 0.11]
        result = run_sensitivity(_base_config(), "annual_return", values)
        for i in range(len(result.deltas) - 1):
            assert result.deltas[i] <= result.deltas[i + 1] + 1.0  # allow small float noise

    def test_single_value(self) -> None:
        result = run_sensitivity(_base_config(), "annual_return", [0.07])
        assert len(result.deltas) == 1

    def test_invalid_param_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown sweep parameter"):
            run_sensitivity(_base_config(), "nonexistent_param", [0.0])

    def test_horizon_years_sweep(self) -> None:
        values = [5.0, 10.0, 15.0, 20.0]
        result = run_sensitivity(_base_config(), "horizon_years", values)
        assert len(result.deltas) == 4


class TestTwoWaySensitivity:
    def test_grid_shape(self) -> None:
        x_vals = [0.04, 0.07, 0.10]
        y_vals = [0.0, 0.5, 1.0]
        result = run_two_way_sensitivity(
            _base_config(),
            "annual_return", x_vals,
            "qualified_use_probability", y_vals,
        )
        assert len(result.delta_grid) == 3  # rows = y values
        assert len(result.delta_grid[0]) == 3  # cols = x values
        assert result.param_x_name == "annual_return"
        assert result.param_y_name == "qualified_use_probability"


class TestSetNestedParam:
    def test_portfolio_param(self) -> None:
        config = _base_config()
        modified = _set_nested_param(config, "annual_return", 0.10)
        assert modified.portfolio_assumptions.annual_return == 0.10
        assert config.portfolio_assumptions.annual_return == 0.07  # original unchanged

    def test_top_level_param(self) -> None:
        config = _base_config()
        modified = _set_nested_param(config, "horizon_years", 25.0)
        assert modified.horizon_years == 25

    def test_all_params_work(self) -> None:
        config = _base_config()
        for param in SWEEPABLE_PARAMS:
            _set_nested_param(config, param, 0.1)  # should not raise
