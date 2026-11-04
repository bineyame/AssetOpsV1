"""W4-03 unit 4: five-day opportunity study identity (`.agent/W4-03-build-spec.md` closure 2 Q4, closure 4 S5/S6,
u3 "Unit 4 dry-read").

A study is the five contiguous Site-local days ending on a day with a selected renewable hour. Its job window runs
from the first day's Site-local midnight to the midnight after the last day, both as UTC. Its physical identity is the S5
`input_sha256`: the canonical hash of each day's selected W4-02 revision ID, input digest, decision and accepted-ID
set (null/empty for a missing day). Selection seq/time and job ID are excluded, so a same-revision reselection hashes
identically and enqueues nothing.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import text

from assetops_backend.analytics.assessment_ports import Window
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.mini_decisions.scenario_rules import decimal_text, physical_range
from assetops_backend.mini_decisions.store import OPPORTUNITY_MODEL_VERSION
from assetops_backend.mini_depth.inputs import local_hour, zone
from assetops_backend.mini_depth.read import iso
from assetops_backend.mini_depth.rules import RENEWABLE_CONSTRAINTS, Bound, headroom_on_every_eligible_day

STUDY_DAYS = 5


@dataclass(frozen=True)
class DayHead:
    """One study hour's selected renewable head, or a missing hour (every selection field None)."""
    local_day: date
    window: Window
    selection_seq: int | None = None
    selection_at: datetime | None = None
    mini_revision_id: str | None = None
    input_sha256: str | None = None
    decision: str | None = None
    evidence_ids: tuple[str, ...] = ()
    # Integrity inputs of a present head (never hashed): selection window end, revision window, stored result.
    selection_end: datetime | None = field(default=None, compare=False)
    revision_window: tuple[datetime, datetime] | None = field(default=None, compare=False)
    result: dict[str, Any] | None = field(default=None, compare=False, hash=False, repr=False)

    def hash_day(self) -> dict[str, Any]:
        return {"local_day": self.local_day.isoformat(), "mini_revision_id": self.mini_revision_id,
                "input_sha256": self.input_sha256, "decision": self.decision, "evidence_ids": list(self.evidence_ids)}


def study_days(last_day: date) -> list[date]:
    return [last_day - timedelta(days=STUDY_DAYS - 1 - i) for i in range(STUDY_DAYS)]


def local_midnight(day: date, tz_name: str | None) -> datetime:
    """Site-local midnight starting `day`, as UTC (first occurrence)."""
    return datetime.combine(day, time(0)).replace(tzinfo=zone(tz_name), fold=0).astimezone(timezone.utc)


def study_window(first_day: date, last_day: date, tz_name: str | None) -> Window:
    """The job window: first day's Site-local midnight to the midnight after the last day, as UTC."""
    return Window(local_midnight(first_day, tz_name), local_midnight(last_day + timedelta(days=1), tz_name))


def input_sha256(tenant_id: UUID, site_id: UUID, first_day: date, last_day: date,
                 days: Sequence[DayHead]) -> str:
    """Closure 4 S5: `sha256:` + SHA-256 of the canonical sorted compact UTF-8 JSON of the study's physical
    identity. Excludes selection seq/time and job ID."""
    body = {"version": OPPORTUNITY_MODEL_VERSION, "tenant_id": str(tenant_id).lower(),
            "site_id": str(site_id).lower(), "first_day": first_day.isoformat(), "last_day": last_day.isoformat(),
            "days": [d.hash_day() for d in sorted(days, key=lambda d: d.local_day)]}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def day_heads(store: Any, c: Any, tenant_id: UUID, site_id: UUID, tz_name: str | None,
              days: Sequence[date], cutoff: datetime | None = None) -> list[DayHead]:
    """Each study hour's latest committed renewable head by `(selected_at DESC, seq DESC)`; an hour with no
    selection is an explicit missing `DayHead`, never a fabricated assessed hour.

    `mini-opportunity/2` (CH-9, CH9-R2 Q4/Q5): a day's hours are `mini_depth.store.daylight_hours` at `cutoff`
    (default: the database clock): its measured daylight hours plus its missing hours (a missing hour is a
    missing head, so the day is missing); the `store.NO_PV_BINDING` hours for a Site with no `pv_available_power`
    binding. A day with neither daylight nor missing hours keeps the `DaylightHours.study_hours` placeholder as one
    missing head, so the study keeps five days and that day reads missing (recorded in the CH-9 packet)."""
    from assetops_backend.mini_depth.store import daylight_hours

    known = cutoff if cutoff is not None else c.execute(text("SELECT now()")).scalar_one()
    windows: dict[date, list[Any]] = {}
    for d in days:
        found = daylight_hours(c, tenant_id, site_id, d, known)
        windows[d] = [local_hour(d, h, tz_name or "") for h in found.study_hours]
    starts = [w.start for ws in windows.values() for w in ws]
    rows = {r[0]: r for r in store.renewable_hour_heads(c, tenant_id, site_id, starts)}
    return [_head(d, w, rows.get(w.start)) for d in days for w in windows[d]]


def _head(d: date, w: Any, r: Any) -> DayHead:
    if r is None:
        return DayHead(d, Window(w.start, w.end))
    return DayHead(d, Window(w.start, w.end), r[1], r[2], r[3].lower(), r[4], r[5],
                   tuple(str(i).lower() for i in r[6]), r[7], (r[8], r[9]), r[10])


# --- u4: the frozen `mini-opportunity/1` result ---------------------------------------------------------------------

#: u4 stored limitation order: missing day, the eleven W4-02 renewable constraints, then the selected class codes.
CONSTRAINT_CODES: tuple[str, ...] = tuple(code for code, _ in RENEWABLE_CONSTRAINTS)
LIMITATION_ORDER: tuple[str, ...] = ("RENEWABLE_DAY_MISSING", *CONSTRAINT_CODES, "SOURCE_CLASS_UNKNOWN",
                                     "SOURCE_CLASS_MIXED")
DECISIONS = ("ELIGIBLE", "EXCLUDED", "LIMITED", "CONFLICT")
ASSESSED = ("ELIGIBLE", "EXCLUDED")


class ProjectionIntegrityError(RuntimeError):
    """A selected W4-02 head that cannot be copied faithfully (u4: a store-integrity 503, never a missing day)."""


def selected_hours(days: Sequence[DayHead]) -> list[dict[str, Any]]:
    """Closure 1 Q17-Q30 "Files:": the ordered pins, one per study hour (CH9-R2 Q5: one per daylight hour),
    selection fields null (IDs empty) for a missing hour."""
    return [{"local_day": d.local_day.isoformat(), "window_from": iso(d.window.start), "window_to": iso(d.window.end),
             "selection_seq": d.selection_seq, "selection_at": iso(d.selection_at) if d.selection_at else None,
             "mini_revision_id": d.mini_revision_id, "evidence_ids": list(d.evidence_ids)}
            for d in sorted(days, key=lambda d: (d.local_day, d.window.start))]


def _ids(values: Any, where: str) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ProjectionIntegrityError(f"{where}: evidence IDs are not a list of strings")
    try:
        return sorted({str(UUID(v)).lower() for v in values})
    except ValueError:
        raise ProjectionIntegrityError(f"{where}: an evidence ID is not a UUID") from None


def day_row(d: DayHead) -> dict[str, Any]:
    """One study hour's row: the selected revision's single hour row copied (decision, ordered constraints,
    decimal-string bound, sorted cited accepted IDs), or the null/empty row of a missing hour. `frozen_result`
    folds a day's hour rows into its `day_rows` entry (`_fold_day`)."""
    day = d.local_day.isoformat()
    if d.mini_revision_id is None:
        return {"local_day": day, "decision": None, "opportunity_kwh": None, "constraints": [], "evidence_ids": []}
    where = f"Renewable revision {d.mini_revision_id} for {day}"
    if (d.selection_end, d.revision_window) != (d.window.end, (d.window.start, d.window.end)):
        raise ProjectionIntegrityError(f"{where}: the selection or revision is not that study hour")
    rows = (d.result or {}).get("rows")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ProjectionIntegrityError(f"{where}: the revision has no single hour row")
    row = rows[0]
    if (row.get("day"), row.get("from"), row.get("to")) != (day, iso(d.window.start), iso(d.window.end)):
        raise ProjectionIntegrityError(f"{where}: the stored row is not that study hour")
    decision = row.get("decision")
    if decision not in DECISIONS or decision != d.decision:
        raise ProjectionIntegrityError(f"{where}: the row decision does not match the revision")
    constraints = row.get("constraints")
    if (not isinstance(constraints, list) or any(c not in CONSTRAINT_CODES for c in constraints)
            or len(set(constraints)) != len(constraints)):
        raise ProjectionIntegrityError(f"{where}: the row constraints are not W4-02 renewable codes")
    evidence = _ids(row.get("evidence_ids"), where)
    if not set(evidence) <= set(d.evidence_ids):
        raise ProjectionIntegrityError(f"{where}: the row cites evidence outside the revision's accepted set")
    try:
        bound = physical_range(row.get("opportunity_kwh"))
    except DecisionRefused:
        raise ProjectionIntegrityError(f"{where}: the opportunity bound is not a finite nonnegative range") from None
    if decision == "ELIGIBLE" and bound is None:
        raise ProjectionIntegrityError(f"{where}: an ELIGIBLE row has no opportunity bound")
    return {"local_day": day, "decision": decision, "opportunity_kwh": bound, "constraints": list(constraints),
            "evidence_ids": evidence}


def _fold_day(hours: list[dict[str, Any]]) -> dict[str, Any]:
    """CH9-R2 Q5: one `day_rows` entry from its hour rows. Any missing hour makes the day missing; else the day
    decision is CONFLICT > LIMITED > ELIGIBLE(any) > EXCLUDED (`mini_depth.rules.day_decision`). An ELIGIBLE day's
    `opportunity_kwh` sums its ELIGIBLE hours and `window_hours` counts them; constraints and cited IDs are the
    union over its hours. One hour reads exactly as the `/1` row, plus `window_hours` and `hours`."""
    from assetops_backend.mini_depth.rules import day_decision

    day = hours[0]["local_day"]
    if any(h["decision"] is None for h in hours):
        return {"local_day": day, "decision": None, "opportunity_kwh": None, "constraints": [], "evidence_ids": [],
                "window_hours": None, "hours": hours}
    if len(hours) == 1:
        one = hours[0]
        return {**one, "window_hours": 1 if one["decision"] == "ELIGIBLE" else 0, "hours": hours}
    decision = day_decision(h["decision"] for h in hours)
    eligible = [h for h in hours if h["decision"] == "ELIGIBLE"]
    bound = None
    if decision == "ELIGIBLE":
        bound = {"low": decimal_text(sum(Decimal(h["opportunity_kwh"]["low"]) for h in eligible)),
                 "high": decimal_text(sum(Decimal(h["opportunity_kwh"]["high"]) for h in eligible))}
    found = {code for h in hours for code in h["constraints"]}
    return {"local_day": day, "decision": decision, "opportunity_kwh": bound,
            "constraints": [code for code in CONSTRAINT_CODES if code in found],
            "evidence_ids": sorted({i for h in hours for i in h["evidence_ids"]}),
            "window_hours": len(eligible) if decision == "ELIGIBLE" else 0, "hours": hours}


def frozen_result(days: Sequence[DayHead], classification: str | None) -> dict[str, Any]:
    """u4: the immutable five-day result. `classification` is the selected five-day W4-02 provenance class (None
    when no day is selected). Status: any missing day UNKNOWN; else any LIMITED/CONFLICT day or UNKNOWN/MIXED
    class LIMITED; else SUPPORTED (including zero eligible days). Read-time currentness is not an input."""
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for d in sorted(days, key=lambda d: d.local_day):  # stable: a day's hours keep their time order
        grouped.setdefault(d.local_day, []).append(day_row(d))
    rows = [_fold_day(hours) for hours in grouped.values()]
    if len(rows) != STUDY_DAYS:
        raise ProjectionIntegrityError(f"A study has exactly {STUDY_DAYS} days, not {len(rows)}")
    missing = any(r["decision"] is None for r in rows)
    mixed = classification in ("UNKNOWN", "MIXED") and any(r["decision"] is not None for r in rows)
    if missing:
        status = "UNKNOWN"
    elif mixed or any(r["decision"] in ("LIMITED", "CONFLICT") for r in rows):
        status = "LIMITED"
    else:
        status = "SUPPORTED"
    eligible = [r for r in rows if r["decision"] == "ELIGIBLE"]
    headroom, window_hours = None, None
    if status == "SUPPORTED" and eligible:
        # CH9-R2 Q5 / §9 R4: the room on every eligible hour of every eligible day; `window_hours` is the fewest
        # eligible hours on any eligible day.
        every = headroom_on_every_eligible_day([
            Bound(Decimal(h["opportunity_kwh"]["low"]), Decimal(h["opportunity_kwh"]["high"]))
            for r in eligible for h in r["hours"] if h["decision"] == "ELIGIBLE"])
        assert every is not None
        headroom = {"low": decimal_text(every.low), "high": decimal_text(every.high)}
        window_hours = min(r["window_hours"] for r in eligible)
    found: dict[str, set[str]] = {}
    for r in rows:
        for code in r["constraints"]:
            found.setdefault(code, set()).update(r["evidence_ids"])
    if missing:
        found["RENEWABLE_DAY_MISSING"] = set()
    if mixed:
        found[f"SOURCE_CLASS_{classification}"] = set()
    limitations = [{"code": code, "evidence_ids": sorted(found[code])} for code in LIMITATION_ORDER if code in found]
    return {"status": status, "assessed_days": sum(r["decision"] in ASSESSED for r in rows),
            "eligible_days": len(eligible), "headroom_kw": headroom, "window_hours": window_hours, "day_rows": rows,
            "limitations": limitations}
