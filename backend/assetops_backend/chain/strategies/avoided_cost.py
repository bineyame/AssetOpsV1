"""`avoided_cost@1`: the stored consequence's amount range via `ChainReader.money_head` (CH-5a1), basis MODELLED.
It never runs a fuel model."""
from __future__ import annotations

from assetops_backend.chain.strategies.base import MODELLED, NOT_PRICED, ContributionContext, Effect


class AvoidedCost:
    key, version = "avoided_cost", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        h = ctx.money_head
        if h is None or not h.priced or h.amount_low is None:
            return Effect(ctx.record.direction, basis=MODELLED, reason=NOT_PRICED)
        return Effect(ctx.record.direction, basis=MODELLED,
                      money={"low": h.amount_low, "high": h.amount_high, "currency": h.currency})
