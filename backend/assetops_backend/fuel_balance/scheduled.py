"""OWN-G2 (build sheet OWN-GAPS §2.4, rulings R1 and R2-G2): which diesel nights the schedule tick checks.

The `fuel_night` stage (`scheduling/stages.py`) calls `run_site` once per Site per tick, at DB time. One read
(`schedule_inputs`) gives the Site's tank readings bucketed by night, its fuel records and each night's latest window;
`due_nights` (pure) picks the nights; each is assessed (`FuelBalanceService.assess_night`) and raised
(`FuelFindingService.raise_night`) in its own transactions. No state is kept: the next tick recomputes the due set.

- A night is **ready** when its window closed (`end + EDGE <= known_at`, the service's own rule) and its tank
  `fuel_level` readings have been quiet for `QUIET` (latest `decided_at <= known_at - QUIET`). A night with no tank
  readings is never due, so Kobo (a tank with no `fuel_level`) gets no row.
- **Base set:** every ready night of the last `BASE_NIGHTS` closed nights `[L - 6, L]`.
- **Record set:** an older ready night touched by a fuel record recorded after its latest window (or with no window),
  within `RECORD_LOOKBACK`.
- **Left-record set (D-R3.8):** an older ready night whose latest window cites a fuel record that has since been
  corrected or no longer counts for this tank.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Callable
from uuid import UUID

from assetops_backend.fuel_balance import rules
from assetops_backend.fuel_balance.model import (
    ASSETS_UNSUPPORTED, CLOCK_BACKWARDS, WINDOW_OPEN, DuePlan, FuelBalanceRefused, ScheduleInputs)
from assetops_backend.fuel_balance.service import FuelBalanceService

BASE_NIGHTS = 7
RECORD_LOOKBACK = timedelta(days=31)  # the work backdate limit (`work/model.py` BACKDATE_LIMIT) plus one day
QUIET = timedelta(minutes=5)
EDGE = timedelta(minutes=rules.EDGE_SEARCH_MIN)

_ANCHOR = date(2000, 1, 3)  # any date: `time` arithmetic goes through `datetime.combine`


def bucket_bounds() -> tuple[time, time]:
    """The local read range of a night, `[NIGHT_START - EDGE, NIGHT_END + EDGE]` (17:30 and 12:30 today; closed: the assessment reads both edges), from the
    rule's own constants (R1 §2.4: one source for the night window). Bound to the `schedule_inputs` SQL."""
    start = (datetime.combine(_ANCHOR, rules.NIGHT_START) - EDGE).time()
    end = (datetime.combine(_ANCHOR, rules.NIGHT_END) + EDGE).time()
    return start, end


def night_of(local: datetime) -> date | None:
    """The night a Site-local instant buckets to; mirrors the `schedule_inputs` SQL `CASE` exactly."""
    start, end = bucket_bounds()
    if local.time() >= start:
        return local.date()
    if local.time() <= end:
        return local.date() - timedelta(days=1)
    return None


def _closed(night: date, tz: str | None, known_at: datetime) -> bool:
    return rules.night_window(night, tz)[1] + EDGE <= known_at


def latest_closed_night(tz: str | None, known_at: datetime) -> date:
    """`L`: the latest night whose window end + EDGE is at or before `known_at`."""
    from zoneinfo import ZoneInfo

    night = known_at.astimezone(ZoneInfo(str(tz))).date()
    while not _closed(night, tz, known_at):
        night -= timedelta(days=1)
    return night


def _night_holding(at: datetime, tz: str | None) -> date | None:
    from zoneinfo import ZoneInfo

    local = at.astimezone(ZoneInfo(str(tz))).date()
    for night in (local - timedelta(days=1), local):
        start, end = rules.night_window(night, tz)
        if start <= at < end:
            return night
    return None


def due_nights(inputs: ScheduleInputs) -> DuePlan:
    """§2.4 steps 1-5 (pure)."""
    if inputs.tank_asset_id is None:
        return DuePlan(False, ())
    tz, known_at = inputs.timezone, inputs.known_at
    last = latest_closed_night(tz, known_at)
    first_base = last - timedelta(days=BASE_NIGHTS - 1)

    def ready(night: date) -> bool:
        seen = inputs.reading_nights.get(night)
        return seen is not None and seen <= known_at - QUIET and night <= last

    due = {night for night in inputs.reading_nights if first_base <= night <= last and ready(night)}
    for occurred_at, recorded_at in inputs.records:
        night = _night_holding(occurred_at, tz)
        if night is None or night >= first_base or not ready(night):
            continue
        held = inputs.latest.get(night)
        if held is None or recorded_at > held:
            due.add(night)
    # 4b (D-R3.8): an older ready night whose stored records changed since its latest window: a stored root whose
    # current head differs, or that is no longer a fuel record of this tank occurring inside the record read
    # (corrected to another time, tank or kind). Only nights whose whole window lies inside the record read are
    # compared; for an earlier night a stored record could be missing only because the read starts after it, which
    # would make the night due on every tick without changing its result.
    read_from = known_at - RECORD_LOOKBACK
    for night, held_ids in inputs.window_records.items():
        if night >= first_base or not ready(night) or rules.night_window(night, tz)[0] < read_from:
            continue
        if any(inputs.record_heads.get(root) != head for root, head in held_ids):
            due.add(night)
    return DuePlan(True, tuple(sorted(due)))


def run_site(store: Any, findings: Any, tenant_id: UUID, site_id: UUID, limit: int,
             deadline: Callable[[], bool] | None) -> dict[str, Any]:
    """§2.4 `run_site` (R2-G2 Q4, Q11): assess and raise the due nights, at most `limit`, before `deadline`."""
    plan = due_nights(store.schedule_inputs(tenant_id, site_id, RECORD_LOOKBACK))
    if not plan.eligible:
        return {"code": "OK", "eligible": False, "processed": 0, "deferred": 0}
    service = FuelBalanceService(store)
    nights: list[dict[str, Any]] = []
    appended = reused = 0
    raised: dict[str, int] = {}
    eligible = True
    refused_nights: list[tuple[date, FuelBalanceRefused]] = []
    for night in plan.nights:
        if len(nights) >= limit or (deadline is not None and deadline()):
            break
        try:
            result = service.assess_night(tenant_id, site_id, night)
        except FuelBalanceRefused as refused:
            if refused.code == WINDOW_OPEN:
                nights.append({"night_date": night.isoformat(), "assess": "OPEN", "revision": None, "state": None,
                               "raise": None})
                continue
            if refused.code == ASSETS_UNSUPPORTED:
                eligible = False
                break
            if refused.code == CLOCK_BACKWARDS:  # D-R3.10: this night only; later nights still run
                nights.append({"night_date": night.isoformat(), "assess": "REFUSED", "revision": None,
                               "state": None, "raise": None})
                refused_nights.append((night, refused))
                continue
            raise
        r = findings.raise_night(tenant_id, site_id, night)
        appended += int(result.appended)
        reused += int(not result.appended)
        raised[r.status] = raised.get(r.status, 0) + 1
        nights.append({"night_date": night.isoformat(), "assess": "APPENDED" if result.appended else "REUSED",
                       "revision": result.window.revision, "state": result.window.state, "raise": r.status})
    if refused_nights:
        raise FuelBalanceRefused(CLOCK_BACKWARDS, f"{len(refused_nights)} night(s) refused "
                                 f"({', '.join(d.isoformat() for d, _ in refused_nights)}); first: "
                                 f"{refused_nights[0][1].detail}")
    return {"code": "OK", "eligible": eligible, "processed": len(nights), "deferred": len(plan.nights) - len(nights),
            "appended": appended, "reused": reused, "raised": raised, "nights": nights}


