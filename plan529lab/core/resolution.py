"""Leftover QTP balance resolution logic.

Computes the after-tax value of leftover 529 funds under different
resolution strategies: nonqualified withdrawal, Roth rollover,
beneficiary change, hold for future education, or a weighted mix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from plan529lab.tax.credits_coordination import compute_aotc_exception_amount
from plan529lab.tax.federal_qtp import (
    compute_additional_tax,
    compute_qtp_after_tax,
    compute_taxable_earnings,
)
from plan529lab.tax.roth_rollover import estimate_roth_rollover

if TYPE_CHECKING:
    from plan529lab.models.scenario import LeftoverResolution
    from plan529lab.models.tax_profile import InvestorTaxProfile
    from plan529lab.tax.state_base import StateRule


class ResolutionResult(BaseModel, frozen=True):
    """Result of resolving leftover QTP balance."""

    after_tax_value: float
    resolution_method: str
    taxable_earnings: float = 0.0
    roth_rollover_value: float = 0.0
    roth_eligible_amount: float = 0.0
    nonqualified_tax_cost: float = 0.0
    additional_tax_cost: float = 0.0
    state_recapture_cost: float = 0.0
    warnings: list[str] = []


def compute_nonqualified_withdrawal(
    distribution: float,
    earnings: float,
    aqee: float,
    aotc_allocated: float,
    tax_profile: InvestorTaxProfile,
    state_rule: StateRule,
    total_contributions: float,
    state_benefit: float,
    year: int,
) -> ResolutionResult:
    """Compute after-tax value for a full nonqualified withdrawal."""
    taxable_earnings = compute_taxable_earnings(
        earnings=earnings, aqee=aqee, distribution=distribution,
    )
    aotc_exception = compute_aotc_exception_amount(
        aotc_allocated_expense=aotc_allocated,
        earnings=earnings,
        distribution=distribution,
    )
    additional_tax = compute_additional_tax(
        taxable_earnings=taxable_earnings, exception_amount=aotc_exception,
    )
    state_recapture = state_rule.recapture_tax(
        recaptured_base=total_contributions,
        tax_profile=tax_profile,
        year=year,
    )
    after_tax = compute_qtp_after_tax(
        distribution=distribution,
        taxable_earnings=taxable_earnings,
        ordinary_rate=tax_profile.combined_ordinary_rate,
        additional_tax=additional_tax,
        state_recapture=state_recapture,
        state_benefit=state_benefit,
    )
    income_tax = taxable_earnings * tax_profile.combined_ordinary_rate
    return ResolutionResult(
        after_tax_value=after_tax,
        resolution_method="withdraw_nonqualified",
        taxable_earnings=taxable_earnings,
        nonqualified_tax_cost=income_tax,
        additional_tax_cost=additional_tax,
        state_recapture_cost=state_recapture,
    )


def compute_roth_rollover_resolution(
    distribution: float,
    earnings: float,
    total_contributions: float,
    account_age_years: int,
    tax_profile: InvestorTaxProfile,
    state_rule: StateRule,
    state_benefit: float,
    year: int,
) -> ResolutionResult:
    """Compute after-tax value when leftover is rolled to Roth IRA.

    The Roth-eligible portion avoids income tax and 10% additional tax.
    The residual (if any) is withdrawn nonqualified.
    """
    warnings: list[str] = []

    roth_estimate = estimate_roth_rollover(
        account_balance=distribution,
        total_contributions=total_contributions,
        account_age_years=account_age_years,
    )
    warnings.extend(roth_estimate.warnings)

    if not roth_estimate.eligible:
        # Fall back to nonqualified withdrawal
        result = compute_nonqualified_withdrawal(
            distribution=distribution,
            earnings=earnings,
            aqee=0.0,
            aotc_allocated=0.0,
            tax_profile=tax_profile,
            state_rule=state_rule,
            total_contributions=total_contributions,
            state_benefit=state_benefit,
            year=year,
        )
        return ResolutionResult(
            after_tax_value=result.after_tax_value,
            resolution_method="roth_rollover_ineligible",
            taxable_earnings=result.taxable_earnings,
            nonqualified_tax_cost=result.nonqualified_tax_cost,
            additional_tax_cost=result.additional_tax_cost,
            state_recapture_cost=result.state_recapture_cost,
            warnings=warnings + list(result.warnings),
        )

    # Roth-eligible portion: rolled tax-free (no income tax, no 10% additional tax)
    roth_amount = roth_estimate.amount_eligible
    residual = roth_estimate.residual_balance

    # The Roth rollover saves the tax that would have been paid on
    # the earnings portion of the rolled-over amount
    if distribution > 0:
        earnings_ratio = earnings / distribution
    else:
        earnings_ratio = 0.0

    # Earnings in the rolled-over portion (tax saved)
    roth_earnings = roth_amount * earnings_ratio
    saved_income_tax = roth_earnings * tax_profile.combined_ordinary_rate
    saved_additional_tax = roth_earnings * 0.10
    roth_option_value = saved_income_tax + saved_additional_tax

    # Residual withdrawn nonqualified
    if residual > 0:
        residual_earnings = residual * earnings_ratio
        residual_taxable = residual_earnings  # no AQEE for leftover
        residual_income_tax = residual_taxable * tax_profile.combined_ordinary_rate
        residual_additional = residual_taxable * 0.10
        residual_after_tax = residual - residual_income_tax - residual_additional
    else:
        residual_income_tax = 0.0
        residual_additional = 0.0
        residual_after_tax = 0.0

    state_recapture = state_rule.recapture_tax(
        recaptured_base=total_contributions,
        tax_profile=tax_profile,
        year=year,
    )

    after_tax = roth_amount + residual_after_tax - state_recapture + state_benefit

    # Total taxable earnings = residual taxable portion (Roth portion is tax-free)
    return ResolutionResult(
        after_tax_value=after_tax,
        resolution_method="roth_rollover",
        taxable_earnings=residual_taxable if residual > 0 else 0.0,
        roth_rollover_value=roth_option_value,
        roth_eligible_amount=roth_amount,
        nonqualified_tax_cost=residual_income_tax,
        additional_tax_cost=residual_additional,
        state_recapture_cost=state_recapture,
        warnings=warnings,
    )


def compute_beneficiary_change_resolution(
    distribution: float,
    total_contributions: float,
    tax_profile: InvestorTaxProfile,
    state_rule: StateRule,
    state_benefit: float,
    year: int,
) -> ResolutionResult:
    """Compute value when leftover is transferred to a new beneficiary.

    No immediate tax hit on the transfer. State recapture may still apply
    depending on the state rule.
    """
    state_recapture = state_rule.recapture_tax(
        recaptured_base=total_contributions,
        tax_profile=tax_profile,
        year=year,
    )
    after_tax = distribution - state_recapture + state_benefit

    return ResolutionResult(
        after_tax_value=after_tax,
        resolution_method="change_beneficiary",
        state_recapture_cost=state_recapture,
    )


def compute_leftover_resolution(
    distribution: float,
    earnings: float,
    total_contributions: float,
    aqee: float,
    aotc_allocated: float,
    account_age_years: int,
    leftover_resolution: LeftoverResolution,
    roth_rollover_fraction: float,
    tax_profile: InvestorTaxProfile,
    state_rule: StateRule,
    state_benefit: float,
    year: int,
) -> ResolutionResult:
    """Compute the after-tax value of leftover QTP balance under the given policy.

    This is the main entry point for resolution logic, dispatching to the
    appropriate strategy based on leftover_resolution.
    """
    if leftover_resolution == "withdraw_nonqualified":
        return compute_nonqualified_withdrawal(
            distribution=distribution,
            earnings=earnings,
            aqee=aqee,
            aotc_allocated=aotc_allocated,
            tax_profile=tax_profile,
            state_rule=state_rule,
            total_contributions=total_contributions,
            state_benefit=state_benefit,
            year=year,
        )

    if leftover_resolution == "roth_rollover":
        return compute_roth_rollover_resolution(
            distribution=distribution,
            earnings=earnings,
            total_contributions=total_contributions,
            account_age_years=account_age_years,
            tax_profile=tax_profile,
            state_rule=state_rule,
            state_benefit=state_benefit,
            year=year,
        )

    if leftover_resolution in ("change_beneficiary", "hold_for_future_education"):
        return compute_beneficiary_change_resolution(
            distribution=distribution,
            total_contributions=total_contributions,
            tax_profile=tax_profile,
            state_rule=state_rule,
            state_benefit=state_benefit,
            year=year,
        )

    # mixed: weighted combination
    roth_result = compute_roth_rollover_resolution(
        distribution=distribution,
        earnings=earnings,
        total_contributions=total_contributions,
        account_age_years=account_age_years,
        tax_profile=tax_profile,
        state_rule=state_rule,
        state_benefit=state_benefit,
        year=year,
    )
    nonqual_result = compute_nonqualified_withdrawal(
        distribution=distribution,
        earnings=earnings,
        aqee=aqee,
        aotc_allocated=aotc_allocated,
        tax_profile=tax_profile,
        state_rule=state_rule,
        total_contributions=total_contributions,
        state_benefit=state_benefit,
        year=year,
    )

    rf = roth_rollover_fraction
    after_tax = rf * roth_result.after_tax_value + (1.0 - rf) * nonqual_result.after_tax_value
    roth_value = rf * roth_result.roth_rollover_value

    return ResolutionResult(
        after_tax_value=after_tax,
        resolution_method="mixed",
        taxable_earnings=(
            rf * roth_result.taxable_earnings
            + (1.0 - rf) * nonqual_result.taxable_earnings
        ),
        roth_rollover_value=roth_value,
        roth_eligible_amount=roth_result.roth_eligible_amount,
        nonqualified_tax_cost=(
            rf * roth_result.nonqualified_tax_cost
            + (1.0 - rf) * nonqual_result.nonqualified_tax_cost
        ),
        additional_tax_cost=(
            rf * roth_result.additional_tax_cost
            + (1.0 - rf) * nonqual_result.additional_tax_cost
        ),
        state_recapture_cost=nonqual_result.state_recapture_cost,
        warnings=roth_result.warnings,
    )
