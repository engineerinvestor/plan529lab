# plan529lab

[![CI](https://github.com/engineerinvestor/plan529lab/actions/workflows/ci.yml/badge.svg)](https://github.com/engineerinvestor/plan529lab/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/plan529lab)](https://pypi.org/project/plan529lab/)
[![Python](https://img.shields.io/pypi/pyversions/plan529lab)](https://pypi.org/project/plan529lab/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/engineerinvestor/plan529lab/blob/main/LICENSE)

A Python package for evaluating the after-tax tradeoff between investing through a **529/Qualified Tuition Program (QTP)** and a **taxable brokerage account** for education savings.

This is not a simple "529 penalty calculator." It is a **scenario engine** that compares after-tax outcomes across multiple future states — including qualified education use, nonqualified withdrawal, beneficiary change, and Roth IRA rollover paths.

> **Disclaimer:** This package is for educational and analytical purposes only. It is not tax, legal, or investment advice. Tax outcomes depend on facts, jurisdiction, and future law changes. Consult a qualified tax professional for your situation.

## Why This Exists

Public discussion of 529 plans often oversimplifies the tradeoff. Common claims that 529s are "risky" because of "penalties" miss key nuances:

- Only the **earnings portion** of a nonqualified withdrawal is taxable — contributions/basis come back tax-free
- The 10% additional tax applies to the **amount included in income**, not the entire withdrawal
- Qualified expenses must be reduced by tax-free educational assistance and expenses used for AOTC/LLC
- State tax benefits, recapture rules, and the Roth rollover path materially affect the comparison

This package makes these interactions explicit and quantifiable.

## Installation

```bash
pip install plan529lab
```

For development:

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Quick Start

### Python API

```python
from plan529lab.api import analyze_tradeoff
from plan529lab.io.yaml_loader import load_config
from plan529lab.state_rules.no_income_tax import NoIncomeTaxStateRule

config = load_config("examples/washington_no_income_tax.yaml")
result = analyze_tradeoff(config, state_rule=NoIncomeTaxStateRule("WA"))

print(result.explain())
print(f"Delta: ${result.delta:,.2f}")
print(f"Break-even probability: {result.break_even_qualified_use_probability:.1%}")
```

### Monte Carlo Simulation

```python
from plan529lab.api import run_monte_carlo
from plan529lab.models.monte_carlo import MonteCarloConfig, StochasticAssumptions

mc_config = MonteCarloConfig(
    n_paths=10_000,
    seed=42,
    stochastic=StochasticAssumptions(return_std=0.15),
)
mc_result = run_monte_carlo(config, mc_config)
print(f"P(529 wins): {mc_result.prob_qtp_wins:.1%}")
print(f"Mean delta: ${mc_result.mean_delta:,.2f}")
```

### Sensitivity Analysis

```python
from plan529lab.api import run_sensitivity

result = run_sensitivity(config, "qualified_use_probability", [0.0, 0.25, 0.5, 0.75, 1.0])
for v, d in zip(result.param_values, result.deltas):
    print(f"  p={v:.0%}: delta=${d:,.0f}")
```

### CLI

```bash
# Deterministic analysis
python -m plan529lab analyze --config examples/washington_no_income_tax.yaml

# Monte Carlo simulation
python -m plan529lab monte-carlo --config examples/washington_no_income_tax.yaml --n-sims 10000 --seed 42

# Sensitivity analysis
python -m plan529lab sensitivity --config examples/washington_no_income_tax.yaml \
    --param qualified_use_probability --min 0 --max 1 --steps 11

# Break-even probability
python -m plan529lab breakeven --config examples/washington_no_income_tax.yaml

# State rule info
python -m plan529lab state-info WA
```

## Configuration

Scenarios are defined in YAML files. See `examples/` for templates.

```yaml
tax_profile:
  ordinary_income_rate: 0.35
  ltcg_rate: 0.15
  qualified_dividend_rate: 0.15

portfolio_assumptions:
  annual_return: 0.07
  dividend_yield: 0.015
  qualified_dividend_share: 0.95
  turnover_realization_rate: 0.05

scenario_policy:
  qualified_use_probability: 0.75

horizon_years: 18
```

## State Rules

The package uses a plugin architecture for state-specific tax treatment:

- **NoIncomeTaxStateRule** — for WA, TX, FL, NV, SD, WY, AK, TN, NH
- **GenericDeductionStateRule** — models a state income tax deduction on 529 contributions
- **GenericCreditStateRule** — models a state tax credit on 529 contributions

Generic rules do not reflect any specific state's exact rules, caps, or conditions.

## Assumptions and Limitations

- Annual timesteps with start-of-year contributions
- Simplified taxable account model (no lot-level accounting, wash-sale rules, or AMT)
- Tax rates are assumed constant over the horizon
- Roth rollover uses one-shot eligibility estimate (not year-by-year staged rollover)
- Monte Carlo treats dividend yield and turnover as per-path constants (not per-year)
- State rules are generic unless specifically implemented

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check .

# Type check
mypy .
```

## License

MIT
