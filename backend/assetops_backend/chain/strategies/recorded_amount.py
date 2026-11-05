"""`recorded_amount@1`: no billing source exists (AG-11), so it returns no money with `NO_RECORDS`, always."""
from __future__ import annotations

from assetops_backend.chain.strategies.base import NO_RECORDS, RECORDED, ContributionContext, Effect


class RecordedAmount:
    key, version = "recorded_amount", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        return Effect(ctx.record.direction, basis=RECORDED, reason=NO_RECORDS)
