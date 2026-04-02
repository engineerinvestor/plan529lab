# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**plan529lab** is a Python 3.11+ open-source package that evaluates the after-tax tradeoff between investing through a 529/Qualified Tuition Program (QTP) and a taxable brokerage account for education savings.

This is **not** a simple penalty calculator. It is a scenario engine that compares after-tax outcomes across multiple future states, including qualified use, nonqualified withdrawal, beneficiary change, Roth IRA rollover, and mixed resolution paths.

The full specification is in `SPEC.md`. Background research and product rationale are in `background_information.md`.

## Architecture

The package lives under `plan529lab/` with these layers:

- **models/** — Pydantic v2 frozen models: `InvestorTaxProfile`, `PortfolioAssumptions`, `QTPAssumptions`, `ScenarioPolicy`, `ContributionSchedule`, `EducationExpenseSchedule`, `MonteCarloConfig`, `TradeoffResult`
- **core/** — Engines: `deterministic.py` (two-state weighted analysis), `resolution.py` (5 leftover resolution modes), `monte_carlo.py` (N-path stochastic simulation), `sensitivity.py` (one-way and two-way parameter sweeps), `breakeven.py` (probability, horizon, tax-efficiency, state-benefit solvers), `growth.py` (year-by-year QTP and taxable account growth)
- **tax/** — Federal QTP formulas (`federal_qtp.py`), taxable account tax drag (`taxable_account.py`), Roth rollover estimation (`roth_rollover.py`), AOTC/LLC credit coordination (`credits_coordination.py`), state plugin ABC (`state_base.py`) and registry (`state_registry.py`)
- **state_rules/** — `NoIncomeTaxStateRule`, `GenericDeductionStateRule`, `GenericCreditStateRule`
- **outputs/** — `tables.py`, `plots.py` (5 matplotlib plot types), `explain.py`, `export.py`
- **io/** — YAML/JSON config loading
- **api.py** — Public API: `analyze_tradeoff()`, `run_monte_carlo()`, `run_sensitivity()`, `run_two_way_sensitivity()`
- **cli.py** — CLI: `analyze`, `monte-carlo`, `sensitivity`, `breakeven`, `state-info`

## Key Tax Rules the Code Must Enforce

1. Only the **earnings portion** of a nonqualified 529 distribution is taxable — basis/contributions come back tax-free
2. The 10% additional tax applies to the **amount included in income**, not the entire withdrawal
3. AQEE = Qualified Expenses - Tax-Free Aid - Expenses used for AOTC/LLC
4. Taxable earnings formula: `E * (1 - min(Q, D) / D)` where E=earnings, Q=AQEE, D=gross distribution
5. Roth rollover has: 15-year account age requirement, annual IRA contribution limit, lifetime cap, 5-year lookback exclusion
6. State deduction/credit and recapture must be modeled via plugins, never hardcoded for specific states

## Build and Development

- **Language:** Python 3.11+
- **Core deps:** numpy, pandas, pydantic>=2.0, pyyaml, matplotlib, scipy, click
- **Linting:** `ruff check .` — all code must pass
- **Type checking:** `mypy .` — all code must pass (strict mode)
- **Testing:** `pytest` — unit, integration, property-based (hypothesis), CLI smoke tests
- **License:** MIT
- **pip:** When pip reports a new version is available, update it with `pip install --upgrade pip`

## Testing Philosophy

- Property tests: taxable earnings never negative, basis never taxed twice, break-even in [0,1]
- Zero-variance bridge test: Monte Carlo with all stds=0 must exactly match deterministic result
- Monotonicity tests: delta increases with annual_return in sensitivity sweeps
- CLI smoke tests via click.testing.CliRunner
- 175+ tests across 14 test files

## Design Principles

- Tax functions are pure (floats in/out) for testability against IRS Publication 970 examples
- Growth functions accept optional `annual_returns: Sequence[float]` for Monte Carlo per-year draws while preserving deterministic backward compatibility
- Frozen Pydantic models prevent mutation; config changes use `model_copy(update=...)`
- Monte Carlo reuses the deterministic engine (N paths, not vectorized numpy) — simple and correct
- Sensitivity sweeps are deterministic, not MC-based — isolated effect of each parameter
- State logic is isolated from the federal core via the plugin architecture
- This is an analytical engine, not tax-prep software — outputs are assumption-dependent estimates
