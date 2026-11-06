"""CH-6a3 R6: the evaluator's readings and per-outcome nodes for the cold and EV composers.

Kept out of `board.py`, which imports only `outcomes/` and the stdlib (`test_board_imports_only_outcomes_and_stdlib`)."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from assetops_backend.chain.outcomes import NodeInputs, OutcomeEvaluator, site_nodes
from assetops_backend.chain.read import local_days
from assetops_backend.outcomes.catalogue import SITE_OUTCOMES


def node_inputs(domain: str, c: str, tz: str | None, lo: Any, hi: Any, rows: Sequence[Any],
                objectives: Sequence[Any], readings: Mapping[str, Any], warnings: Sequence[Any] = (),
                price: Mapping[str, Any] | None = None) -> NodeInputs:
    """The cold/EV `NodeInputs` over the request's local days (kept on the composition, CH6b1-R Q1)."""
    days = local_days(lo, hi, tz)
    return NodeInputs(site_code=c, domain=domain, tz=tz or "UTC", window=(days[0], days[-1]), rows=tuple(rows),
                      objectives=tuple(objectives), readings=readings, warnings=tuple(warnings), price=price)


def domain_nodes(domain: str, c: str, tz: str | None, lo: Any, hi: Any, rows: Sequence[Any],
                 objectives: Sequence[Any], readings: Mapping[str, Any], warnings: Sequence[Any] = (),
                 price: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """CH-6a3 R6 for cold and EV: the evaluator's readings and per-outcome nodes over the request's local days.
    Returns `(readings, nodes)`."""
    inp = node_inputs(domain, c, tz, lo, hi, rows, objectives, readings, warnings, price)
    readings = OutcomeEvaluator().readings(inp)
    return readings, site_nodes(inp, [o.key for o in SITE_OUTCOMES if o.domain == domain])
