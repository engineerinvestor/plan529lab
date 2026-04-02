"""Investor tax profile model."""

from pydantic import BaseModel, Field


class InvestorTaxProfile(BaseModel, frozen=True):
    """Federal and state tax rate assumptions for an investor."""

    ordinary_income_rate: float = Field(ge=0.0, le=1.0)
    ltcg_rate: float = Field(ge=0.0, le=1.0)
    qualified_dividend_rate: float = Field(ge=0.0, le=1.0)
    niit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    state_ordinary_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    state_cap_gains_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    filing_status: str | None = None

    @property
    def combined_ordinary_rate(self) -> float:
        """Federal + state ordinary income rate."""
        return self.ordinary_income_rate + self.state_ordinary_rate

    @property
    def combined_ltcg_rate(self) -> float:
        """Federal + state long-term capital gains rate."""
        return self.ltcg_rate + self.state_cap_gains_rate

    @property
    def combined_qualified_dividend_rate(self) -> float:
        """Federal qualified dividend rate + state cap gains rate."""
        return self.qualified_dividend_rate + self.state_cap_gains_rate
