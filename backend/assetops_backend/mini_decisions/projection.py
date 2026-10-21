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
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.analytics.assessment_ports import Window
from assetops_backend.mini_decisions.store import OPPORTUNITY_MODEL_VERSION
from assetops_backend.mini_depth.inputs import local_noon, zone

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
                               tuple(str(i).lower() for i in r[6])))
    return out
