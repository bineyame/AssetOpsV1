"""W4-02 unit 5: the historical mini-depth reads (`D-2026-10-20-w4-02-buildspec`).

One read-only REPEATABLE READ transaction whose first statement captures `clock_timestamp()` (closure 4 N6; a
constructor-only `test_read_clock_override` replaces it in tests). Inside it:

- the window is validated against the pinned `site.timezone` (closure 1 Q4/Q5/Q33, S8): service, fuel and backup
  take exactly one Site-local clock hour; renewable takes 1-5 consecutive complete Site-local days, each composed
  from its individually selected local hours (CH-9: its measured daylight and missing hours, `store.daylight_hours`;
  a nonexistent local hour refuses `INVALID_WINDOW`);
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

import json
import logging
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import quote
from uuid import UUID

from assetops_backend import read_scope
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_backend.financials import fuel_cost
from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.inputs import (
    QUERY_ROLES,
    MiniInputsRefused,
    load_hour_inputs,
    local_hour,
    zone,
)
from assetops_backend.mini_depth.provenance import LinkRowsOn, mini_blocks
from assetops_backend.mini_depth.store import (
    _ACCEPTED, DOMAINS, JOB_DOMAIN, NO_PV_BINDING, DaylightHours, daylight_hours, read_hour_rows,
)
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4

HOUR = timedelta(hours=1)
SUPPLY_USE, PRODUCTIVE = "supply-use", "PRODUCTIVE"  # WALK1-3 §4.2 (sites/models.py STATE_PROPERTY_VALUES)
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
    "renewable": dict.fromkeys(("capability_kw", "used_kw", "headroom_kw", "all_hours_headroom_kw", "eligible_days",
                              "assessed_days")),
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


def productive_loads(content: Mapping[str, Any]) -> list[dict[str, Any]]:
    """K10 v2 (R3t): the LOAD components of one Foundation revision's `content` declared `supply-use = PRODUCTIVE`.
    The one filter shared by `MiniDepthRead.productive_users` (the builder's subject rule) and the chain adapter's
    `declared_none_days`, so "declared absent" and "no subject" cannot drift apart."""
    return [x for x in content.get("components") or () if x.get("component_type") == "LOAD"
            and any(q.get("property_key") == SUPPLY_USE and q.get("unit") == "state"
                    and q.get("value") == PRODUCTIVE for q in x.get("properties") or ())]


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


def hour_windows(domain: str, lo: datetime, hi: datetime, tz_name: str | None,
                 daylight: Callable[[date], DaylightHours] | None = None) -> list[tuple[date, rules.Window]]:
    """The requested `(local_day, hour)` windows, or `INVALID_WINDOW` (Q4/Q5; an unknown zone refuses, S8).

    Renewable (CH-9 §9 R3, CH9-R2 Q2): each day's measured daylight hours and its missing hours from `daylight`
    (`store.daylight_hours` at the read's cutoff), so a missing hour reads as missing; without it, the
    `store.NO_PV_BINDING` hours."""
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
                out = []
                for d in days[:n]:
                    found = daylight(d) if daylight is not None else NO_PV_BINDING
                    out += [(d, local_hour(d, h, tz_name or "")) for h in sorted({*found.hours, *found.missing})]
                return out
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
    job_ids: tuple[str, ...] = ()


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
_JOBS_WHERE = (
    "j.tenant_id = :t AND j.site_id = :s AND j.domain = :jd "
    "AND j.window_start < {hi} AND j.window_end > {lo} AND j.status IN ('PENDING', 'LEASED', 'FAILED') "
    "AND j.available_at <= :k AND NOT EXISTS (SELECT 1 FROM mini_depth_selection x WHERE x.tenant_id = j.tenant_id "
    "AND x.site_id = j.site_id AND x.domain = :d AND x.window_start = j.window_start "
    "AND x.window_end = j.window_end AND x.selected_at > j.available_at AND x.selected_at <= :k)")
_JOBS = text("SELECT j.id, j.status FROM recompute_job j WHERE " + _JOBS_WHERE.format(lo=":lo", hi=":hi"))
# D-ANY.6a: the same `_JOBS` predicate over many hours in one statement (the rows path's live job check at k).
_JOBS_BATCH = text(
    "SELECT w.n, j.id, j.status FROM unnest(CAST(:los AS timestamptz[]), CAST(:his AS timestamptz[])) "
    "WITH ORDINALITY AS w(lo, hi, n) JOIN recompute_job j ON " + _JOBS_WHERE.format(lo="w.lo", hi="w.hi"))
LOG = logging.getLogger("assetops.mini_depth.read")
JOB_FALLBACK_LOG_EVENT = "period_row_job_fallback"
_JOB_FALLBACK_SEEN = [0]


def job_fallback_count() -> int:
    """Hours the rows path served through `_hour` because the live jobs at k differ from the row's (D-ANY.6a)."""
    return _JOB_FALLBACK_SEEN[0]


def _job_state(statuses: set[str], has_head: bool) -> str:
    return next((x for x in ("FAILED", "LEASED", "PENDING") if x in statuses), "SETTLED" if has_head else "NONE")


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
    """q6 ruling 1: the page `status` and five `cards` over the requested days' selected hours only.

    CH-9 (CH9-R2 Q2/Q5): a day may hold several daylight hours; a day with any unselected (missing) hour is a
    missing day, so only complete days feed the cards, and days are counted by their day decision."""
    missing_days = {d for d, _w, r in hours if r is None}
    selected = [_stored_hour(d, w, r) for d, w, r in hours if r is not None and d not in missing_days]
    cards = rules.summarize_renewable(selected, requested_days=len({d for d, _w, _r in hours}))
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
        "headroom_kw": _bound_json(cards.headroom_kw),
        "all_hours_headroom_kw": _bound_json(cards.all_hours_headroom_kw), "eligible_days": cards.eligible_days,
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
                 test_read_clock_override: Callable[[], datetime] | None = None,
                 period_rows: Any = None) -> None:
        self._engine = engine
        self._link_rows = link_rows
        self.test_read_clock_override = test_read_clock_override
        #: ANY-1 AR-2: `(PeriodReader, PeriodReadStore)`; with a kind in `served_kinds()` the board's hours read rows.
        self.period_rows = period_rows

    @classmethod
    def from_url(cls, database_url: str, link_rows: LinkRowsOn, **options: Any) -> "MiniDepthRead":
        return cls(create_engine(database_url, pool_pre_ping=True), link_rows, **options)

    def dispose(self) -> None:
        self._engine.dispose()

    # --- WALK1-3 §4.3: productive users and their measured use (SELECT only, read at request time) ------------

    def _readonly(self, work: Callable[[Connection, datetime], Any], known_at: datetime | None) -> Any:
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    read_time = read_scope.read_instant(c.execute(text("SELECT clock_timestamp()")).scalar_one())
                    if self.test_read_clock_override is not None:
                        read_time = self.test_read_clock_override()
                    if known_at is not None and known_at > read_time:
                        raise MiniReadRefused("INVALID_KNOWN_AT")
                    return work(c, read_time if known_at is None else known_at)
        except (MiniReadRefused, MiniReadUnavailable):
            raise
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise MiniReadUnavailable(f"The productive-use read failed: {error.__class__.__name__}") from error

    def productive_users(self, *, tenant_id: UUID, site_id: UUID, at: datetime,
                         known_at: datetime | None) -> list[dict[str, Any]]:
        """The LOAD components the single Foundation revision in force at `at` (known at the cutoff) declares
        `supply-use = PRODUCTIVE`, as `{"asset_code", "asset_id", "name"}`; an empty list when none is declared.
        No covering revision, or more than one, is unavailable (never "none declared")."""
        def work(c: Connection, known: datetime) -> list[dict[str, Any]]:
            p = {"t": tenant_id, "s": site_id, "k": known, "at": at}
            rows = c.execute(text(
                "SELECT content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                "AND recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k) "
                "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at)"), p).all()
            if len(rows) != 1:
                raise MiniReadUnavailable("No single Foundation revision covers the productive-use instant")
            content = rows[0][0] if isinstance(rows[0][0], dict) else json.loads(rows[0][0])
            users = productive_loads(content)
            ids = dict(c.execute(text("SELECT asset_code, id FROM asset WHERE tenant_id = :t AND site_id = :s"),
                                 p).all())
            return [{"asset_code": x["component_id"], "asset_id": ids.get(x["component_id"]),
                     "name": str(x.get("display_name") or x["component_id"])}
                    for x in sorted(users, key=lambda x: str(x.get("component_id")))]
        return self._readonly(work, known_at)

    def productive_readings(self, *, tenant_id: UUID, site_id: UUID, asset_ids: Sequence[UUID], lo: datetime,
                            hi: datetime, known_at: datetime | None) -> list[dict[str, Any]]:
        """The accepted, cutoff-visible `feeder_demand` interval readings of `asset_ids` touching `[lo, hi)`, as
        `{"evidence_id", "asset_id", "start", "end", "value_kw", "quality"}`; a reading in another unit has no
        value (a gap for `productive_use.productive_energy`, never a zero)."""
        wanted = {str(a) for a in asset_ids if a is not None}

        def work(c: Connection, known: datetime) -> list[dict[str, Any]]:
            if not wanted:
                return []
            rows = c.execute(text(_ACCEPTED), {"t": tenant_id, "s": site_id, "k": known, "lo": lo, "hi": hi,
                                               "roles": [rules.FEEDER_DEMAND]}).all()
            return [{"evidence_id": r[0], "asset_id": r[2], "start": r[4], "end": r[5],
                     "value_kw": r[7] if r[8] == "kW" else None, "quality": r[6]}
                    for r in rows if str(r[2]) in wanted and r[4] is not None and r[5] is not None]
        return self._readonly(work, known_at)

    def read(self, *, tenant_id: UUID, site_id: UUID, site_code: str, domain: str, lo: datetime, hi: datetime,
             known_at: datetime | None) -> dict[str, Any]:
        if domain not in DOMAINS:
            raise ValueError(f"Unknown mini-depth domain {domain!r}")
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    read_time = read_scope.read_instant(c.execute(text("SELECT clock_timestamp()")).scalar_one())
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
        from_rows = self._row_hours(c, t, s, code, domain, lo, hi, tz_name, explicit, known, historical)
        if from_rows is not None:  # ANY-1 AR-2: stored hour facts; no raw reading, no on-read `_cutoff_sha`
            hours, link_rows = from_rows
        else:
            windows = hour_windows(domain, lo, hi, tz_name, lambda d: daylight_hours(c, t, s, d, known))
            hours = [self._hour(c, t, s, domain, d, w, known, historical) for d, w in windows]
            link_rows = self._link_rows
        return self._envelope(c, link_rows, t, s, code, domain, lo, hi, known, tz_name, hours)

    def _envelope(self, c: Connection | None, link_rows: LinkRowsOn, t: UUID, s: UUID, code: str, domain: str,
                  lo: datetime, hi: datetime, known: datetime, tz_name: str | None,
                  hours: Sequence[_Hour]) -> dict[str, Any]:
        """The one envelope composition over the request's hours, from compose (`_hour`) or stored rows alike."""
        live = [h for h in hours if h.pending_ids is not None]
        blocks = mini_blocks(
            c, link_rows, t, s, selected_revision_ids=[h.head.revision_id for h in hours if h.head],
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
            # Final review ruling 2 (M2): Service only; the stored pinned critical series' coverage, else null.
            **({"critical_delivered_coverage": (hours[0].head.result.get("critical_delivered_coverage")
                                                if hours[0].head else None)} if domain == "service" else {}),
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
        jobs = c.execute(_JOBS, p).all()
        statuses = {str(j[1]) for j in jobs}
        job_state = _job_state(statuses, head is not None)
        pending_ids = tuple(_hour_ids(c, t, s, window, known)) if statuses else None
        if head is None:
            state = "UNKNOWN"
        elif statuses:
            state = "PENDING_RECOMPUTE"
        elif _cutoff_sha(c, t, s, window, known, head.knowledge_cutoff) != head.input_sha256:
            state = "STALE_SOURCE"
        else:
            state = "HISTORICAL" if historical else "CURRENT"
        return _Hour(day, window, head, job_state, state, pending_ids, tuple(sorted(str(j[0]) for j in jobs)))

    # --- ANY-1 AR-2: the board's hours from stored read-period rows (`mini_depth/period_rows.py`) ---------------

    def _row_hours(self, c: Connection, t: UUID, s: UUID, code: str, domain: str, lo: datetime, hi: datetime,
                   tz_name: str | None, explicit: datetime | None, known: datetime,
                   historical: bool) -> tuple[list[_Hour], LinkRowsOn] | None:
        """The request's hours from `site_period_read` when its kind is served (`ASSETOPS_PERIOD_READ_KINDS`; empty
        = today's compose) and the request is a stored shape (renewable: 1-5 whole local days; fuel, service and
        backup: the local noon hour the board reads). None = compose. No raw reading and no `_cutoff_sha` here,
        except for an hour whose live jobs at k differ from its row's (D-ANY.6a): that hour alone is `_hour`."""
        from assetops_backend.chain.grading import PENDING
        from assetops_backend.chain.period_read import served_kinds
        from assetops_backend.chain.ports import SiteRef
        from assetops_backend.mini_depth import period_rows as pr

        kind = pr.kind_of(domain)
        if self.period_rows is None or not tz_name or kind not in served_kinds():
            return None
        windows = hour_windows(domain, lo, hi, tz_name)  # the compose's own validation and refusals
        if domain == "renewable":
            days = sorted({d for d, _w in windows})
        else:
            if windows[0][1] != local_hour(windows[0][0], 12, tz_name):
                return None  # only the board's hour is stored for the hourly domains
            days = [windows[0][0]]
        reader, store = self.period_rows
        try:
            result = reader.read(t, [SiteRef(t, s, code, MINIGRID, tz_name)], [kind], days[0], days[-1], explicit)
        except Exception as error:  # the row store failing is a 503, never a guessed empty page
            raise MiniReadUnavailable(f"The mini-depth row read failed: {error.__class__.__name__}") from error
        by_day = {r.row.local_day: r for r in result.rows if r.row.kind == kind and r.row.site_id == s}
        hours: list[_Hour] = []
        stored_links: dict[str, Any] = {}
        for day in days:
            read = by_day.get(day)
            if read is None:  # D-ANY.5 M1: absent renders as compose renders nothing known at k
                found = (pr.absent_renewable_windows(code, tz_name, day) if domain == "renewable"
                         else [(day, windows[0][1])])
                hours += [pr.absent_hour(d, w) for d, w in found]
                continue
            pending = bool(read.pending) or result.day_state(s, day, kind) == PENDING
            for value in read.row.body.get("hours") or ():
                hours.append(pr.hour_from_json(value, historical=historical, pending=pending))
                stored_links.update(value.get("pending_link_rows") or {})
        if domain != "renewable" and [h.window for h in hours] != [windows[0][1]]:
            raise MiniReadUnavailable("A stored mini-depth hour does not match the requested hour.")
        if self._job_fallback(c, t, s, code, domain, hours, known, historical):
            return hours, self._link_rows  # a recompute in flight: link rows read live, as the compose reads them
        revisions = sorted({h.head.revision_id for h in hours if h.head}, key=str)
        if revisions:
            try:
                blocks = store.provenance(t, revisions, pr.BUILDER_VERSION)
            except Exception as error:
                raise MiniReadUnavailable(f"The mini-depth provenance read failed: {error.__class__.__name__}") \
                    from error
            if len(blocks) != len(revisions):
                raise MiniReadUnavailable("A selected mini-depth revision has no stored provenance.")
            for block in blocks.values():
                stored_links.update(block.get("link_rows") or {})
        return hours, pr.StoredLinkRows(stored_links)

    def _job_fallback(self, c: Connection, t: UUID, s: UUID, code: str, domain: str, hours: list[_Hour],
                      known: datetime, historical: bool) -> int:
        """D-ANY.6a: the compose's own `_JOBS` predicate, one statement over the request's hours at k (live and
        historical). An hour whose job set at k (IDs and the job state they give) equals its stored row's renders
        from the row; any other hour is replaced in place by `_hour` (the D-ANY.1 "cannot be proven equal stays on
        the old path" rule), logged `period_row_job_fallback` and counted. Returns the number replaced."""
        if not hours:
            return 0
        p = {"t": t, "s": s, "d": domain, "jd": JOB_DOMAIN[domain], "k": known,
             "los": [h.window.start for h in hours], "his": [h.window.end for h in hours]}
        live: dict[int, list[tuple[str, str]]] = {}
        for n, job_id, status in c.execute(_JOBS_BATCH, p).all():
            live.setdefault(int(n) - 1, []).append((str(job_id), str(status)))
        replaced = []
        for i, h in enumerate(hours):
            jobs = live.get(i, [])
            ids = tuple(sorted(j for j, _ in jobs))
            statuses = {st for _, st in jobs}
            if ids == tuple(h.job_ids) and (not statuses or _job_state(statuses, h.head is not None) == h.job_state):
                continue
            hours[i] = self._hour(c, t, s, domain, h.day, h.window, known, historical)
            replaced.append(h)
        if replaced:
            _JOB_FALLBACK_SEEN[0] += len(replaced)
            LOG.warning(JOB_FALLBACK_LOG_EVENT, extra={
                "event": JOB_FALLBACK_LOG_EVENT, "tenant_id": str(t), "site": code, "domain": domain,
                "count": len(replaced), "first": iso(replaced[0].window.start), "known_at": iso(known)})
        return len(replaced)

    def build_period(self, *, tenant_id: UUID, site_id: UUID, domain: str, local_day: date
                     ) -> tuple[datetime, datetime, list[dict[str, Any]], dict[str, dict[str, Any]]] | None:
        """AR-2 builder: one stored period of a kind at this transaction's clock, through `_hour` (the compose's own
        head, job, `_cutoff_sha` and pending logic). Returns `(start, end, hour facts, {revision_id: link rows})`;
        None when the day has no such period (an unknown zone or a nonexistent local hour)."""
        from assetops_backend.mini_depth import period_rows as pr

        def work(c: Connection, known: datetime) -> Any:
            tz_name = c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"),
                                {"t": tenant_id, "s": site_id}).scalar_one_or_none()
            if not tz_name:
                return None
            try:
                if domain == "renewable":
                    start = _local_midnight(local_day, tz_name)
                    end = _local_midnight(local_day + timedelta(days=1), tz_name)
                    windows = hour_windows(domain, start, end, tz_name,
                                           lambda d: daylight_hours(c, tenant_id, site_id, d, known))
                else:
                    w = local_hour(local_day, 12, tz_name)
                    start, end, windows = w.start, w.end, [(local_day, w)]
            except (MiniReadRefused, MiniInputsRefused):
                return None
            hours = [self._hour(c, tenant_id, site_id, domain, d, w, known, False) for d, w in windows]
            ids = sorted({str(i).lower() for h in hours if h.head for i in h.head.evidence_ids}
                         | {str(i).lower() for h in hours for i in (h.pending_ids or ())})
            grouped = pr.group_link_rows(self._link_rows(c, tenant_id, site_id, ids)) if ids else {}
            facts = [pr.hour_json(h, pending_link_rows=None if h.pending_ids is None else
                                  {i.lower(): grouped[i.lower()] for i in h.pending_ids if i.lower() in grouped})
                     for h in hours]
            provenance = {str(h.head.revision_id): {str(i).lower(): grouped[str(i).lower()]
                                                    for i in h.head.evidence_ids if str(i).lower() in grouped}
                          for h in hours if h.head}
            return start, end, facts, provenance
        return self._readonly(work, None)

    # --- W4-03 closure 4 S9: the one selected-renewable basis reader -------------------------------------------

    def read_selected_renewable_basis(self, c: Connection, *, tenant_id: UUID, site_id: UUID, days: Sequence[date],
                                      known: datetime, historical: bool,
                                      windows: Sequence[tuple[date, rules.Window]] | None = None) -> dict[str, Any]:
        """The selected renewable hour basis of `days` on the caller's connection and cutoff (W4-03 S9).

        Uses this reader's own head, overlapping-job, cutoff-digest and provenance logic (`_hour`, `mini_blocks`),
        never a reimplementation. Per hour: the selected `(selection_seq, mini_revision_id)`, the stored decision and
        one-hour `opportunity_kwh` bound, the revision's input digest and accepted IDs, the hour currentness and live
        job IDs. The three provenance blocks cover the complete hour set. Nothing is written.

        CH-9 (CH9-R2 Q4/Q5): a day's hours are `store.daylight_hours(...).study_hours` at `known` (its measured
        daylight and missing hours), one row each, ordered `(day, start)`. `windows` instead reads exactly the
        named `(day, hour)` windows (a stored pin set: a `mini-opportunity/1` study or a scenario's pinned hours).
        A nonexistent local hour is `INVALID_WINDOW`."""
        tz_name = c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"),
                            {"t": tenant_id, "s": site_id}).scalar_one_or_none()
        if windows is None:
            try:
                windows = [(day, local_hour(day, h, tz_name or ""))
                           for day in days for h in daylight_hours(c, tenant_id, site_id, day, known).study_hours]
            except MiniInputsRefused as error:
                raise MiniReadRefused("INVALID_WINDOW") from error
        hours: list[_Hour] = [self._hour(c, tenant_id, site_id, "renewable", day, window, known, historical)
                              for day, window in sorted(windows, key=lambda w: (w[0], w[1].start))]
        live = [h for h in hours if h.pending_ids is not None]
        blocks = mini_blocks(
            c, self._link_rows, tenant_id, site_id, selected_revision_ids=[h.head.revision_id for h in hours if h.head],
            selected_evidence_ids=[i for h in hours if h.head for i in h.head.evidence_ids],
            pending_evidence_ids=None if not live else [i for h in live for i in (h.pending_ids or ())])
        rows = []
        for h in hours:
            hour = h.head.result.get("hour") or {} if h.head else {}
            # The one stored row of a renewable hour carries its one-hour `opportunity_kwh` bound.
            stored_rows = (h.head.result.get("rows") or []) if h.head else []
            rows.append({
                "local_day": h.day.isoformat(), "window_start": h.window.start, "window_end": h.window.end,
                "selection_seq": h.head.seq if h.head else None,
                "mini_revision_id": str(h.head.revision_id).lower() if h.head else None,
                "decision": hour.get("decision"),
                "opportunity_kwh": stored_rows[0].get("opportunity_kwh") if len(stored_rows) == 1 else None,
                "input_sha256": h.head.input_sha256 if h.head else None,
                "evidence_ids": list(h.head.evidence_ids) if h.head else [],
                "state": h.state, "job_state": h.job_state, "pending_job_ids": list(h.job_ids)})
        return {"timezone": tz_name, "days": rows,
                "currentness": {"state": aggregate_state(h.state for h in hours) if hours else
                                ("HISTORICAL" if historical else "CURRENT"),
                                "job_state": aggregate_job(h.job_state for h in hours) if hours else "NONE"},
                "pending_job_ids": sorted({j for h in hours for j in h.job_ids}),
                "pending_evidence_ids": None if not live else sorted({i for h in live for i in (h.pending_ids or ())}),
                **blocks}

    def provenance_blocks(self, c: Connection, *, tenant_id: UUID, site_id: UUID,
                          selected_revision_ids: Iterable[UUID | str], selected_evidence_ids: Iterable[UUID | str],
                          pending_evidence_ids: Iterable[UUID | str] | None) -> dict[str, Any]:
        """`mini_blocks` with this reader's link-row resolver, for a caller's own exact pinned revision set."""
        return mini_blocks(c, self._link_rows, tenant_id, site_id, selected_revision_ids=selected_revision_ids,
                           selected_evidence_ids=selected_evidence_ids, pending_evidence_ids=pending_evidence_ids)


_RENEWABLE_REVISIONS = text(
    "SELECT r.id::text, r.window_start, r.knowledge_cutoff, COALESCE((SELECT array_agg(v.evidence_id::text "
    "ORDER BY v.evidence_id::text) FROM mini_depth_revision_evidence v WHERE v.tenant_id = r.tenant_id "
    "AND v.site_id = r.site_id AND v.revision_id = r.id), '{}') FROM mini_depth_revision r "
    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.domain = 'renewable' AND r.id = ANY(CAST(:ids AS uuid[]))")


def renewable_revisions(c: Connection, tenant_id: UUID, site_id: UUID,
                        revision_ids: Iterable[UUID | str]) -> dict[str, dict[str, Any]]:
    """W4-03: the named revisions that are renewable revisions of this tenant/Site, keyed by lowercase ID, with their
    hour start, knowledge cutoff and exact accepted-ID set. A foreign, other-domain or unknown ID is absent."""
    ids = sorted({str(i).lower() for i in revision_ids})
    if not ids:
        return {}
    rows = c.execute(_RENEWABLE_REVISIONS, {"t": tenant_id, "s": site_id, "ids": ids}).all()
    return {str(r[0]).lower(): {"window_start": r[1], "knowledge_cutoff": r[2],
                                "evidence_ids": [str(i).lower() for i in r[3]]} for r in rows}


__all__ = ["MESSAGES", "MiniDepthRead", "MiniReadRefused", "MiniReadUnavailable", "aggregate_job", "aggregate_state",
           "check_lineage", "compose_renewable", "hour_windows", "iso", "limit_claim", "links", "renewable_envelope",
           "renewable_revisions", "site_path"]
