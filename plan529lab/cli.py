"""Command-line interface for plan529lab."""

from __future__ import annotations

import json
import sys

import click

from plan529lab.api import analyze_tradeoff, run_monte_carlo, run_sensitivity
from plan529lab.io.yaml_loader import load_config
from plan529lab.models.monte_carlo import MonteCarloConfig, StochasticAssumptions
from plan529lab.outputs.explain import explain
from plan529lab.outputs.export import result_to_json
from plan529lab.outputs.tables import format_driver_table, format_summary_table
from plan529lab.tax.state_registry import get_state_rule


def _load_state_rule(state_code: str | None) -> object | None:
    if not state_code:
        return None
    try:
        return get_state_rule(state_code)
    except KeyError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


def _load_config(config_path: str) -> object:
    try:
        return load_config(config_path)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)


@click.group()
def main() -> None:
    """plan529lab — 529 vs taxable brokerage after-tax tradeoff engine."""


@main.command()
@click.option("--config", "config_path", required=True, help="Path to YAML config file.")
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text", help="Output format.",
)
@click.option("--state", "state_code", default=None, help="State code.")
def analyze(config_path: str, output_format: str, state_code: str | None) -> None:
    """Run a deterministic 529 vs taxable tradeoff analysis."""
    config = _load_config(config_path)
    state_rule = _load_state_rule(state_code)
    result = analyze_tradeoff(config, state_rule=state_rule)  # type: ignore[arg-type]

    if output_format == "json":
        click.echo(result_to_json(result))
    else:
        click.echo(explain(result))
        click.echo()
        click.echo(format_summary_table(result))
        click.echo()
        click.echo(format_driver_table(result))


@main.command()
@click.option("--config", "config_path", required=True, help="Path to YAML config file.")
@click.option("--state", "state_code", default=None, help="State code.")
def breakeven(config_path: str, state_code: str | None) -> None:
    """Compute break-even qualified-use probability."""
    config = _load_config(config_path)
    state_rule = _load_state_rule(state_code)
    result = analyze_tradeoff(config, state_rule=state_rule)  # type: ignore[arg-type]

    if result.break_even_qualified_use_probability is not None:
        click.echo(
            f"Break-even qualified-use probability: "
            f"{result.break_even_qualified_use_probability:.1%}"
        )
        click.echo()
        click.echo(
            f"At probabilities above "
            f"{result.break_even_qualified_use_probability:.1%}, "
            f"the 529 strategy is expected to outperform."
        )
    else:
        click.echo("Break-even probability is undefined for this scenario.")


@main.command(name="state-info")
@click.argument("state_code")
def state_info(state_code: str) -> None:
    """Show metadata for a state rule implementation."""
    try:
        rule = get_state_rule(state_code)
    except KeyError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    meta = rule.metadata()
    click.echo(f"State Code: {meta['state_code']}")
    click.echo(f"Rule Class: {meta['class']}")
    for key, value in meta.items():
        if key not in ("state_code", "class"):
            click.echo(f"{key}: {value}")


@main.command(name="monte-carlo")
@click.option("--config", "config_path", required=True, help="Path to YAML config file.")
@click.option("--n-sims", default=10000, help="Number of simulation paths.")
@click.option("--seed", default=None, type=int, help="Random seed.")
@click.option("--return-std", default=0.15, help="Return volatility (std dev).")
@click.option("--state", "state_code", default=None, help="State code.")
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text", help="Output format.",
)
def monte_carlo(
    config_path: str,
    n_sims: int,
    seed: int | None,
    return_std: float,
    state_code: str | None,
    output_format: str,
) -> None:
    """Run a Monte Carlo simulation."""
    config = _load_config(config_path)
    state_rule = _load_state_rule(state_code)

    mc_config = MonteCarloConfig(
        n_paths=n_sims,
        seed=seed,
        stochastic=StochasticAssumptions(return_std=return_std),
    )
    result = run_monte_carlo(
        config, mc_config, state_rule=state_rule,  # type: ignore[arg-type]
    )

    if output_format == "json":
        out = {
            "n_paths": result.n_paths,
            "seed": result.seed,
            "mean_delta": result.mean_delta,
            "median_delta": result.median_delta,
            "std_delta": result.std_delta,
            "prob_qtp_wins": result.prob_qtp_wins,
            "percentiles": result.percentile_values,
        }
        click.echo(json.dumps(out, indent=2))
    else:
        click.echo(f"Monte Carlo Simulation ({result.n_paths:,} paths)")
        click.echo(f"  Mean Delta:     ${result.mean_delta:,.2f}")
        click.echo(f"  Median Delta:   ${result.median_delta:,.2f}")
        click.echo(f"  Std Dev:        ${result.std_delta:,.2f}")
        click.echo(f"  P(529 wins):    {result.prob_qtp_wins:.1%}")
        click.echo()
        click.echo("Percentiles:")
        for p, v in sorted(result.percentile_values.items(), key=lambda x: float(x[0])):
            click.echo(f"  {float(p):5.1f}th: ${v:,.2f}")


@main.command()
@click.option("--config", "config_path", required=True, help="Path to YAML config file.")
@click.option("--param", required=True, help="Parameter to sweep.")
@click.option("--min", "min_val", required=True, type=float, help="Minimum value.")
@click.option("--max", "max_val", required=True, type=float, help="Maximum value.")
@click.option("--steps", default=10, type=int, help="Number of steps.")
@click.option("--state", "state_code", default=None, help="State code.")
def sensitivity(
    config_path: str,
    param: str,
    min_val: float,
    max_val: float,
    steps: int,
    state_code: str | None,
) -> None:
    """Run a one-way sensitivity analysis."""
    config = _load_config(config_path)
    state_rule = _load_state_rule(state_code)

    step_size = (max_val - min_val) / max(steps - 1, 1)
    values = [min_val + i * step_size for i in range(steps)]

    try:
        result = run_sensitivity(
            config, param, values, state_rule=state_rule,  # type: ignore[arg-type]
        )
    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    click.echo(f"Sensitivity: {param}")
    click.echo(f"{'Value':>12}  {'Delta':>14}  {'Break-Even':>12}")
    click.echo("-" * 42)
    for v, d, be in zip(result.param_values, result.deltas, result.break_evens):
        be_str = f"{be:.1%}" if be is not None else "N/A"
        click.echo(f"{v:12.4f}  ${d:13,.2f}  {be_str:>12}")
