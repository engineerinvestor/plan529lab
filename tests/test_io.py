"""Tests for config file loading."""

from pathlib import Path

import pytest

from plan529lab.exceptions import ConfigLoadError
from plan529lab.io.yaml_loader import load_config

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestYAMLLoader:
    def test_load_washington_config(self) -> None:
        config = load_config(EXAMPLES_DIR / "washington_no_income_tax.yaml")
        assert config.horizon_years == 18
        assert config.tax_profile.ordinary_income_rate == 0.35
        assert config.tax_profile.state_ordinary_rate == 0.0
        assert config.qtp_contributions.total_amount == 10000.0
        assert config.taxable_contributions.total_amount == 10000.0
        assert config.scenario_policy.qualified_use_probability == 0.75

    def test_load_deduction_config(self) -> None:
        config = load_config(EXAMPLES_DIR / "generic_deduction_state.yaml")
        assert config.tax_profile.state_ordinary_rate == 0.05
        assert config.scenario_policy.qualified_use_probability == 0.80

    def test_missing_file(self) -> None:
        with pytest.raises(ConfigLoadError, match="Failed to load"):
            load_config("/nonexistent/path.yaml")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("not: [valid: yaml: {", encoding="utf-8")
        with pytest.raises(ConfigLoadError):
            load_config(bad_file)
