"""Summary table formatting for tradeoff results."""

from __future__ import annotations

from plan529lab.models.monte_carlo import MonteCarloResult
from plan529lab.models.results import TradeoffResult


def format_summary_table(result: TradeoffResult) -> str:
    """Format a complete summary table of the tradeoff analysis."""
    rows = [
        ("529/QTP Account", ""),
        ("  Ending Value", f"${result.qtp_ending_value:,.2f}"),
        ("  Basis (Contributions)", f"${result.qtp_basis:,.2f}"),
        ("  Earnings", f"${result.qtp_earnings:,.2f}"),
        ("  AQEE", f"${result.qtp_aqee:,.2f}"),
        ("  Taxable Earnings", f"${result.qtp_taxable_earnings:,.2f}"),
        ("  Income Tax Due", f"${result.qtp_income_tax:,.2f}"),
        ("  Additional Tax (10%)", f"${result.qtp_additional_tax:,.2f}"),
        ("  State Recapture", f"${result.qtp_state_recapture_tax:,.2f}"),
        ("  State Benefit", f"${result.qtp_state_benefit:,.2f}"),
        ("  After-Tax Value", f"${result.qtp_after_tax_value:,.2f}"),
        ("", ""),
        ("Taxable Brokerage Account", ""),
        (
            "  Ending Value (Pre-Liquidation)",
            f"${result.taxable_ending_value_pre_liquidation:,.2f}",
        ),
        ("  Tax Basis", f"${result.taxable_basis:,.2f}"),
        ("  Unrealized Gain", f"${result.taxable_unrealized_gain:,.2f}"),
        ("  Cumulative Dividend Taxes", f"${result.taxable_dividend_tax_drag:,.2f}"),
        ("  Cumulative Realized Gain Taxes", f"${result.taxable_realized_gain_tax_drag:,.2f}"),
        ("  Terminal Liquidation Tax", f"${result.taxable_terminal_liquidation_tax:,.2f}"),
        ("  After-Tax Value", f"${result.taxable_after_tax_value:,.2f}"),
        ("", ""),
        ("Comparison", ""),
        ("  Delta (529 - Taxable)", f"${result.delta:,.2f}"),
    ]

    if result.break_even_qualified_use_probability is not None:
        rows.append((
            "  Break-Even Qualified-Use Probability",
            f"{result.break_even_qualified_use_probability:.1%}",
        ))

    # Format as aligned table
    max_label = max(len(r[0]) for r in rows)
    lines = []
    for label, value in rows:
        if not label and not value:
            lines.append("")
        elif not value:
            lines.append(label)
        else:
            lines.append(f"  {label:<{max_label}}  {value}")
    return "\n".join(lines)


def format_driver_table(result: TradeoffResult) -> str:
    """Format the driver decomposition table."""
    d = result.drivers
    rows = [
        ("Federal Tax-Free Growth Benefit", f"+${d.federal_tax_free_growth_benefit:,.2f}"),
        ("Taxable Dividend Drag Cost", f"-${d.taxable_dividend_drag_cost:,.2f}"),
        ("Taxable Realization Drag Cost", f"-${d.taxable_realization_drag_cost:,.2f}"),
        ("Taxable Liquidation Cost", f"-${d.taxable_liquidation_cost:,.2f}"),
        ("Nonqualified 529 Income Tax Cost", f"-${d.nonqualified_qtp_income_tax_cost:,.2f}"),
        ("529 10% Additional Tax Cost", f"-${d.qtp_10_percent_additional_tax_cost:,.2f}"),
        ("State Benefit Value", f"+${d.state_benefit_value:,.2f}"),
        ("State Recapture Cost", f"-${d.state_recapture_cost:,.2f}"),
        ("Roth Rollover Option Value", f"+${d.roth_rollover_option_value:,.2f}"),
    ]

    max_label = max(len(r[0]) for r in rows)
    lines = ["Driver Decomposition"]
    for label, value in rows:
        lines.append(f"  {label:<{max_label}}  {value}")
    return "\n".join(lines)


def format_mc_summary_table(result: MonteCarloResult) -> str:
    """Format a summary table of Monte Carlo simulation results."""
    lines = [
        f"Monte Carlo Simulation ({result.n_paths:,} paths)",
        f"  Mean Delta:     ${result.mean_delta:,.2f}",
        f"  Median Delta:   ${result.median_delta:,.2f}",
        f"  Std Dev:        ${result.std_delta:,.2f}",
        f"  P(529 wins):    {result.prob_qtp_wins:.1%}",
        "",
        "Percentiles:",
    ]
    for p, v in sorted(
        result.percentile_values.items(), key=lambda x: float(x[0])
    ):
        lines.append(f"  {float(p):5.1f}th: ${v:,.2f}")
    return "\n".join(lines)
