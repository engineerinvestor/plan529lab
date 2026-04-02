"""Result export utilities."""

from __future__ import annotations

from typing import Any

from plan529lab.models.results import TradeoffResult


def result_to_dict(result: TradeoffResult) -> dict[str, Any]:
    """Export a TradeoffResult to a plain dictionary."""
    return result.to_dict()


def result_to_json(result: TradeoffResult, indent: int = 2) -> str:
    """Export a TradeoffResult to a JSON string."""
    return result.to_json(indent=indent)
