"""Tests for output formatting."""

from plan529lab.models.results import DriverDecomposition, TradeoffResult
from plan529lab.outputs.tables import format_driver_table, format_summary_table


def _sample_result() -> TradeoffResult:
    return TradeoffResult(
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
        drivers=DriverDecomposition(
            federal_tax_free_growth_benefit=3000,
            taxable_dividend_drag_cost=1500,
            taxable_realization_drag_cost=800,
        ),
    )


class TestSummaryTable:
    def test_contains_key_rows(self) -> None:
        table = format_summary_table(_sample_result())
        assert "529/QTP Account" in table
        assert "Taxable Brokerage Account" in table
        assert "Delta" in table
        assert "Break-Even" in table

    def test_contains_values(self) -> None:
        table = format_summary_table(_sample_result())
        assert "$50,000.00" in table
        assert "$5,000.00" in table


class TestDriverTable:
    def test_contains_drivers(self) -> None:
        table = format_driver_table(_sample_result())
        assert "Federal Tax-Free Growth Benefit" in table
        assert "Taxable Dividend Drag Cost" in table
        assert "Driver Decomposition" in table


class TestExplain:
    def test_explain_output(self) -> None:
        result = _sample_result()
        text = result.explain()
        assert "529 strategy" in text
        assert "$5,000" in text
        assert "42.0%" in text
