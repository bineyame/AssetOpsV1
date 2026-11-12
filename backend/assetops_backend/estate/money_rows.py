"""ANY-2 AR-4 MN-2: kind `money.lines`, a mini-grid Site's stored potential money per Site-local day (architect answer
money-snapshot 2026-11-10 §6; D-MONEY.1-4; sequence rev 5 "AR-4 contract line"; D-ANY.8 step 3).

- What is stored: one row per (Site, local day d). Body `lines` holds the potential line in the receipt shape
  (`financials.money_lines.potential_line`): the opportunity study's headroom low/high kW x 1 h x the productive price
  valid at d's start, as the board composes it (`site_outcomes/mini.py` `_opportunity_item` over the
  `RENEWABLE_DAYS` local days ending on d, and `productive_price(start)`). The body also names the inputs it used
  (`study`, `price`), so a reader serves the line only when the page's own study and price are the same (else
  today's compose, the D-ANY.6a rule). No totals are ever stored (MN-3 `refuse_totals`, enforced at build).
- What rebuilds it (register `kinds: money.lines`): `price.revised@1` by assumption key. The 0044 trigger's subject
  is `{"key", "valid": [valid_from, valid_to | null]}` and the `valid_local` day rule runs an open revision to the
  Site's today, so a saved price (PR-3, `SITE_ADMIN_ENTRY`, same trigger) dirties every day from its applies-from
  date to today; the drain rebuilds them as new revisions. Renewable inputs (the study's headroom source) dirty it
  too. An opportunity study revision raises no day event (`opportunity.revised@1` is `days: none`): the read-time
  study comparison covers it.
- Not built here (resume list in `.agent/AR-4-packet.md`): the read side (`priced_energy._potential` /
  `OutcomeEvaluator._potential` reading the stored line) and its parity.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.chain.period_read import PeriodFragment
from assetops_backend.financials.money_lines import potential_line, refuse_totals

KIND_MONEY = "money.lines"
BUILDER_VERSION = "estate-money-lines-1"
MINIGRID = "MINIGRID"
PRODUCTIVE_PRICE_KEY = "productive_use_price_per_kwh"
RENEWABLE_DAYS = 5  # site_outcomes/mini.py RENEWABLE_DAYS: the board's opportunity look-up days
SUPPORTED = "SUPPORTED"


def _midnight(day: date, tz: str) -> datetime:
    return datetime.combine(day, time(0), tzinfo=ZoneInfo(tz or "UTC")).astimezone(timezone.utc)


def _dec(value: Any) -> Decimal | None:
    try:
        return None if value is None else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def price_of(selection: Any) -> dict[str, Any] | None:
    """The PRICED selection as the board's sales price (`{"amount", "currency", "revision_id"}`), else None."""
    sel = selection or {}
    price = sel.get("price") or {}
    if sel.get("state") != "PRICED" or _dec(price.get("value")) is None:
        return None
    return {"amount": str(_dec(price.get("value"))), "currency": price.get("currency"),
            "revision_id": None if sel.get("revision_id") is None else str(sel["revision_id"]).lower()}


def study_of(item: Any) -> dict[str, Any] | None:
    """The study fields the potential reads (`OutcomeEvaluator._potential`): status and headroom low/high."""
    study = (item or {}).get("study") if item else None
    if not study:
        return None
    head = study.get("headroom_kw") or None
    return {"status": study.get("status"),
            "headroom_kw": None if not head else {"low": str(head.get("low")), "high": str(head.get("high"))}}


def day_body(site_id: Any, day: date, item: Any, selection: Any) -> dict[str, Any]:
    """The stored `money.lines` body of one local day; `lines` is empty when today's compose shows no money."""
    study, price = study_of(item), price_of(selection)
    lines: list[dict[str, Any]] = []
    head = (study or {}).get("headroom_kw")
    if study and study["status"] == SUPPORTED and head and price and price.get("currency"):
        lo, hi, rate = _dec(head["low"]), _dec(head["high"]), _dec(price["amount"])
        if lo is not None and hi is not None and rate is not None:
            line = potential_line(lo, hi, rate, price["currency"], price["revision_id"])
            lines.append({"kind": "potential", "site_id": str(site_id).lower(), **line})
    body = {"day": day.isoformat(), "study": study, "price": price, "lines": lines}
    refuse_totals(body)  # MN-3: never a stored total
    return body


class MoneyLinesKindBuilder:
    """`chain.period_read.KindBuilder` for `money.lines` over the read-only estate reader (its
    `opportunity_threads`, the board's CH-4 read) and the assumption read service (`series`, the board's price)."""

    kind = KIND_MONEY
    builder_version = BUILDER_VERSION

    def __init__(self, estate_read: Any | Callable[[], Any], assumptions: Any | Callable[[], Any]) -> None:
        self._estate, self._assumptions = estate_read, assumptions

    @staticmethod
    def _get(source: Any, attr: str) -> Any:
        return source() if callable(source) and not hasattr(source, attr) else source

    def fragments(self, ctx: Any, site: Any) -> Sequence[PeriodFragment]:
        if site.site_type != MINIGRID:
            return []
        day, tz = ctx.local_day, site.timezone
        start, end = _midnight(day, tz), _midnight(day + timedelta(days=1), tz)
        lo = _midnight(day - timedelta(days=RENEWABLE_DAYS - 1), tz)
        estate = self._get(self._estate, "read")

        def work(snap: Any) -> PeriodFragment:
            items = snap.opportunity_threads(ctx.tenant_id, [site.site_id], lo, end, snap.read_at) or ()
            item = next((i for i in items if i.get("site_code") == site.site_code and i.get("study")), None)
            series = self._get(self._assumptions, "series").series(
                ctx.tenant_id, site.site_id, PRODUCTIVE_PRICE_KEY, valid_at=start, recorded_at=snap.read_at)
            return self.fragment(site.site_id, day, start, end, item, (series or {}).get("selection"))

        return [estate.read(work)]

    @staticmethod
    def fragment(site_id: UUID, day: date, start: datetime, end: datetime, item: Any,
                 selection: Any) -> PeriodFragment:
        body = day_body(site_id, day, item, selection)
        state = "PRICED" if body["lines"] else "NO_MONEY"
        # D-MONEY: input_fp covers every rate_ref (the body's price revision) and the study it read.
        inputs = {"rate_refs": sorted({x["receipt"]["rate_ref"] for x in body["lines"] if x["receipt"]["rate_ref"]}),
                  "study": body["study"], "price": body["price"]}
        return PeriodFragment(start, end, state, body, inputs=inputs, local_day=day)


def kind_builders(estate_read: Any, assumptions: Any) -> dict[str, MoneyLinesKindBuilder]:
    return {KIND_MONEY: MoneyLinesKindBuilder(estate_read, assumptions)}


def kind_versions() -> dict[str, str]:
    return {KIND_MONEY: BUILDER_VERSION}


__all__ = ["BUILDER_VERSION", "KIND_MONEY", "MoneyLinesKindBuilder", "day_body", "kind_builders", "kind_versions",
           "price_of", "study_of"]
