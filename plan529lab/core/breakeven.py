"""Break-even solvers for qualified-use probability, horizon, and tax efficiency."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plan529lab.core.deterministic import run_deterministic
from plan529lab.core.sensitivity import _set_nested_param

if TYPE_CHECKING:
    from plan529lab.models.config import ScenarioConfig
    from plan529lab.tax.state_base import StateRule


def compute_breakeven_probability(
    qtp_qualified_value: float,
    qtp_nonqualified_value: float,
    taxable_value: float,
) -> float | None:
    """Compute the break-even probability of qualified use.

    Solves: p* * QTP_A + (1 - p*) * QTP_B = Taxable
    Thus:   p* = (Taxable - QTP_B) / (QTP_A - QTP_B)

    Returns None if QTP_A == QTP_B (no distinct states).
    Result is clipped to [0, 1].
    """
    denominator = qtp_qualified_value - qtp_nonqualified_value
    if abs(denominator) < 1e-10:
        return None
    p_star = (taxable_value - qtp_nonqualified_value) / denominator
    return max(0.0, min(1.0, p_star))


def compute_breakeven_horizon(
    config: ScenarioConfig,
    state_rule: StateRule,
    max_years: int = 30,
) -> int | None:
    """Find the minimum horizon (years) where the 529 delta crosses zero.

    Scans from 1 to max_years. Returns the first year where delta >= 0,
    or None if delta never reaches zero within the range.
    """
    for years in range(1, max_years + 1):
        modified = _set_nested_param(config, "horizon_years", float(years))
        result = run_deterministic(modified, state_rule)
        if result.delta >= 0:
            return years
    return None


def compute_breakeven_tax_efficiency(
    config: ScenarioConfig,
    state_rule: StateRule,
    low: float = 0.0,
    high: float = 0.5,
    tolerance: float = 0.001,
) -> float | None:
    """Find the turnover_realization_rate where 529 delta crosses zero.

    Uses bisection search. Returns None if delta doesn't cross zero
    within the [low, high] range.
    """
    return _bisect_param(
        config, state_rule, "turnover_realization_rate", low, high, tolerance,
    )


def compute_breakeven_state_benefit(
    config: ScenarioConfig,
    state_rule: StateRule,
    low: float = 0.0,
    high: float = 0.15,
    tolerance: float = 0.001,
) -> float | None:
    """Find the state_ordinary_rate where 529 delta crosses zero.

    Uses bisection search. Returns None if delta doesn't cross zero
    within the [low, high] range.
    """
    return _bisect_param(
        config, state_rule, "state_ordinary_rate", low, high, tolerance,
    )


def _bisect_param(
    config: ScenarioConfig,
    state_rule: StateRule,
    param: str,
    low: float,
    high: float,
    tolerance: float,
) -> float | None:
    """Bisection search for the parameter value where delta = 0."""
    config_low = _set_nested_param(config, param, low)
    config_high = _set_nested_param(config, param, high)
    delta_low = run_deterministic(config_low, state_rule).delta
    delta_high = run_deterministic(config_high, state_rule).delta

    # Check that delta changes sign
    if delta_low * delta_high > 0:
        return None

    for _ in range(50):  # max iterations
        mid = (low + high) / 2.0
        if high - low < tolerance:
            return mid
        config_mid = _set_nested_param(config, param, mid)
        delta_mid = run_deterministic(config_mid, state_rule).delta
        if delta_low * delta_mid <= 0:
            high = mid
            delta_high = delta_mid
        else:
            low = mid
            delta_low = delta_mid

    return (low + high) / 2.0
