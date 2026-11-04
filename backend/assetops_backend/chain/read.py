"""ChainReader (CH-5a1, build sheet Part A §A2-§A3): the board's chain reads, one indexed query each, memoised
per request in the read scope (`assetops_backend.read_scope`, CH5a-R R1).

Pure: the rules here (`site_cutoff`, `readiness_of`, `day_settled`, `day_gaps`, `board_day`, `summary_day`,
`assessment_state`) and the `ChainReader` that composes its ports. It imports no store, driver or other domain's
adapter; the SQL lives in `chain/adapters/postgres_chain_read.py` and the composition hands the ports in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend import read_scope
from assetops_backend.chain.grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING
from assetops_backend.chain.measures import measures_for

FULL, LIMITED, NONE, UNKNOWN = "FULL", "LIMITED", "NONE", "UNKNOWN"
MINI_DOMAIN = "mini_grid"
#: The chain measure Site type of each board domain (`chain/measures.py`).
SITE_TYPE_OF_DOMAIN = {"mini_grid": "MINIGRID", "cold_chain": "COLDCHAIN", "ev_charging": "EV"}


# ---- rules -------------------------------------------------------------------------------------------------------

def site_cutoff(domain: str | None, request_known_at: datetime | None, evidence_cutoff: datetime | None,
                k: datetime | None) -> datetime | None:
    """R7, the one cutoff rule: mini -> the request's cutoff (None = as known now); cold/EV -> the evidence cutoff
    bounded by `k` when the evidence cutoff is known, else the request's cutoff."""
    if domain == MINI_DOMAIN or evidence_cutoff is None:
        return request_known_at
    return evidence_cutoff if k is None else min(evidence_cutoff, k)


def _per_day(rows: Iterable[Any]) -> dict[date, dict[str, list[str]]]:
    out: dict[date, dict[str, list[str]]] = {}
    for r in rows:
        out.setdefault(r.local_day, {}).setdefault(r.measure, []).append(r.grade)
    return out


def _day_grades(per_measure: Mapping[str, Sequence[str]], measures: Sequence[str]) -> list[str]:
    """CH5a1-R Q9 (the `chain/reader.py` `_counts` rule): a measure with no stored row is NO_DATA, unless the day
    carries a NOT_EXPECTED row."""
    not_expected_day = any(NOT_EXPECTED in g for g in per_measure.values())
    grades: list[str] = []
    for m in measures:
        grades.extend(per_measure.get(m) or [NOT_EXPECTED if not_expected_day else NO_DATA])
    return grades


def readiness_of(rows: Iterable[Any], days: Iterable[date], measures: Sequence[str]) -> str:
    """R5 over a day set (CH5a1-R Q8, rows pooled): any PENDING or no expected row -> UNKNOWN; every expected row
    COMPLETE -> FULL; any COMPLETE or PARTIAL -> LIMITED; else (LOW or NO_DATA only) -> NONE."""
    by_day = _per_day(rows)
    grades: list[str] = []
    for d in days:
        grades.extend(_day_grades(by_day.get(d, {}), measures))
    expected = [g for g in grades if g != NOT_EXPECTED]
    if not expected or PENDING in expected:
        return UNKNOWN
    if all(g == COMPLETE for g in expected):
        return FULL
    if any(g in (COMPLETE, PARTIAL) for g in expected):
        return LIMITED
    return NONE


def day_grade(per_measure: Mapping[str, Sequence[str]], measures: Sequence[str]) -> str:
    """The weakest grade of the day's expected rows (`chain/reader.py` `_day_grade`), missing rows as Q9."""
    expected = [g for g in _day_grades(per_measure, measures) if g != NOT_EXPECTED]
    if not expected:
        return NOT_EXPECTED
    for g in (PENDING, NO_DATA, LOW, PARTIAL, COMPLETE):
        if g in expected:
            return g
    return NO_DATA


def day_settled(rows: Iterable[Any], day: date, measures: Sequence[str]) -> bool:
    """R4: a board day is settled when every measure's latest snapshot at the cutoff exists and is not PENDING
    (a NOT_EXPECTED row covers the whole day)."""
    per = _per_day(rows).get(day, {})
    if any(NOT_EXPECTED in g for g in per.values()):
        return not any(PENDING in g for g in per.values())
    return bool(measures) and all(per.get(m) and PENDING not in per[m] for m in measures)


def day_gaps(rows: Iterable[Any], days: Iterable[date], measures: Sequence[str]) -> tuple[date, ...]:
    """R8 / Q9: the requested days whose day grade is PENDING or NO_DATA (a missing row counts as NO_DATA)."""
    by_day = _per_day(rows)
    return tuple(d for d in days if day_grade(by_day.get(d, {}), measures) in (PENDING, NO_DATA))


def _zone(tz: str | None) -> Any:
    return timezone.utc if not tz else ZoneInfo(tz)


def board_day(d: date, tz: str | None) -> tuple[datetime, datetime]:
    """R6: the board day D is the Site-local day `[local 00:00 D, local 00:00 D+1)` as UTC instants."""
    z = _zone(tz)
    lo = datetime.combine(d, time(0), tzinfo=z).astimezone(timezone.utc)
    hi = datetime.combine(d + timedelta(days=1), time(0), tzinfo=z).astimezone(timezone.utc)
    return lo, hi


def summary_day(to: datetime, tz: str | None) -> date:
    """R6 (the CH3-R `day_at` rule): the summary's mini day is the Site-local day of `to - 1 µs`."""
    return (to - timedelta(microseconds=1)).astimezone(_zone(tz)).date()


def local_days(lo: datetime, hi: datetime, tz: str | None) -> tuple[date, ...]:
    """Every Site-local day the window `[lo, hi)` intersects (CH5a1-R Q8)."""
    z = _zone(tz)
    first, last = lo.astimezone(z).date(), (hi - timedelta(microseconds=1)).astimezone(z).date()
    out, d = [], first
    while d <= last:
        out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def assessment_state(dispatch_status: str | None) -> str | None:
    """CH5a1-R Q2: the overview's UNASSESSED -> UNKNOWN map over the dispatch body's raw `status`."""
    if dispatch_status is None:
        return None
    return UNKNOWN if dispatch_status == "UNASSESSED" else dispatch_status


# ---- facts -------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class DayFacts:
    days: tuple[date, ...]
    grades: Mapping[date, Mapping[str, Mapping[str, str]]]   # day -> measure -> subject_ref -> grade
    settled: bool                                             # the last day of `days` (the board day), R4
    readiness: str                                            # R5 over `days`
    gaps: tuple[date, ...]                                    # R8 / Q9 over `days`


@dataclass(frozen=True)
class FindingHead:
    finding_id: str
    revision_id: str
    revision_no: int
    lifecycle: str
    transition: str | None
    episode_start: datetime
    episode_end: datetime | None
    mechanism: str | None
    subject_ref: str | None
    thread_id: str | None = None
    occurrence_no: int | None = None


@dataclass(frozen=True)
class ActionFacts:
    action_id: str
    verification_state: str | None
    cost_check: Any
    trial_hours: Any
    has_change: bool


@dataclass(frozen=True)
class MoneyHead:
    priced: bool
    amount_low: Any
    amount_high: Any
    currency: str | None
    source_provenance: Any
    body: Any = None                        # the consequence read's money body (the fields `_money` shows)


class ChainReadPort(Protocol):
    """The SQL adapter (`chain/adapters/postgres_chain_read.py`)."""

    def snapshots(self, tenant_id: UUID, site_id: UUID, lo: date, hi: date, measures: Sequence[str],
                  known_at: datetime | None) -> Sequence[Any]: ...

    def finding_heads(self, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str, lo: datetime,
                      hi: datetime, known_at: datetime | None) -> Sequence[FindingHead]: ...

    def findings_settled(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> bool: ...

    def has_change(self, tenant_id: UUID, action_ids: Sequence[str]) -> Mapping[str, bool]: ...


@dataclass(frozen=True)
class ChainRequest:
    """One per route request (`ChainReader.request`): the tenant, the cutoff `k` and the ports."""

    reader: "ChainReader"
    tenant_id: UUID
    k: datetime | None

    def day(self, site_id: UUID, site_type: str, days: Sequence[date]) -> DayFacts:
        """One snapshot read per (Site, day range); `days` ends on the board day."""
        days = tuple(sorted(days))
        measures = tuple(m.measure for m in measures_for(site_type))
        rows = read_scope.memo("chain.day", self.reader.ports.snapshots, self.tenant_id, site_id, days[0],
                               days[-1], measures, self.k)
        grades: dict[date, dict[str, dict[str, str]]] = {}
        for r in rows:
            grades.setdefault(r.local_day, {}).setdefault(r.measure, {})[r.subject_ref] = r.grade
        return DayFacts(days, grades, day_settled(rows, days[-1], measures), readiness_of(rows, days, measures),
                        day_gaps(rows, days, measures))

    def findings(self, site_id: UUID, domain: str, analytic_id: str, lo: datetime,
                 hi: datetime) -> tuple[FindingHead, ...]:
        return tuple(read_scope.memo("chain.findings", self.reader.ports.finding_heads, self.tenant_id, site_id,
                                     domain, analytic_id, lo, hi, self.k))

    def findings_settled(self, site_id: UUID) -> bool:
        return bool(read_scope.memo("chain.findings_settled", self.reader.ports.findings_settled, self.tenant_id,
                                    site_id, self.k))

    def action_facts(self, site_id: UUID, site_code: str, action_ids: Sequence[str]) -> tuple[ActionFacts, ...]:
        """C6: the state, cost check and trial hours from one memoised `VerificationService.summary` per Action;
        `has_change` from one SQL over every id (replacing the `action` detail read)."""
        ids = tuple(str(a) for a in action_ids)
        if not ids:
            return ()
        changes = read_scope.memo("chain.has_change", self.reader.ports.has_change, self.tenant_id, ids)
        out = []
        for aid in ids:
            body = read_scope.memo("action_read", self.reader.verification, self.tenant_id, site_id, site_code, aid)
            body = body or {}
            out.append(ActionFacts(aid, body.get("state"), body.get("cost_check"), body.get("trial_hours"),
                                   bool(changes.get(aid))))
        return tuple(out)

    def money_head(self, site_id: UUID, finding_id: str, revision_id: str, *, is_latest: bool,
                   source_open: bool, settled: bool) -> MoneyHead | None:
        """One consequence read on the lead Finding (CH5a1-R Q5); `priced` per §A3."""
        if self.reader.money is None:
            return None
        body = read_scope.memo("chain.money_head", self.reader.money, self.tenant_id, site_id, finding_id,
                               revision_id, is_latest, source_open)
        if body is None:
            return None
        money = body.get("money") if isinstance(body, Mapping) and "money" in body else body
        elig = (money or {}).get("money_eligibility") or {}
        cur = (money or {}).get("currentness") or {}
        low, high = (money or {}).get("amount_low"), (money or {}).get("amount_high")
        priced = (elig.get("state") == "ELIGIBLE" and bool(cur.get("current_amount_shown"))
                  and low is not None and high is not None and settled)
        return MoneyHead(priced, low, high, (money or {}).get("currency"), (money or {}).get("source_provenance"),
                         money)


class ChainReader:
    """`ChainReader(ports, verification=..., money=...)`; `request(tenant_id, known_at)` per route request."""

    def __init__(self, ports: ChainReadPort, *, verification: Callable[..., Any] | None = None,
                 money: Callable[..., Any] | None = None) -> None:
        self.ports = ports
        self.verification = verification or (lambda *a: None)
        self.money = money

    def request(self, tenant_id: UUID, known_at: datetime | None) -> ChainRequest:
        return ChainRequest(self, tenant_id, known_at)
