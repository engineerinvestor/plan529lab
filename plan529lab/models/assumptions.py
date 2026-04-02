"""Portfolio and QTP assumption models."""

from pydantic import BaseModel, Field


class PortfolioAssumptions(BaseModel, frozen=True):
    """Expected investment behavior assumptions, shared by both account types."""

    annual_return: float = Field(ge=-1.0, le=1.0)
    dividend_yield: float = Field(ge=0.0, le=1.0)
    qualified_dividend_share: float = Field(ge=0.0, le=1.0)
    turnover_realization_rate: float = Field(ge=0.0, le=1.0)
    expense_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    inflation_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class QTPAssumptions(BaseModel, frozen=True):
    """529/QTP-specific assumptions beyond portfolio behavior."""

    state_tax_deduction_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    state_tax_credit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    state_tax_recapture_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    plan_fee_drag: float = Field(default=0.0, ge=0.0, le=1.0)
    roth_rollover_enabled: bool = False
    beneficiary_change_allowed: bool = True
