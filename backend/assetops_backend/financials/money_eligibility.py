"""The shared, read-derived money eligibility gate (LR-01 phase 2, `money-eligibility-1`).

Decision `D-2026-10-15-lr01-source-time-cohort` (Q4) and `D-2026-10-14-s402c-late-sequence-and-s5-money`. For one
Finding it is computed on every read from persisted lineage, never stored and never a UI-only predicate:

- the Finding's LATEST FindingRevision (episode bounds, matcher version, cited window assessments, and the
  `finding-episode-3` `series_limits` / `end_reason` it carries), and
- every latest selected UTC-day dispatch window overlapping the episode plus its six-hour bracket (the same
  bracket as the S3 query and requeue), with its S3 read state, live jobs, selected run/model and cohort limits,
  and the S4 match state of that day.

States, in precedence order:

1. `PENDING_REASSESSMENT` - relevant S3/S4 work or staleness remains: a day overlapping the episode has no
   selected window (N3), a bracketed day's read is not CURRENT (stale selection, outstanding or failed job,
   model change), a live S3 job, a day not yet matched by the current matcher, or a latest FindingRevision
   that does not cite the selected window revision of every episode day or was written by an older matcher.
2. `WITHHELD_GENERATOR_SERIES` - settled, but a material unresolved generator series refusal remains: the
   latest revision carries a series limit (`SERIES_LIMIT` end or `series_limits`), or a selected window's
   generator-role cohort limit for the Finding's generator intersects the bracketed episode.
3. `ELIGIBLE` - passes this series/reassessment gate only. A current amount ALSO needs the exact-head
   `CURRENT PRICED` consequence of the latest FindingRevision and the existing source/currentness checks
   (`consequence_read`); eligibility is never an amount authorization.

Historical or pinned FindingRevisions are judged by the Finding's latest revision: their rows stay recorded or
audit-only. The S4 consequence read, the Finding bridge, the Financials API and the S5 upstream seam all consume
this one function.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.analytics.dispatch_v3 import ANALYTIC_ID, MODEL_VERSION
from assetops_backend.analytics.finding_episode import GENERATOR_ROLES, MATCHER_VERSION, SERIES_LIMIT

VERSION = "money-eligibility-1"
BRACKET = timedelta(hours=6)
ELIGIBLE = "ELIGIBLE"
WITHHELD_GENERATOR_SERIES = "WITHHELD_GENERATOR_SERIES"
PENDING_REASSESSMENT = "PENDING_REASSESSMENT"
STATES = (ELIGIBLE, WITHHELD_GENERATOR_SERIES, PENDING_REASSESSMENT)

NOTES = {
    ELIGIBLE: "No pending reassessment and no unresolved generator-series refusal touches this finding. This "
              "gate alone is not an amount: a current cost also needs the latest consequence to be current and "
              "priced.",
    WITHHELD_GENERATOR_SERIES: "The generator readings around this finding could not be put in a proven time "
                               "order, so the end of the episode is not known and no current cost is shown. "
                               "Earlier recorded costs stay available for the record.",
    PENDING_REASSESSMENT: "The finding is being reassessed after new evidence or clock proof, so no current cost "
                          "is shown until the reassessment settles.",
}


class DispatchWindows(Protocol):
    def window(self, tenant_id: UUID, site_id: UUID, day: date) -> dict[str, Any]: ...


class FindingRows(Protocol):
    def finding_detail(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None: ...

    def match_state(self, tenant_id: UUID, site_id: UUID, analytic_id: str, window_start: datetime
                    ) -> dict[str, Any]: ...


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value: Any) -> str | None:
    return None if value is None else _utc(value).isoformat().replace("+00:00", "Z")


def days_over(lo: datetime, hi: datetime) -> list[date]:
    """UTC days intersecting [lo, hi]."""
    out, d = [], lo.astimezone(timezone.utc).date()
    while datetime(d.year, d.month, d.day, tzinfo=timezone.utc) <= hi:
        out.append(d)
        d += timedelta(days=1)
    return out


def _start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def evaluate(finding_id: str, latest: dict[str, Any], asset_id: str, days: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure precedence over already-read rows. `latest` is the latest FindingRevision row (with `assessments`);
    each `days` item is `{"day": date, "read": DispatchReadService.window(...), "match": match_state(...)}`."""
    start, end = _utc(latest["episode_start"]), _utc(latest["episode_end"])
    lo, hi = start - BRACKET, end + BRACKET
    claim = latest.get("claim") or {}
    cited = {str(a["assessment_revision_id"]) for a in latest.get("assessments") or () if a.get("scope") == "WINDOW"}
    pending: list[str] = []
    windows: list[dict[str, Any]] = []
    limits: list[dict[str, Any]] = []
    for item in days:
        d, read, match = item["day"], item["read"], item.get("match") or {}
        sel = read.get("selection") or {}
        wa = read.get("window_assessment") or {}
        episode_day = _start(d) < end and start < _start(d) + timedelta(days=1)
        status = read["status"]
        jobs = [str(j["id"]) for j in read.get("jobs") or ()]
        code = f"DAY {d.isoformat()}"
        if not sel:
            if episode_day:
                pending.append(f"NO_SELECTED_WINDOW: {code} overlaps the episode and has no selected assessment")
            elif status != "UNASSESSED":
                pending.append(f"S3_{status}: {code}")
        elif status != "CURRENT":
            pending.append(f"S3_{status}: {code}")
        elif sel.get("model_version") != MODEL_VERSION:
            pending.append(f"MODEL_NOT_CURRENT: {code} selected {sel.get('model_version')}")
        if jobs:
            pending.append(f"LIVE_JOB: {code} " + ", ".join(jobs))
        if sel and not match.get("matched"):
            pending.append(f"MATCH_PENDING: {code} not yet matched by {MATCHER_VERSION}")
        if sel and episode_day and wa.get("id") is not None and str(wa["id"]) not in cited:
            pending.append(f"FINDING_NOT_ON_SELECTED_WINDOW: {code} window assessment {wa['id']} is not cited by "
                           f"the latest FindingRevision")
        for x in ((sel.get("cohort") or {}).get("limits") or ()):
            if x.get("role") in GENERATOR_ROLES and str(x.get("asset_id")) == asset_id and \
                    _utc(x["start"]) <= hi and lo <= _utc(x["end"]):
                limits.append({"kind": x["kind"], "role": x["role"], "start": x["start"], "end": x["end"],
                               "evidence_ids": [str(e) for e in x.get("evidence_ids") or ()],
                               "clock": x.get("clock"), "attestation_refs": list(x.get("attestation_refs") or ()),
                               "window_start": _iso(_start(d)),
                               "window_assessment_revision_id": None if wa.get("id") is None else str(wa["id"]),
                               "analytic_run_id": None if not sel else str(sel["run_id"]), "source": "SELECTED_WINDOW"})
        windows.append({"day": d.isoformat(), "s3_status": status, "episode_day": episode_day,
                        "analytic_run_id": None if not sel else str(sel["run_id"]),
                        "model_version": sel.get("model_version"),
                        "window_assessment_revision_id": None if wa.get("id") is None else str(wa["id"]),
                        "matched": bool(match.get("matched")), "match_pass_id": match.get("match_pass_id"),
                        "live_job_ids": jobs})
    if latest.get("matcher_version") != MATCHER_VERSION:
        pending.append(f"FINDING_MATCHER_NOT_CURRENT: latest FindingRevision was written by "
                       f"{latest.get('matcher_version')}")
    revision_limits = [{**x, "source": "FINDING_REVISION"} for x in claim.get("series_limits") or ()]
    if pending:
        state = PENDING_REASSESSMENT
    elif revision_limits or limits or claim.get("end_reason") == SERIES_LIMIT:
        state = WITHHELD_GENERATOR_SERIES
    else:
        state = ELIGIBLE
    return {
        "version": VERSION, "state": state, "note": NOTES[state],
        "finding_id": finding_id, "latest_finding_revision_id": str(latest["id"]),
        "latest_revision_no": latest.get("revision_no"), "end_reason": claim.get("end_reason"),
        "episode": {"start": _iso(start), "end": _iso(end)}, "bracket": {"start": _iso(lo), "end": _iso(hi)},
        "pending_reasons": pending, "series_limits": revision_limits + limits, "windows": windows,
        "amount_rule": "ELIGIBLE passes the series/reassessment gate only; a current amount also needs the "
                       "exact-head CURRENT PRICED consequence of the latest FindingRevision and an open source.",
    }


def unavailable(finding_id: str, reason: str) -> dict[str, Any]:
    """Fail closed: when the gate cannot be read, no current money is shown."""
    return {"version": VERSION, "state": PENDING_REASSESSMENT, "note": NOTES[PENDING_REASSESSMENT],
            "finding_id": finding_id, "latest_finding_revision_id": None, "latest_revision_no": None,
            "end_reason": None, "episode": None, "bracket": None, "pending_reasons": [reason],
            "series_limits": [], "windows": [], "amount_rule": None}


class MoneyEligibility:
    """Reads the persisted lineage for one Finding and applies `evaluate`."""

    def __init__(self, windows: DispatchWindows, findings: FindingRows, analytic_id: str = ANALYTIC_ID) -> None:
        self.windows, self.findings, self.analytic_id = windows, findings, analytic_id

    def for_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any]:
        detail = self.findings.finding_detail(tenant_id, site_id, finding_id)
        if detail is None or not detail["revisions"]:
            return unavailable(str(finding_id), "NO_FINDING_REVISION")
        latest = detail["revisions"][-1]
        asset = str(detail["finding"].get("generator_asset_id"))
        lo, hi = _utc(latest["episode_start"]) - BRACKET, _utc(latest["episode_end"]) + BRACKET
        days = [{"day": d, "read": self.windows.window(tenant_id, site_id, d),
                 "match": self.findings.match_state(tenant_id, site_id, self.analytic_id, _start(d))}
                for d in days_over(lo, hi)]
        return evaluate(str(finding_id), latest, asset, days)
