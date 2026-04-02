# SPEC.md — Open-Source Python Trade Analysis Package for 529 Plan vs. Taxable Brokerage Evaluation

**Working package names:** `collegeplan-qtp`, `qtp-tradeoff`, `plan529lab`  
**Recommended initial home:** `collegeplan.qtp_tradeoff` inside the existing `collegeplan` ecosystem  
**Status:** Draft v1 specification  
**License target:** MIT or BSD-3-Clause  
**Primary language:** Python 3.11+

---

## 1. Purpose

Build an open-source Python package that evaluates the **after-tax tradeoff** between:

1. Investing through a **529 / Qualified Tuition Program (QTP)**, and
2. Investing through a **taxable brokerage account**

for education savings and related fallback paths.

The package must quantify, not merely describe:

- when a 529 clearly dominates,
- when a taxable account is competitive because flexibility matters,
- how large the downside is if 529 funds are not fully used for qualified education,
- and what assumptions drive the answer.

This is **not** just a “529 penalty calculator.” It is a **scenario engine** for comparing after-tax outcomes across multiple future states.

---

## 2. Product Thesis

Public discussion of 529 plans is often too simplistic. A common framing is that the 529 is “risky” because a nonqualified withdrawal gets “penalized.” That framing is incomplete.

The package should make the following distinctions explicit:

- Contributions / basis are generally returned tax-free.
- Only the **earnings portion** of a nonqualified distribution can become taxable.
- The federal **10% additional tax** generally applies to the **amount included in income**, not the entire withdrawal.
- Qualified expenses must be reduced by **tax-free educational assistance**.
- Expenses used to claim the **American Opportunity Credit (AOTC)** or **Lifetime Learning Credit (LLC)** cannot also shield the same 529 distribution from tax.
- State tax benefits, state recapture rules, beneficiary changes, and Roth rollover rules materially affect the comparison.

The package exists to surface these interactions clearly and reproducibly.

---

## 3. Goals

### 3.1 Primary goals

- Compute **after-tax ending wealth** under 529 and taxable-account strategies.
- Model both **fully qualified** and **partially/nonqualified** 529 outcomes.
- Estimate **break-even qualified-use probability** where 529 overtakes taxable.
- Decompose outcome differences into interpretable drivers:
  - federal tax-free growth benefit,
  - taxable-account annual tax drag,
  - nonqualified withdrawal tax cost,
  - 10% additional tax,
  - state deduction/credit benefit,
  - state recapture,
  - AOTC/LLC overlap,
  - Roth rollover salvage value.
- Support deterministic and Monte Carlo analysis.
- Be transparent enough for users to audit assumptions.

### 3.2 Secondary goals

- Provide a clean Python API.
- Provide a CLI for quick scenario analysis.
- Provide exportable tables and plots.
- Serve as the computational core for a future whitepaper, notebook, or web calculator.

---

## 4. Non-goals

The v1 package is **not** intended to:

- file taxes,
- provide personalized tax or legal advice,
- replicate every state 529 program in full detail at launch,
- optimize household-wide tax returns,
- model every education benefit in the U.S. tax code,
- or replace a CPA/EA/financial planner.

The package is an **analytical engine**, not tax-prep software.

---

## 5. User Personas

### 5.1 Individual saver / parent
Wants to know whether uncertain future education use still justifies 529 funding.

### 5.2 Financial blogger / researcher
Wants to publish transparent math on the tradeoff.

### 5.3 Financial planner / analytically oriented advisor
Wants scenario-based evidence instead of rules of thumb.

### 5.4 Open-source contributor
Wants a modular framework to add state-specific rules, new scenario types, and visualizations.

---

## 6. Core Questions the Package Must Answer

1. If education use is highly likely, how much better is a 529 than taxable?
2. If qualified use is uncertain, how bad is the downside of “overfunding” a 529?
3. At what probability of qualified use does the 529 break even versus taxable?
4. How much do dividends, turnover, and liquidation taxes hurt the taxable account?
5. How much do scholarships and AOTC/LLC coordination reduce 529 tax-free treatment?
6. How valuable are state tax deductions/credits and how costly is recapture?
7. How much salvage value comes from changing beneficiaries or using the Roth rollover path?
8. How sensitive are conclusions to investment horizon, tax rates, and portfolio tax efficiency?

---

## 7. Governing Tax Model Assumptions

This package must be explicit that it encodes a **rule model**, not a legal opinion.

### 7.1 Federal 529 / QTP principles to encode

The engine must reflect the following federal concepts:

- The gross distribution is split between **earnings** and **basis/return of investment**.
- The basis portion is not included in income.
- Earnings are tax-free to the extent matched by **AQEE**.
- **AQEE** equals qualified education expenses reduced by **tax-free educational assistance**.
- AQEE must also be reduced by expenses used for the **AOTC/LLC**.
- If there is taxable distributed earnings, a **10% additional tax** generally applies to the amount included in income unless an exception applies.
- Exceptions include, among others, death, disability, scholarship/tax-free assistance, military academy attendance, and amounts made taxable only because expenses were used for AOTC/LLC.

### 7.2 Roth rollover path to encode

The package must support the post-2023 special rollover from a 529/QTP to the beneficiary’s Roth IRA, subject to rule checks, including:

- direct trustee-to-trustee transfer,
- annual Roth IRA contribution limit constraint,
- lifetime cap constraint,
- account age requirement,
- and exclusion of recent contributions / attributable earnings under the lookback rule.

### 7.3 State modeling principles

State treatment varies. Some states offer deductions or credits; some may require **recapture** if conditions are later violated or if an out-of-state plan is chosen. The package must model state benefits through plugins rather than hard-coded assumptions.

### 7.4 Washington example

Washington currently does **not** impose a state personal income tax, so for Washington users there is generally no state income-tax deduction/credit to model on 529 contributions. This makes the comparison more directly about federal tax-free qualified growth versus taxable-account flexibility and tax drag.

---

## 8. Recommendation on Product Direction

### Recommendation
**Build it.**

### Why

- The public discourse around 529 “penalties” is often materially incomplete.
- The tradeoff is multidimensional and benefits from reusable open-source tooling.
- This package would support research, blog posts, calculators, and future planning tools.
- It is especially valuable for users in states with no deduction/credit, because the comparison becomes more subtle and probability-based.

### Why not build it as a standalone repo first

I recommend **starting inside `collegeplan`** unless there is a strong branding or packaging reason not to.

#### Pros of integrating into `collegeplan`
- Lower maintenance burden
- Shared distributions / education-savings audience
- Easier reuse of contribution schedules and education cost logic
- Faster path to whitepaper and app integration

#### Cons of integrating into `collegeplan`
- Broader scope inside one repo
- Some users may want a narrower package

#### Final recommendation
Start as `collegeplan.qtp_tradeoff`, then split out later only if adoption justifies a dedicated package.

---

## 9. High-Level Functional Requirements

### 9.1 Deterministic analysis
The package shall support deterministic modeling with explicit user assumptions.

### 9.2 Monte Carlo analysis
The package shall support Monte Carlo analysis for:

- uncertain returns,
- uncertain qualified-use percentage,
- uncertain scholarship/tax-free aid,
- uncertain education timing,
- uncertain state of leftover-balance resolution.

### 9.3 Scenario branching
The package shall support distinct scenario branches, including:

- fully qualified education use,
- partially qualified use,
- fully nonqualified withdrawal,
- beneficiary change,
- hold for future education,
- rollover to Roth IRA,
- mixed resolution of leftover balances.

### 9.4 Sensitivity analysis
The package shall support one-way and two-way sensitivity analyses over:

- years to withdrawal,
- expected return,
- dividend yield,
- turnover/realization rate,
- ordinary income tax rate,
- LTCG rate,
- qualified dividend rate,
- state deduction/credit,
- state recapture,
- qualified-use probability.

### 9.5 Break-even analysis
The package shall compute:

- break-even probability of qualified use,
- break-even years-to-use,
- break-even taxable-account tax efficiency,
- break-even state tax benefit.

---

## 10. Core Domain Model

### 10.1 Main entities

#### `InvestorTaxProfile`
Represents federal and state tax assumptions.

Fields:
- `ordinary_income_rate: float`
- `ltcg_rate: float`
- `qualified_dividend_rate: float`
- `niit_rate: float = 0.0`
- `state_ordinary_rate: float = 0.0`
- `state_cap_gains_rate: float = 0.0`
- `filing_status: str | None = None`

#### `Contribution`
Represents a dated contribution.

Fields:
- `date: datetime | date`
- `amount: float`
- `account_type: Literal["qtp", "taxable"]`
- `source: Optional[str]`

#### `ContributionSchedule`
Represents a contribution plan over time.

Fields:
- `items: list[Contribution]`

#### `PortfolioAssumptions`
Represents expected investment behavior.

Fields:
- `annual_return: float`
- `dividend_yield: float`
- `qualified_dividend_share: float`
- `turnover_realization_rate: float`
- `expense_ratio: float = 0.0`
- `inflation_rate: float = 0.0`

#### `QTPAssumptions`
Represents 529-specific assumptions.

Fields:
- `state_tax_deduction_rate: float = 0.0`
- `state_tax_credit_rate: float = 0.0`
- `state_tax_recapture_rate: float = 0.0`
- `plan_fee_drag: float = 0.0`
- `roth_rollover_enabled: bool = False`
- `beneficiary_change_allowed: bool = True`

#### `EducationExpenseSchedule`
Represents expected education expenses by year.

Fields:
- `items: list[EducationExpenseItem]`

#### `EducationExpenseItem`
Fields:
- `date: datetime | date`
- `qualified_expense: float`
- `tax_free_assistance: float = 0.0`
- `aotc_or_llc_allocated_expense: float = 0.0`
- `notes: Optional[str]`

#### `ScenarioPolicy`
Represents how leftover funds are handled.

Fields:
- `leftover_resolution: Literal[
    "withdraw_nonqualified",
    "change_beneficiary",
    "hold_for_future_education",
    "roth_rollover",
    "mixed"
  ]`
- `qualified_use_probability: float | None`
- `scholarship_exception_probability: float | None`
- `roth_rollover_fraction: float = 0.0`

#### `StateRule`
Abstract interface for state-specific 529 treatment.

Methods:
- `contribution_benefit(...) -> float`
- `recapture_tax(...) -> float`
- `validate_plan_choice(...) -> list[str]`
- `metadata() -> dict`

---

## 11. Calculation Engine Requirements

## 11.1 General design
The engine shall separate:

1. **account growth modeling**,
2. **expense coverage and AQEE allocation**,
3. **tax computation**, and
4. **scenario aggregation**.

This separation is mandatory for transparency and testability.

### 11.2 529 / QTP growth model
For a given time horizon, the QTP account shall accumulate:

- contributions,
- net returns,
- fees,
- and optionally track lot-level contribution dates for Roth rollover eligibility.

Minimum tracked state variables:
- `ending_value`
- `total_contributions`
- `total_earnings`
- `eligible_for_roth_rollover_value`
- `ineligible_recent_contributions_value`

### 11.3 Taxable brokerage growth model
The taxable account shall model:

- annual dividend distributions,
- fraction of dividends that are qualified,
- annual realized gains from turnover,
- tax drag from those realizations,
- reinvestment after taxes,
- optional terminal liquidation taxes.

Minimum tracked state variables:
- `ending_value_pre_liquidation`
- `tax_basis`
- `unrealized_gain`
- `cumulative_dividend_tax`
- `cumulative_realized_gain_tax`
- `terminal_liquidation_tax`
- `ending_value_after_tax`

---

## 12. Required Tax Formulas

### 12.1 Basic notation
Let:

- `D` = gross QTP distribution
- `E` = earnings portion of distribution
- `B` = basis portion of distribution
- `Q` = adjusted qualified education expenses (AQEE)
- `T_ord` = combined ordinary tax rate on taxable QTP earnings
- `P` = 10% additional tax rate, usually `0.10`

By definition:

- `D = E + B`
- `B` is not included in income

### 12.2 AQEE formula

```text
AQEE = Qualified Education Expenses
       - Tax-Free Educational Assistance
       - Expenses Used for AOTC/LLC
       - Other required adjustments
```

### 12.3 QTP taxable earnings formula
If `Q >= D`, taxable earnings are zero.

If `Q < D`, then:

```text
Tax-Free Earnings = E * (Q / D)
Taxable Earnings  = E - Tax-Free Earnings
                  = E * (1 - Q / D)
```

with floor/ceiling logic so that:

```text
Taxable Earnings = max(0, E * (1 - min(Q, D) / D))
```

### 12.4 QTP additional tax formula
Unless an exception applies:

```text
Additional Tax = 0.10 * Taxable Earnings
```

If an exception applies to all or part of the taxable earnings, the relevant portion must be exempted.

### 12.5 QTP after-tax value for nonqualified withdrawal
For a full liquidation resolved as a nonqualified withdrawal:

```text
QTP After-Tax Value
= Basis
+ Tax-Free Earnings
+ Taxable Earnings * (1 - T_ord)
- Additional Tax
- State Recapture Tax
```

Equivalent expanded form:

```text
QTP After-Tax Value
= D - Taxable Earnings * T_ord - Additional Tax - State Recapture Tax
```

### 12.6 Taxable brokerage annual tax drag
For each year `t`:

```text
Qualified Dividends_t = PortfolioValue_t * DividendYield * QualifiedDividendShare
Ordinary Dividends_t  = PortfolioValue_t * DividendYield * (1 - QualifiedDividendShare)
Realized Gains_t      = UnrealizedGainBase_t * TurnoverRealizationRate
```

Taxes owed for year `t`:

```text
Dividend Tax_t
= Qualified Dividends_t * T_qd
+ Ordinary Dividends_t * T_ord_div

Realized Gain Tax_t
= Realized Gains_t * T_ltcg_or_applicable
```

The implementation may use simplifying assumptions in v1, but they must be clearly documented.

### 12.7 Taxable terminal liquidation
If liquidation occurs at horizon end:

```text
Terminal Gain = max(0, Ending Value - Tax Basis)
Terminal Liquidation Tax = Terminal Gain * T_ltcg_or_applicable
Ending Value After Tax = Ending Value - Terminal Liquidation Tax
```

### 12.8 Tradeoff delta
The core comparison metric:

```text
Delta = QTP_AfterTax_Outcome - Taxable_AfterTax_Outcome
```

Interpretation:
- `Delta > 0`: QTP wins
- `Delta < 0`: taxable wins

### 12.9 Expected-value framework under uncertain qualified use
If the scenario tree is probability-weighted:

```text
Expected QTP Value
= Σ p_i * QTP_AfterTax_Outcome_i

Expected Taxable Value
= Σ p_i * Taxable_AfterTax_Outcome_i

Expected Delta
= Expected QTP Value - Expected Taxable Value
```

### 12.10 Break-even qualified-use probability
For a two-state simplification:

- state A = qualified use
- state B = nonqualified / fallback resolution

Break-even probability `p*` satisfies:

```text
p* * QTP_A + (1 - p*) * QTP_B = Taxable
```

Thus:

```text
p* = (Taxable - QTP_B) / (QTP_A - QTP_B)
```

subject to domain checks and clipping.

---

## 13. Required Scenario Types

### 13.1 Fully qualified use
All withdrawals are matched by AQEE.

### 13.2 Partially qualified use
Some but not all distributed earnings are sheltered by AQEE.

### 13.3 Nonqualified withdrawal
No relevant AQEE remains to shelter the withdrawal.

### 13.4 Scholarship / tax-free aid exception case
Taxable earnings may still arise, but the additional 10% tax may not fully apply.

### 13.5 AOTC / LLC overlap case
Some expenses are intentionally allocated to credits, reducing AQEE available for the QTP.

### 13.6 Beneficiary reassignment
Leftover value is preserved in tax-advantaged form and held for a qualifying family member.

### 13.7 Roth rollover path
Subject to rule checks, all or part of the remaining QTP balance is moved to the beneficiary’s Roth IRA over time.

### 13.8 Mixed-resolution case
Example:
- 70% used for qualified education,
- 20% rolled to Roth over several years,
- 10% withdrawn nonqualified.

The engine must support mixture modeling.

---

## 14. State Plugin Architecture

### 14.1 Design goals
State treatment changes and varies widely. The package must isolate state logic from the federal core.

### 14.2 Abstract base class

```python
from abc import ABC, abstractmethod

class StateRule(ABC):
    state_code: str

    @abstractmethod
    def contribution_benefit(self, contribution_amount: float, tax_profile, year: int) -> float:
        ...

    @abstractmethod
    def recapture_tax(self, recaptured_base: float, tax_profile, year: int) -> float:
        ...

    @abstractmethod
    def validate(self, context) -> list[str]:
        ...
```

### 14.3 v1 state support recommendation
Ship with:
- `NoIncomeTaxStateRule` (for Washington and similar comparisons where appropriate)
- `GenericDeductionStateRule`
- `GenericCreditStateRule`
- 1–3 concrete example states after careful validation

### 14.4 Important constraint
The package must never imply that a generic state rule is legally equivalent to a named state’s exact rules unless explicitly implemented and documented.

---

## 15. Roth Rollover Modeling Requirements

### 15.1 Eligibility checks
The engine shall check at minimum:

- account open > 15 years,
- direct trustee-to-trustee transfer assumption,
- annual Roth contribution cap interaction,
- lifetime rollover cap,
- exclusion of amounts contributed within the disallowed lookback period and attributable earnings.

### 15.2 Modeling approach
Because the rollover may occur over multiple years, the engine shall support:

- one-shot theoretical cap estimate, and
- year-by-year staged rollover schedule.

### 15.3 Outputs
Must report:
- amount eligible today,
- amount ineligible due to age/lookback,
- years required to complete rollover under annual caps,
- assumed tax value of funds once in Roth,
- and residual balance still unresolved.

---

## 16. Monte Carlo Requirements

### 16.1 Stochastic inputs
Support random variables for:

- annual returns,
- dividend yield,
- turnover rate,
- scholarship / aid amount,
- qualified-use fraction,
- years to enrollment / use,
- residual-balance resolution.

### 16.2 Output statistics
Return:
- mean,
- median,
- standard deviation,
- selected percentiles,
- probability QTP outperforms taxable,
- distribution of deltas.

### 16.3 Reproducibility
Support explicit random seeds.

### 16.4 Performance target
A 10,000-path Monte Carlo with a moderate number of annual timesteps should run comfortably on a laptop in a reasonable time. Vectorization is preferred where feasible.

---

## 17. API Design

### 17.1 Top-level functional API

```python
from qtp_tradeoff import analyze_tradeoff

result = analyze_tradeoff(
    tax_profile=tax_profile,
    qtp_contributions=qtp_contribs,
    taxable_contributions=taxable_contribs,
    portfolio_assumptions=portfolio,
    education_schedule=edu_schedule,
    qtp_assumptions=qtp_assumptions,
    scenario_policy=scenario_policy,
    state_rule=state_rule,
)
```

### 17.2 Object-oriented API

```python
engine = TradeoffEngine(
    tax_profile=tax_profile,
    portfolio_assumptions=portfolio,
    state_rule=state_rule,
)

result = engine.run_case(case)
```

### 17.3 Result object

```python
@dataclass
class TradeoffResult:
    qtp_after_tax_value: float
    taxable_after_tax_value: float
    delta: float
    qtp_taxable_earnings: float
    qtp_additional_tax: float
    qtp_state_recapture_tax: float
    taxable_dividend_tax_drag: float
    taxable_realized_gain_tax_drag: float
    taxable_terminal_liquidation_tax: float
    break_even_qualified_use_probability: float | None
    warnings: list[str]
    assumptions_snapshot: dict
```

### 17.4 Explainability API
The package should support:

```python
result.explain()
result.to_frame()
result.to_json()
result.plot_heatmap()
```

The `explain()` method should provide a human-readable decomposition.

---

## 18. CLI Requirements

### 18.1 Commands

#### `qtp analyze`
Run a deterministic analysis from a YAML/JSON config.

#### `qtp monte-carlo`
Run a Monte Carlo simulation.

#### `qtp breakeven`
Compute break-even qualified-use probability or break-even horizon.

#### `qtp state-info`
Show metadata for a state rule implementation.

#### `qtp validate-config`
Validate scenario files before running.

### 18.2 Example

```bash
qtp analyze --config examples/seattle_no_income_tax.yaml
qtp monte-carlo --config examples/base_case.yaml --n-sims 10000 --seed 42
qtp breakeven --config examples/base_case.yaml --variable qualified_use_probability
```

---

## 19. Configuration File Format

### 19.1 Preferred formats
- YAML for human-authored scenarios
- JSON for machine-generated scenarios

### 19.2 Example YAML

```yaml
tax_profile:
  ordinary_income_rate: 0.35
  ltcg_rate: 0.15
  qualified_dividend_rate: 0.15
  niit_rate: 0.038
  state_ordinary_rate: 0.00
  state_cap_gains_rate: 0.00

portfolio_assumptions:
  annual_return: 0.07
  dividend_yield: 0.015
  qualified_dividend_share: 0.95
  turnover_realization_rate: 0.05
  expense_ratio: 0.0005

qtp_assumptions:
  state_tax_deduction_rate: 0.00
  state_tax_credit_rate: 0.00
  state_tax_recapture_rate: 0.00
  roth_rollover_enabled: true
  beneficiary_change_allowed: true

scenario_policy:
  leftover_resolution: mixed
  qualified_use_probability: 0.75
  roth_rollover_fraction: 0.20

education_schedule:
  items:
    - date: 2042-09-01
      qualified_expense: 30000
      tax_free_assistance: 5000
      aotc_or_llc_allocated_expense: 4000
```

---

## 20. Output Requirements

### 20.1 Summary table
Every run must produce a summary table including:

- QTP ending pre-tax value
- QTP basis
- QTP earnings
- AQEE
- QTP taxable earnings
- QTP income tax due
- QTP additional tax
- QTP state recapture
- QTP after-tax value
- taxable ending pre-liquidation value
- taxable basis
- taxable unrealized gain
- taxable dividend taxes paid
- taxable realized gain taxes paid
- taxable terminal liquidation tax
- taxable after-tax value
- delta

### 20.2 Driver decomposition
Must report a driver breakdown like:

- `federal_tax_free_growth_benefit`
- `taxable_dividend_drag_cost`
- `taxable_realization_drag_cost`
- `nonqualified_qtp_income_tax_cost`
- `qtp_10_percent_additional_tax_cost`
- `state_benefit_value`
- `state_recapture_cost`
- `roth_rollover_option_value`

### 20.3 Plots
v1 plotting should include:

- delta vs. qualified-use probability
- delta vs. years to withdrawal
- heatmap: years × qualified-use probability
- waterfall chart for outcome decomposition
- Monte Carlo histogram of delta

---

## 21. Package Structure

```text
qtp_tradeoff/
  __init__.py
  api.py
  cli.py
  constants.py
  exceptions.py

  core/
    engine.py
    deterministic.py
    monte_carlo.py
    scenario_tree.py
    breakeven.py

  tax/
    federal_qtp.py
    taxable_account.py
    roth_rollover.py
    credits_coordination.py
    state_base.py
    state_registry.py

  state_rules/
    no_income_tax.py
    generic_deduction.py
    generic_credit.py
    washington.py

  models/
    assumptions.py
    contributions.py
    education.py
    result.py
    config.py

  outputs/
    tables.py
    plots.py
    explain.py
    export.py

  io/
    yaml_loader.py
    json_loader.py
    schema.py

  tests/
    test_federal_qtp.py
    test_taxable_account.py
    test_roth_rollover.py
    test_state_rules.py
    test_breakeven.py
    test_cli.py
    fixtures/

examples/
  base_case.yaml
  washington_no_income_tax.yaml
  scholarship_case.yaml
  aotc_overlap_case.yaml
  roth_rollover_case.yaml

notebooks/
  529_vs_taxable_walkthrough.ipynb

README.md
SPEC.md
pyproject.toml
LICENSE
```

---

## 22. Testing Requirements

### 22.1 Unit tests
Must cover:

- QTP taxable earnings formula
- additional 10% tax application
- exception handling
- AOTC/LLC coordination
- state deduction/credit math
- state recapture math
- taxable-account dividend drag
- taxable-account liquidation tax
- break-even solver
- Roth rollover eligibility logic

### 22.2 Regression tests
Must include a set of hand-verified scenarios that should never change unless intended.

### 22.3 Property tests
Use property-based testing where helpful, e.g.:

- taxable earnings cannot be negative,
- basis cannot be taxed twice,
- after-tax ending value cannot exceed pre-tax ending value absent modeled state credits/deductions,
- break-even probability must be clipped or flagged outside `[0, 1]`.

### 22.4 Golden tests for explainability
String/JSON explanation outputs should be snapshot-tested where stable.

---

## 23. Validation Strategy

### 23.1 Federal rule validation
Validate formulas and scenario behavior against official IRS guidance and examples where applicable.

### 23.2 State rule validation
For any named-state plugin, validate the logic against the relevant official state guidance at the time of implementation.

### 23.3 Cross-validation
Cross-check selected scenarios using independent spreadsheet calculations.

### 23.4 Disclosure requirement
Documentation must state that tax laws can change and users should verify current rules for their state and situation.

---

## 24. Documentation Requirements

### 24.1 README
The README must include:

- what the package does,
- why the 529 tradeoff is subtle,
- installation,
- quick-start example,
- CLI usage,
- assumptions and limitations,
- contribution guidelines.

### 24.2 Methodology document
A `docs/methodology.md` or notebook should describe:

- formulas,
- interpretation,
- limitations,
- examples,
- and how state plugins work.

### 24.3 Disclaimer language
Suggested disclaimer:

> This package is for educational and analytical purposes only. It is not tax, legal, or investment advice. Tax outcomes depend on facts, jurisdiction, and future law changes.

---

## 25. Performance and Engineering Requirements

### 25.1 Language/runtime
- Python 3.11+
- Optional support for 3.12+

### 25.2 Core dependencies
Recommended:
- `numpy`
- `pandas`
- `pydantic` or `attrs`/`dataclasses`
- `pyyaml`
- `matplotlib`
- `scipy` for optional numerical solving

Optional:
- `numba` for acceleration later
- `plotly` for richer interactive visuals

### 25.3 Code quality
- type hints throughout
- `ruff` or `flake8`
- `mypy` or pyright checks
- CI via GitHub Actions
- semantic versioning

---

## 26. Security / Trust Requirements

Because the package relates to tax-sensitive financial decisions:

- all assumptions must be user-visible,
- formulas must be inspectable,
- state logic must be traceable,
- and no black-box heuristic should override disclosed math.

The package should favor **clarity over cleverness**.

---

## 27. Risks and Caveats

### 27.1 Tax law changes
The package may become stale if rules change.

### 27.2 State complexity
Some states have nuanced plan-specific rules, caps, or recapture provisions.

### 27.3 Taxable-account simplification risk
Real-world taxable-account treatment depends on lot selection, holding periods, wash-sale interactions, municipal securities, foreign tax credit issues, and more. V1 should explicitly limit scope.

### 27.4 Overprecision risk
Users may mistake scenario modeling for certainty. Outputs should be described as assumption-dependent estimates.

---

## 28. Open Questions for v1 vs v2

### v1 candidates
- deterministic engine
- Monte Carlo engine
- generic state plugin system
- no-income-tax state example
- Roth rollover model
- CLI
- plots and summary tables

### v2 candidates
- lot-level taxable-account accounting
- multiple beneficiaries and household optimization
- richer state library
- direct integration with web calculators
- college cost inflation / tuition scenario modules
- notebook templates and whitepaper generator

---

## 29. Acceptance Criteria

The package will be considered v1-ready when it can:

1. Run a deterministic comparison between 529 and taxable accounts.
2. Correctly separate basis and earnings in the QTP distribution model.
3. Correctly compute AQEE after scholarships and AOTC/LLC overlap.
4. Correctly apply the 10% additional tax only to the taxable amount, subject to modeled exceptions.
5. Model annual taxable-account tax drag and terminal liquidation tax.
6. Compute a break-even qualified-use probability.
7. Support at least one no-income-tax state rule and one generic deduction/credit rule.
8. Support a Roth rollover scenario with eligibility validation.
9. Produce machine-readable and human-readable outputs.
10. Pass a documented test suite.

---

## 30. Example Research Questions This Package Should Enable

- “For a Washington household using a tax-efficient index fund in taxable, how much qualified-use probability is needed for the 529 to win?”
- “How much does claiming the AOTC reduce the effective benefit of the 529?”
- “How valuable is the Roth rollover fallback if the account has been open long enough?”
- “How much worse is a taxable account if the portfolio has higher dividend yield or turnover?”
- “How much do state tax deductions matter versus federal qualified-growth treatment?”

---

## 31. Example Human-Readable Explanation Output

```text
Under the assumptions provided, the 529 strategy ends with $14,820 more after tax than the taxable brokerage strategy.

Key drivers:
- +$11,450 from federally tax-free qualified growth inside the 529
- -$3,120 from reduced AQEE because $4,000 of expenses were allocated to the AOTC
- -$1,860 expected cost from the chance of leftover funds being withdrawn nonqualified
- +$8,350 avoided taxable-account dividend and capital-gain drag
- +$0 from state tax benefit because the selected state rule has no personal income tax

Break-even qualified-use probability: 58.4%
```

---

## 32. Implementation Roadmap

### Phase 1 — Core deterministic engine
- data models
- federal QTP formulas
- taxable-account formulas
- result object
- basic tests

### Phase 2 — Scenario and break-even engine
- multi-state scenario handling
- expected-value calculations
- break-even solver
- summary tables

### Phase 3 — Roth and state plugins
- Roth rollover logic
- state plugin base class
- Washington/no-income-tax plugin
- generic deduction/credit plugins

### Phase 4 — Monte Carlo + visualization
- stochastic simulation engine
- plots
- notebooks
- CLI polish

### Phase 5 — Documentation and public release
- README
- methodology notes
- examples
- versioned release to PyPI

---

## 33. Source Basis for Rule Modeling

The package’s rule-model assumptions should be validated and documented against official guidance, including:

- IRS Publication 970 (Tax Benefits for Education)
- IRS Topic no. 313 (Qualified tuition programs)
- IRS guidance on Roth IRA contribution limits and related IRA rules
- Investor.gov / SEC guidance on 529 plans and state tax considerations
- Official state tax authority guidance for any named state plugin

---

## 34. Final Recommendation

**Proceed.**

This is a strong open-source project because it translates a fuzzy personal-finance argument into transparent, auditable, reusable math.

The best version is not a toy “penalty calculator.” It is a **529-vs-taxable tradeoff engine** with:

- explicit federal tax mechanics,
- state plugin support,
- taxable-account tax drag modeling,
- and fallback-path analysis including Roth rollovers.

For your use case, especially with a Washington/no-income-tax framing, this package would be genuinely useful because it can show when taxable is “close enough” and when the 529 still wins by more than intuition suggests.

---

## Appendix A — Recommended Initial Public API Skeleton

```python
from qtp_tradeoff.models import (
    InvestorTaxProfile,
    PortfolioAssumptions,
    QTPAssumptions,
    ScenarioPolicy,
    ContributionSchedule,
    EducationExpenseSchedule,
)
from qtp_tradeoff.api import analyze_tradeoff
from qtp_tradeoff.state_rules import NoIncomeTaxStateRule

result = analyze_tradeoff(
    tax_profile=InvestorTaxProfile(
        ordinary_income_rate=0.35,
        ltcg_rate=0.15,
        qualified_dividend_rate=0.15,
        niit_rate=0.038,
        state_ordinary_rate=0.0,
        state_cap_gains_rate=0.0,
    ),
    qtp_contributions=ContributionSchedule(...),
    taxable_contributions=ContributionSchedule(...),
    portfolio_assumptions=PortfolioAssumptions(
        annual_return=0.07,
        dividend_yield=0.015,
        qualified_dividend_share=0.95,
        turnover_realization_rate=0.05,
    ),
    education_schedule=EducationExpenseSchedule(...),
    qtp_assumptions=QTPAssumptions(
        roth_rollover_enabled=True,
        beneficiary_change_allowed=True,
    ),
    scenario_policy=ScenarioPolicy(
        leftover_resolution="mixed",
        qualified_use_probability=0.75,
        roth_rollover_fraction=0.20,
    ),
    state_rule=NoIncomeTaxStateRule(state_code="WA"),
)

print(result.delta)
print(result.explain())
```

---

## Appendix B — Minimal Washington Example Interpretation

For a Washington-based comparison:

- there is generally no state personal income-tax deduction/credit to model for 529 contributions,
- so the primary advantage of the 529 is federal tax-free qualified growth,
- while the primary advantage of taxable is flexibility,
- making portfolio tax efficiency, qualified-use probability, and fallback options the key swing factors.

