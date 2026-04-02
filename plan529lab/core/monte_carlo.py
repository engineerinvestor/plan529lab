"""Monte Carlo simulation engine.

Runs N deterministic paths with stochastic parameter draws, reusing
the existing growth and resolution logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from plan529lab.core.growth import grow_qtp_account, grow_taxable_account
from plan529lab.core.resolution import compute_leftover_resolution
from plan529lab.models.monte_carlo import MonteCarloConfig, MonteCarloResult

if TYPE_CHECKING:
    from plan529lab.models.config import ScenarioConfig
    from plan529lab.tax.state_base import StateRule


def run_monte_carlo(
    base_config: ScenarioConfig,
    mc_config: MonteCarloConfig,
    state_rule: StateRule,
) -> MonteCarloResult:
    """Run a Monte Carlo simulation of the 529 vs taxable tradeoff.

    For each path, draws stochastic parameters and runs the deterministic
    comparison. Per-year returns are drawn from a log-normal distribution.
    """
    rng = np.random.default_rng(mc_config.seed)
    stoch = mc_config.stochastic
    horizon = base_config.horizon_years
    portfolio = base_config.portfolio_assumptions
    tax_profile = base_config.tax_profile
    policy = base_config.scenario_policy

    # Determine start year
    first_qtp = base_config.qtp_contributions.first_date
    first_taxable = base_config.taxable_contributions.first_date
    if first_qtp is not None and first_taxable is not None:
        start_year = min(first_qtp.year, first_taxable.year)
    elif first_qtp is not None:
        start_year = first_qtp.year
    elif first_taxable is not None:
        start_year = first_taxable.year
    else:
        start_year = 0

    # State benefit (constant across paths)
    state_benefit = state_rule.contribution_benefit(
        contribution_amount=base_config.qtp_contributions.total_amount,
        tax_profile=tax_profile,
        year=start_year,
    )

    deltas: list[float] = []

    for _ in range(mc_config.n_paths):
        # Draw per-year returns (log-normal)
        if stoch.return_std > 0:
            log_returns = rng.normal(
                loc=np.log(1.0 + portfolio.annual_return),
                scale=stoch.return_std,
                size=horizon,
            )
            path_returns = list(np.exp(log_returns) - 1.0)
        else:
            path_returns = None  # use fixed return

        # Draw per-path qualified use probability
        has_prob_std = stoch.qualified_use_probability_std > 0
        if has_prob_std and policy.qualified_use_probability is not None:
            prob_draw = rng.normal(
                loc=policy.qualified_use_probability,
                scale=stoch.qualified_use_probability_std,
            )
            path_prob: float | None = max(0.0, min(1.0, float(prob_draw)))
        else:
            path_prob = policy.qualified_use_probability

        # Grow QTP account
        qtp_growth = grow_qtp_account(
            contributions=base_config.qtp_contributions,
            portfolio=portfolio,
            qtp=base_config.qtp_assumptions,
            horizon_years=horizon,
            start_year=start_year,
            annual_returns=path_returns,
        )

        # Grow taxable account
        taxable_growth = grow_taxable_account(
            contributions=base_config.taxable_contributions,
            portfolio=portfolio,
            tax_profile=tax_profile,
            horizon_years=horizon,
            start_year=start_year,
            liquidate=True,
            annual_returns=path_returns,
        )

        # QTP_A: fully qualified
        qtp_a = qtp_growth.ending_value + state_benefit

        # QTP_B: leftover resolution
        resolution = compute_leftover_resolution(
            distribution=qtp_growth.ending_value,
            earnings=qtp_growth.total_earnings,
            total_contributions=qtp_growth.total_contributions,
            aqee=base_config.education_schedule.total_aqee,
            aotc_allocated=base_config.education_schedule.total_aotc_llc_allocated,
            account_age_years=horizon,
            leftover_resolution=policy.leftover_resolution,
            roth_rollover_fraction=policy.roth_rollover_fraction,
            tax_profile=tax_profile,
            state_rule=state_rule,
            state_benefit=state_benefit,
            year=start_year + horizon,
        )
        qtp_b = resolution.after_tax_value

        # Weight by probability
        if path_prob is not None:
            qtp_value = path_prob * qtp_a + (1.0 - path_prob) * qtp_b
        else:
            qtp_value = qtp_a

        taxable_value = taxable_growth.ending_value_after_tax
        deltas.append(qtp_value - taxable_value)

    # Compute statistics
    delta_array = np.array(deltas)
    percentile_values = {
        str(p): float(np.percentile(delta_array, p))
        for p in mc_config.percentiles
    }

    return MonteCarloResult(
        deltas=deltas,
        mean_delta=float(np.mean(delta_array)),
        median_delta=float(np.median(delta_array)),
        std_delta=float(np.std(delta_array)),
        percentile_values=percentile_values,
        prob_qtp_wins=float(np.mean(delta_array > 0)),
        n_paths=mc_config.n_paths,
        seed=mc_config.seed,
    )
