"""The bounded environment tick: S3 -> conditional S4 -> consequence drain per selected Site (S4-02d phase 1).

One timer per environment invokes `ScheduleTick.tick()` (phase 2 installs it; this module installs nothing).
A tick:

1. takes the environment claim in `schedule_tick_head` (a second host or an overlapping timer finds it held and
   reports `SKIPPED_CLAIMED`, which never advances the heartbeat); a tick inside its failure back-off returns
   `RETRY_DUE`;
2. runs the `discover` stage child: global `reconcile_all()` (measured) and the persisted inventory;
3. selects active Sites (imported, lifecycle neither `DECOMMISSIONED` nor `ARCHIVED`, with at least one
   `accepted_evidence` row or explicit enrolment; `PLANNED` qualifies) plus every Site with live S3 jobs or pending
   consequence work (reported as `EXCLUDED_WITH_WORK` when it is not otherwise active, never discarded);
4. visits at most `max_sites` of them in (tenant_id, site_id) order after the durable fair cursor, skipping a
   Site inside its schedule-level back-off (`RETRY_DUE`) and deferring the rest to later ticks;
5. per visited Site takes the Site claim (`schedule_site_head`; held -> `SKIPPED_CLAIMED`), runs the `s3`, `s4`
   and `consequence` stage children in that order, each killable at its wall-time bound with server-side
   statement/lock timeouts, records typed outcomes and releases the claim with completion or the first failure
   and its back-off, then advances the cursor;
6. finishes: success and heartbeat on completion; failure and back-off (no heartbeat) when discovery fails.

Every stage runs even after an earlier stage of the same Site failed: S4 leaves non-CURRENT windows unchanged
and the drain is independent, so one failed stage never freezes the Site's other work.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from assetops_backend.scheduling.ports import ScheduleStore

EXCLUDED_LIFECYCLES = frozenset({"DECOMMISSIONED", "ARCHIVED"})
S3_JOB_LEASE_SECONDS = 300  # DispatchAssessmentWorker's lease; the S3 stage bound must stay below it.
# The directory holding the `assetops_backend` package: the stage child imports it from there.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S4_OK = ("MATCHED", "SKIPPED_UNCHANGED_FENCE")


@dataclass(frozen=True)
class TickLimits:
    max_sites: int = 20
    s3_jobs_per_site: int = 10
    consequence_items_per_site: int = 50
    discover_seconds: float = 120
    s3_seconds: float = 120
    s4_seconds: float = 120
    consequence_seconds: float = 60
    tick_seconds: float = 240
    statement_timeout_ms: int = 30_000
    lock_timeout_ms: int = 5_000
    backoff_base_seconds: float = 60
    backoff_cap_seconds: float = 960

    def __post_init__(self) -> None:
        if min(self.max_sites, self.s3_jobs_per_site, self.consequence_items_per_site) < 1:
            raise ValueError("Every per-tick bound is at least 1.")
        if self.s3_seconds >= S3_JOB_LEASE_SECONDS:
            raise ValueError("The S3 stage bound must be shorter than the five-minute S3 job lease.")
        if self.statement_timeout_ms / 1000 >= min(self.discover_seconds, self.s3_seconds, self.s4_seconds,
                                                   self.consequence_seconds):
            raise ValueError("The server statement timeout must be shorter than every stage bound.")

    @property
    def site_lease_seconds(self) -> float:
        return self.s3_seconds + self.s4_seconds + self.consequence_seconds + 60

    @property
    def tick_lease_seconds(self) -> float:
        return self.discover_seconds + self.tick_seconds + self.site_lease_seconds + 60

    def backoff(self, failures: int) -> float:
        return min(self.backoff_base_seconds * (2 ** max(failures, 0)), self.backoff_cap_seconds)


class StageRunner:
    """Starts each stage as a child process (`python -m assetops_backend.scheduling.stages`) with the server-side
    timeouts in `PGOPTIONS`, and kills it at its wall-time bound (typed `TIMEOUT`). `overrides` replaces one
    stage's command (fault injection in tests)."""

    def __init__(self, database_url: str | None, limits: TickLimits,
                 overrides: dict[str, list[str]] | None = None) -> None:
        self.database_url, self.limits, self.overrides = database_url, limits, overrides or {}

    def run(self, stage: str, args: dict[str, Any], seconds: float) -> dict[str, Any]:
        env = dict(os.environ)
        if self.database_url:
            env["DATABASE_URL"] = self.database_url
        env["PYTHONPATH"] = os.pathsep.join(x for x in (_BACKEND_ROOT, env.get("PYTHONPATH")) if x)
        env["PGOPTIONS"] = (f"-c statement_timeout={self.limits.statement_timeout_ms} "
                            f"-c lock_timeout={self.limits.lock_timeout_ms}")
        command = self.overrides.get(stage) or [sys.executable, "-m", "assetops_backend.scheduling.stages", stage]
        started = time.perf_counter()
        try:
            done = subprocess.run([*command, json.dumps(args, default=str)], env=env, cwd=_BACKEND_ROOT,
                                  capture_output=True, text=True, timeout=seconds)
        except subprocess.TimeoutExpired:
            return {"code": "TIMEOUT", "error": f"stage {stage} exceeded {seconds:g} s and was killed",
                    "killed": True, "elapsed_ms": int((time.perf_counter() - started) * 1000)}
        elapsed = int((time.perf_counter() - started) * 1000)
        for line in reversed((done.stdout or "").splitlines()):
            if line.startswith("STAGE_RESULT "):
                return {**json.loads(line[len("STAGE_RESULT "):]), "elapsed_ms": elapsed}
        return {"code": "FAILED", "elapsed_ms": elapsed,
                "error": f"stage {stage} exited {done.returncode} without a result: {(done.stderr or '')[-1500:]}"}


@dataclass
class SiteResult:
    tenant_id: UUID
    site_id: UUID
    site_code: str | None
    reason: str
    result: str = "DEFERRED"
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    failure: tuple[str, str, str] | None = None


@dataclass
class TickReport:
    outcome: str
    environment: str
    token: UUID
    db_now: Any = None
    reconcile_ms: int | None = None
    selected: list[SiteResult] = field(default_factory=list)
    excluded_with_work: list[dict[str, Any]] = field(default_factory=list)
    not_selected: int = 0
    failure: dict[str, Any] | None = None

    def visited(self) -> list[SiteResult]:
        return [s for s in self.selected if s.result not in ("DEFERRED",)]

    def as_json(self) -> dict[str, Any]:
        return json.loads(json.dumps({
            "outcome": self.outcome, "environment": self.environment, "token": self.token, "db_now": self.db_now,
            "reconcile_ms": self.reconcile_ms, "not_selected": self.not_selected, "failure": self.failure,
            "excluded_with_work": self.excluded_with_work,
            "sites": [{"tenant_id": s.tenant_id, "site_id": s.site_id, "site_code": s.site_code,
                       "reason": s.reason, "result": s.result, "failure": s.failure,
                       "stages": {k: {x: v.get(x) for x in ("code", "error", "processed", "deferred", "selected",
                                                            "failed", "backlog", "revision_ids", "elapsed_ms")
                                      if x in v} for k, v in s.stages.items()}}
                      for s in self.selected]}, default=str))


def select_sites(discovered: dict[str, Any]) -> tuple[list[SiteResult], list[dict[str, Any]], int]:
    """Apply the active-Site predicate to the discovered inventory (packet item 1, N4). Returns the selected Sites
    in (tenant_id, site_id) order, the excluded Sites kept for their work, and the count left unselected."""
    work: dict[tuple[UUID, UUID], dict[str, Any]] = {}
    for job in discovered["live_jobs"]:
        key = (UUID(str(job["tenant_id"])), UUID(str(job["site_id"])))
        w = work.setdefault(key, {"live_jobs": [], "pending_work": 0})
        w["live_jobs"].append({"id": str(job["id"]), "status": job["status"], "last_error": job["last_error"]})
    for row in discovered["pending_work_sites"]:
        key = (UUID(str(row["tenant_id"])), UUID(str(row["site_id"])))
        work.setdefault(key, {"live_jobs": [], "pending_work": 0})["pending_work"] = int(row["pending"])
    selected: list[SiteResult] = []
    excluded: list[dict[str, Any]] = []
    not_selected = 0
    seen: set[tuple[UUID, UUID]] = set()
    for site in discovered["inventory"]:
        key = (UUID(str(site["tenant_id"])), UUID(str(site["site_id"])))
        seen.add(key)
        if site["lifecycle"] not in EXCLUDED_LIFECYCLES and (site["has_evidence"] or site["enrolled"]):
            selected.append(SiteResult(*key, site["site_code"], "EVIDENCE" if site["has_evidence"] else "ENROLLED"))
        elif key in work:
            selected.append(SiteResult(*key, site["site_code"], "EXCLUDED_WITH_WORK"))
            excluded.append({"tenant_id": str(key[0]), "site_id": str(key[1]), "site_code": site["site_code"],
                             "lifecycle": site["lifecycle"], **work[key]})
        else:
            not_selected += 1
    for key in sorted(set(work) - seen):  # work of a Site with no import record: still drained, and reported
        selected.append(SiteResult(*key, None, "EXCLUDED_WITH_WORK"))
        excluded.append({"tenant_id": str(key[0]), "site_id": str(key[1]), "site_code": None,
                         "lifecycle": None, **work[key]})
    selected.sort(key=lambda s: (s.tenant_id, s.site_id))
    return selected, excluded, not_selected


def fair_order(sites: list[SiteResult], cursor: tuple[UUID, UUID] | None) -> list[SiteResult]:
    if cursor is None:
        return list(sites)
    after = [s for s in sites if (s.tenant_id, s.site_id) > cursor]
    return after + [s for s in sites if (s.tenant_id, s.site_id) <= cursor]


class ScheduleTick:
    def __init__(self, store: ScheduleStore, runner: StageRunner, limits: TickLimits, *,
                 environment: str = "default", owner: str | None = None) -> None:
        self.store, self.runner, self.limits = store, runner, limits
        self.environment = environment
        self.owner = owner or f"{socket.gethostname()}:{os.getpid()}"

    def tick(self) -> TickReport:
        token = uuid4()
        report = TickReport("FAILED", self.environment, token)
        try:
            claim = self.store.claim_tick(self.environment, token, self.owner, self.limits.tick_lease_seconds)
        except Exception as error:  # noqa: BLE001 - the schedule store itself is down or stalled
            report.failure = {"code": "SCHEDULE_STORE_UNAVAILABLE", "error": f"{type(error).__name__}: {error}"}
            return report
        report.db_now = claim["db_now"]
        if not claim["claimed"]:
            report.outcome = "SKIPPED_CLAIMED"
            return report
        if claim["retry_due_at"] is not None and claim["retry_due_at"] > claim["db_now"]:
            self.store.release_tick(self.environment, token)
            report.outcome = "RETRY_DUE"
            return report
        started = time.monotonic()
        try:
            discovered = self.runner.run("discover", {}, self.limits.discover_seconds)
            if discovered["code"] != "OK":
                report.failure = {"stage": "DISCOVER", **{k: discovered.get(k) for k in ("code", "error")}}
                self.store.fail_tick(self.environment, token, discovered["code"], str(discovered.get("error")),
                                     self.limits.backoff(int(claim["consecutive_failures"])))
                return report
            report.reconcile_ms = discovered.get("reconcile_ms")
            selected, report.excluded_with_work, report.not_selected = select_sites(discovered)
            report.selected = selected
            heads = {(h["tenant_id"], h["site_id"]): h for h in self.store.site_heads()}
            visited = 0
            for site in fair_order(selected, self.store.cursor(self.environment)):
                if visited >= self.limits.max_sites or time.monotonic() - started > self.limits.tick_seconds:
                    break  # bounded: the rest stays DEFERRED for later ticks
                visited += 1
                head = heads.get((site.tenant_id, site.site_id))
                if head and head["retry_due_at"] is not None and head["retry_due_at"] > self.store.db_now():
                    site.result = "RETRY_DUE"
                else:
                    self._site(site, token)
                self.store.set_cursor(self.environment, site.tenant_id, site.site_id)
            deferred = sum(1 for s in selected if s.result == "DEFERRED")
            if not self.store.finish_tick(self.environment, token, sites_selected=len(selected),
                                          sites_processed=visited, sites_deferred=deferred,
                                          excluded_with_work=len(report.excluded_with_work),
                                          reconcile_ms=report.reconcile_ms):
                report.outcome = "CLAIM_LOST"
                return report
            report.outcome = "COMPLETED"
            return report
        except Exception as error:  # noqa: BLE001 - recorded as a typed tick failure with back-off
            from assetops_backend.scheduling.stages import classify

            code = classify(error)
            report.failure = {"code": code, "error": f"{type(error).__name__}: {error}"[:2000]}
            try:
                self.store.fail_tick(self.environment, token, code, report.failure["error"],
                                     self.limits.backoff(int(claim["consecutive_failures"])))
            except Exception:  # noqa: BLE001 - the claim then expires by its lease
                pass
            return report

    def _site(self, site: SiteResult, token: UUID) -> None:
        t, s = site.tenant_id, site.site_id
        claim = self.store.claim_site(t, s, token, self.owner, self.limits.site_lease_seconds)
        if not claim["claimed"]:
            site.result = "SKIPPED_CLAIMED"
            return
        ids = {"tenant_id": str(t), "site_id": str(s)}
        failure: tuple[str, str, str] | None = None

        self.store.set_stage(t, s, token, "S3")
        r3 = self.runner.run("s3", {**ids, "limit": self.limits.s3_jobs_per_site}, self.limits.s3_seconds)
        site.stages["s3"] = r3
        if r3["code"] == "OK":
            self.store.record_s3(t, s, token, int(r3["processed"]), int(r3["deferred"]))
        else:
            failure = ("S3", r3["code"], str(r3.get("error")))

        self.store.set_stage(t, s, token, "S4")
        r4 = self.runner.run("s4", {**ids, "matched_fence": claim["matched_fence"],
                                    "matched_version": claim["matched_version"]}, self.limits.s4_seconds)
        site.stages["s4"] = r4
        if r4["code"] == "MATCHED":
            self.store.record_s4(t, s, token, "MATCHED", r4["fence"], r4["version"])
        else:
            self.store.record_s4(t, s, token, r4["code"])
        if r4["code"] not in S4_OK:
            failure = failure or ("S4", r4["code"], str(r4.get("error")))

        self.store.set_stage(t, s, token, "CONSEQUENCE")
        now = self.store.db_now()
        rc = self.runner.run("consequence", {**ids, "limit": self.limits.consequence_items_per_site,
                                             "now": now.isoformat()}, self.limits.consequence_seconds)
        site.stages["consequence"] = rc
        if rc["code"] == "OK":
            self.store.record_consequence(t, s, token, int(rc["selected"]), int(rc["deferred"]))
        else:
            failure = failure or ("CONSEQUENCE", rc["code"], str(rc.get("error")))

        released = self.store.release_site(t, s, token, failure=failure,
                                           backoff_seconds=self.limits.backoff(int(claim["consecutive_failures"])))
        site.failure = failure
        site.result = "CLAIM_LOST" if not released else ("FAILED" if failure else "COMPLETED")
