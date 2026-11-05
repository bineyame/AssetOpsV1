"""`priced_energy@1` (build sheet CH-6 §A2.3, R4, R11).

earnings: the sum of the stored day `money.amount` over the measure's COMPLETE and PARTIAL rows, in one currency, or
no money with `CURRENCY_MIXED`. A PARTIAL day is never scaled; nothing is extrapolated or summed across Sites (the
context holds one Site's rows).
potential: headroom kW low/high x 1 h x the declared price, only when the opportunity's evidence is SUPPORTED."""
from __future__ import annotations

from decimal import Decimal

from assetops_backend.chain.grading import COMPLETE, PARTIAL
from assetops_backend.chain.strategies.base import (
    CURRENCY_MIXED, DECLARED, MEASURED, NO_RECORDS, NOT_PRICED, NOT_SUPPORTED, SUPPORTED, ContributionContext, Effect)
from assetops_backend.chain.strategies.graded_verdict import grade_counts

COUNTED = (COMPLETE, PARTIAL)
ONE_HOUR = Decimal(1)


class PricedEnergy:
    key, version = "priced_energy", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        if ctx.record.node == "potential":
            return self._potential(ctx)
        return self._earnings(ctx)

    def _earnings(self, ctx: ContributionContext) -> Effect:
        d = ctx.record.direction
        days = grade_counts(ctx.day_rows)
        rows = [r for r in ctx.day_rows if r.grade in COUNTED]
        if not rows:
            return Effect(d, basis=MEASURED, days=days, reason=NO_RECORDS)
        priced = [r for r in rows if r.money and r.money.get("amount") is not None]
        if not priced:
            return Effect(d, basis=MEASURED, days=days, reason=NOT_PRICED)
        currencies = {str(r.money.get("currency")) for r in priced}
        if len(currencies) != 1:
            return Effect(d, basis=MEASURED, days=days, reason=CURRENCY_MIXED)
        total = sum((Decimal(str(r.money["amount"])) for r in priced), Decimal("0.00"))
        ids = tuple(f"{r.local_day.isoformat()}/{r.measure}/{r.subject_ref}" for r in priced)
        return Effect(d, basis=MEASURED, days=days, explanation_ids=ids,
                      money={"amount": total, "currency": currencies.pop()})

    def _potential(self, ctx: ContributionContext) -> Effect:
        d = ctx.record.direction
        if ctx.evidence_status != SUPPORTED or ctx.headroom_kw is None:
            return Effect(d, basis=DECLARED, reason=NOT_SUPPORTED)
        if ctx.price is None or not ctx.currency:
            return Effect(d, basis=DECLARED, reason=NOT_PRICED)
        lo, hi = ctx.headroom_kw
        return Effect(d, magnitude=(hi, "kW"), basis=DECLARED,
                      money={"low": lo * ONE_HOUR * ctx.price, "high": hi * ONE_HOUR * ctx.price,
                             "currency": ctx.currency})
