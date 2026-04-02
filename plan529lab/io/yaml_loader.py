"""YAML configuration file loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from plan529lab.exceptions import ConfigLoadError
from plan529lab.models.config import ScenarioConfig


def load_config(path: str | Path) -> ScenarioConfig:
    """Load a ScenarioConfig from a YAML file.

    Raises ConfigLoadError if the file cannot be read or parsed.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as e:
        raise ConfigLoadError(f"Failed to load config from {path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigLoadError(f"Expected a YAML mapping at top level, got {type(data).__name__}")

    try:
        return ScenarioConfig.model_validate(data)
    except Exception as e:
        raise ConfigLoadError(f"Config validation failed: {e}") from e
