"""High-level TradeoffEngine class (OOP wrapper per SPEC Section 17.2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plan529lab.core.deterministic import run_deterministic
from plan529lab.core.monte_carlo import run_monte_carlo as _run_mc
from plan529lab.core.sensitivity import (
    run_one_way_sensitivity as _run_one_way,
)
from plan529lab.core.sensitivity import (
    run_two_way_sensitivity as _run_two_way,
)

if TYPE_CHECKING:
    from plan529lab.core.sensitivity import SensitivityResult, TwoWaySensitivityResult
    from plan529lab.models.config import ScenarioConfig
    from plan529lab.models.monte_carlo import MonteCarloConfig, MonteCarloResult
    from plan529lab.models.results import TradeoffResult
    from plan529lab.tax.state_base import StateRule


class TradeoffEngine:
    """OOP interface for running tradeoff analyses.

    Pre-binds a state rule, then runs deterministic, Monte Carlo,
    or sensitivity analyses via method calls.
    """

    def __init__(self, state_rule: StateRule) -> None:
        self.state_rule = state_rule

    def run(self, config: ScenarioConfig) -> TradeoffResult:
        """Run a deterministic tradeoff analysis."""
        return run_deterministic(config, self.state_rule)

    def run_monte_carlo(
        self, config: ScenarioConfig, mc_config: MonteCarloConfig
    ) -> MonteCarloResult:
        """Run a Monte Carlo simulation."""
        return _run_mc(config, mc_config, self.state_rule)

    def run_sensitivity(
        self, config: ScenarioConfig, param: str, values: list[float]
    ) -> SensitivityResult:
        """Run a one-way sensitivity sweep."""
        return _run_one_way(config, self.state_rule, param, values)

    def run_two_way_sensitivity(
        self,
        config: ScenarioConfig,
        param_x: str,
        values_x: list[float],
        param_y: str,
        values_y: list[float],
    ) -> TwoWaySensitivityResult:
        """Run a two-way sensitivity sweep."""
        return _run_two_way(
            config, self.state_rule, param_x, values_x, param_y, values_y,
        )
