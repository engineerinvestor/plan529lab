"""Top-level public API for plan529lab."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plan529lab.core.deterministic import run_deterministic
from plan529lab.core.monte_carlo import run_monte_carlo as _run_monte_carlo
from plan529lab.core.sensitivity import run_one_way_sensitivity as _run_one_way
from plan529lab.core.sensitivity import run_two_way_sensitivity as _run_two_way
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule

if TYPE_CHECKING:
    from plan529lab.core.sensitivity import SensitivityResult, TwoWaySensitivityResult
    from plan529lab.models.config import ScenarioConfig
    from plan529lab.models.monte_carlo import MonteCarloConfig, MonteCarloResult
    from plan529lab.models.results import TradeoffResult
    from plan529lab.tax.state_base import StateRule


def analyze_tradeoff(
    config: ScenarioConfig,
    state_rule: StateRule | None = None,
) -> TradeoffResult:
    """Run a deterministic 529 vs taxable tradeoff analysis.

    Args:
        config: Complete scenario configuration.
        state_rule: State-specific tax rule plugin. Defaults to NoIncomeTaxStateRule.

    Returns:
        TradeoffResult with after-tax outcomes, delta, break-even, and drivers.
    """
    if state_rule is None:
        state_rule = NoIncomeTaxStateRule()
    return run_deterministic(config, state_rule)


def run_monte_carlo(
    config: ScenarioConfig,
    mc_config: MonteCarloConfig,
    state_rule: StateRule | None = None,
) -> MonteCarloResult:
    """Run a Monte Carlo simulation of the 529 vs taxable tradeoff.

    Args:
        config: Base scenario configuration.
        mc_config: Monte Carlo simulation parameters.
        state_rule: State-specific tax rule plugin. Defaults to NoIncomeTaxStateRule.

    Returns:
        MonteCarloResult with delta distribution statistics.
    """
    if state_rule is None:
        state_rule = NoIncomeTaxStateRule()
    return _run_monte_carlo(config, mc_config, state_rule)


def run_sensitivity(
    config: ScenarioConfig,
    param: str,
    values: list[float],
    state_rule: StateRule | None = None,
) -> SensitivityResult:
    """Run a one-way sensitivity sweep over a single parameter.

    Args:
        config: Base scenario configuration.
        param: Parameter name to sweep (e.g., 'annual_return').
        values: List of values to test.
        state_rule: State-specific tax rule plugin. Defaults to NoIncomeTaxStateRule.
    """
    if state_rule is None:
        state_rule = NoIncomeTaxStateRule()
    return _run_one_way(config, state_rule, param, values)


def run_two_way_sensitivity(
    config: ScenarioConfig,
    param_x: str,
    values_x: list[float],
    param_y: str,
    values_y: list[float],
    state_rule: StateRule | None = None,
) -> TwoWaySensitivityResult:
    """Run a two-way sensitivity sweep over two parameters.

    Args:
        config: Base scenario configuration.
        param_x: First parameter name.
        values_x: Values for first parameter.
        param_y: Second parameter name.
        values_y: Values for second parameter.
        state_rule: State-specific tax rule plugin. Defaults to NoIncomeTaxStateRule.
    """
    if state_rule is None:
        state_rule = NoIncomeTaxStateRule()
    return _run_two_way(config, state_rule, param_x, values_x, param_y, values_y)
