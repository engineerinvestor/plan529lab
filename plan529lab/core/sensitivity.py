"""One-way and two-way deterministic parameter sweeps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from plan529lab.core.deterministic import run_deterministic

if TYPE_CHECKING:
    from plan529lab.models.config import ScenarioConfig
    from plan529lab.tax.state_base import StateRule

# Maps short param names to (nested_path, field_name) for config mutation
_PARAM_MAP: dict[str, tuple[str, str]] = {
    "annual_return": ("portfolio_assumptions", "annual_return"),
    "dividend_yield": ("portfolio_assumptions", "dividend_yield"),
    "turnover_realization_rate": ("portfolio_assumptions", "turnover_realization_rate"),
    "ordinary_income_rate": ("tax_profile", "ordinary_income_rate"),
    "ltcg_rate": ("tax_profile", "ltcg_rate"),
    "qualified_dividend_rate": ("tax_profile", "qualified_dividend_rate"),
    "state_ordinary_rate": ("tax_profile", "state_ordinary_rate"),
    "qualified_use_probability": ("scenario_policy", "qualified_use_probability"),
    "horizon_years": ("", "horizon_years"),
}

SWEEPABLE_PARAMS = list(_PARAM_MAP.keys())


class SensitivityResult(BaseModel, frozen=True):
    """Result of a one-way sensitivity sweep."""

    param_name: str
    param_values: list[float]
    deltas: list[float]
    break_evens: list[float | None]


class TwoWaySensitivityResult(BaseModel, frozen=True):
    """Result of a two-way sensitivity sweep."""

    param_x_name: str
    param_y_name: str
    param_x_values: list[float]
    param_y_values: list[float]
    delta_grid: list[list[float]]


def _set_nested_param(
    config: ScenarioConfig, param_name: str, value: float
) -> ScenarioConfig:
    """Create a new ScenarioConfig with one parameter changed."""
    if param_name not in _PARAM_MAP:
        available = sorted(_PARAM_MAP.keys())
        msg = f"Unknown sweep parameter '{param_name}'. Available: {available}"
        raise ValueError(msg)

    parent_attr, field_name = _PARAM_MAP[param_name]

    if parent_attr == "":
        # Top-level field (e.g., horizon_years)
        return config.model_copy(update={field_name: int(value)})

    parent_obj = getattr(config, parent_attr)
    new_parent = parent_obj.model_copy(update={field_name: value})
    return config.model_copy(update={parent_attr: new_parent})


def run_one_way_sensitivity(
    config: ScenarioConfig,
    state_rule: StateRule,
    param: str,
    values: list[float],
) -> SensitivityResult:
    """Run a one-way sensitivity sweep over a single parameter."""
    deltas: list[float] = []
    break_evens: list[float | None] = []

    for v in values:
        modified = _set_nested_param(config, param, v)
        result = run_deterministic(modified, state_rule)
        deltas.append(result.delta)
        break_evens.append(result.break_even_qualified_use_probability)

    return SensitivityResult(
        param_name=param,
        param_values=values,
        deltas=deltas,
        break_evens=break_evens,
    )


def run_two_way_sensitivity(
    config: ScenarioConfig,
    state_rule: StateRule,
    param_x: str,
    values_x: list[float],
    param_y: str,
    values_y: list[float],
) -> TwoWaySensitivityResult:
    """Run a two-way sensitivity sweep over two parameters."""
    delta_grid: list[list[float]] = []

    for vy in values_y:
        row: list[float] = []
        config_y = _set_nested_param(config, param_y, vy)
        for vx in values_x:
            config_xy = _set_nested_param(config_y, param_x, vx)
            result = run_deterministic(config_xy, state_rule)
            row.append(result.delta)
        delta_grid.append(row)

    return TwoWaySensitivityResult(
        param_x_name=param_x,
        param_y_name=param_y,
        param_x_values=values_x,
        param_y_values=values_y,
        delta_grid=delta_grid,
    )
