"""The selected-window upstream currentness seam for S5-01 (S4-02d phase 2, packet item 4).

    UpstreamCurrentness.window(tenant_id, site_id, window_start, window_end, environment="default") -> dict

Inputs: a tenant, a Site and a half-open UTC window `[window_start, window_end)`; the schedule environment whose
tick owns the Site. It writes nothing and builds no UI; S5-01 consumes it and applies its own F1 money rule and
same-basis `CURRENT/PRICED` test on top.

Outputs (all IDs as strings, instants as returned by the database):

- `db_now`: the database `clock_timestamp()` every age and threshold is measured against (never the host clock).
- `days[]`: per UTC day window intersecting the selection, the existing S3 read (`DispatchReadService.window`):
  `s3_status` (`UNASSESSED|PENDING|CURRENT|STALE_PROJECTION|FAILED`) and reasons, `limitations`, the accepted
  input/source basis (`current_basis`), the selected run and window-assessment revision IDs, and the watermark
  `{selection_seq, input_sha256, configuration_sha256}` (the selected input basis plus its
  `analytic_run_selection.seq`, D-2026-10-11-s3-phase-2-selection-and-read; never a disposition timestamp or a
  heartbeat).
- `s3_jobs[]`: live S3 jobs intersecting any day's six-hour continuity bracket, with status, attempts, lease and
  `last_error`.
- `match[]`: `match_state` for every day intersecting the window plus its bracket: window selection seq, match
  pass ID, matched-through seq and `matched`.
- `findings[]`: the latest FindingRevision of each Finding whose episode intersects the bracketed window, with its
  consequence read (`currentness.state`/reasons, head consequence revision ID, pending work with attempts, last
  error and age), `STALE_NO_WORK` included.
- `consequence_work[]`: the Site's unsucceeded consequence work touching those revisions or the bracketed range.
- `schedule`: environment state/heartbeat and the Site head observation (review Q1: a healthy Site head is
  required as well as the environment heartbeat).
- `findings[].money_eligibility`: the shared LR-01 gate (`financials/money_eligibility.py`) with its exact lineage;
  S5-01 shows a current amount only when it is `ELIGIBLE` (plus its own same-basis CURRENT PRICED test). This seam
  turns an `ELIGIBLE` gate into `PENDING_REASSESSMENT` (reasons `UPSTREAM_<code>`) while any S3, S4 or schedule
  blocker of this read stands. The gate does not change `eligibility` below, which stays upstream currentness.
- `eligibility`: `{status, stage, reasons, errors}`. `CURRENT` only when every day's S3 read is CURRENT, no live S3
  job intersects the bracket, every bracketed day with a selection is matched, every relevant consequence is
  CURRENT with no outstanding or stale-without-work entry, the selection seq did not move during this read, and
  the schedule observed the Site healthily. Otherwise: `FAILED` when an S3 failure left no usable prior result,
  `UNASSESSED` when no day has evidence or work, `PENDING` for a first build, and `STALE_PROJECTION` when an older
  result exists under advanced basis/work, failures or an unobserved schedule. `stage` is the first blocking stage
  in pipeline order (`S3`, `S4`, `CONSEQUENCE`, `SCHEDULE`); `errors` keeps typed stage errors.

Commit safety: the match states are read before and after the S3 reads; a different window selection seq between
them means a selection committed during the read, which is reported as `SELECTION_MOVED_DURING_READ` (never
CURRENT). Acceptance creates or widens a job in its own transaction, so newer evidence is visible as a live job or
an advanced selection seq; a read is CURRENT only as of its `db_now`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from assetops_backend.scheduling.health import HealthThresholds, environment_health, release, site_observation

BRACKET = timedelta(hours=6)
_ORDER = ("S3", "S4", "CONSEQUENCE", "SCHEDULE")


def _days(lo: datetime, hi: datetime) -> list[date]:
    out, d = [], lo.astimezone(timezone.utc).date()
    while datetime(d.year, d.month, d.day, tzinfo=timezone.utc) < hi:
        out.append(d)
        d += timedelta(days=1)
    return out


def _start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _overlaps(a0, a1, b0, b1) -> bool:
    return (a0 is None or b1 is None or a0 < b1) and (a1 is None or b0 is None or b0 < a1)


class UpstreamCurrentness:
    def __init__(self, schedule: Any, dispatch_read: Any, findings: Any, consequences: Any, consequence_read: Any,
                 *, analytic_id: str, thresholds: HealthThresholds = HealthThresholds()) -> None:
        self.schedule, self.dispatch_read, self.findings = schedule, dispatch_read, findings
        self.consequences, self.consequence_read = consequences, consequence_read
        self.analytic_id, self.th = analytic_id, thresholds

    def dispose(self) -> None:
        release(self.schedule, self.dispatch_read, self.findings, self.consequences, self.consequence_read)

    def _match(self, t: UUID, s: UUID, days: list[date]) -> dict[date, dict[str, Any]]:
        return {d: self.findings.match_state(t, s, self.analytic_id, _start(d)) for d in days}

    def window(self, tenant_id: UUID, site_id: UUID, window_start: datetime, window_end: datetime,
               environment: str = "default") -> dict[str, Any]:
        if window_start.tzinfo is None or window_end.tzinfo is None or not window_start < window_end:
            raise ValueError("The window is a non-empty half-open UTC interval with explicit offsets.")
        t, s = tenant_id, site_id
        lo, hi = window_start - BRACKET, window_end + BRACKET
        days, bracket_days = _days(window_start, window_end), _days(lo, hi)

        before = self._match(t, s, bracket_days)
        reads = {d: self.dispatch_read.window(t, s, d) for d in days}
        after = self._match(t, s, bracket_days)
        now = self.schedule.db_now()

        blockers: list[tuple[str, str]] = []
        errors: list[dict[str, Any]] = []
        day_out, jobs = [], {}
        for d, r in reads.items():
            sel = r.get("selection") or {}
            wa = r.get("window_assessment") or {}
            status = r["status"]
            if status != "CURRENT":
                blockers.append(("S3", f"S3_{status}"))
            for j in r.get("jobs") or []:
                jobs[str(j["id"])] = j
            seq = (after.get(d) or {}).get("window_selection_seq")
            day_out.append({
                "day": d.isoformat(), "window": r.get("window"), "s3_status": status,
                "s3_status_reasons": r.get("status_reasons"), "limitations": r.get("limitations"),
                "current_basis": r.get("current_basis"), "run_id": sel.get("run_id"),
                "window_assessment_revision_id": wa.get("id"), "claim_level": wa.get("claim_level"),
                "watermark": {"selection_seq": seq, "input_sha256": sel.get("input_sha256"),
                              "configuration_sha256": sel.get("configuration_sha256")}})
        for j in jobs.values():
            blockers.append(("S3", "LIVE_JOB"))
            if j["status"] == "FAILED":
                errors.append({"stage": "S3", "code": "RECOMPUTE_FAILED", "job_id": str(j["id"]),
                               "error": j.get("last_error")})

        match_out = []
        for d in bracket_days:
            a, b = after[d], before[d]
            if a.get("window_selection_seq") != b.get("window_selection_seq"):
                blockers.append(("S4", "SELECTION_MOVED_DURING_READ"))
            if a.get("window_selection_seq") is not None and not a.get("matched"):
                blockers.append(("S4", "MATCH_PENDING"))
            match_out.append({"day": d.isoformat(), **{k: a.get(k) for k in (
                "window_selection_seq", "matcher_version", "match_pass_id", "matched_through_selection_seq",
                "match_completed_at", "matched")}})

        findings_out, revision_ids = [], set()
        for f in self.findings.findings_over(t, s, lo, hi):
            revision_ids.add(str(f["revision_id"]))
            body = self.consequence_read.read(t, s, UUID(str(f["finding_id"])), UUID(str(f["revision_id"])),
                                              finding_revision_is_latest=True, source_open=True) or {}
            cur = body.get("currentness") or {}
            sel = body.get("consequence_selection") or {}
            state, reasons = cur.get("state"), list(cur.get("reasons") or [])
            stale_no_work = state == "STALE" and "NO_WORK_RECORDED" in reasons
            if state != "CURRENT":
                blockers.append(("CONSEQUENCE", "STALE_NO_WORK" if stale_no_work else f"CONSEQUENCE_{state}"))
            # LR-01: the shared money eligibility gate, with its exact lineage, consumed by S5-01 (downgraded
            # below when this read's own S3/S4/schedule blockers stand).
            money = body.get("money_eligibility") or {"state": "PENDING_REASSESSMENT", "pending_reasons": [
                "ELIGIBILITY_NOT_READ"]}
            for w in cur.get("pending_work") or []:
                if w.get("last_error_code"):
                    errors.append({"stage": "CONSEQUENCE", "code": w["last_error_code"], "work_id": w["work_id"],
                                   "attempts": w.get("attempts")})
            findings_out.append({
                "finding_id": str(f["finding_id"]), "finding_revision_id": str(f["revision_id"]),
                "lifecycle": f.get("lifecycle"), "episode_start": f.get("episode_start"),
                "episode_end": f.get("episode_end"), "consequence_state": state, "consequence_reasons": reasons,
                "stale_no_work": stale_no_work,
                "head_consequence_revision_id": sel.get("head_consequence_revision_id"),
                "pending_work": cur.get("pending_work") or [], "money_eligibility": money})

        work_out = []
        for w in self.consequences.pending_work(t, s):
            if str(w.get("finding_revision_id")) in revision_ids or _overlaps(
                    w.get("affected_from"), w.get("affected_to"), lo, hi):
                blockers.append(("CONSEQUENCE", "WORK_OUTSTANDING"))
                work_out.append({"work_id": str(w["id"]), "cause": w["cause"], "attempts": int(w["attempts"]),
                                 "last_outcome": w.get("last_outcome"),
                                 "finding_revision_id": None if w.get("finding_revision_id") is None
                                 else str(w["finding_revision_id"]),
                                 "age_seconds": round((now - w["enqueued_at"]).total_seconds(), 3)})

        env = environment_health(self.schedule.tick_head(environment), now, self.th)
        head = self.schedule.site_head(t, s)
        observation = site_observation(head, now, self.th)
        if env["state"] == "STOPPED":
            blockers.append(("SCHEDULE", "SCHEDULE_STOPPED"))
        for o in observation:
            blockers.append(("SCHEDULE", o["code"]))
        if head and head.get("last_failure_code") and int(head.get("consecutive_failures") or 0) > 0:
            errors.append({"stage": head.get("last_failure_stage"), "code": head["last_failure_code"],
                           "error": head.get("last_failure_detail"), "source": "SCHEDULE"})

        eligibility = self._eligibility(blockers, errors, reads, jobs)
        # LR-01: pending S3/S4 work, a selection moving during the read or a stopped/unobserved schedule never
        # leaves the money gate ELIGIBLE in this seam (fail closed; the gate itself already withholds or pends).
        upstream_pending = [code for stage, code in blockers if stage in ("S3", "S4", "SCHEDULE")]
        for f in findings_out:
            m = f["money_eligibility"]
            if m["state"] == "ELIGIBLE" and upstream_pending:
                f["money_eligibility"] = {**m, "state": "PENDING_REASSESSMENT",
                                          "pending_reasons": [f"UPSTREAM_{c}" for c in dict.fromkeys(upstream_pending)]}
        return {
            "tenant_id": str(t), "site_id": str(s), "window_start": window_start, "window_end": window_end,
            "bracket": {"start": lo, "end": hi}, "db_now": now, "eligibility": eligibility, "days": day_out,
            "s3_jobs": [{"id": str(j["id"]), "status": j["status"], "attempts": j.get("attempts"),
                         "window_start": j.get("window_start"), "window_end": j.get("window_end"),
                         "last_error": j.get("last_error")} for j in jobs.values()],
            "match": match_out, "findings": findings_out, "consequence_work": work_out,
            "schedule": {"environment": environment, "state": env["state"], "heartbeat_at": env["heartbeat_at"],
                         "heartbeat_age_seconds": env["heartbeat_age_seconds"], "environment_alarms": env["alarms"],
                         "site_observation": observation,
                         "site_last_completed_at": None if head is None else head.get("last_completed_at")}}

    @staticmethod
    def _eligibility(blockers, errors, reads, jobs) -> dict[str, Any]:
        if not blockers:
            return {"status": "CURRENT", "stage": None, "reasons": [], "errors": []}
        reasons = list(dict.fromkeys(code for _, code in blockers))
        stage = min((st for st, _ in blockers), key=_ORDER.index)
        has_result = all(r.get("selection") for r in reads.values())
        if has_result:
            status = "STALE_PROJECTION"
        elif any(r["status"] == "FAILED" for r in reads.values()):
            status = "FAILED"
        elif all(r["status"] == "UNASSESSED" for r in reads.values()) and not jobs:
            status = "UNASSESSED"
        else:
            status = "PENDING"
        return {"status": status, "stage": stage, "reasons": reasons, "errors": errors}
