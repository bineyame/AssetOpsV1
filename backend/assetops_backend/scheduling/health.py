"""Read-only schedule health report and alarms (S4-02d phase 2, packet item 3).

Durable state comes from the schedule heads (`schedule_tick_head`, `schedule_site_head`); backlog is derived from
the existing authorities on every read: live S3 jobs (`live_jobs`), the S4 matcher fence against the last
`finding_match_pass` (`fence` / `match_state`), and consequence work (`pending_work_sites` / `pending_work`),
plus pre-0012 `STALE` consequence heads with no recorded work (`STALE_NO_WORK`, from the consequence read). It
writes nothing. Every age and threshold is measured against the database's `clock_timestamp()` (I3), never the
host clock.

States, per Site and in aggregate (worst first): `STOPPED`, `FAILED`, `RETRY_DUE`, `BACKLOG`, `RUNNING`, `IDLE`.

- Environment `STOPPED`: no completed tick yet, or the heartbeat (advanced only by a completed tick) is older than
  `stop_after_seconds`. A stopped environment makes every scheduled Site `STOPPED`.
- Site `STOPPED`: a scheduled Site never visited, or with no finished visit (completed or failed) within
  `site_stop_after_seconds`, whose claim outlived its lease (a hung or crashed holder), or whose claim was skipped
  `claim_skip_alarm` times running. A visited Site that has not completed since (`SITE_NEVER_COMPLETED`,
  `SITE_COMPLETION_STALE`) is reported by its failure state and still blocks the S5 seam.
- Site `FAILED`: a terminal FAILED S3 job (ID and `last_error`; recovery `assess_dispatch requeue`), repeated Site
  stage failures, a repeated `FENCE_MOVED`, the deterministic `MATCH_EVIDENCE_NOT_ACCEPTED`, consequence work whose
  uncapped attempts reached `consequence_attempt_alarm`, `STALE_NO_WORK` heads, or `S3_STALE_NO_JOB`: a selected
  UTC day window whose S3 read is `STALE_PROJECTION` (for example `INPUT_BASIS_CHANGED`) while no live S3 job
  intersects it, so nothing scheduled will rebuild it (phase-2 review F-A: an app-clock `decided_at` after the
  DB-clock knowledge cutoff of a job it widened). Recovery: `assess_dispatch requeue --tenant-id T --site-id S
  --day D` once the cause is understood.
- `RETRY_DUE`: inside a schedule back-off. `RUNNING`: claim held within its lease. `BACKLOG`: live S3 jobs, an
  unmatched selection, or pending consequence work. A Site outside the active set keeps its S4 backlog in the
  report (`S4_BACKLOG_OUTSIDE_ACTIVE_SET`): the tick no longer visits it, so nothing will match it.

`last_started_at` on the tick head is stamped when a tick takes its claim, including one that then returns
`RETRY_DUE`; it is reported but never read as liveness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from assetops_backend.scheduling.tick import EXCLUDED_LIFECYCLES

RANK = {"IDLE": 0, "RUNNING": 1, "BACKLOG": 2, "RETRY_DUE": 3, "FAILED": 4, "STOPPED": 5}
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class HealthThresholds:
    stop_after_seconds: float = 300  # five one-minute ticks without a completed tick
    site_stop_after_seconds: float = 900  # a scheduled Site unvisited this long (covers max_sites rotation)
    claim_skip_alarm: int = 3
    fence_moved_alarm: int = 3
    failure_alarm: int = 3
    consequence_attempt_alarm: int = 5


def release(*objects: Any) -> None:
    """Dispose the database engines of these collaborators and the stores they wrap (callers that build a report
    or seam per request release their connections instead of waiting for garbage collection)."""
    seen: set[int] = set()
    stack = list(objects)
    while stack:
        obj = stack.pop()
        if obj is None or id(obj) in seen:
            continue
        seen.add(id(obj))
        stack += [getattr(obj, name, None) for name in ("store", "_store", "_prices",
                                                       # LR-01: the money eligibility gate's two reads
                                                       "_eligibility", "windows", "findings")]
        if callable(getattr(obj, "dispose", None)):
            obj.dispose()
        elif getattr(obj, "_engine", None) is not None:
            obj._engine.dispose()


def _age(now: datetime, at: datetime | None) -> float | None:
    return None if at is None else round((now - at).total_seconds(), 3)


def environment_health(tick: dict[str, Any] | None, now: datetime, th: HealthThresholds) -> dict[str, Any]:
    alarms: list[dict[str, Any]] = []
    tick = tick or {}
    beat = tick.get("heartbeat_at")
    held = tick.get("claim_token") is not None
    if beat is None:
        alarms.append({"code": "TICK_NEVER_COMPLETED"})
    elif (now - beat).total_seconds() > th.stop_after_seconds:
        alarms.append({"code": "HEARTBEAT_STALE", "heartbeat_age_seconds": _age(now, beat),
                       "threshold_seconds": th.stop_after_seconds})
    if held and tick.get("lease_until") is not None and tick["lease_until"] < now:
        alarms.append({"code": "TICK_CLAIM_STALE", "claim_owner": tick.get("claim_owner"),
                       "claim_age_seconds": _age(now, tick.get("claimed_at"))})
    if int(tick.get("consecutive_failures") or 0) >= th.failure_alarm:
        alarms.append({"code": "TICK_FAILING", "consecutive_failures": tick["consecutive_failures"],
                       "last_failure_code": tick.get("last_failure_code")})
    if int(tick.get("claim_skips") or 0) >= th.claim_skip_alarm:
        alarms.append({"code": "TICK_CLAIM_SKIPS", "claim_skips": tick["claim_skips"]})
    retry_due = tick.get("retry_due_at")
    if any(a["code"] in ("TICK_NEVER_COMPLETED", "HEARTBEAT_STALE") for a in alarms):
        state = "STOPPED"
    elif retry_due is not None and retry_due > now:
        state = "RETRY_DUE"
    elif held and tick.get("lease_until") is not None and tick["lease_until"] >= now:
        state = "RUNNING"
    else:
        state = "IDLE"
    return {"state": state, "alarms": alarms, "heartbeat_at": beat, "heartbeat_age_seconds": _age(now, beat),
            "last_started_at": tick.get("last_started_at"), "last_succeeded_at": tick.get("last_succeeded_at"),
            "last_failed_at": tick.get("last_failed_at"), "last_failure_code": tick.get("last_failure_code"),
            "last_failure_detail": tick.get("last_failure_detail"), "retry_due_at": retry_due,
            "consecutive_failures": tick.get("consecutive_failures"), "claim_owner": tick.get("claim_owner"),
            "claim_age_seconds": _age(now, tick.get("claimed_at")) if held else None,
            "claim_skips": tick.get("claim_skips"), "last_reconcile_ms": tick.get("last_reconcile_ms"),
            "last_sites_selected": tick.get("last_sites_selected"),
            "last_sites_deferred": tick.get("last_sites_deferred")}


def site_observation(head: dict[str, Any] | None, now: datetime, th: HealthThresholds) -> list[dict[str, Any]]:
    """Why the schedule has not observed this Site healthily (empty when it has). Used by the report and by the
    S5 upstream seam, which requires a healthy Site head as well as a live environment heartbeat (review Q1)."""
    if head is None:
        return [{"code": "SITE_NOT_OBSERVED"}]
    out: list[dict[str, Any]] = []
    visits = [x for x in (head.get("last_completed_at"), head.get("last_failed_at")) if x is not None]
    visit_age = _age(now, max(visits)) if visits else None
    if visit_age is None or visit_age > th.site_stop_after_seconds:
        # No visit finished (completed or failed) within the threshold: the schedule is not reaching this Site.
        out.append({"code": "SITE_VISIT_STALE", "last_visit_age_seconds": visit_age,
                    "threshold_seconds": th.site_stop_after_seconds})
    done_age = _age(now, head.get("last_completed_at"))
    if done_age is None:
        out.append({"code": "SITE_NEVER_COMPLETED"})
    elif done_age > th.site_stop_after_seconds and visit_age is not None and visit_age <= th.site_stop_after_seconds:
        out.append({"code": "SITE_COMPLETION_STALE", "last_completed_age_seconds": done_age})
    if head.get("claim_token") is not None and head.get("lease_until") is not None and head["lease_until"] < now:
        out.append({"code": "SITE_CLAIM_STALE", "claim_owner": head.get("claim_owner"), "stage": head.get("stage"),
                    "claim_age_seconds": _age(now, head.get("claimed_at"))})
    if int(head.get("claim_skips") or 0) >= th.claim_skip_alarm:
        out.append({"code": "SITE_CLAIM_SKIPS", "claim_skips": head["claim_skips"],
                    "claim_owner": head.get("claim_owner")})
    if int(head.get("consecutive_failures") or 0) >= th.failure_alarm:
        out.append({"code": "SITE_FAILING", "consecutive_failures": head["consecutive_failures"],
                    "last_failure_stage": head.get("last_failure_stage"),
                    "last_failure_code": head.get("last_failure_code")})
    if int(head.get("fence_moved_streak") or 0) >= th.fence_moved_alarm:
        out.append({"code": "FENCE_MOVED_STREAK", "fence_moved_streak": head["fence_moved_streak"]})
    if head.get("s4_outcome") == "MATCH_EVIDENCE_NOT_ACCEPTED":
        out.append({"code": "MATCH_EVIDENCE_NOT_ACCEPTED", "detail": head.get("last_failure_detail")})
    return out


_STOPPING = {"SITE_NOT_OBSERVED", "SITE_VISIT_STALE", "SITE_CLAIM_STALE", "SITE_CLAIM_SKIPS"}


class ScheduleHealth:
    """The operator report. Collaborators are the existing stores and reads, received from compositions."""

    def __init__(self, schedule: Any, assessments: Any, findings: Any, consequences: Any, consequence_read: Any,
                 *, analytic_id: str, domain: str, thresholds: HealthThresholds = HealthThresholds(),
                 dispatch_read: Any = None) -> None:
        self.schedule, self.assessments, self.findings = schedule, assessments, findings
        self.consequences, self.consequence_read = consequences, consequence_read
        self.analytic_id, self.domain, self.th = analytic_id, domain, thresholds
        self.dispatch_read = dispatch_read

    def dispose(self) -> None:
        release(self.schedule, self.assessments, self.findings, self.consequences, self.consequence_read,
                self.dispatch_read)

    def stale_without_job(self, tenant_id: UUID, site_id: UUID, live: list[dict]) -> list[dict]:
        """Selected UTC day windows read `STALE_PROJECTION` with no live S3 job intersecting them (review F-A).

        One S3 read per selected day without a live job: cost grows with assessed days, like `stale_no_work`."""
        if self.dispatch_read is None:
            return []
        out = []
        for head in self.assessments.run_heads(tenant_id, site_id, self.analytic_id):
            w0, w1 = head.window.start, head.window.end
            day = w0.astimezone(timezone.utc).date()
            if w1 - w0 != timedelta(days=1) or w0 != datetime(day.year, day.month, day.day, tzinfo=timezone.utc):
                continue  # DEFAULT selections are UTC days; anything else is not this read's window
            if any(j["window_start"] < w1 and j["window_end"] > w0 for j in live):
                continue  # live work will rebuild it; that is backlog, not a stuck window
            read = self.dispatch_read.window(tenant_id, site_id, day)
            if read["status"] == "STALE_PROJECTION":
                out.append({"code": "S3_STALE_NO_JOB", "day": day.isoformat(),
                            "run_id": (read.get("selection") or {}).get("run_id"),
                            "status_reasons": read.get("status_reasons"),
                            "recovery": "assess_dispatch requeue --tenant-id T --site-id S --day " + day.isoformat()})
        return out

    def stale_no_work(self, tenant_id: UUID, site_id: UUID, revisions: list[tuple[Any, Any]]) -> list[dict]:
        out = []
        for finding_id, revision_id in revisions:
            body = self.consequence_read.read(tenant_id, site_id, UUID(str(finding_id)), UUID(str(revision_id)),
                                              finding_revision_is_latest=True, source_open=True)
            cur = (body or {}).get("currentness") or {}
            if cur.get("state") == "STALE" and "NO_WORK_RECORDED" in (cur.get("reasons") or []):
                sel = body.get("consequence_selection") or {}
                out.append({"code": "STALE_NO_WORK", "finding_id": str(finding_id),
                            "finding_revision_id": str(revision_id),
                            "consequence_revision_id": sel.get("head_consequence_revision_id"),
                            "reasons": cur.get("reasons")})
        return out

    def report(self, environment: str = "default") -> dict[str, Any]:
        now = self.schedule.db_now()
        env = environment_health(self.schedule.tick_head(environment), now, self.th)
        inventory = {(UUID(str(s["tenant_id"])), UUID(str(s["site_id"]))): s for s in self.schedule.site_inventory()}
        heads = {(UUID(str(h["tenant_id"])), UUID(str(h["site_id"]))): h for h in self.schedule.site_heads()}
        jobs: dict[tuple[UUID, UUID], list[dict]] = {}
        for j in self.assessments.live_jobs(self.analytic_id, self.domain):
            jobs.setdefault((UUID(str(j["tenant_id"])), UUID(str(j["site_id"]))), []).append(j)
        pending_sites = {(UUID(str(p["tenant_id"])), UUID(str(p["site_id"]))): p
                         for p in self.consequences.pending_work_sites()}
        sites = []
        for key in sorted(set(inventory) | set(heads) | set(jobs) | set(pending_sites)):
            sites.append(self._site(key, inventory.get(key), heads.get(key), jobs.get(key, []),
                                    key in pending_sites, now, env["state"]))
        worst = max([env["state"]] + [s["state"] for s in sites], key=RANK.__getitem__)
        return {"environment": environment, "db_now": now, "state": worst, "tick": env,
                "thresholds": self.th.__dict__, "sites": sites,
                "alarm_count": len(env["alarms"]) + sum(len(s["alarms"]) for s in sites)}

    def _site(self, key, inv, head, live, has_pending, now, env_state) -> dict[str, Any]:
        t, s = key
        active = inv is not None and inv["lifecycle"] not in EXCLUDED_LIFECYCLES and (
            inv["has_evidence"] or inv["enrolled"])
        scheduled = active or bool(live) or has_pending
        alarms: list[dict[str, Any]] = []

        failed_jobs = [j for j in live if j["status"] == "FAILED"]
        for j in failed_jobs:
            alarms.append({"code": "S3_JOB_FAILED", "job_id": str(j["id"]), "last_error": j["last_error"],
                           "window_start": j["window_start"], "window_end": j["window_end"],
                           "recovery": "assess_dispatch requeue --tenant-id T --site-id S --job-id J"})
        s3_backlog = [j for j in live if j["status"] in ("PENDING", "LEASED")]

        fence = self.findings.fence(t, s, self.analytic_id)
        # match_state's pass row is per Site; the window argument only selects its window seq, unused here.
        ms = self.findings.match_state(t, s, self.analytic_id, _EPOCH)
        through = ms.get("matched_through_selection_seq")
        s4_backlog = fence.selection_seq is not None and (through is None or through < fence.selection_seq)
        if s4_backlog and not active:
            alarms.append({"code": "S4_BACKLOG_OUTSIDE_ACTIVE_SET", "selection_seq": fence.selection_seq,
                           "matched_through_selection_seq": through,
                           "lifecycle": None if inv is None else inv["lifecycle"]})

        work = self.consequences.pending_work(t, s) if has_pending else []
        grown = [w for w in work if int(w["attempts"]) >= self.th.consequence_attempt_alarm]
        if grown:
            alarms.append({"code": "CONSEQUENCE_ATTEMPTS_GROWING",
                           "work": [{"work_id": str(w["id"]), "attempts": int(w["attempts"]),
                                     "last_outcome": w["last_outcome"]} for w in grown]})
        revisions = [(f["finding_id"], f["revision_id"]) for f in self.findings.findings_over(
            t, s, _EPOCH, datetime(9999, 1, 1, tzinfo=timezone.utc))] if inv is not None else []
        stale = self.stale_no_work(t, s, revisions)
        alarms += stale
        stuck = self.stale_without_job(t, s, live) if inv is not None else []
        alarms += stuck

        observation = site_observation(head, now, self.th) if scheduled else []
        alarms += observation
        if not active and scheduled:
            alarms.append({"code": "EXCLUDED_WITH_WORK", "lifecycle": None if inv is None else inv["lifecycle"]})
        codes = {a["code"] for a in alarms}
        held = head is not None and head.get("claim_token") is not None
        if scheduled and (env_state == "STOPPED" or codes & _STOPPING):
            state = "STOPPED"
        elif codes & {"S3_JOB_FAILED", "SITE_FAILING", "FENCE_MOVED_STREAK", "MATCH_EVIDENCE_NOT_ACCEPTED",
                      "CONSEQUENCE_ATTEMPTS_GROWING", "STALE_NO_WORK", "S3_STALE_NO_JOB"}:
            state = "FAILED"
        elif head is not None and head.get("retry_due_at") is not None and head["retry_due_at"] > now:
            state = "RETRY_DUE"
        elif held and head.get("lease_until") is not None and head["lease_until"] >= now:
            state = "RUNNING"
        elif s3_backlog or s4_backlog or work:
            state = "BACKLOG"
        else:
            state = "IDLE"
        oldest = min((w["enqueued_at"] for w in work), default=None)
        h = head or {}
        return {
            "tenant_id": str(t), "site_id": str(s), "site_code": None if inv is None else inv["site_code"],
            "lifecycle": None if inv is None else inv["lifecycle"], "active": active, "scheduled": scheduled,
            "state": state, "alarms": alarms,
            "claim": {"owner": h.get("claim_owner"), "stage": h.get("stage"),
                      "claim_age_seconds": _age(now, h.get("claimed_at")) if held else None,
                      "lease_until": h.get("lease_until"), "claim_skips": h.get("claim_skips"),
                      "last_skipped_at": h.get("last_skipped_at")},
            "last_completed_at": h.get("last_completed_at"),
            "last_failure": {"stage": h.get("last_failure_stage"), "code": h.get("last_failure_code"),
                             "detail": h.get("last_failure_detail"), "at": h.get("last_failed_at")},
            "consecutive_failures": h.get("consecutive_failures"), "retry_due_at": h.get("retry_due_at"),
            "fence_moved_streak": h.get("fence_moved_streak"), "s4_outcome": h.get("s4_outcome"),
            "s3": {"backlog": len(s3_backlog), "failed": len(failed_jobs),
                   "live_jobs": [{"id": str(j["id"]), "status": j["status"], "attempts": j["attempts"],
                                  "lease_until": j["lease_until"], "last_error": j["last_error"]} for j in live]},
            "s4": {"backlog": s4_backlog, "selection_seq": fence.selection_seq, "match_pass_id": ms.get(
                "match_pass_id"), "matched_through_selection_seq": through},
            "consequence": {"pending": len(work), "attempts": sum(int(w["attempts"]) for w in work),
                            "oldest_age_seconds": _age(now, oldest),
                            "work": [{"work_id": str(w["id"]), "cause": w["cause"], "attempts": int(w["attempts"]),
                                      "last_outcome": w["last_outcome"],
                                      "age_seconds": _age(now, w["enqueued_at"])} for w in work]},
            "stale_no_work": stale,
            "s3_stale_no_job": stuck,
        }
