I’d build it, but **not** as a simple “529 penalty calculator.” I’d build it as a **tradeoff engine** that compares after-tax outcomes for a 529 versus a taxable brokerage under different probabilities of qualified use. The reason is that the 529 downside is more nuanced than most people think: the **basis/contributions come back tax-free**, only the **earnings portion** can become taxable, and the extra **10% federal tax generally applies to the amount included in income**, not the whole withdrawal. On top of that, AQEE gets reduced by scholarships and other tax-free aid, and expenses used for the AOTC/LLC cannot also shelter 529 distributions. ([IRS][1])

My practical recommendation: **yes, build the package**, especially if the goal is to quantify when “taxable is close enough” versus when the 529 clearly dominates. For a Washington-based user, one common 529 advantage is weaker because Washington currently says it has **no personal income tax**, so there is no ordinary in-state income-tax deduction/credit to model there. That makes the main comparison more about **federal tax-free qualified growth** versus **flexibility and taxable-account tax drag**. In that setup, taxable can be more competitive when education use is uncertain and the portfolio is low-turnover; the 529 tends to win when qualified use is likely, beneficiary reassignment is acceptable, or the Roth rollover fallback is plausible. That last fallback exists, but it has restrictions, including annual IRA limits, a 15-year account-age rule, a 5-year contribution-aging rule, and a lifetime rollover cap described by the SEC bulletin. ([Washington Department of Revenue][2])

I would also make **state tax treatment a first-class plugin**, not an afterthought. The SEC’s investor bulletin says many states offer 529 tax benefits, and the SEC has also brought an enforcement action highlighting that advisers failed to consider **foregone home-state tax benefits** and possible **state tax recapture** when recommending out-of-state 529 plans. That is exactly the kind of thing your package should surface instead of hand-waving away. ([SEC][3])

## What I’d build

**Suggested scope**
A Python package that answers:

1. What is the **after-tax ending wealth** under 529-qualified, 529-nonqualified, and taxable scenarios?
2. What is the **break-even probability of qualified education use** where a 529 overtakes taxable?
3. How sensitive is the answer to:

   * dividend yield and turnover,
   * ordinary income tax rate,
   * LTCG/qualified dividend rate,
   * scholarships/AOTC overlap,
   * state tax deduction/credit and recapture,
   * leftover-funds options like beneficiary change or Roth rollover? ([IRS][1])

## Core package design

**Package name ideas**
`qtp-tradeoff`, `plan529lab`, or `529x`

**Top-level modules**

* `qtp.rules` — federal 529 rules and exception handling
* `qtp.state` — state deduction/credit/recapture plugins
* `qtp.taxable` — taxable brokerage tax-drag model
* `qtp.scenarios` — qualified use / partial use / nonqualified / leftover / rollover scenarios
* `qtp.engine` — deterministic and Monte Carlo engines
* `qtp.outputs` — summary tables, heatmaps, break-even charts
* `qtp.validation` — tests against IRS examples and edge cases

## Minimum viable data model

```python
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class InvestorTaxProfile:
    ordinary_income_rate: float
    ltcg_rate: float
    qualified_dividend_rate: float
    niit_rate: float = 0.0
    state_ordinary_rate: float = 0.0
    state_cap_gains_rate: float = 0.0

@dataclass
class TaxableAccountAssumptions:
    annual_return: float
    dividend_yield: float
    qualified_dividend_share: float
    turnover_realization_rate: float
    terminal_liquidation: bool = True

@dataclass
class QTPAssumptions:
    annual_return: float
    state_tax_deduction_rate: float = 0.0
    state_tax_credit_rate: float = 0.0
    state_recapture_rate: float = 0.0
    scholarship_exception: bool = False
    aotc_overlap_amount: float = 0.0
    roth_rollover_enabled: bool = False

@dataclass
class EducationScenario:
    years_to_withdrawal: int
    qualified_expense_ratio: float   # 0.0 to 1.0
    scholarship_ratio: float = 0.0
    beneficiary_change_allowed: bool = True
```

## Core calculations the engine should implement

For the 529 side, the engine should explicitly separate **basis** from **earnings**, because IRS reporting and taxability hinge on that split. Form 1099-Q reports the gross distribution, earnings, and basis separately, and the IRS formula taxes only the portion of earnings not matched to AQEE. ([IRS][1])

At minimum:

* `earnings = ending_value - contributions`
* `taxable_earnings = earnings * max(0, 1 - AQEE / distribution)`
* `additional_tax = 0.10 * taxable_earnings`, unless an exception applies
* `nonqualified_after_tax_value = basis + taxable_earnings * (1 - ordinary_tax_rate - penalty_rate) + tax_free_earnings_portion`

That structure mirrors the IRS rule that the taxable portion is based on the **earnings share not covered by AQEE**, and the 10% additional tax is generally on the **amount included in income**. Exceptions should cover death, disability, scholarship/tax-free aid, military academy attendance, and the portion made taxable only because expenses were used for the AOTC or LLC. ([IRS][1])

For the taxable account side, model:

* annual tax drag from dividends,
* user-set realization/turnover,
* terminal liquidation tax based on basis,
* qualified versus ordinary dividend treatment.

That matches the basic IRS treatment that basis matters for gain/loss, capital gains are recognized on disposition, and qualified dividends can be taxed at lower capital-gain rates while ordinary dividends are taxed as ordinary income. ([IRS][4])

## Inputs the package absolutely needs

I would not ship without these:

* contribution schedule by year
* years until use
* expected return, dividend yield, turnover
* federal ordinary and LTCG/qualified-dividend rates
* optional NIIT
* state tax treatment
* expected qualified expense schedule
* scholarship / grant / tax-free aid inputs
* education credit overlap inputs
* nonqualified exception flags
* leftover-balance policy:

  * withdraw and pay tax/penalty
  * change beneficiary
  * hold for future education
  * Roth rollover path with restriction checks ([IRS][1])

## Outputs I’d want

Not just one answer. I’d want:

* `delta_after_tax_value_529_vs_taxable`
* `break_even_qualified_use_probability`
* `break_even_years_to_use`
* `penalty_isolation`
  how much of the drag came from:

  * ordinary income tax on earnings,
  * 10% additional tax,
  * lost state benefits / recapture,
  * AOTC/LLC overlap,
  * taxable annual dividend drag
* scenario heatmaps:

  * x-axis: probability of qualified use
  * y-axis: years invested
* optional Monte Carlo distribution of outcomes

That turns the package from a blog-post calculator into something analytically useful.

## Validation plan

I’d validate the library against:

* IRS Publication 970 worked examples for taxable QTP distributions and AOTC coordination,
* hand-built unit tests for exception scenarios,
* regression tests for state plugins,
* property tests making sure basis is never taxed twice. ([IRS][1])

## What I would *not* do in v1

I would **not**:

* hardcode all 50 states at launch,
* pretend to be tax-prep software,
* assume all dividends are qualified,
* ignore education-credit interactions,
* bury policy assumptions in the code.

Start with a federal core plus a few state plugins and a transparent assumptions object.

## My strongest product recommendation

Given your existing work, I’d probably make this **a module inside `collegeplan` first**, not a brand-new repo. Something like:

* `collegeplan.qtp_tradeoff`
* `collegeplan.qtp_state_plugins`
* `collegeplan.qtp_break_even`

Why:

* lower maintenance burden,
* immediate relevance to your existing audience,
* easier to turn into a whitepaper/calculator later.

## Bottom line

**Yes, I recommend building it.**
But build a **529-vs-taxable trade analysis engine**, not a one-line penalty calculator.

Why:

* the common intuition about 529 “penalties” is often too crude,
* the real comparison depends on earnings-vs-basis, scholarships, credits, state tax treatment, and leftover-funds options,
* and those moving parts are substantial enough to justify reusable open-source tooling. ([IRS][1])

If you want, I can turn this into a proper `SPEC.md` with package architecture, formulas, CLI/API examples, and a test plan.

[1]: https://www.irs.gov/publications/p970 "Publication 970 (2025), Tax Benefits for Education | Internal Revenue Service"
[2]: https://dor.wa.gov/taxes-rates/income-tax "Income tax | Washington Department of Revenue"
[3]: https://www.sec.gov/reportspubs/investor-publications/investorpubsintro529htm.html?start=123&start=205&start=82&start=82&start=82 "An Introduction to 529 Plans - Investor Bulletin | Investor.gov"
[4]: https://www.irs.gov/publications/p551?utm_source=chatgpt.com "Publication 551 (12/2025), Basis of Assets"
