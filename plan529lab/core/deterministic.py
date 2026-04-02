"""Deterministic tradeoff analysis engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from plan529lab.core.growth import grow_qtp_account, grow_taxable_account
from plan529lab.core.resolution import compute_leftover_resolution
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.results import DriverDecomposition, TradeoffResult

if TYPE_CHECKING:
    from plan529lab.tax.state_base import StateRule


def run_deterministic(
    config: ScenarioConfig,
    state_rule: StateRule,
) -> TradeoffResult:
    """Run a deterministic 529 vs taxable tradeoff analysis.

    Computes two QTP outcomes:
    - QTP_A: fully qualified use (all earnings tax-free)
    - QTP_B: leftover resolution per ScenarioPolicy

    Then weights them by qualified_use_probability from the scenario policy.
    """
    warnings: list[str] = []

    # Determine start year from contributions
    first_qtp = config.qtp_contributions.first_date
    first_taxable = config.taxable_contributions.first_date
    if first_qtp is not None and first_taxable is not None:
        start_year = min(first_qtp.year, first_taxable.year)
    elif first_qtp is not None:
        start_year = first_qtp.year
    elif first_taxable is not None:
        start_year = first_taxable.year
    else:
        start_year = 0

    # Grow both accounts
    qtp_growth = grow_qtp_account(
        contributions=config.qtp_contributions,
        portfolio=config.portfolio_assumptions,
        qtp=config.qtp_assumptions,
        horizon_years=config.horizon_years,
        start_year=start_year,
    )

    taxable_growth = grow_taxable_account(
        contributions=config.taxable_contributions,
        portfolio=config.portfolio_assumptions,
        tax_profile=config.tax_profile,
        horizon_years=config.horizon_years,
        start_year=start_year,
        liquidate=True,
    )

    # State benefit from contributions
    state_benefit = state_rule.contribution_benefit(
        contribution_amount=qtp_growth.total_contributions,
        tax_profile=config.tax_profile,
        year=start_year,
    )

    # QTP_A: Fully qualified use — all earnings tax-free
    qtp_a = qtp_growth.ending_value + state_benefit

    # QTP_B: Leftover resolution via resolution module
    distribution = qtp_growth.ending_value
    earnings = qtp_growth.total_earnings
    aqee = config.education_schedule.total_aqee

    resolution = compute_leftover_resolution(
        distribution=distribution,
        earnings=earnings,
        total_contributions=qtp_growth.total_contributions,
        aqee=aqee,
        aotc_allocated=config.education_schedule.total_aotc_llc_allocated,
        account_age_years=config.horizon_years,
        leftover_resolution=config.scenario_policy.leftover_resolution,
        roth_rollover_fraction=config.scenario_policy.roth_rollover_fraction,
        tax_profile=config.tax_profile,
        state_rule=state_rule,
        state_benefit=state_benefit,
        year=start_year + config.horizon_years,
    )
    qtp_b = resolution.after_tax_value
    warnings.extend(resolution.warnings)

    # Weight by qualified use probability
    prob = config.scenario_policy.qualified_use_probability
    if prob is not None:
        qtp_value = prob * qtp_a + (1.0 - prob) * qtp_b
    else:
        # Default: assume fully qualified
        qtp_value = qtp_a
        if aqee < distribution:
            warnings.append(
                "No qualified_use_probability set and AQEE < distribution. "
                "Assuming fully qualified use."
            )

    taxable_value = taxable_growth.ending_value_after_tax
    delta = qtp_value - taxable_value

    # Break-even probability
    break_even: float | None = None
    if qtp_a != qtp_b:
        p_star = (taxable_value - qtp_b) / (qtp_a - qtp_b)
        break_even = max(0.0, min(1.0, p_star))

    # Driver decomposition
    tax_drag = (
        taxable_growth.cumulative_dividend_tax
        + taxable_growth.cumulative_realized_gain_tax
        + taxable_growth.terminal_liquidation_tax
    )
    drivers = DriverDecomposition(
        federal_tax_free_growth_benefit=tax_drag,
        taxable_dividend_drag_cost=taxable_growth.cumulative_dividend_tax,
        taxable_realization_drag_cost=taxable_growth.cumulative_realized_gain_tax,
        taxable_liquidation_cost=taxable_growth.terminal_liquidation_tax,
        nonqualified_qtp_income_tax_cost=(
            resolution.nonqualified_tax_cost if prob is not None else 0.0
        ),
        qtp_10_percent_additional_tax_cost=(
            resolution.additional_tax_cost if prob is not None else 0.0
        ),
        state_benefit_value=state_benefit,
        state_recapture_cost=(
            resolution.state_recapture_cost if prob is not None else 0.0
        ),
        roth_rollover_option_value=resolution.roth_rollover_value,
    )

    # Validate state rule
    state_warnings = state_rule.validate(config)
    warnings.extend(state_warnings)

    return TradeoffResult(
        qtp_after_tax_value=qtp_value,
        taxable_after_tax_value=taxable_value,
        delta=delta,
        qtp_ending_value=qtp_growth.ending_value,
        qtp_basis=qtp_growth.total_contributions,
        qtp_earnings=qtp_growth.total_earnings,
        qtp_aqee=aqee,
        qtp_taxable_earnings=resolution.taxable_earnings,
        qtp_income_tax=resolution.nonqualified_tax_cost,
        qtp_additional_tax=resolution.additional_tax_cost,
        qtp_state_recapture_tax=resolution.state_recapture_cost,
        qtp_state_benefit=state_benefit,
        taxable_ending_value_pre_liquidation=taxable_growth.ending_value_pre_liquidation,
        taxable_basis=taxable_growth.tax_basis,
        taxable_unrealized_gain=taxable_growth.unrealized_gain,
        taxable_dividend_tax_drag=taxable_growth.cumulative_dividend_tax,
        taxable_realized_gain_tax_drag=taxable_growth.cumulative_realized_gain_tax,
        taxable_terminal_liquidation_tax=taxable_growth.terminal_liquidation_tax,
        break_even_qualified_use_probability=break_even,
        drivers=drivers,
        resolution_method=resolution.resolution_method,
        warnings=warnings,
    )
