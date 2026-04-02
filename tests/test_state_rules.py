"""Tests for state rule plugins and registry."""

import pytest

from plan529lab.models.tax_profile import InvestorTaxProfile
from plan529lab.state_rules.generic_credit import GenericCreditStateRule
from plan529lab.state_rules.generic_deduction import GenericDeductionStateRule
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule
from plan529lab.tax.state_registry import get_state_rule


def _profile_with_state() -> InvestorTaxProfile:
    return InvestorTaxProfile(
        ordinary_income_rate=0.24,
        ltcg_rate=0.15,
        qualified_dividend_rate=0.15,
        state_ordinary_rate=0.05,
    )


class TestNoIncomeTaxStateRule:
    def test_zero_benefit(self) -> None:
        rule = NoIncomeTaxStateRule("WA")
        assert rule.contribution_benefit(10000, _profile_with_state(), 2025) == 0.0

    def test_zero_recapture(self) -> None:
        rule = NoIncomeTaxStateRule("WA")
        assert rule.recapture_tax(10000, _profile_with_state(), 2025) == 0.0

    def test_metadata(self) -> None:
        rule = NoIncomeTaxStateRule("TX")
        meta = rule.metadata()
        assert meta["state_code"] == "TX"


class TestGenericDeductionStateRule:
    def test_benefit(self) -> None:
        rule = GenericDeductionStateRule("NY")
        profile = _profile_with_state()
        # 10000 * 0.05 = 500
        assert rule.contribution_benefit(10000, profile, 2025) == pytest.approx(500.0)

    def test_recapture(self) -> None:
        rule = GenericDeductionStateRule("NY")
        profile = _profile_with_state()
        assert rule.recapture_tax(10000, profile, 2025) == pytest.approx(500.0)

    def test_zero_state_rate_warning(self) -> None:
        rule = GenericDeductionStateRule()
        profile = InvestorTaxProfile(
            ordinary_income_rate=0.24,
            ltcg_rate=0.15,
            qualified_dividend_rate=0.15,
        )

        class FakeContext:
            tax_profile = profile

        warnings = rule.validate(FakeContext())
        assert len(warnings) == 1
        assert "state_ordinary_rate is 0" in warnings[0]


class TestGenericCreditStateRule:
    def test_benefit(self) -> None:
        rule = GenericCreditStateRule("IN", credit_rate=0.20)
        profile = _profile_with_state()
        # 5000 * 0.20 = 1000
        assert rule.contribution_benefit(5000, profile, 2025) == pytest.approx(1000.0)

    def test_recapture(self) -> None:
        rule = GenericCreditStateRule("IN", credit_rate=0.20)
        assert rule.recapture_tax(5000, _profile_with_state(), 2025) == pytest.approx(1000.0)

    def test_zero_credit_warning(self) -> None:
        rule = GenericCreditStateRule()
        warnings = rule.validate(None)
        assert any("credit_rate is 0" in w for w in warnings)


class TestStateRegistry:
    def test_lookup_wa(self) -> None:
        rule = get_state_rule("WA")
        assert isinstance(rule, NoIncomeTaxStateRule)
        assert rule.state_code == "WA"

    def test_lookup_deduction(self) -> None:
        rule = get_state_rule("DEDUCTION")
        assert isinstance(rule, GenericDeductionStateRule)

    def test_lookup_case_insensitive(self) -> None:
        rule = get_state_rule("wa")
        assert isinstance(rule, NoIncomeTaxStateRule)

    def test_unknown_state_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown state code"):
            get_state_rule("ZZ")

    def test_no_income_tax_states(self) -> None:
        for code in ["WA", "TX", "FL", "NV", "SD", "WY", "AK", "TN", "NH"]:
            rule = get_state_rule(code)
            assert isinstance(rule, NoIncomeTaxStateRule)
