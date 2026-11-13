"""ANY-2 AR-3: the Portfolio's mini-grid dispatch days served from stored read-period rows (architect answer
2026-11-10 §4 AR-3; D-ANY.1-6; sequence revision 4: on DATA-12's graded local days, not on-read `dispatch_days`).

Kind `dispatch.day` (`site_period_read`, migration 0059), grain `s3_day`: one row per (Site, UTC day D) whose period
is the S3 dispatch window of D (`dispatch_read.day_window`) and whose `local_day` column is D. That is the key
DATA-12's coverage rule already matches on: "a Site-local day D with readings is checked only if the dispatch day
with D's date has an available selection" (`estate/coverage.py`, D-E5.42). The body is the exact day dict
`PostgresAssessmentStore.select_dispatch_days_on` builds for D on a live read, minus its request-time `known_at`,
type-tagged so the read hands `coverage._mini_grid_basis` the same Python values (dates, instants, UUIDs) today's
compose does. It is built when the inputs change (event register -> `snapshot_dirty` -> builder in the tick, or the
backfill CLI), never on read.

Read rules (D-ANY.5):
- the latest revision with `computed_at <= k` for an explicit cutoff (historical or a continuation page), the latest
  revision live;
- a day PENDING at k (an unconsumed input event, a live dirty mark, an older builder version) keeps its stored facts
  and gains one outstanding job, so the Site reads PENDING_RECOMPUTE and its job state PENDING (today's compose sees
  the recompute job the input created);
- a day with no row at k (live or explicit) is marked `ABSENT_MARK`; `coverage.dispatch_days` fills it from today's
  compose, once per contiguous run of absent days at the same k; each run is logged/counted `period_row_absent` here.
  Ruled D-ANY.10 (overrides D-ANY.5's no-fallback rule for this kind only): rows built later than their input would
  otherwise read as "nothing known" at a k between the input and the build.

`ASSETOPS_PERIOD_READ_KINDS` without `dispatch.day` (the D-ANY.6 kill switch) leaves coverage on today's compose.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID

from assetops_backend.analytics.dispatch_read import UNASSESSED, day_window

from .period_read import PeriodFragment, PeriodReader, record_absent_run, served_kinds
from .ports import SiteRef

KIND = "dispatch.day"
BUILDER_VERSION = "dispatch-day-rows-1"
#: The status code of a row whose day is not reconstructable (`available` false: no S3 status).
UNAVAILABLE_STATE = "UNAVAILABLE"
#: The synthetic outstanding job a day PENDING at k carries (never stored).
PENDING_JOB = {"id": None, "status": "PENDING", "source": "period_read"}
ABSENT_REASON = "NOT_BUILT: no stored dispatch.day row at the cutoff"
#: D-ANY.10: the key on a day the provider found no row for; `coverage.dispatch_days` replaces it with today's compose
#: (and strips the key from the `absent_day` it falls back to when compose returns no such day).
ABSENT_MARK = "_absent_row"
_TAGS = {"$dt": datetime.fromisoformat, "$date": date.fromisoformat, "$uuid": UUID, "$dec": Decimal}


class DispatchRowsUnavailable(RuntimeError):
    """The stored dispatch day rows cannot be read for this Site (no Site row): the read fails, never guesses."""


# --- the body codec ---------------------------------------------------------------------------------------------


def encode(value: Any) -> Any:
    """A JSON value that `decode` turns back into the same Python value (instants, dates, UUIDs and Decimals are
    tagged; tuples and read-only mappings become lists and objects)."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise TypeError("a stored instant is timezone-aware")
        return {"$dt": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, UUID):
        return {"$uuid": str(value)}
    if isinstance(value, Decimal):
        return {"$dec": str(value)}
    if isinstance(value, Mapping):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"{type(value).__name__} is not a stored dispatch day value")


def decode(value: Any) -> Any:
    if isinstance(value, dict):
        if len(value) == 1:
            (tag, raw), = value.items()
            if tag in _TAGS:
                return _TAGS[tag](raw)
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def body_of(day: Mapping[str, Any]) -> dict[str, Any]:
    """The stored body of one composed dispatch day: everything but the request's `known_at`."""
    return encode({k: v for k, v in day.items() if k != "known_at"})


def state_of(day: Mapping[str, Any]) -> str:
    if not day.get("available"):
        return UNAVAILABLE_STATE
    return str(day.get("status") or UNASSESSED)


def day_from_body(body: Mapping[str, Any], known_at: datetime, pending: bool) -> dict[str, Any]:
    """A stored day as `select_dispatch_days_on` returns it at the request's `known_at`."""
    day = decode(dict(body))
    day["known_at"] = known_at
    if pending:
        day["jobs"] = [*(day.get("jobs") or ()), dict(PENDING_JOB)]
    return day


def absent_day(day: date, known_at: datetime, pending: bool = False) -> dict[str, Any]:
    """The fallback day for a requested day with no row at k (marked by the provider): `estate.coverage` composes such
    runs (D-ANY.10) and uses this day only when compose returns none for it (nothing stored by k: no selection, run
    or job; D-ANY.5 M1)."""
    window = day_window(day)
    return {"day": day, "window_start": window.start, "window_end": window.end, "known_at": known_at,
            "available": True, "unavailable_reasons": [], "status": UNASSESSED, "status_reasons": [ABSENT_REASON],
            "selection": None, "run_id": None, "assessment_revision_ids": [], "window_assessment_revision_id": None,
            "accepted_reading_count": None, "input_sha256": None, "configuration_sha256": None,
            "accepted_watermarks": None, "jobs": [dict(PENDING_JOB)] if pending else []}


def dispatch_spans(from_: datetime, to: datetime) -> list[date]:
    """The UTC days `select_dispatch_days_on` returns for `[from_, to)` (each day window intersecting it), in order."""
    if from_ >= to:
        return []
    out: list[date] = []
    day = from_.astimezone(timezone.utc).date()
    while (window := day_window(day)).start < to:
        if window.end > from_:
            out.append(day)
        day += timedelta(days=1)
    return out


# --- the builder ------------------------------------------------------------------------------------------------


class DispatchDayKindBuilder:
    """`chain.period_read.KindBuilder` for `dispatch.day`: the builder's `local_day` is the UTC day D of the S3
    window (the register resolves this `s3_day` kind's events to UTC days, `chain/events.py`)."""

    kind = KIND
    builder_version = BUILDER_VERSION

    def __init__(self, day_now: Callable[[UUID, UUID, date], Mapping[str, Any] | None]) -> None:
        self._day_now = day_now

    def fragments(self, ctx: Any, site: Any) -> Sequence[PeriodFragment]:
        day = self._day_now(ctx.tenant_id, site.site_id, ctx.local_day)
        if day is None:
            return []
        window = day_window(ctx.local_day)
        body = body_of(day)
        return [PeriodFragment(window.start, window.end, state_of(day), body, inputs=body)]


# --- the serve-path read ----------------------------------------------------------------------------------------


class DispatchDayRows:
    """`coverage.dispatch_rows_provider`: `(t, s, from_, to, k, explicit) -> [day] | None`. None when the kind is
    not served (`ASSETOPS_PERIOD_READ_KINDS`), so coverage keeps today's compose; otherwise ONE period read (rows,
    then PENDING-at-k) for the Site's UTC days of `[from_, to)`."""

    def __init__(self, reader: PeriodReader, site_ref: Callable[[UUID, UUID], SiteRef | None]) -> None:
        self._reader = reader
        self._site_ref = site_ref

    def __call__(self, tenant_id: UUID, site_id: UUID, from_: datetime, to: datetime, known_at: datetime,
                 explicit: bool) -> list[dict[str, Any]] | None:
        if KIND not in served_kinds():
            return None
        days = dispatch_spans(from_, to)
        if not days:
            return []
        site = self._site_ref(tenant_id, site_id)
        if site is None:
            raise DispatchRowsUnavailable(f"no Site {site_id} for its stored dispatch days")
        result = self._reader.read(tenant_id, [site], [KIND], days[0], days[-1], known_at if explicit else None,
                                   log_absent=False)
        sid = str(site.site_id).lower()
        stored = {r.row.local_day: r for r in result.rows if str(r.row.site_id).lower() == sid and r.row.kind == KIND}
        out = []
        for d in days:
            pending = result.is_pending(site.site_id, d, KIND)
            r = stored.get(d)
            if r is None:  # D-ANY.10: marked, not rendered; `coverage.dispatch_days` composes each run
                out.append({**absent_day(d, known_at, pending), ABSENT_MARK: True})
            else:
                out.append(day_from_body(r.row.body, known_at, pending or bool(r.pending)))
        run: list[date] = []
        for day in [*(x["day"] for x in out if x.get(ABSENT_MARK)), None]:  # one log + count per contiguous run
            if run and (day is None or day != run[-1] + timedelta(days=1)):
                record_absent_run(tenant_id, KIND, site.site_id, run)
                run = []
            if day is not None:
                run.append(day)
        return out


__all__ = ["ABSENT_MARK", "ABSENT_REASON", "BUILDER_VERSION", "DispatchDayKindBuilder", "DispatchDayRows", "DispatchRowsUnavailable",
           "KIND", "PENDING_JOB", "UNAVAILABLE_STATE", "absent_day", "body_of", "day_from_body", "decode",
           "dispatch_spans", "encode", "state_of"]
