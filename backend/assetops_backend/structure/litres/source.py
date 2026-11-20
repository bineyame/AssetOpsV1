"""4d unit 2 (spec §3.2): `LitreLeafSource`, the provider of the three litre leaves.

It answers `necessary_l`, `candidate_l` and `unexplained_l` from `rules.month_litres` over the inputs its port reads,
and passes every other leaf to its fallback. Within one instance, a pinned read's `LitreMonth` (`known_at` set) is
kept, at most 16, least recently used dropped, so the three leaves of one pinned read cost one input read; a live
read (`known_at` None) is never memoised.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from datetime import datetime
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.evaluate import LeafValue
from assetops_backend.structure.litres.rules import LITRE_ORDER, LitreInputs, LitreMonth, month_litres
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.sources import LITRE_LEAVES, LeafSource, ReadContext

MEMO_SIZE = 16
#: The MINI_GRID registry rows' `filled_by`: what an absent litre leaf names.
FILLED_BY = MappingProxyType({f: REGISTRIES["MINI_GRID"].row(f).filled_by for f in LITRE_ORDER})


class LitreInputsPort(Protocol):
    def read(self, site: SiteRef, month: str, known_at: datetime) -> LitreInputs: ...


class LitreLeafSource:
    def __init__(self, inputs: LitreInputsPort, fallback: LeafSource, now: Callable[[], datetime]) -> None:
        self._inputs = inputs
        self._fallback = fallback
        self._now = now
        self._memo: OrderedDict[tuple[UUID, UUID, str, datetime], LitreMonth] = OrderedDict()

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        if factor_id not in LITRE_LEAVES:
            return self._fallback.leaf(ctx, factor_id)
        return self._month(ctx).values[factor_id]

    def _month(self, ctx: ReadContext) -> LitreMonth:
        if ctx.known_at is None:  # a live read: never memoised
            return month_litres(self._inputs.read(ctx.site, ctx.month, self._now()), FILLED_BY)
        key = (ctx.site.tenant_id, ctx.site.site_id, ctx.month, ctx.known_at)
        held = self._memo.get(key)
        if held is not None:
            self._memo.move_to_end(key)
            return held
        month = month_litres(self._inputs.read(ctx.site, ctx.month, ctx.known_at), FILLED_BY)
        self._memo[key] = month
        while len(self._memo) > MEMO_SIZE:
            self._memo.popitem(last=False)
        return month


__all__ = ["FILLED_BY", "MEMO_SIZE", "LitreInputsPort", "LitreLeafSource"]
