"""Roth IRA rollover estimation from 529/QTP accounts (post-SECURE 2.0)."""

from __future__ import annotations

import math

from pydantic import BaseModel

from plan529lab.constants import (
    ROTH_ROLLOVER_ACCOUNT_AGE_YEARS,
    ROTH_ROLLOVER_ANNUAL_LIMIT,
    ROTH_ROLLOVER_CONTRIBUTION_LOOKBACK_YEARS,
    ROTH_ROLLOVER_LIFETIME_CAP,
)


class RothRolloverEstimate(BaseModel, frozen=True):
    """Result of a Roth rollover eligibility and cap estimate."""

    eligible: bool
    account_age_years: int
    amount_eligible: float
    amount_ineligible_recent: float
    lifetime_cap_remaining: float
    years_to_complete: int
    residual_balance: float
    warnings: list[str] = []


def estimate_roth_rollover(
    account_balance: float,
    total_contributions: float,
    account_age_years: int,
    contributions_within_lookback: float = 0.0,
    prior_rollovers: float = 0.0,
    annual_limit: float = ROTH_ROLLOVER_ANNUAL_LIMIT,
) -> RothRolloverEstimate:
    """Estimate the Roth rollover opportunity from a 529 account.

    Checks eligibility based on account age, lookback exclusions,
    and the lifetime cap.
    """
    warnings: list[str] = []

    # Check account age
    if account_age_years < ROTH_ROLLOVER_ACCOUNT_AGE_YEARS:
        return RothRolloverEstimate(
            eligible=False,
            account_age_years=account_age_years,
            amount_eligible=0.0,
            amount_ineligible_recent=contributions_within_lookback,
            lifetime_cap_remaining=max(0.0, ROTH_ROLLOVER_LIFETIME_CAP - prior_rollovers),
            years_to_complete=0,
            residual_balance=account_balance,
            warnings=[
                f"Account must be open at least {ROTH_ROLLOVER_ACCOUNT_AGE_YEARS} years. "
                f"Current age: {account_age_years} years."
            ],
        )

    # Lifetime cap remaining
    cap_remaining = max(0.0, ROTH_ROLLOVER_LIFETIME_CAP - prior_rollovers)

    if cap_remaining <= 0:
        return RothRolloverEstimate(
            eligible=False,
            account_age_years=account_age_years,
            amount_eligible=0.0,
            amount_ineligible_recent=contributions_within_lookback,
            lifetime_cap_remaining=0.0,
            years_to_complete=0,
            residual_balance=account_balance,
            warnings=["Lifetime rollover cap already exhausted."],
        )

    # Exclude contributions within lookback period
    eligible_basis = max(0.0, total_contributions - contributions_within_lookback)

    # The rollover comes from the account balance, but is limited by:
    # 1. The eligible basis (contributions outside lookback)
    # 2. The lifetime cap remaining
    # 3. The account balance itself
    amount_eligible = min(account_balance, eligible_basis, cap_remaining)

    if contributions_within_lookback > 0:
        warnings.append(
            f"${contributions_within_lookback:,.0f} in contributions within the "
            f"{ROTH_ROLLOVER_CONTRIBUTION_LOOKBACK_YEARS}-year lookback period "
            "are excluded from rollover eligibility."
        )

    # Years needed to complete rollover at annual limit
    if annual_limit > 0 and amount_eligible > 0:
        years_to_complete = math.ceil(amount_eligible / annual_limit)
    else:
        years_to_complete = 0

    residual = account_balance - amount_eligible

    return RothRolloverEstimate(
        eligible=amount_eligible > 0,
        account_age_years=account_age_years,
        amount_eligible=amount_eligible,
        amount_ineligible_recent=contributions_within_lookback,
        lifetime_cap_remaining=cap_remaining,
        years_to_complete=years_to_complete,
        residual_balance=residual,
        warnings=warnings,
    )
