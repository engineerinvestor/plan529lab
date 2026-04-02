"""Monte Carlo simulation models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StochasticAssumptions(BaseModel, frozen=True):
    """Distribution parameters for stochastic inputs.

    Returns are modeled as log-normal: log(1 + r) ~ N(return_mean, return_std).
    Other parameters are modeled as per-path constants drawn from normal
    distributions centered on the base config values.
    """

    return_std: float = Field(default=0.0, ge=0.0, description="Std dev of log-normal returns")
    dividend_yield_std: float = Field(default=0.0, ge=0.0)
    turnover_std: float = Field(default=0.0, ge=0.0)
    qualified_use_probability_std: float = Field(default=0.0, ge=0.0)


class MonteCarloConfig(BaseModel, frozen=True):
    """Configuration for Monte Carlo simulation."""

    n_paths: int = Field(default=10_000, gt=0)
    seed: int | None = None
    stochastic: StochasticAssumptions = StochasticAssumptions()
    percentiles: list[float] = Field(default=[5.0, 25.0, 50.0, 75.0, 95.0])


class MonteCarloResult(BaseModel, frozen=True):
    """Result of a Monte Carlo simulation."""

    deltas: list[float]
    mean_delta: float
    median_delta: float
    std_delta: float
    percentile_values: dict[str, float]
    prob_qtp_wins: float
    n_paths: int
    seed: int | None = None
