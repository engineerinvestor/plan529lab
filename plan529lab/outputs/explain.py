"""Human-readable explanation output."""

from __future__ import annotations

from plan529lab.models.results import TradeoffResult


def explain(result: TradeoffResult) -> str:
    """Generate a human-readable explanation of the tradeoff result.

    Delegates to TradeoffResult.explain() which contains the formatting logic.
    """
    return result.explain()
