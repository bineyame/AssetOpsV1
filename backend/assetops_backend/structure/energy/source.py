"""4a unit 1 (spec §3; D-4A.14, D-4A.23): `EnergyLeafSource`, the provider of the energy leaves and stated kWh nodes.

It answers the six `ENERGY_LEAVES` and the two `ENERGY_STATED` nodes from `rules.month_energy` over the inputs its
port reads, once per `ReadContext` object (D-4B.12's rule), and passes every other leaf or stated node to its
fallback. A live read passes `known_at` None to the port (D-4A.23). Nothing here catches a reader's refusal or
outage: it propagates, never a figure and never an absence.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from types import MappingProxyType
from typing import Any, Protocol

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.energy.rules import ENERGY_ORDER, EnergyInputs, EnergyMonth, month_energy
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.sources import (
    ENERGY_LEAVES,
    ENERGY_STATED,
    PROVIDED,
    SOURCE_STATE,
    STATED_STATE,
    ReadContext,
)
from assetops_backend.structure.evaluate import LeafValue

_MG = REGISTRIES["MINI_GRID"]
#: What an absent value names: the row's `filled_by` for a leaf, its `stated_by` for the two stated nodes.
NAMES = MappingProxyType({f: (_MG.row(f).stated_by if f in ENERGY_STATED else _MG.row(f).filled_by)
                          for f in ENERGY_ORDER})


class EnergyInputsPort(Protocol):
    def read(self, site: SiteRef, month: str, known_at: datetime | None, now: datetime) -> EnergyInputs: ...


class EnergyLeafSource:
    """Implements `LeafSource` and `StatedSource`."""

    def __init__(self, inputs: EnergyInputsPort, fallback: Any, now: Callable[[], datetime]) -> None:
        self._inputs = inputs
        self._fallback = fallback
        self._now = now
        self._last: tuple[ReadContext, EnergyMonth] | None = None

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        if factor_id in ENERGY_LEAVES and _state(SOURCE_STATE, ctx, factor_id) == PROVIDED:
            return self._month(ctx).values[factor_id]
        return self._fallback.leaf(ctx, factor_id)

    def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        if factor_id in ENERGY_STATED and _state(STATED_STATE, ctx, factor_id) == PROVIDED:
            return self._month(ctx).values[factor_id]
        return self._fallback.stated(ctx, factor_id)

    def _month(self, ctx: ReadContext) -> EnergyMonth:
        last = self._last
        if last is not None and last[0] is ctx:
            return last[1]
        month = month_energy(self._inputs.read(ctx.site, ctx.month, ctx.known_at, self._now()), NAMES)
        self._last = (ctx, month)
        return month


def _state(table: Any, ctx: ReadContext, factor_id: str) -> str | None:
    key = SITE_TYPE_TO_STRUCTURE.get(ctx.site.site_type)
    return table.get(key, {}).get(factor_id) if key is not None else None


__all__ = ["NAMES", "EnergyInputsPort", "EnergyLeafSource"]
