"""Tests for domain models."""

import datetime

import pytest
from pydantic import ValidationError

from plan529lab.models import (
    Contribution,
    ContributionSchedule,
    EducationExpenseItem,
    EducationExpenseSchedule,
    InvestorTaxProfile,
    PortfolioAssumptions,
    QTPAssumptions,
    ScenarioConfig,
    ScenarioPolicy,
    TradeoffResult,
)


class TestInvestorTaxProfile:
    def test_valid_construction(self) -> None:
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.35,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
            niit_rate=0.038,
            state_ordinary_rate=0.05,
            state_cap_gains_rate=0.05,
        )
        assert profile.ordinary_income_rate == 0.35
        assert profile.combined_ordinary_rate == pytest.approx(0.40)
        assert profile.combined_ltcg_rate == pytest.approx(0.20)
        assert profile.combined_qualified_dividend_rate == pytest.approx(0.20)

    def test_defaults(self) -> None:
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.22,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )
        assert profile.niit_rate == 0.0
        assert profile.state_ordinary_rate == 0.0
        assert profile.filing_status is None

    def test_rate_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InvestorTaxProfile(
                ordinary_income_rate=1.5,
                ltcg_rate=0.15,
                qualified_dividend_rate=0.15,
            )

    def test_negative_rate_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InvestorTaxProfile(
                ordinary_income_rate=-0.1,
                ltcg_rate=0.15,
                qualified_dividend_rate=0.15,
            )

    def test_frozen(self) -> None:
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.22,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )
        with pytest.raises(ValidationError):
            profile.ordinary_income_rate = 0.30  # type: ignore[misc]


class TestContribution:
    def test_valid_contribution(self) -> None:
        c = Contribution(
            date=datetime.date(2025, 1, 15),
            amount=5000.0,
            account_type="qtp",
        )
        assert c.amount == 5000.0
        assert c.account_type == "qtp"

    def test_zero_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Contribution(
                date=datetime.date(2025, 1, 1),
                amount=0.0,
                account_type="qtp",
            )

    def test_invalid_account_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Contribution(
                date=datetime.date(2025, 1, 1),
                amount=1000.0,
                account_type="roth",
            )


class TestContributionSchedule:
    def test_total_and_dates(self) -> None:
        schedule = ContributionSchedule(
            items=[
                Contribution(date=datetime.date(2025, 1, 1), amount=5000, account_type="qtp"),
                Contribution(date=datetime.date(2026, 1, 1), amount=5000, account_type="qtp"),
                Contribution(date=datetime.date(2027, 1, 1), amount=5000, account_type="qtp"),
            ]
        )
        assert schedule.total_amount == 15000.0
        assert schedule.first_date == datetime.date(2025, 1, 1)
        assert schedule.last_date == datetime.date(2027, 1, 1)
        assert schedule.total_for_year(2025) == 5000.0
        assert schedule.total_for_year(2028) == 0.0

    def test_empty_schedule(self) -> None:
        schedule = ContributionSchedule()
        assert schedule.total_amount == 0.0
        assert schedule.first_date is None
        assert schedule.last_date is None


class TestEducationExpenseItem:
    def test_aqee_basic(self) -> None:
        item = EducationExpenseItem(
            date=datetime.date(2042, 9, 1),
            qualified_expense=30000,
            tax_free_assistance=5000,
            aotc_or_llc_allocated_expense=4000,
        )
        assert item.aqee == pytest.approx(21000.0)

    def test_aqee_floors_at_zero(self) -> None:
        item = EducationExpenseItem(
            date=datetime.date(2042, 9, 1),
            qualified_expense=5000,
            tax_free_assistance=10000,
        )
        assert item.aqee == 0.0

    def test_aqee_no_adjustments(self) -> None:
        item = EducationExpenseItem(
            date=datetime.date(2042, 9, 1),
            qualified_expense=30000,
        )
        assert item.aqee == 30000.0


class TestEducationExpenseSchedule:
    def test_total_aqee(self) -> None:
        schedule = EducationExpenseSchedule(
            items=[
                EducationExpenseItem(
                    date=datetime.date(2042, 9, 1),
                    qualified_expense=30000,
                    tax_free_assistance=5000,
                    aotc_or_llc_allocated_expense=4000,
                ),
                EducationExpenseItem(
                    date=datetime.date(2043, 9, 1),
                    qualified_expense=30000,
                ),
            ]
        )
        assert schedule.total_aqee == pytest.approx(51000.0)
        assert schedule.total_qualified_expense == 60000.0
        assert schedule.total_tax_free_assistance == 5000.0
        assert schedule.total_aotc_llc_allocated == 4000.0


class TestScenarioPolicy:
    def test_defaults(self) -> None:
        policy = ScenarioPolicy()
        assert policy.leftover_resolution == "withdraw_nonqualified"
        assert policy.qualified_use_probability is None
        assert policy.roth_rollover_fraction == 0.0

    def test_probability_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ScenarioPolicy(qualified_use_probability=1.5)


class TestPortfolioAssumptions:
    def test_valid(self) -> None:
        pa = PortfolioAssumptions(
            annual_return=0.07,
            dividend_yield=0.015,
            qualified_dividend_share=0.95,
            turnover_realization_rate=0.05,
        )
        assert pa.expense_ratio == 0.0

    def test_return_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PortfolioAssumptions(
                annual_return=2.0,
                dividend_yield=0.01,
                qualified_dividend_share=0.9,
                turnover_realization_rate=0.05,
            )


class TestQTPAssumptions:
    def test_defaults(self) -> None:
        qtp = QTPAssumptions()
        assert qtp.state_tax_deduction_rate == 0.0
        assert qtp.roth_rollover_enabled is False
        assert qtp.beneficiary_change_allowed is True


class TestScenarioConfig:
    def test_full_config(self) -> None:
        config = ScenarioConfig(
            tax_profile=InvestorTaxProfile(
                ordinary_income_rate=0.35,
                ltcg_rate=0.15,
                qualified_dividend_rate=0.15,
            ),
            qtp_contributions=ContributionSchedule(
                items=[
                    Contribution(
                        date=datetime.date(2025, 1, 1), amount=10000, account_type="qtp"
                    ),
                ]
            ),
            taxable_contributions=ContributionSchedule(
                items=[
                    Contribution(
                        date=datetime.date(2025, 1, 1), amount=10000, account_type="taxable"
                    ),
                ]
            ),
            portfolio_assumptions=PortfolioAssumptions(
                annual_return=0.07,
                dividend_yield=0.015,
                qualified_dividend_share=0.95,
                turnover_realization_rate=0.05,
            ),
            education_schedule=EducationExpenseSchedule(),
            horizon_years=18,
        )
        assert config.horizon_years == 18


class TestTradeoffResult:
    def test_explain_529_wins(self) -> None:
        result = TradeoffResult(
            qtp_after_tax_value=50000,
            taxable_after_tax_value=45000,
            delta=5000,
            qtp_ending_value=50000,
            qtp_basis=30000,
            qtp_earnings=20000,
            qtp_aqee=50000,
            qtp_taxable_earnings=0,
            qtp_income_tax=0,
            qtp_additional_tax=0,
            qtp_state_recapture_tax=0,
            qtp_state_benefit=0,
            taxable_ending_value_pre_liquidation=48000,
            taxable_basis=30000,
            taxable_unrealized_gain=18000,
            taxable_dividend_tax_drag=1500,
            taxable_realized_gain_tax_drag=800,
            taxable_terminal_liquidation_tax=700,
            break_even_qualified_use_probability=0.42,
        )
        text = result.explain()
        assert "529 strategy" in text
        assert "$5,000 more" in text
        assert "Break-even" in text
        assert "42.0%" in text

    def test_serialization_roundtrip(self) -> None:
        result = TradeoffResult(
            qtp_after_tax_value=50000,
            taxable_after_tax_value=45000,
            delta=5000,
            qtp_ending_value=50000,
            qtp_basis=30000,
            qtp_earnings=20000,
            qtp_aqee=50000,
            qtp_taxable_earnings=0,
            qtp_income_tax=0,
            qtp_additional_tax=0,
            qtp_state_recapture_tax=0,
            qtp_state_benefit=0,
            taxable_ending_value_pre_liquidation=48000,
            taxable_basis=30000,
            taxable_unrealized_gain=18000,
            taxable_dividend_tax_drag=1500,
            taxable_realized_gain_tax_drag=800,
            taxable_terminal_liquidation_tax=700,
        )
        d = result.to_dict()
        assert d["delta"] == 5000
        json_str = result.to_json()
        assert '"delta": 5000' in json_str
