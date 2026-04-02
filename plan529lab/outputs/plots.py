"""Plotting functions for plan529lab results.

All functions return matplotlib Figure objects and accept an optional
Axes for embedding into existing figures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from plan529lab.core.sensitivity import SensitivityResult, TwoWaySensitivityResult
    from plan529lab.models.monte_carlo import MonteCarloResult
    from plan529lab.models.results import TradeoffResult


def plot_delta_vs_probability(
    result: SensitivityResult,
    ax: Axes | None = None,
) -> Figure:
    """Plot delta vs qualified-use probability."""
    fig: Figure | None = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    ax.plot(result.param_values, result.deltas, "b-", linewidth=2)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.7)
    ax.set_xlabel(result.param_name.replace("_", " ").title())
    ax.set_ylabel("Delta (529 - Taxable, $)")
    ax.set_title("529 vs Taxable: Sensitivity to " + result.param_name.replace("_", " ").title())
    ax.grid(True, alpha=0.3)

    # Annotate break-even if it crosses zero
    for i, d in enumerate(result.deltas):
        if i > 0 and result.deltas[i - 1] * d < 0:
            ax.axvline(
                x=result.param_values[i], color="red", linestyle=":",
                alpha=0.7, label="~Break-even",
            )
            ax.legend()
            break

    assert fig is not None
    fig.tight_layout()
    return fig


def plot_delta_vs_years(
    result: SensitivityResult,
    ax: Axes | None = None,
) -> Figure:
    """Plot delta vs years to withdrawal."""
    fig: Figure | None = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    ax.plot(result.param_values, result.deltas, "b-", linewidth=2, marker="o", markersize=4)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.7)
    ax.set_xlabel("Years to Withdrawal")
    ax.set_ylabel("Delta (529 - Taxable, $)")
    ax.set_title("529 vs Taxable: Sensitivity to Investment Horizon")
    ax.grid(True, alpha=0.3)

    assert fig is not None
    fig.tight_layout()
    return fig


def plot_heatmap(
    result: TwoWaySensitivityResult,
    ax: Axes | None = None,
) -> Figure:
    """Plot a two-way sensitivity heatmap."""
    fig: Figure | None = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 7))
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    grid = np.array(result.delta_grid)
    vmax = max(abs(grid.min()), abs(grid.max()))

    im = ax.imshow(
        grid, aspect="auto", cmap="RdYlGn",
        vmin=-vmax, vmax=vmax, origin="lower",
    )

    ax.set_xticks(range(len(result.param_x_values)))
    ax.set_xticklabels([f"{v:.2f}" for v in result.param_x_values], rotation=45)
    ax.set_yticks(range(len(result.param_y_values)))
    ax.set_yticklabels([f"{v:.2f}" for v in result.param_y_values])

    ax.set_xlabel(result.param_x_name.replace("_", " ").title())
    ax.set_ylabel(result.param_y_name.replace("_", " ").title())
    ax.set_title("Delta Heatmap (529 - Taxable, $)")

    assert fig is not None
    fig.colorbar(im, ax=ax, label="Delta ($)")
    fig.tight_layout()
    return fig


def plot_waterfall(
    result: TradeoffResult,
    ax: Axes | None = None,
) -> Figure:
    """Plot a waterfall chart of the driver decomposition."""
    fig: Figure | None = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    d = result.drivers
    items = [
        ("Tax-Free Growth", d.federal_tax_free_growth_benefit),
        ("Dividend Drag", -d.taxable_dividend_drag_cost),
        ("Realization Drag", -d.taxable_realization_drag_cost),
        ("Liquidation Tax", -d.taxable_liquidation_cost),
        ("529 Income Tax", -d.nonqualified_qtp_income_tax_cost),
        ("529 10% Tax", -d.qtp_10_percent_additional_tax_cost),
        ("State Benefit", d.state_benefit_value),
        ("State Recapture", -d.state_recapture_cost),
        ("Roth Rollover", d.roth_rollover_option_value),
    ]

    labels = [item[0] for item in items]
    values = [item[1] for item in items]
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]

    cumulative = 0.0
    bottoms = []
    for v in values:
        if v >= 0:
            bottoms.append(cumulative)
        else:
            bottoms.append(cumulative + v)
        cumulative += v

    ax.barh(labels, [abs(v) for v in values], left=bottoms, color=colors, edgecolor="white")
    ax.axvline(x=0, color="black", linewidth=0.5)
    ax.set_xlabel("Impact on Delta ($)")
    ax.set_title("Driver Decomposition: 529 vs Taxable")
    ax.invert_yaxis()

    assert fig is not None
    fig.tight_layout()
    return fig


def plot_mc_histogram(
    result: MonteCarloResult,
    ax: Axes | None = None,
    bins: int = 50,
) -> Figure:
    """Plot a histogram of Monte Carlo delta distribution."""
    fig: Figure | None = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    deltas = np.array(result.deltas)
    ax.hist(deltas, bins=bins, color="#3498db", edgecolor="white", alpha=0.8)
    ax.axvline(x=result.mean_delta, color="red", linestyle="-", linewidth=2, label="Mean")
    ax.axvline(x=result.median_delta, color="orange", linestyle="--", linewidth=2, label="Median")
    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)

    # Shade regions
    ax.axvspan(0, deltas.max() if deltas.max() > 0 else 0, alpha=0.05, color="green")
    ax.axvspan(deltas.min() if deltas.min() < 0 else 0, 0, alpha=0.05, color="red")

    ax.set_xlabel("Delta (529 - Taxable, $)")
    ax.set_ylabel("Frequency")
    ax.set_title(
        f"Monte Carlo Distribution (n={result.n_paths:,}, "
        f"P(529 wins)={result.prob_qtp_wins:.1%})"
    )
    ax.legend()

    assert fig is not None
    fig.tight_layout()
    return fig
