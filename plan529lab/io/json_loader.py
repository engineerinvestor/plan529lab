"""JSON configuration file loader and result exporter."""

from __future__ import annotations

import json
from pathlib import Path

from plan529lab.exceptions import ConfigLoadError
from plan529lab.models.config import ScenarioConfig
from plan529lab.models.results import TradeoffResult


def load_config_from_json(path: str | Path) -> ScenarioConfig:
    """Load a ScenarioConfig from a JSON file."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigLoadError(f"Failed to load config from {path}: {e}") from e

    try:
        return ScenarioConfig.model_validate(data)
    except Exception as e:
        raise ConfigLoadError(f"Config validation failed: {e}") from e


def save_result_to_json(result: TradeoffResult, path: str | Path) -> None:
    """Save a TradeoffResult to a JSON file."""
    path = Path(path)
    path.write_text(result.to_json(), encoding="utf-8")
