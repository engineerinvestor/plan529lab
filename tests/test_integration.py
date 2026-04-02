"""End-to-end integration tests."""

import datetime
from pathlib import Path

import pytest

from plan529lab.api import analyze_tradeoff
from plan529lab.io.yaml_loader import load_config
from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.contributions import Contribution, ContributionSchedule
from plan529lab.models.education import EducationExpenseItem, EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.generic_deduction import GenericDeductionStateRule
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule
from plan529lab.tax.roth_rollover import estimate_roth_rollover

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _make_config(
    ordinary_rate: float = 0.35,
    ltcg_rate: float = 0.15,
    state_rate: float = 0.0,
    contribution: float = 10000.0,
    horizon: int = 18,
    qualified_expense: float = 100000.0,
    tax_free_assistance: float = 0.0,
    aotc_allocated: float = 0.0,
    qualified_use_probability: float | None = None,
    dividend_yield: float = 0.015,
    turnover: float = 0.05,
) -> ScenarioConfig:
    return ScenarioConfig(
        tax_profile=InvestorTaxProfile(
            ordinary_income_rate=ordinary_rate,
            ltcg_rate=ltcg_rate,
            qualified_dividend_rate=ltcg_rate,
            state_ordinary_rate=state_rate,
            state_cap_gains_rate=state_rate,
        ),
        qtp_contributions=ContributionSchedule(
            items=[
                Contribution(
                    date=datetime.date(2025, 1, 1),
                    amount=contribution,
                    account_type="qtp",
                ),
            ]
        ),
        taxable_contributions=ContributionSchedule(
            items=[
                Contribution(
                    date=datetime.date(2025, 1, 1),
                    amount=contribution,
                    account_type="taxable",
                ),
            ]
        ),
        portfolio_assumptions=PortfolioAssumptions(
            annual_return=0.07,
            dividend_yield=dividend_yield,
            qualified_dividend_share=0.95,
            turnover_realization_rate=turnover,
        ),
        education_schedule=EducationExpenseSchedule(
            items=[
                EducationExpenseItem(
                    date=datetime.date(2043, 9, 1),
                    qualified_expense=qualified_expense,
                    tax_free_assistance=tax_free_assistance,
                    aotc_or_llc_allocated_expense=aotc_allocated,
                ),
            ]
        ),
        qtp_assumptions=QTPAssumptions(),
        scenario_policy=ScenarioPolicy(
            qualified_use_probability=qualified_use_probability,
        ),
        horizon_years=horizon,
    )


class TestWashingtonBaseCase:
    def test_from_yaml(self) -> None:
        config = load_config(EXAMPLES_DIR / "washington_no_income_tax.yaml")
        result = analyze_tradeoff(config, NoIncomeTaxStateRule("WA"))

        assert result.delta > 0
        assert result.qtp_state_benefit == 0.0
        assert result.qtp_state_recapture_tax == 0.0
        assert result.qtp_after_tax_value > 0
        assert result.taxable_after_tax_value > 0

    def test_fully_qualified(self) -> None:
        config = _make_config(qualified_use_probability=1.0)
        result = analyze_tradeoff(config, NoIncomeTaxStateRule())

        assert result.delta > 0
        assert result.qtp_taxable_earnings == pytest.approx(0.0)
        assert result.qtp_additional_tax == pytest.approx(0.0)


class TestHighScholarship:
    def test_scholarship_reduces_benefit(self) -> None:
        config_no_aid = _make_config(
            qualified_use_probability=1.0,
            qualified_expense=30000,
        )
        config_with_aid = _make_config(
            qualified_use_probability=1.0,
            qualified_expense=30000,
            tax_free_assistance=20000,
        )

        result_no = analyze_tradeoff(config_no_aid)
        result_with = analyze_tradeoff(config_with_aid)

        # More scholarship -> lower AQEE -> 529 benefit reduced
        assert result_with.qtp_aqee < result_no.qtp_aqee


class TestFullyNonqualified:
    def test_basis_still_tax_free(self) -> None:
        config = _make_config(
            qualified_use_probability=0.0,
            qualified_expense=0.0,
        )
        result = analyze_tradeoff(config)

        # After-tax value should exceed contributions (basis tax-free + some growth)
        assert result.qtp_after_tax_value > 0
        assert result.qtp_taxable_earnings > 0
        assert result.qtp_additional_tax > 0


class TestStateDeduction:
    def test_deduction_increases_delta(self) -> None:
        config = _make_config(
            qualified_use_probability=1.0,
            state_rate=0.05,
        )
        rule = GenericDeductionStateRule("NY")
        result = analyze_tradeoff(config, rule)

        assert result.qtp_state_benefit > 0


class TestRothRolloverSalvage:
    def test_eligible_rollover(self) -> None:
        estimate = estimate_roth_rollover(
            account_balance=50000,
            total_contributions=30000,
            account_age_years=18,
        )

        assert estimate.eligible is True
        assert estimate.amount_eligible > 0
        assert estimate.years_to_complete > 0
        assert estimate.residual_balance >= 0


class TestExplainOutput:
    def test_explain_has_key_components(self) -> None:
        config = _make_config(qualified_use_probability=0.75, qualified_expense=30000)
        result = analyze_tradeoff(config)
        text = result.explain()

        assert "strategy" in text
        assert "Key drivers:" in text
        assert "tax-free" in text.lower() or "growth" in text.lower()


class TestMidRangeProbabilityWithMixedResolution:
    def test_p60_mixed_roth(self) -> None:
        """Mid-range probability with mixed resolution should blend outcomes."""
        config = ScenarioConfig(
            tax_profile=InvestorTaxProfile(
                ordinary_income_rate=0.35, ltcg_rate=0.15, qualified_dividend_rate=0.15,
            ),
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
            qtp_assumptions=QTPAssumptions(roth_rollover_enabled=True),
            scenario_policy=ScenarioPolicy(
                leftover_resolution="mixed",
                qualified_use_probability=0.6,
                roth_rollover_fraction=0.3,
            ),
            horizon_years=18,
        )
        result = analyze_tradeoff(config, NoIncomeTaxStateRule())

        assert result.delta > 0
        assert result.resolution_method == "mixed"
        assert result.drivers.roth_rollover_option_value > 0


class TestStateRecaptureEndToEnd:
    def test_deduction_state_nonqualified(self) -> None:
        """State recapture should reduce the 529 value when withdrawing nonqualified."""
        config_with_state = _make_config(
            qualified_use_probability=0.5,
            qualified_expense=0.0,
            state_rate=0.05,
        )
        rule = GenericDeductionStateRule("NY")

        result_with = analyze_tradeoff(config_with_state, rule)

        # State benefit helps qualified path, but recapture hurts nonqualified path
        assert result_with.qtp_state_benefit > 0
        assert result_with.qtp_state_recapture_tax > 0


class TestMultiYearAOTCScholarship:
    def test_combined_reductions(self) -> None:
        """Multi-year expenses with scholarships and AOTC should reduce AQEE."""
        edu = EducationExpenseSchedule(items=[
            EducationExpenseItem(
                date=datetime.date(2043, 9, 1),
                qualified_expense=40000,
                tax_free_assistance=20000,
                aotc_or_llc_allocated_expense=4000,
            ),
            EducationExpenseItem(
                date=datetime.date(2044, 9, 1),
                qualified_expense=40000,
                tax_free_assistance=20000,
                aotc_or_llc_allocated_expense=4000,
            ),
            EducationExpenseItem(
                date=datetime.date(2045, 9, 1),
                qualified_expense=40000,
                tax_free_assistance=25000,
            ),
            EducationExpenseItem(
                date=datetime.date(2046, 9, 1),
                qualified_expense=40000,
                tax_free_assistance=25000,
            ),
        ])
        # AQEE = (40-20-4) + (40-20-4) + (40-25) + (40-25) = 16+16+15+15 = 62k
        assert edu.total_aqee == pytest.approx(62000.0)

        config = ScenarioConfig(
            tax_profile=InvestorTaxProfile(
                ordinary_income_rate=0.35, ltcg_rate=0.15, qualified_dividend_rate=0.15,
            ),
            qtp_contributions=ContributionSchedule(items=[
                Contribution(
                    date=datetime.date(2025 + i, 1, 1), amount=10000, account_type="qtp",
                )
                for i in range(5)
            ]),
            taxable_contributions=ContributionSchedule(items=[
                Contribution(
                    date=datetime.date(2025 + i, 1, 1), amount=10000, account_type="taxable",
                )
                for i in range(5)
            ]),
            portfolio_assumptions=PortfolioAssumptions(
                annual_return=0.07, dividend_yield=0.015,
                qualified_dividend_share=0.95, turnover_realization_rate=0.05,
            ),
            education_schedule=edu,
            qtp_assumptions=QTPAssumptions(),
            scenario_policy=ScenarioPolicy(qualified_use_probability=0.75),
            horizon_years=18,
        )
        result = analyze_tradeoff(config, NoIncomeTaxStateRule())

        assert result.qtp_aqee == pytest.approx(62000.0)
        assert result.delta > 0


class TestLossScenario:
    def test_negative_returns(self) -> None:
        """With negative returns, taxable account may have no gain to tax."""
        config = _make_config(qualified_use_probability=1.0)
        # Override with a portfolio that loses money
        config = config.model_copy(update={
            "portfolio_assumptions": PortfolioAssumptions(
                annual_return=-0.03,
                dividend_yield=0.0,
                qualified_dividend_share=0.0,
                turnover_realization_rate=0.0,
            ),
            "horizon_years": 5,
        })
        result = analyze_tradeoff(config, NoIncomeTaxStateRule())

        # Both accounts should have lost value
        assert result.qtp_ending_value < 10000
        assert result.taxable_ending_value_pre_liquidation < 10000
        # No liquidation tax when there's a loss
        assert result.taxable_terminal_liquidation_tax == pytest.approx(0.0)
        # 529 earnings should be negative
        assert result.qtp_earnings < 0


class TestExampleYAMLConfigs:
    def test_base_case(self) -> None:
        config = load_config(EXAMPLES_DIR / "base_case.yaml")
        result = analyze_tradeoff(config)
        assert result.delta > 0

    def test_scholarship_case(self) -> None:
        config = load_config(EXAMPLES_DIR / "scholarship_case.yaml")
        result = analyze_tradeoff(config)
        assert result.qtp_aqee < config.education_schedule.total_qualified_expense

    def test_aotc_overlap_case(self) -> None:
        config = load_config(EXAMPLES_DIR / "aotc_overlap_case.yaml")
        result = analyze_tradeoff(config)
        assert result.qtp_aqee < config.education_schedule.total_qualified_expense

    def test_roth_rollover_case(self) -> None:
        config = load_config(EXAMPLES_DIR / "roth_rollover_case.yaml")
        result = analyze_tradeoff(config)
        assert result.resolution_method == "mixed"
        assert result.drivers.roth_rollover_option_value > 0


class TestJSONRoundTrip:
    def test_to_json_and_back(self) -> None:
        config = _make_config(qualified_use_probability=0.8)
        result = analyze_tradeoff(config)

        json_str = result.to_json()
        d = result.to_dict()

        assert d["delta"] == result.delta
        assert '"delta"' in json_str
