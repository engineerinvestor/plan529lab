# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-04-01

### Added

- Deterministic 529 vs taxable brokerage tradeoff analysis
- Federal QTP tax formulas: AQEE, taxable earnings, 10% additional tax with exceptions
- Taxable account tax drag: dividend tax, realized gain tax, terminal liquidation tax
- Year-by-year growth models for both account types
- 5 leftover resolution modes: withdraw nonqualified, Roth rollover, beneficiary change, hold for future education, mixed
- Roth IRA rollover estimation (post-SECURE 2.0): eligibility, cap, timeline
- AOTC/LLC credit coordination with 529 distributions
- Break-even solvers: qualified-use probability, horizon, tax efficiency, state benefit
- Monte Carlo stochastic simulation with per-year log-normal returns
- One-way and two-way sensitivity analysis
- State tax plugin architecture with 3 built-in rules: no-income-tax, generic deduction, generic credit
- 5 matplotlib plots: delta vs probability, delta vs years, 2D heatmap, waterfall, MC histogram
- CLI with 5 commands: analyze, monte-carlo, sensitivity, breakeven, state-info
- YAML and JSON configuration loaders
- TradeoffEngine OOP wrapper
- 183 tests including property-based tests with hypothesis
- Full type annotations (mypy strict)
