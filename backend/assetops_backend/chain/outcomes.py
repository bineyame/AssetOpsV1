"""CH-6a2 (build sheet CH-6 §A3, R5, R6, R8, R11, R12, R13; CH6a2-R): the OutcomeEvaluator.

Pure: its inputs are frozen facts the composer read through ChainReader (`NodeInputs`); no I/O, no clock, no store.
For one outcome it gives the three node claims `{"kpi", "earnings", "potential"}` (PC-1 `Claim`s, rendered in
`chain/vocabulary.py`), and `readings` gives the R5/R6-adjusted KPI readings. `objectives.judge` and `judge_month`
are called unchanged; every day count is the one day rule (`chain/reader.py` `counts` / `day_grade`).
"""
from __future__ import annotations

import calendar
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from assetops_backend.chain import vocabulary as v
from assetops_backend.chain.grading import COMPLETE, PARTIAL
from assetops_backend.chain.lifecycle import TRANSITIONS
from assetops_backend.chain.reader import GradeCounts, counts
from assetops_backend.chain.strategies import REGISTRY
from assetops_backend.chain.strategies.base import ContributionContext, Registry
from assetops_backend.chain.strategies.graded_verdict import day_grades
from assetops_backend.outcomes.objectives import MEASURES, NOT_JUDGED, ObjectiveFact, Reading, judge, judge_month
from assetops_backend.outcomes.outcome_map import (
    CONTRIBUTIONS, NODE_EARNINGS, NODE_KPI, NODE_POTENTIAL, OutcomeContribution)

#: Design §4.3b: only MEASURED and RECORDED rows are authoritative for a node.
AUTHORITY = {"MEASURED": True, "RECORDED": True, "DECLARED": False, "MODELLED": False, "EXTERNAL": False}
COUNTED = (COMPLETE, PARTIAL)
#: CH6a3-R D2: the potential shows the thread's latest study in every thread state except these (a verified or
#: withdrawn study is not the latest evidence). Defined by exclusion so a state cannot be left out again.
POTENTIAL_EXCLUDED = ("RESOLVED_MONITORING", "CLOSED", "WITHDRAWN")
#: Every thread state of `chain/lifecycle.py` `TRANSITIONS` (sources and targets) not in `POTENTIAL_EXCLUDED`.
POTENTIAL_STATES = tuple(sorted({s for (f, _), t in TRANSITIONS.items() for s in (f, t) if s}
                                - set(POTENTIAL_EXCLUDED)))


def potential_shown(item: Mapping[str, Any] | None) -> bool:
    """CH6a3-R D2/Q5: the headroom study (the Potential part and the Grow headroom words) is shown for this thread."""
    return bool(item) and bool(item.get("state")) and item.get("state") not in POTENTIAL_EXCLUDED
#: R13: the `SIGNAL:PRODUCTIVE_USE_HEADROOM` status signal is open exactly in these thread states.
SIGNAL_OPEN_STATES = ("OPEN", "RECURRED")
#: CH6a2-R Q2: an objective measure with no `kpi` record whose composer Reading is computed from one stored chain
#: measure's board-day row. MG-5's `unserved_critical_kwh` Reading is the board day's `critical_served` row
#: (`site_outcomes/mini.py` `critical_served` and `mini_readings`, `served=critical_served(day_facts, day)`).
READING_MEASURE = {"unserved_critical_kwh": "critical_served"}


@dataclass(frozen=True)
class NodeInputs:
    """Built by the composer from one ChainRequest; frozen."""
    site_code: str
    domain: str
    tz: str
    window: tuple[date, date]                  # Site-local [lo, hi] inclusive; hi is the board day
    rows: tuple[Any, ...] = ()                 # SnapshotRow of every measure over the window (and the MG-1 month)
    objectives: tuple[ObjectiveFact, ...] = ()
    readings: Mapping[str, Reading] = field(default_factory=dict)   # the composer's KPI readings
    opportunity: Mapping[str, Any] | None = None   # the CH-4 item of the Site's headroom thread at k
    warnings: tuple[Any, ...] = ()             # outcomes.warnings.Warning
    money_heads: Mapping[str, Any] = field(default_factory=dict)    # chain.read.MoneyHead by Finding id
    price: Mapping[str, Any] | None = None     # the declared productive price {"amount", "currency"} at hi
    #: Additive (CH-6a2): the lead Finding id per mechanism, so an `avoided_cost@1` record finds its money head.
    lead_findings: Mapping[str, str] = field(default_factory=dict)


def headroom_signal_on(item: Mapping[str, Any] | None) -> bool:
    """R13: the headroom status signal is open exactly when the opportunity thread is OPEN or RECURRED at k."""
    return bool(item) and item.get("state") in SIGNAL_OPEN_STATES


def _kind(record: OutcomeContribution) -> tuple[str, str]:
    kind, _, name = record.source.partition(":")
    return kind, name


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


class OutcomeEvaluator:
    def __init__(self, contributions: tuple[OutcomeContribution, ...] = CONTRIBUTIONS,
                 strategies: Registry = REGISTRY) -> None:
        self._records = contributions
        self._strategies = strategies

    # ---- lookups ------------------------------------------------------------------------------------------------

    def _record(self, outcome_key: str, node: str) -> OutcomeContribution | None:
        return next((r for r in self._records if r.outcome == outcome_key and r.node == node), None)

    @staticmethod
    def _rows(inp: NodeInputs, measure: str, lo: date, hi: date) -> tuple[Any, ...]:
        return tuple(r for r in inp.rows if r.measure == measure and AUTHORITY.get(r.evidence_class, False)
                     and lo <= r.local_day <= hi)

    @staticmethod
    def _objective(inp: NodeInputs, outcome_key: str) -> ObjectiveFact | None:
        return next((o for o in inp.objectives if o.outcome_key == outcome_key), None)

    # ---- A3.1 verdict -------------------------------------------------------------------------------------------

    def _month_reading(self, inp: NodeInputs, measure: str) -> tuple[Reading, GradeCounts]:
        """R5: MG-1 from day snapshots over the Site-local month to the board day. Value = sum of kWh over the
        COMPLETE and PARTIAL days; checked = COMPLETE days; LOW days are counted in `days` and never totalled."""
        hi = inp.window[1]
        lo = hi.replace(day=1)
        rows = self._rows(inp, measure, lo, hi)
        grades = day_grades(rows)
        counted = {d for d, g in grades.items() if g in COUNTED}
        kwh = [Decimal(str(r.value["kwh"])) for r in rows
               if r.local_day in counted and r.grade in COUNTED and r.value and r.value.get("kwh") is not None]
        value = sum(kwh, Decimal(0)) if counted else None
        checked = sum(1 for g in grades.values() if g == COMPLETE)
        elapsed = (hi - lo).days + 1
        month_days = calendar.monthrange(hi.year, hi.month)[1]
        reading = Reading(value, elapsed == month_days and checked == month_days, None, checked, elapsed, month_days)
        return reading, counts(rows, lo, hi, [measure])

    def _reading(self, inp: NodeInputs, o: ObjectiveFact) -> tuple[Reading | None, GradeCounts | None]:
        rec = self._record(o.outcome_key, NODE_KPI)
        measure = MEASURES.get(o.measure_key)
        lo, hi = inp.window
        if rec is not None:
            chain_measure = _kind(rec)[1]
            if measure is not None and measure.monthly:
                return self._month_reading(inp, chain_measure)
            days = counts(self._rows(inp, chain_measure, lo, hi), lo, hi, [chain_measure])
            base = inp.readings.get(o.outcome_key)
            if base is None:
                return None, days
            # R6: a MET needs every expected day of the record's measure COMPLETE; the value is unchanged.
            all_complete = days.expected > 0 and days.complete == days.expected
            return replace(base, complete=base.complete and all_complete), days
        base = inp.readings.get(o.outcome_key)
        source = READING_MEASURE.get(o.measure_key)
        if source is None:
            return base, None
        return base, counts(self._rows(inp, source, hi, hi), hi, hi, [source])

    def readings(self, inp: NodeInputs) -> dict[str, Reading]:
        """The composer's readings with R5 (MG-1 from snapshots, its text by §A4) and R6 (completeness) applied."""
        out = dict(inp.readings)
        for o in inp.objectives:
            r, _ = self._reading(inp, o)
            if r is None:
                continue
            m = MEASURES.get(o.measure_key)
            if m is not None and m.monthly:
                r = replace(r, actual_text=self._month_text(o, r))
            out[o.outcome_key] = r
        return out

    @staticmethod
    def _month_text(o: ObjectiveFact, r: Reading) -> str:
        return v.mg1_text(judge_month(o, r), r.value, r.checked_days or 0, r.elapsed_days or 0, r.month_days or 0,
                          o.target, o.min_checked_days)

    def _kpi(self, inp: NodeInputs, outcome_key: str) -> v.Claim:
        o = self._objective(inp, outcome_key)
        if o is None:
            return v.verdict_claim(outcome_key, None, None, None)     # CH6a2-R Q6
        r, days = self._reading(inp, o)
        m = MEASURES.get(o.measure_key)
        if m is not None and m.monthly:
            return v.verdict_claim(outcome_key, judge_month(o, r), days, self._month_text(o, r))
        if r is None:
            return v.verdict_claim(outcome_key, NOT_JUDGED, days, None)
        return v.verdict_claim(outcome_key, judge(o, r), days, r.actual_text)

    # ---- A3.2 earnings ------------------------------------------------------------------------------------------

    def _earnings(self, inp: NodeInputs, outcome_key: str) -> v.Claim | None:
        rec = self._record(outcome_key, NODE_EARNINGS)
        if rec is None:
            return None
        strategy = self._strategies.resolve(rec.strategy)
        label = (rec.money or {}).get("label") or rec.driver
        kind, name = _kind(rec)
        if kind == "FINDING":
            # CH6a2-R Q2: the stored consequence is the lead Finding's fuel-cost read (`chain/read.py` `money_head`,
            # `consequence.display`), not computed from `avoidable_gen_min` rows, so it has no days: NOT_KNOWN.
            head = inp.money_heads.get(inp.lead_findings.get(name, ""))
            e = strategy.effect(ContributionContext(rec, money_head=head))
            claim = v.money_claim(label, e.money, None, e.reason)
            return claim if not e.money else _with(claim, fuel_basis(head))
        lo, hi = inp.window
        measure = (rec.money or {}).get("measure") or name
        rows = self._rows(inp, measure, lo, hi)
        e = strategy.effect(ContributionContext(rec, day_rows=rows))
        claim = v.money_claim(label, e.money, counts(rows, lo, hi, [measure]), e.reason)
        return claim if not e.money else _with(claim, energy_basis(rows, inp.price))

    # ---- A3.3 potential -----------------------------------------------------------------------------------------

    def _potential(self, inp: NodeInputs, outcome_key: str) -> v.Claim | None:
        rec = self._record(outcome_key, NODE_POTENTIAL)
        if rec is None:
            return None
        kind, name = _kind(rec)
        strategy = self._strategies.resolve(rec.strategy)
        if kind == "WARNING":
            # R12: the warning's own title when present, else "No potential found yet"; no days, NOT_KNOWN.
            w = next((w for w in inp.warnings if w.kind == name), None)
            e = strategy.effect(ContributionContext(rec, title=None if w is None else w.title))
            return v.potential_claim(rec.driver, None, None, [e.title] if e.title else [])
        item = inp.opportunity
        if not potential_shown(item):
            return v.potential_claim(rec.driver, None, None, [])          # CH6a2-R Q4
        study = item.get("study") or {}
        days = self._study_days(study)
        status, headroom = study.get("status"), study.get("headroom_kw")
        if status == "SUPPORTED" and headroom:
            lo, hi = _dec(headroom["low"]), _dec(headroom["high"])
            price = inp.price or {}
            e = strategy.effect(ContributionContext(
                rec, headroom_kw=(lo, hi), evidence_status=status, price=_dec(price.get("amount")),
                currency=price.get("currency") or None))
            value: dict[str, Any] = {"low": str(lo), "high": str(hi), "unit": "kW"}
            if e.money:
                value.update(money_low=str(e.money["low"]), money_high=str(e.money["high"]),
                             currency=e.money["currency"])
            return v.potential_claim(rec.driver, value, days, v.potential_lines(lo, hi, e.money))
        line = item.get("limit_line")
        return v.potential_claim(rec.driver, None, days, [line] if line else [])

    @staticmethod
    def _study_days(study: Mapping[str, Any]) -> GradeCounts | None:
        """CH6a2-R Q2: the potential's days are the study's own days when the CH-4 item carries their grades
        (`study.day_grades`, ISO day -> grade); today's item (`chain/opportunities.py` `_item`) carries first and
        last day but no grade, so the days are None and the basis NOT_KNOWN (MD-CH6-4)."""
        grades = study.get("day_grades")
        if not grades or not study.get("first_day") or not study.get("last_day"):
            return None
        first, last = date.fromisoformat(study["first_day"]), date.fromisoformat(study["last_day"])
        rows = [_StudyDay(date.fromisoformat(d), g) for d, g in grades.items()]
        return counts(rows, first, last, [_StudyDay.measure])

    # ---- public -------------------------------------------------------------------------------------------------

    def nodes(self, inp: NodeInputs, outcome_key: str) -> dict[str, v.Claim | None]:
        return {"kpi": self._kpi(inp, outcome_key), "earnings": self._earnings(inp, outcome_key),
                "potential": self._potential(inp, outcome_key)}


# ---- CH6a3-R Q3: the price basis of a money claim ("Why?" names it) ------------------------------------------

def _with(claim: v.Claim, extra: Mapping[str, Any] | None) -> v.Claim:
    return claim if not extra else replace(claim, value={**claim.value, **extra})


def energy_basis(rows: tuple[Any, ...], price: Mapping[str, Any] | None) -> dict[str, Any]:
    """`kwh` = the counted days' stored kWh (the rows the earnings sum adds); `measured_seconds` = their stored
    measured seconds when every counted row carries them. CH6a3-R2 M5: `price` = the declared price only when its
    `revision_id` IS the counted rows' one price revision (so kWh x price reproduces the figure); several revisions
    give `price_count`; no revision on the rows, or another revision than the price's, gives no price line."""
    grades = day_grades(rows)
    counted = [r for r in rows if grades.get(r.local_day) in COUNTED and r.grade in COUNTED
               and r.money and r.money.get("amount") is not None]
    kwh = sum((Decimal(str(r.value["kwh"])) for r in counted if r.value and r.value.get("kwh") is not None),
              Decimal(0))
    revs: set[str] = set()
    for r in counted:
        one = r.money.get("assumption_revision_id")
        revs.update(str(x).lower() for x in ([one] if one else (r.money.get("tariff_revision_ids") or ())))
    out: dict[str, Any] = {"kwh": str(kwh)}
    seconds = [(r.value or {}).get("measured_seconds") for r in counted]
    if counted and all(s is not None for s in seconds):
        out["measured_seconds"] = sum(int(s) for s in seconds)
    if len(revs) > 1:
        out["price_count"] = len(revs)
    elif (len(revs) == 1 and price and price.get("amount") is not None
          and str(price.get("revision_id") or "").lower() in revs):
        out["price"] = {"amount": str(price["amount"]), "currency": price.get("currency")}
    return out


def _litres(value: Any) -> str:
    """CH6a3-R2 M5: litres to one place, half up, trailing zeros dropped (`analytics/dispatch.py` `_dec(.., 1)`)."""
    text = str(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    return text.rstrip("0").rstrip(".") if "." in text else text


def fuel_basis(head: Any) -> dict[str, Any] | None:
    """MG-2: the stored consequence's litres (`quantity` low/high, unit L) and its one declared fuel price
    (`financials/consequence_read.py`). None (no line) when the body carries no price."""
    cons = ((getattr(head, "body", None) or {}).get("consequence")) or {}
    q, p = cons.get("quantity") or {}, cons.get("price") or {}
    if q.get("low") is None or q.get("high") is None or p.get("value") is None:
        return None
    return {"litres_low": _litres(q["low"]), "litres_high": _litres(q["high"]),
            "price": {"amount": str(p["value"]), "currency": p.get("currency")}}


def has_node(outcome_key: str, objectives: tuple[ObjectiveFact, ...]) -> bool:
    """CH6a3-R Q1: an outcome carries nodes when it has an objective or any kpi/earnings/potential record."""
    return any(o.outcome_key == outcome_key for o in objectives) or any(
        r.outcome == outcome_key and r.node in (NODE_KPI, NODE_EARNINGS, NODE_POTENTIAL) for r in CONTRIBUTIONS)


def site_nodes(inp: NodeInputs, keys: Any) -> dict[str, dict[str, Any]]:
    """The composers' one call: per outcome key with nodes, the claims as JSON (`SiteFacts.nodes`)."""
    ev = OutcomeEvaluator()
    return {k: {n: None if c is None else c.to_json() for n, c in ev.nodes(inp, k).items()}
            for k in keys if has_node(k, inp.objectives)}


@dataclass(frozen=True)
class _StudyDay:
    local_day: date
    grade: str
    measure: str = "study_day"
    subject_ref: str = "SITE"


def earnings_money(claim: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """CH6a3-R Q4: a board headline money from an earnings claim JSON; None when the claim is NOT_KNOWN."""
    value = (claim or {}).get("value")
    if not value:
        return None
    low, high = value.get("low", value.get("amount")), value.get("high", value.get("amount"))
    return {"amount_low": low, "amount_high": high, "currency": value.get("currency")}


def earnings_parts(claim: Mapping[str, Any] | None, day: date | None = None) -> dict[str, Any]:
    """CH6a3-R2 H3 (ONE-SOURCE): what a Grow row may state about sales or charging, from the earnings claim alone.
    Known: the headline money, the basis kWh, the basis price (None without a single-revision price line) and the
    stored measured seconds. NOT_KNOWN: `text` = "Not known yet" with the claim's own days line (`day` only when the
    window is one Site-local day, M4); the caller then states no kWh, price or subline."""
    value = (claim or {}).get("value")
    if not value:
        line = v.days_line((claim or {}).get("days"), day)
        return {"known": False, "text": v.NOT_KNOWN_TEXT if line is None else f"{v.NOT_KNOWN_TEXT} · {line}"}
    return {"known": True, "money": earnings_money(claim), "kwh": _dec(value.get("kwh")),
            "price": value.get("price"), "measured_seconds": value.get("measured_seconds")}
