"""Tests for leftover resolution logic."""

import datetime

import pytest

from plan529lab.core.deterministic import run_deterministic
from plan529lab.core.resolution import (
    compute_beneficiary_change_resolution,
    compute_leftover_resolution,
    compute_nonqualified_withdrawal,
    compute_roth_rollover_resolution,
)
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule


def _profile() -> InvestorTaxProfile:
    return InvestorTaxProfile(
        ordinary_income_rate=0.35,
        ltcg_rate=0.15,
        qualified_dividend_rate=0.15,
    )


def _state_rule() -> NoIncomeTaxStateRule:
    return NoIncomeTaxStateRule("WA")


class TestNonqualifiedWithdrawal:
    def test_fully_nonqualified(self) -> None:
        result = compute_nonqualified_withdrawal(
            distribution=25000,
            earnings=5000,
            aqee=0,
            aotc_allocated=0,
            tax_profile=_profile(),
            state_rule=_state_rule(),
            total_contributions=20000,
            state_benefit=0,
            year=2043,
        )
        assert result.resolution_method == "withdraw_nonqualified"
        assert result.after_tax_value < 25000  # taxes reduce value
        assert result.nonqualified_tax_cost > 0
        assert result.additional_tax_cost > 0

    def test_with_aqee_reduces_tax(self) -> None:
        result_no_aqee = compute_nonqualified_withdrawal(
            distribution=25000, earnings=5000, aqee=0, aotc_allocated=0,
            tax_profile=_profile(), state_rule=_state_rule(),
            total_contributions=20000, state_benefit=0, year=2043,
        )
        result_with_aqee = compute_nonqualified_withdrawal(
            distribution=25000, earnings=5000, aqee=20000, aotc_allocated=0,
            tax_profile=_profile(), state_rule=_state_rule(),
            total_contributions=20000, state_benefit=0, year=2043,
        )
        assert result_with_aqee.after_tax_value > result_no_aqee.after_tax_value


class TestRothRolloverResolution:
    def test_eligible_rollover(self) -> None:
        result = compute_roth_rollover_resolution(
            distribution=50000,
            earnings=20000,
            total_contributions=30000,
            account_age_years=18,
            tax_profile=_profile(),
            state_rule=_state_rule(),
            state_benefit=0,
            year=2043,
        )
        assert result.resolution_method == "roth_rollover"
        assert result.roth_eligible_amount > 0
        assert result.roth_rollover_value > 0  # tax savings from rollover

    def test_ineligible_falls_back(self) -> None:
        result = compute_roth_rollover_resolution(
            distribution=50000,
            earnings=20000,
            total_contributions=30000,
            account_age_years=10,  # too young
            tax_profile=_profile(),
            state_rule=_state_rule(),
            state_benefit=0,
            year=2033,
        )
        assert result.resolution_method == "roth_rollover_ineligible"
        assert result.roth_rollover_value == 0.0
        assert result.roth_eligible_amount == 0.0

    def test_rollover_better_than_nonqualified(self) -> None:
        """Roth rollover should yield higher after-tax value than nonqualified."""
        nonqual = compute_nonqualified_withdrawal(
            distribution=50000, earnings=20000, aqee=0, aotc_allocated=0,
            tax_profile=_profile(), state_rule=_state_rule(),
            total_contributions=30000, state_benefit=0, year=2043,
        )
        roth = compute_roth_rollover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            account_age_years=18, tax_profile=_profile(),
            state_rule=_state_rule(), state_benefit=0, year=2043,
        )
        assert roth.after_tax_value > nonqual.after_tax_value


class TestBeneficiaryChangeResolution:
    def test_no_tax_hit(self) -> None:
        result = compute_beneficiary_change_resolution(
            distribution=50000,
            total_contributions=30000,
            tax_profile=_profile(),
            state_rule=_state_rule(),
            state_benefit=0,
            year=2043,
        )
        assert result.resolution_method == "change_beneficiary"
        assert result.after_tax_value == pytest.approx(50000.0)
        assert result.nonqualified_tax_cost == 0.0
        assert result.additional_tax_cost == 0.0

    def test_best_outcome(self) -> None:
        """Beneficiary change should be the best or equal to best outcome."""
        bene = compute_beneficiary_change_resolution(
            distribution=50000, total_contributions=30000,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        nonqual = compute_nonqualified_withdrawal(
            distribution=50000, earnings=20000, aqee=0, aotc_allocated=0,
            tax_profile=_profile(), state_rule=_state_rule(),
            total_contributions=30000, state_benefit=0, year=2043,
        )
        assert bene.after_tax_value >= nonqual.after_tax_value


class TestMixedResolution:
    def test_mixed_between_pure_modes(self) -> None:
        """Mixed resolution value should be between Roth and nonqualified."""
        nonqual = compute_leftover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            aqee=0, aotc_allocated=0, account_age_years=18,
            leftover_resolution="withdraw_nonqualified",
            roth_rollover_fraction=0.0,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        roth = compute_leftover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            aqee=0, aotc_allocated=0, account_age_years=18,
            leftover_resolution="roth_rollover",
            roth_rollover_fraction=0.0,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        mixed = compute_leftover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            aqee=0, aotc_allocated=0, account_age_years=18,
            leftover_resolution="mixed",
            roth_rollover_fraction=0.5,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        low = min(nonqual.after_tax_value, roth.after_tax_value)
        high = max(nonqual.after_tax_value, roth.after_tax_value)
        assert low <= mixed.after_tax_value <= high + 0.01

    def test_mixed_method(self) -> None:
        result = compute_leftover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            aqee=0, aotc_allocated=0, account_age_years=18,
            leftover_resolution="mixed", roth_rollover_fraction=0.3,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        assert result.resolution_method == "mixed"


class TestDispatch:
    def test_hold_for_future_uses_beneficiary_logic(self) -> None:
        result = compute_leftover_resolution(
            distribution=50000, earnings=20000, total_contributions=30000,
            aqee=0, aotc_allocated=0, account_age_years=18,
            leftover_resolution="hold_for_future_education",
            roth_rollover_fraction=0.0,
            tax_profile=_profile(), state_rule=_state_rule(),
            state_benefit=0, year=2043,
        )
        assert result.resolution_method == "change_beneficiary"
        assert result.after_tax_value == pytest.approx(50000.0)


class TestIntegrationWithEngine:
    def _config(
        self,
        leftover: str = "withdraw_nonqualified",
        roth_fraction: float = 0.0,
        prob: float = 0.5,
    ) -> ScenarioConfig:
        return ScenarioConfig(
            tax_profile=_profile(),
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
            scenario_policy=ScenarioPolicy(
                leftover_resolution=leftover,
                qualified_use_probability=prob,
                roth_rollover_fraction=roth_fraction,
            ),
            horizon_years=18,
        )

    def test_roth_rollover_wired(self) -> None:
        result = run_deterministic(self._config("roth_rollover"), _state_rule())
        assert result.resolution_method == "roth_rollover"
        assert result.drivers.roth_rollover_option_value > 0

    def test_mixed_resolution_wired(self) -> None:
        result = run_deterministic(
            self._config("mixed", roth_fraction=0.3), _state_rule()
        )
        assert result.resolution_method == "mixed"

    def test_beneficiary_change_wired(self) -> None:
        result = run_deterministic(
            self._config("change_beneficiary"), _state_rule()
        )
        assert result.resolution_method == "change_beneficiary"

    def test_roth_better_than_nonqualified(self) -> None:
        """Roth rollover resolution should improve delta vs nonqualified."""
        result_nonqual = run_deterministic(
            self._config("withdraw_nonqualified"), _state_rule()
        )
        result_roth = run_deterministic(
            self._config("roth_rollover"), _state_rule()
        )
        assert result_roth.qtp_after_tax_value >= result_nonqual.qtp_after_tax_value
