"""Result models for tradeoff analysis."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


class QTPGrowthResult(BaseModel, frozen=True):
    """Growth result for a 529/QTP account."""

    ending_value: float
    total_contributions: float
    total_earnings: float
    state_tax_benefit: float = 0.0


class TaxableGrowthResult(BaseModel, frozen=True):
    """Growth result for a taxable brokerage account."""

    ending_value_pre_liquidation: float
    tax_basis: float
    unrealized_gain: float
    cumulative_dividend_tax: float
    cumulative_realized_gain_tax: float
    terminal_liquidation_tax: float
    ending_value_after_tax: float


class DriverDecomposition(BaseModel, frozen=True):
    """Decomposition of the delta into interpretable drivers."""

    federal_tax_free_growth_benefit: float = 0.0
    taxable_dividend_drag_cost: float = 0.0
    taxable_realization_drag_cost: float = 0.0
    taxable_liquidation_cost: float = 0.0
    nonqualified_qtp_income_tax_cost: float = 0.0
    qtp_10_percent_additional_tax_cost: float = 0.0
    state_benefit_value: float = 0.0
    state_recapture_cost: float = 0.0
    roth_rollover_option_value: float = 0.0


class TradeoffResult(BaseModel, frozen=True):
    """Complete result of a 529 vs taxable tradeoff analysis."""

    # Core outcomes
    qtp_after_tax_value: float
    taxable_after_tax_value: float
    delta: float

    # QTP detail
    qtp_ending_value: float
    qtp_basis: float
    qtp_earnings: float
    qtp_aqee: float
    qtp_taxable_earnings: float
    qtp_income_tax: float
    qtp_additional_tax: float
    qtp_state_recapture_tax: float
    qtp_state_benefit: float

    # Taxable detail
    taxable_ending_value_pre_liquidation: float
    taxable_basis: float
    taxable_unrealized_gain: float
    taxable_dividend_tax_drag: float
    taxable_realized_gain_tax_drag: float
    taxable_terminal_liquidation_tax: float

    # Break-even
    break_even_qualified_use_probability: float | None = None

    # Decomposition
    drivers: DriverDecomposition = DriverDecomposition()

    # Resolution detail
    resolution_method: str | None = None

    # Metadata
    warnings: list[str] = []
    assumptions_snapshot: dict[str, Any] = {}

    def explain(self) -> str:
        """Human-readable explanation of the tradeoff result."""
        lines: list[str] = []

        if self.delta > 0:
            lines.append(
                f"Under the assumptions provided, the 529 strategy ends with "
                f"${self.delta:,.0f} more after tax than the taxable brokerage strategy."
            )
        elif self.delta < 0:
            lines.append(
                f"Under the assumptions provided, the taxable brokerage strategy ends with "
                f"${abs(self.delta):,.0f} more after tax than the 529 strategy."
            )
        else:
            lines.append(
                "Under the assumptions provided, the 529 and taxable strategies "
                "produce identical after-tax outcomes."
            )

        lines.append("")
        lines.append("Key drivers:")

        d = self.drivers
        driver_items = [
            (d.federal_tax_free_growth_benefit, "from federally tax-free qualified growth"),
            (-d.taxable_dividend_drag_cost, "from taxable-account dividend tax drag"),
            (-d.taxable_realization_drag_cost, "from taxable-account realization tax drag"),
            (-d.taxable_liquidation_cost, "from taxable-account terminal liquidation tax"),
            (-d.nonqualified_qtp_income_tax_cost, "from nonqualified 529 income tax"),
            (-d.qtp_10_percent_additional_tax_cost, "from 529 10% additional tax"),
            (d.state_benefit_value, "from state tax benefit"),
            (-d.state_recapture_cost, "from state tax recapture"),
            (d.roth_rollover_option_value, "from Roth rollover option value"),
        ]

        for value, label in driver_items:
            sign = "+" if value >= 0 else "-"
            lines.append(f"  {sign}${abs(value):,.0f} {label}")

        if self.break_even_qualified_use_probability is not None:
            lines.append("")
            lines.append(
                f"Break-even qualified-use probability: "
                f"{self.break_even_qualified_use_probability:.1%}"
            )

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
