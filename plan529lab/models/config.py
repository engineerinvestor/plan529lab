"""Top-level scenario configuration model."""

from pydantic import BaseModel

from plan529lab.models.assumptions import PortfolioAssumptions, QTPAssumptions
from plan529lab.models.contributions import ContributionSchedule
from plan529lab.models.education import EducationExpenseSchedule
from plan529lab.models.scenario import ScenarioPolicy
from plan529lab.models.tax_profile import InvestorTaxProfile


class ScenarioConfig(BaseModel, frozen=True):
    """Complete configuration for a tradeoff analysis scenario."""

    tax_profile: InvestorTaxProfile
    qtp_contributions: ContributionSchedule
    taxable_contributions: ContributionSchedule
    portfolio_assumptions: PortfolioAssumptions
    education_schedule: EducationExpenseSchedule
    qtp_assumptions: QTPAssumptions = QTPAssumptions()
    scenario_policy: ScenarioPolicy = ScenarioPolicy()
    horizon_years: int
