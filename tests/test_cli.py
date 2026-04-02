"""Tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from plan529lab.cli import main

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestAnalyzeCommand:
    def test_text_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "analyze",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
        ])
        assert result.exit_code == 0
        assert "529 strategy" in result.output or "taxable" in result.output

    def test_json_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "analyze",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--format", "json",
        ])
        assert result.exit_code == 0
        assert '"delta"' in result.output

    def test_with_state(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "analyze",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--state", "WA",
        ])
        assert result.exit_code == 0

    def test_missing_config(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--config", "/nonexistent.yaml"])
        assert result.exit_code != 0


class TestBreakevenCommand:
    def test_basic(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "breakeven",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
        ])
        assert result.exit_code == 0
        assert "Break-even" in result.output or "undefined" in result.output


class TestStateInfoCommand:
    def test_wa(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["state-info", "WA"])
        assert result.exit_code == 0
        assert "WA" in result.output
        assert "NoIncomeTaxStateRule" in result.output

    def test_unknown(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["state-info", "ZZ"])
        assert result.exit_code != 0


class TestMonteCarloCommand:
    def test_text_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "monte-carlo",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--n-sims", "50",
            "--seed", "42",
        ])
        assert result.exit_code == 0
        assert "Monte Carlo" in result.output
        assert "Mean Delta" in result.output

    def test_json_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "monte-carlo",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--n-sims", "50",
            "--seed", "42",
            "--format", "json",
        ])
        assert result.exit_code == 0
        assert '"mean_delta"' in result.output


class TestSensitivityCommand:
    def test_basic(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "sensitivity",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--param", "annual_return",
            "--min", "0.03",
            "--max", "0.10",
            "--steps", "4",
        ])
        assert result.exit_code == 0
        assert "annual_return" in result.output

    def test_invalid_param(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "sensitivity",
            "--config", str(EXAMPLES_DIR / "washington_no_income_tax.yaml"),
            "--param", "bogus",
            "--min", "0",
            "--max", "1",
        ])
        assert result.exit_code != 0
