"""W4-03 unit 4: five-day opportunity study identity (`.agent/W4-03-build-spec.md` closure 2 Q4, closure 4 S5/S6,
u3 "Unit 4 dry-read").

A study is the five contiguous Site-local days ending on a selected renewable noon day. Its job window runs from the
first day's Site-local midnight to the midnight after the last day, both as UTC. Its physical identity is the S5
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

from assetops_backend.analytics.assessment_ports import Window
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.mini_decisions.scenario_rules import decimal_text, physical_range
from assetops_backend.mini_decisions.store import OPPORTUNITY_MODEL_VERSION
from assetops_backend.mini_depth.inputs import local_noon, zone
from assetops_backend.mini_depth.read import iso
from assetops_backend.mini_depth.rules import RENEWABLE_CONSTRAINTS

STUDY_DAYS = 5


@dataclass(frozen=True)
class DayHead:
    """One study day's selected renewable noon head, or a missing day (every selection field None)."""
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
              days: Sequence[date]) -> list[DayHead]:
    """Each day's latest committed renewable noon head by `(selected_at DESC, seq DESC)`; a day with no selection
    is an explicit missing `DayHead`, never a fabricated assessed day."""
    windows = {d: local_noon(d, tz_name or "") for d in days}
    starts = [w.start for w in windows.values()]
    rows = {r[0]: r for r in store.renewable_noon_heads(c, tenant_id, site_id, starts)}
    out = []
    for d in days:
        w = windows[d]
        r = rows.get(w.start)
        if r is None:
            out.append(DayHead(d, Window(w.start, w.end)))
        else:
            out.append(DayHead(d, Window(w.start, w.end), r[1], r[2], r[3].lower(), r[4], r[5],
                               tuple(str(i).lower() for i in r[6]), r[7], (r[8], r[9]), r[10]))
    return out


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
    """Closure 1 Q17-Q30 "Files:": the five ordered pins, selection fields null (IDs empty) for a missing day."""
    return [{"local_day": d.local_day.isoformat(), "window_from": iso(d.window.start), "window_to": iso(d.window.end),
             "selection_seq": d.selection_seq, "selection_at": iso(d.selection_at) if d.selection_at else None,
             "mini_revision_id": d.mini_revision_id, "evidence_ids": list(d.evidence_ids)}
            for d in sorted(days, key=lambda d: d.local_day)]


def _ids(values: Any, where: str) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ProjectionIntegrityError(f"{where}: evidence IDs are not a list of strings")
    try:
        return sorted({str(UUID(v)).lower() for v in values})
    except ValueError:
        raise ProjectionIntegrityError(f"{where}: an evidence ID is not a UUID") from None


def day_row(d: DayHead) -> dict[str, Any]:
    """One u4 `day_rows` entry: the selected revision's single noon row copied (decision, ordered constraints,
    decimal-string bound, sorted cited accepted IDs), or the null/empty row of a missing day."""
    day = d.local_day.isoformat()
    if d.mini_revision_id is None:
        return {"local_day": day, "decision": None, "opportunity_kwh": None, "constraints": [], "evidence_ids": []}
    where = f"Renewable revision {d.mini_revision_id} for {day}"
    if (d.selection_end, d.revision_window) != (d.window.end, (d.window.start, d.window.end)):
        raise ProjectionIntegrityError(f"{where}: the selection or revision is not that day's local noon hour")
    rows = (d.result or {}).get("rows")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ProjectionIntegrityError(f"{where}: the revision has no single noon row")
    row = rows[0]
    if (row.get("day"), row.get("from"), row.get("to")) != (day, iso(d.window.start), iso(d.window.end)):
        raise ProjectionIntegrityError(f"{where}: the stored row is not that noon hour")
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


def frozen_result(days: Sequence[DayHead], classification: str | None) -> dict[str, Any]:
    """u4: the immutable five-day result. `classification` is the selected five-day W4-02 provenance class (None
    when no day is selected). Status: any missing day UNKNOWN; else any LIMITED/CONFLICT day or UNKNOWN/MIXED
    class LIMITED; else SUPPORTED (including zero eligible days). Read-time currentness is not an input."""
    rows = [day_row(d) for d in sorted(days, key=lambda d: d.local_day)]
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
    headroom = None
    if status == "SUPPORTED" and eligible:
        lows = [Decimal(r["opportunity_kwh"]["low"]) for r in eligible]
        highs = [Decimal(r["opportunity_kwh"]["high"]) for r in eligible]
        headroom = {"low": decimal_text(min(lows)), "high": decimal_text(min(highs))}
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
            "eligible_days": len(eligible), "headroom_kw": headroom, "day_rows": rows, "limitations": limitations}
