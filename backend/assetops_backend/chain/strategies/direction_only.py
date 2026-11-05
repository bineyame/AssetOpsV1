"""`direction_only@1`: the direction and the source's own title; never a number or money."""
from __future__ import annotations

from assetops_backend.chain.strategies.base import NOT_PRESENT, ContributionContext, Effect


class DirectionOnly:
    key, version = "direction_only", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        return Effect(ctx.record.direction, title=ctx.title, reason=None if ctx.title else NOT_PRESENT)
