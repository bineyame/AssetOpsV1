"""W4-02 unit 5: the historical mini-depth reads (`D-2026-10-20-w4-02-buildspec`).

One read-only REPEATABLE READ transaction whose first statement captures `clock_timestamp()` (closure 4 N6; a
constructor-only `test_read_clock_override` replaces it in tests). Inside it:

- the window is validated against the pinned `site.timezone` (closure 1 Q4/Q5/Q33, S8): service, fuel and backup
  take exactly one Site-local clock hour; renewable takes 1-5 consecutive complete Site-local days, each composed
  from its individually selected local noon hour (first occurrence; a nonexistent noon refuses `INVALID_WINDOW`);
- each hour's head is the greatest `(selected_at, seq)` with `selected_at <= known_at` **and** the revision's
  `knowledge_cutoff <= known_at` (Q14), rechecked for tenant/Site/domain/window lineage and its stored basis;
- per hour currentness (Q6/Q7, q6 ruling 5): a live (PENDING/LEASED/FAILED) overlapping job not cleared by a later
  selection gives PENDING_RECOMPUTE; an input digest recomputed at the read cutoff that differs from the selected
  revision's (a newer eligible accepted row, Foundation or binding publication) gives STALE_SOURCE without touching
  the frozen result; an explicit cutoff before the read time gives HISTORICAL; otherwise CURRENT;
- the dual source provenance (Q18) through `mini_depth/provenance.py`;
- renewable `status`/`cards` composed with `rules.summarize_renewable` over the selected hours only (q6 ruling 1).

Nothing is computed into a claim or persisted: the read never writes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_backend.financials import fuel_cost
from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.inputs import (
    QUERY_ROLES,
    MiniInputsRefused,
    load_hour_inputs,
    local_noon,
    zone,
)
from assetops_backend.mini_depth.provenance import LinkRowsOn, mini_blocks
from assetops_backend.mini_depth.store import DOMAINS, JOB_DOMAIN, read_hour_rows
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4

HOUR = timedelta(hours=1)
MAX_DAYS = 5
SCHEMA_VERSION = "mini-depth-1"
MINIGRID = "MINIGRID"
LIVE_JOB_STATUSES = ("PENDING", "LEASED", "FAILED")
#: Aggregate precedence, first match (closure 1 Q6/Q7).
CURRENTNESS_ORDER = ("UNKNOWN", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "CURRENT")
JOB_ORDER = ("FAILED", "LEASED", "PENDING", "NONE", "SETTLED")
#: Closure 1 Q11 refusal copy.
MESSAGES = {
    "INVALID_WINDOW": "Select a valid complete site-local hour or one to five site-local days.",
    "INVALID_KNOWN_AT": "Select a knowledge time at or before this read.",
    "MINI_DEPTH_STORE_UNAVAILABLE": "Mini-grid evidence is unavailable right now. Try again.",
}
NULL_CARDS: dict[str, dict[str, None]] = {
    "renewable": dict.fromkeys(("capability_kw", "used_kw", "headroom_kw", "eligible_days", "assessed_days")),
    "service": dict.fromkeys(("delivered_load_kw", "interruptions_seen", "critical_delivered_kw", "unserved_kwh")),
    "fuel": dict.fromkeys(("opening_l", "deliveries_l", "expected_use_l", "closing_l", "residual_l")),
    "backup": dict.fromkeys(("outage_count", "start_success_count", "last_witnessed_test_at", "critical_recovery")),
}
_LIMIT_ORDER = {code: i for i, code in enumerate(rules.LIMITATION_ORDER)}


class MiniReadRefused(ValueError):
    """A 422 refusal (`INVALID_WINDOW` or `INVALID_KNOWN_AT`)."""

    def __init__(self, code: str) -> None:
        super().__init__(MESSAGES[code])
        self.code = code


class MiniReadUnavailable(RuntimeError):
    """The mini store, its lineage or the provenance resolver failed: 503, never an empty or guessed result."""


def iso(at: datetime | None) -> str | None:
    """Q33 token: UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ`."""
    return fuel_cost.iso(at)


def _local_midnight(day: date, tz_name: str) -> datetime:
    tz = zone(tz_name)
    naive = datetime.combine(day, time(0))
    start = naive.replace(tzinfo=tz, fold=0).astimezone(timezone.utc)
    if start.astimezone(tz).replace(tzinfo=None) != naive:
        raise MiniReadRefused("INVALID_WINDOW")
    return start


def hour_windows(domain: str, lo: datetime, hi: datetime, tz_name: str | None) -> list[tuple[date, rules.Window]]:
    """The requested `(local_day, hour)` windows, or `INVALID_WINDOW` (Q4/Q5; an unknown zone refuses, S8)."""
    try:
        tz = zone(tz_name)
        if not lo < hi:
            raise MiniReadRefused("INVALID_WINDOW")
        if domain != "renewable":
            local = lo.astimezone(tz)
            if (local.minute, local.second, local.microsecond) != (0, 0, 0) or hi - lo != HOUR:
                raise MiniReadRefused("INVALID_WINDOW")
            return [(local.date(), rules.Window(lo, hi))]
        first = lo.astimezone(tz).date()
        days = [first + timedelta(days=i) for i in range(MAX_DAYS)]
        for n in range(1, MAX_DAYS + 1):
            if (_local_midnight(first, tz_name or ""), _local_midnight(first + timedelta(days=n), tz_name or "")
                    ) == (lo, hi):
                return [(d, local_noon(d, tz_name or "")) for d in days[:n]]
        raise MiniReadRefused("INVALID_WINDOW")
    except MiniInputsRefused as error:
        raise MiniReadRefused("INVALID_WINDOW") from error


@dataclass(frozen=True)
class _Head:
    seq: int
    revision_id: UUID
    knowledge_cutoff: datetime
    input_sha256: str
    result: dict[str, Any]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class _Hour:
    day: date
    window: rules.Window
    head: _Head | None
    job_state: str
    state: str
    pending_ids: tuple[str, ...] | None


_HEAD = text(
    "SELECT s.seq, s.revision_id, r.knowledge_cutoff, r.input_sha256, r.result, r.domain, r.window_start, "
    "r.window_end, COALESCE((SELECT array_agg(v.evidence_id::text ORDER BY v.evidence_id::text) "
    "FROM mini_depth_revision_evidence v WHERE v.tenant_id = r.tenant_id AND v.site_id = r.site_id "
    "AND v.revision_id = r.id), '{}') "
    "FROM mini_depth_selection s JOIN mini_depth_revision r "
    "ON r.tenant_id = s.tenant_id AND r.site_id = s.site_id AND r.id = s.revision_id "
    "WHERE s.tenant_id = :t AND s.site_id = :s AND s.domain = :d AND s.window_start = :lo AND s.window_end = :hi "
    "AND s.selected_at <= :k AND r.knowledge_cutoff <= :k "
    "ORDER BY s.selected_at DESC, s.seq DESC LIMIT 1")
# A live job overlapping the hour that no later selection of that job's hour (visible at the cutoff) has cleared.
_JOBS = text(
    "SELECT j.status FROM recompute_job j WHERE j.tenant_id = :t AND j.site_id = :s AND j.domain = :jd "
    "AND j.window_start < :hi AND j.window_end > :lo AND j.status IN ('PENDING', 'LEASED', 'FAILED') "
    "AND j.available_at <= :k AND NOT EXISTS (SELECT 1 FROM mini_depth_selection x WHERE x.tenant_id = j.tenant_id "
    "AND x.site_id = j.site_id AND x.domain = :d AND x.window_start = j.window_start "
    "AND x.window_end = j.window_end AND x.selected_at > j.available_at AND x.selected_at <= :k)")


def _cutoff_sha(c: Connection, tenant_id: UUID, site_id: UUID, window: rules.Window, known: datetime,
                stored_cutoff: datetime) -> str | None:
    """The digest of the inputs visible at the read cutoff, with the selected revision's own cutoff in its basis,
    so it equals the stored digest iff no accepted row, Foundation or binding publication changed (q6 ruling 5).
    None when the configuration no longer yields one covering basis (a changed configuration)."""
    try:
        inputs = load_hour_inputs(c, tenant_id, site_id, window, known)
    except MiniInputsRefused:
        return None
    return replace(inputs, knowledge_cutoff=stored_cutoff).input_sha256


def _hour_ids(c: Connection, tenant_id: UUID, site_id: UUID, window: rules.Window, known: datetime) -> list[str]:
    raw = read_hour_rows(c, tenant_id, site_id, window.start, window.end, known, role_set=ROLE_SET_MINIGRID_4,
                         roles=QUERY_ROLES, supply_role=rules.SITE_SUPPLY)
    return sorted({str(r[0]).lower() for r in (*raw.accepted, *raw.prior_supply)})


def _gap(lo: datetime, hi: datetime) -> dict[str, str | None]:
    return {"from": iso(lo), "to": iso(hi)}


def _empty_coverage(window: rules.Window) -> dict[str, Any]:
    return {"required_seconds": 3600, "observed_seconds": 0, "source_count": 0,
            "gaps": [_gap(window.start, window.end)]}


def _limitations(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, set[str]] = {}
    for item in items:
        merged.setdefault(item["code"], set()).update(item.get("evidence_ids") or ())
    return [{"code": code, "evidence_ids": sorted(ids)}
            for code, ids in sorted(merged.items(), key=lambda kv: _LIMIT_ORDER.get(kv[0], len(_LIMIT_ORDER)))]


def _bound(value: Any) -> rules.Bound | None:
    return None if value is None else rules.Bound(Decimal(str(value["low"])), Decimal(str(value["high"])))


def _number(value: Decimal | None) -> float | int | None:
    if value is None:
        return None
    return int(value) if value == value.to_integral_value() else float(value)


def _bound_json(value: rules.Bound | None) -> dict[str, Any] | None:
    return None if value is None else {"low": _number(value.low), "high": _number(value.high)}


def _stored_hour(day: date, window: rules.Window, result: dict[str, Any]) -> rules.RenewableHour:
    """The selected stored hour as the pure rule type `summarize_renewable` takes (no recomputation)."""
    hour = result["hour"]
    used = hour.get("used_kw")
    return rules.RenewableHour(
        day=day, window=window, capability_kw=_bound(hour.get("capability_kw")),
        used_kw=None if used is None else Decimal(str(used)), headroom_kw=_bound(hour.get("headroom_kw")),
        opportunity_kwh=None, constraints=(), decision=hour["decision"],
        coverage=rules.Coverage(3600, 0, 0, ()), evidence_ids=())


def compose_renewable(hours: Sequence[tuple[date, rules.Window, dict[str, Any] | None]]) -> dict[str, Any]:
    """q6 ruling 1: the page `status` and five `cards` over the requested days' selected noon hours only."""
    selected = [_stored_hour(d, w, r) for d, w, r in hours if r is not None]
    cards = rules.summarize_renewable(selected, requested_days=len(hours))
    decisions = [h.decision for h in selected]
    if len(selected) < len(hours):
        status = "UNKNOWN"
    elif any(d in ("LIMITED", "CONFLICT") for d in decisions):
        status = "LIMITED"
    elif all(d in ("ELIGIBLE", "EXCLUDED") for d in decisions):
        status = "SUPPORTED"
    else:
        status = "UNKNOWN"
    return {"status": status, "cards": {
        "capability_kw": _bound_json(cards.capability_kw), "used_kw": _bound_json(cards.used_kw),
        "headroom_kw": _bound_json(cards.headroom_kw), "eligible_days": cards.eligible_days,
        "assessed_days": cards.assessed_days}}


def _renewable_coverage(hours: Sequence[_Hour]) -> dict[str, Any]:
    observed, sources, gaps = 0, 0, []
    for h in hours:
        cov = h.head.result.get("coverage") if h.head else None
        cov = cov or _empty_coverage(h.window)
        observed += int(cov["observed_seconds"])
        sources = max(sources, int(cov["source_count"]))
        gaps.extend(cov["gaps"])
    return {"required_seconds": 3600 * len(hours), "observed_seconds": observed, "source_count": sources,
            "gaps": sorted(gaps, key=lambda g: (g["from"], g["to"]))}


def site_path(code: str) -> str:
    """The URL-encoded `/sites/{code}` prefix (q9 ruling 8)."""
    return f"/sites/{quote(code, safe='')}"


def _dispatch_link(code: str, hours: Sequence[_Hour]) -> str | None:
    """Closure 1 Q5, q9 ruling 8: `PerformanceDispatch` reads `?day=YYYY-MM-DD`; a link only when one exact UTC day
    contains every requested hour, otherwise null."""
    days = {h.window.start.astimezone(timezone.utc).date() for h in hours}
    ends = {(h.window.end - timedelta(microseconds=1)).astimezone(timezone.utc).date() for h in hours}
    if len(days | ends) != 1:
        return None
    return f"{site_path(code)}/performance/dispatch?day={next(iter(days)).isoformat()}"


def links(code: str, hours: Sequence[_Hour]) -> dict[str, str | None]:
    """q9 ruling 8: `actions` is the merged estate root, not a Site-filtered Action or verification link."""
    return {"dispatch": _dispatch_link(code, hours), "evidence": f"{site_path(code)}/evidence",
            "financials": None, "actions": "/actions"}


def aggregate_state(states: Iterable[str]) -> str:
    """q9 ruling 5: `UNKNOWN > PENDING_RECOMPUTE > STALE_SOURCE > HISTORICAL > CURRENT` across requested hours."""
    seen = set(states)
    return next(x for x in CURRENTNESS_ORDER if x in seen)


def aggregate_job(job_states: Iterable[str]) -> str:
    """q9 ruling 5: `FAILED > LEASED > PENDING > NONE > SETTLED` (NONE: unselected hour without a visible job)."""
    seen = set(job_states)
    return next(x for x in JOB_ORDER if x in seen)


def limit_claim(status: str, selected_class: str | None, state: str,
                limitations: Sequence[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """q9 ruling 4: provenance and currentness may only further limit a positive claim. HISTORICAL alone does not
    downgrade; an absent selection stays UNKNOWN. Limitations are merged by code and ordered by `LIMITATION_ORDER`."""
    items = list(limitations)
    if selected_class in ("UNKNOWN", "MIXED"):
        items.append({"code": f"SOURCE_CLASS_{selected_class}", "evidence_ids": []})
    if state == "PENDING_RECOMPUTE":
        items.append({"code": "RECOMPUTE_PENDING", "evidence_ids": []})
    if state == "STALE_SOURCE":
        items.append({"code": "SOURCE_STALE", "evidence_ids": []})
    if status == "SUPPORTED" and (selected_class in ("UNKNOWN", "MIXED")
                                  or state in ("PENDING_RECOMPUTE", "STALE_SOURCE")):
        status = "LIMITED"
    return status, _limitations(items)


def renewable_envelope(hours: Sequence[_Hour]) -> dict[str, Any]:
    """q9 ruling 6: status/cards over selected noon hours, their stored rows sorted `(day, from)`, row constraints as
    limitations citing that row's IDs, and coverage over every requested day (`source_count` is the maximum per
    assessed hour, not a distinct-source count across days)."""
    composed = compose_renewable([(h.day, h.window, h.head.result if h.head else None) for h in hours])
    rows = sorted((row for h in hours if h.head for row in h.head.result["rows"]),
                  key=lambda r: (r["day"], r["from"]))
    limitations = [{"code": code, "evidence_ids": row["evidence_ids"]}
                   for row in rows for code in row["constraints"]]
    return {"status": composed["status"], "cards": composed["cards"], "rows": rows, "limitations": limitations,
            "coverage": _renewable_coverage(hours), "basis": None}


def check_lineage(domain: str, window: rules.Window, row: Sequence[Any]) -> None:
    """q9 ruling 10: the selected revision's domain and hour equal its selection's, and its sorted
    `basis.accepted_evidence_ids` equal the exact `mini_depth_revision_evidence` set; otherwise 503 (no ID leaks)."""
    result = row[4]
    if (row[5], row[6], row[7]) != (domain, window.start, window.end) or not isinstance(result, dict) \
            or not isinstance(result.get("basis"), dict) \
            or sorted(str(i) for i in result["basis"].get("accepted_evidence_ids") or []) != list(row[8]):
        raise MiniReadUnavailable("A selected mini-depth revision's lineage or basis is broken.")


class MiniDepthRead:
    """The read-only mini-depth reader (closure 1 Q6-Q8, Q14, Q15, Q18, Q31; q6 rulings 1 and 5)."""

    def __init__(self, engine: Engine, link_rows: LinkRowsOn, *,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._engine = engine
        self._link_rows = link_rows
        self.test_read_clock_override = test_read_clock_override

    @classmethod
    def from_url(cls, database_url: str, link_rows: LinkRowsOn, **options: Any) -> "MiniDepthRead":
        return cls(create_engine(database_url, pool_pre_ping=True), link_rows, **options)

    def dispose(self) -> None:
        self._engine.dispose()

    def read(self, *, tenant_id: UUID, site_id: UUID, site_code: str, domain: str, lo: datetime, hi: datetime,
             known_at: datetime | None) -> dict[str, Any]:
        if domain not in DOMAINS:
            raise ValueError(f"Unknown mini-depth domain {domain!r}")
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    read_time = c.execute(text("SELECT clock_timestamp()")).scalar_one()
                    if self.test_read_clock_override is not None:
                        read_time = self.test_read_clock_override()
                    return self._read(c, tenant_id, site_id, site_code, domain, lo, hi, known_at, read_time)
        except (MiniReadRefused, MiniReadUnavailable):
            raise
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise MiniReadUnavailable(f"The mini-depth read failed: {error.__class__.__name__}") from error

    def _read(self, c: Connection, t: UUID, s: UUID, code: str, domain: str, lo: datetime, hi: datetime,
              explicit: datetime | None, read_time: datetime) -> dict[str, Any]:
        if explicit is not None and explicit > read_time:  # Q31: a future cutoff; equality is current-eligible
            raise MiniReadRefused("INVALID_KNOWN_AT")
        known = read_time if explicit is None else explicit
        historical = explicit is not None and explicit < read_time
        tz_name = c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"),
                            {"t": t, "s": s}).scalar_one_or_none()
        windows = hour_windows(domain, lo, hi, tz_name)
        hours = [self._hour(c, t, s, domain, d, w, known, historical) for d, w in windows]

        live = [h for h in hours if h.pending_ids is not None]
        blocks = mini_blocks(
            c, self._link_rows, t, s, selected_revision_ids=[h.head.revision_id for h in hours if h.head],
            selected_evidence_ids=[i for h in hours if h.head for i in h.head.evidence_ids],
            pending_evidence_ids=None if not live else [i for h in live for i in (h.pending_ids or ())])
        state = aggregate_state(h.state for h in hours)
        job_state = aggregate_job(h.job_state for h in hours)

        if domain == "renewable":
            env = renewable_envelope(hours)
            status, cards, rows, coverage, basis = (env[k] for k in ("status", "cards", "rows", "coverage", "basis"))
            limitations = env["limitations"]
        else:
            head = hours[0].head
            stored = head.result if head else {}
            status = stored.get("status", "UNKNOWN") if head else "UNKNOWN"
            cards = dict(stored.get("cards") or NULL_CARDS[domain])
            rows = list(stored.get("rows") or [])
            limitations = list(stored.get("limitations") or [])
            coverage = stored.get("coverage") or _empty_coverage(hours[0].window)
            basis = stored.get("basis")

        selected_class = (blocks["selected_source_provenance"] or {}).get("classification")
        status, limitations = limit_claim(status, selected_class, state, limitations)
        return {
            "schema_version": SCHEMA_VERSION, "domain": domain,
            "site": {"id": str(s), "code": code, "timezone": tz_name},
            "window": {"from": iso(lo), "to": iso(hi), "known_at": iso(known), "bounds": "[from,to)"},
            "currentness": {"state": state, "job_state": job_state, "windows": [{
                "local_day": h.day.isoformat(), "window_start": iso(h.window.start), "window_end": iso(h.window.end),
                "selection_id": h.head.seq if h.head else None,
                "assessment_revision_id": str(h.head.revision_id) if h.head else None,
                "input_sha256": h.head.input_sha256 if h.head else None,
                "committed_watermark": h.head.result["basis"].get("committed_watermark") if h.head else None,
                "state": h.state, "job_state": h.job_state} for h in hours]},
            **blocks,
            "status": status, "coverage": coverage, "cards": cards, "rows": rows,
            "limitations": limitations, "basis": basis, "links": links(code, hours),
        }

    def _hour(self, c: Connection, t: UUID, s: UUID, domain: str, day: date, window: rules.Window, known: datetime,
              historical: bool) -> _Hour:
        p = {"t": t, "s": s, "d": domain, "jd": JOB_DOMAIN[domain], "lo": window.start, "hi": window.end, "k": known}
        row = c.execute(_HEAD, p).one_or_none()
        head = None
        if row is not None:
            check_lineage(domain, window, row)
            result = row[4]
            head = _Head(int(row[0]), row[1], row[2], row[3], result, tuple(row[8]))
        statuses = set(c.execute(_JOBS, p).scalars())
        job_state = next((x for x in ("FAILED", "LEASED", "PENDING") if x in statuses),
                         "SETTLED" if head else "NONE")
        pending_ids = tuple(_hour_ids(c, t, s, window, known)) if statuses else None
        if head is None:
            state = "UNKNOWN"
        elif statuses:
            state = "PENDING_RECOMPUTE"
        elif _cutoff_sha(c, t, s, window, known, head.knowledge_cutoff) != head.input_sha256:
            state = "STALE_SOURCE"
        else:
            state = "HISTORICAL" if historical else "CURRENT"
        return _Hour(day, window, head, job_state, state, pending_ids)


__all__ = ["MESSAGES", "MiniDepthRead", "MiniReadRefused", "MiniReadUnavailable", "aggregate_job", "aggregate_state",
           "check_lineage", "compose_renewable", "hour_windows", "iso", "limit_claim", "links", "renewable_envelope",
           "site_path"]
