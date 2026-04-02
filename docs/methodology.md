# Methodology

This document describes the formulas, assumptions, and limitations of plan529lab.

> **Disclaimer:** This package is for educational and analytical purposes only. It is not tax, legal, or investment advice. Tax laws change. Consult a qualified tax professional for your situation.

## Core Comparison

The package compares two strategies for the same dollars:

1. **529/QTP account** — tax-free growth if used for qualified education expenses; subject to income tax + 10% additional tax on earnings if withdrawn nonqualified.
2. **Taxable brokerage account** — full flexibility, but subject to annual dividend taxes, realized capital gains taxes, and terminal liquidation taxes.

The **delta** = 529 after-tax value minus taxable after-tax value. Positive delta means the 529 wins.

## 529/QTP Tax Formulas

### Adjusted Qualified Education Expenses (AQEE)

```
AQEE = Qualified Education Expenses
     - Tax-Free Educational Assistance (scholarships, grants)
     - Expenses Allocated to AOTC/LLC
```

Floored at zero. Reference: IRS Publication 970.

### Taxable Earnings on Distribution

A 529 distribution has two components: **basis** (contributions, always tax-free) and **earnings**.

If AQEE >= distribution, all earnings are tax-free.

Otherwise:

```
Taxable Earnings = E × (1 - min(AQEE, D) / D)
```

Where E = earnings portion, D = gross distribution, AQEE = adjusted qualified expenses.

### 10% Additional Tax

```
Additional Tax = 0.10 × max(0, Taxable Earnings - Exception Amount)
```

Exceptions include: amounts made taxable only because expenses were allocated to AOTC/LLC, scholarship/tax-free aid amounts, death, disability, military academy attendance.

### After-Tax Value (Nonqualified Withdrawal)

```
After-Tax = Distribution - (Taxable Earnings × Ordinary Rate)
          - Additional Tax - State Recapture + State Benefit
```

## Taxable Account Tax Drag

Each year, the taxable account pays taxes that reduce the compounding base:

### Annual Dividend Tax

```
Qualified Dividends = Portfolio Value × Dividend Yield × Qualified Share
Ordinary Dividends  = Portfolio Value × Dividend Yield × (1 - Qualified Share)

Dividend Tax = Qualified Dividends × QD Rate + Ordinary Dividends × Ordinary Rate
```

### Annual Realized Gain Tax

```
Realized Gains = max(0, Unrealized Gain) × Turnover Realization Rate
Realized Gain Tax = Realized Gains × LTCG Rate
```

After realization, basis adjusts upward for the realized portion.

### Terminal Liquidation Tax

```
Terminal Tax = max(0, Ending Value - Tax Basis) × LTCG Rate
```

## Growth Model

Both accounts use annual timesteps with start-of-year contributions.

**QTP growth** per year:
```
value = (value + contributions) × (1 + annual_return - expense_ratio - plan_fee_drag)
```

**Taxable growth** per year:
1. Add contributions (increases value and basis)
2. Pay dividend taxes (reduces value)
3. Pay realized gain taxes from turnover (reduces value, adjusts basis up)
4. Apply price appreciation (net of dividends already distributed)

## Scenario Branching

The engine computes two outcomes:

- **QTP_A** (fully qualified): all earnings tax-free, after-tax = ending value + state benefit
- **QTP_B** (leftover resolution): determined by `leftover_resolution` policy

The weighted result:
```
QTP Value = p × QTP_A + (1 - p) × QTP_B
```

Where p = `qualified_use_probability`.

### Leftover Resolution Modes

| Mode | Tax Treatment |
|------|--------------|
| `withdraw_nonqualified` | Income tax + 10% additional tax on earnings + state recapture |
| `roth_rollover` | Eligible portion rolled tax-free; residual withdrawn nonqualified |
| `change_beneficiary` | No immediate tax; possible state recapture |
| `hold_for_future_education` | Same as change_beneficiary |
| `mixed` | Weighted: `roth_fraction × roth_value + (1 - roth_fraction) × nonqualified_value` |

## Roth Rollover Rules (Post-SECURE 2.0)

Leftover 529 funds may be rolled into the beneficiary's Roth IRA subject to:

- Account must be open ≥ 15 years
- Annual limit: IRA contribution limit ($7,000 for 2024)
- Lifetime cap: $35,000
- Contributions within the 5-year lookback period are excluded
- Rolls into the **beneficiary's** Roth IRA (not the account owner's)

The **option value** of the Roth rollover = income tax + 10% additional tax saved on the earnings portion of the rolled-over amount.

## Break-Even Probability

```
p* = (Taxable - QTP_B) / (QTP_A - QTP_B)
```

Clipped to [0, 1]. At probabilities above p*, the 529 is expected to outperform.

## Monte Carlo Simulation

Per-year returns are drawn from a log-normal distribution:
```
log(1 + r_t) ~ N(log(1 + base_return), σ)
```

Dividend yield and turnover are treated as per-path constants. For each path, the deterministic engine computes the delta. Statistics (mean, median, percentiles, P(529 wins)) are computed from the distribution of deltas.

## State Tax Plugin Architecture

State tax treatment is modeled through a plugin system. Each state rule implements:

- `contribution_benefit(amount, profile, year)` — tax savings from contributing to a 529
- `recapture_tax(base, profile, year)` — tax owed if state benefit conditions are violated
- `validate(context)` — warnings about assumption mismatches

Built-in rules:
- **NoIncomeTaxStateRule** — for states with no personal income tax (WA, TX, FL, etc.)
- **GenericDeductionStateRule** — benefit = contribution × state ordinary rate; recapture at same rate
- **GenericCreditStateRule** — benefit = contribution × credit rate; recapture at credit rate

Generic rules do not reflect any specific state's exact rules, caps, phase-outs, or conditions.

### Adding a Custom State Rule

```python
from plan529lab.tax.state_base import StateRule

class MyStateRule(StateRule):
    state_code = "XX"

    def contribution_benefit(self, contribution_amount, tax_profile, year):
        # Your state's deduction/credit logic
        return contribution_amount * 0.05  # example: 5% deduction

    def recapture_tax(self, recaptured_base, tax_profile, year):
        return recaptured_base * 0.05

    def validate(self, context):
        return []  # return list of warning strings
```

## Limitations

- **Annual timesteps**: No intra-year compounding or monthly contributions
- **Constant tax rates**: Rates are assumed fixed over the horizon
- **Simplified taxable account**: No lot-level accounting, wash-sale rules, AMT, or foreign tax credit
- **NIIT**: Net Investment Income Tax rate is stored but not applied in calculations
- **Roth rollover**: One-shot eligibility estimate, not year-by-year staged rollover
- **No inflation adjustment**: All values are nominal
- **Monte Carlo**: Dividend yield and turnover are per-path constants, not per-year draws

## Source Basis

Formulas and rules are modeled based on:
- IRS Publication 970 (Tax Benefits for Education)
- IRS Topic No. 313 (Qualified Tuition Programs)
- SEC Investor Bulletin on 529 Plans
- SECURE 2.0 Act provisions on 529-to-Roth rollovers

Tax laws change. Users should verify current rules for their state and situation.
