"""S4-02d phase 3: the automatic late-power walkthrough (tasks/S4-02d-analytic-finding-worker-schedule.md).

Reuses the S4-02c walkthrough (`tools/s402c_late_power_walkthrough.py`: the same private tree from git HEAD, the
same isolated-database deployment shape, the `P02-power-late` SOURCE_ORDER variant and the same consequence read)
but drives every analytic, Finding and consequence step by full schedule ticks
(`python -m assetops_backend.scheduling.run tick`). The tool never runs `process-jobs`, `match-findings` or
`recompute_consequences run`; every subprocess it starts is written to a command log that is grepped at the end
(W4/N6). No timer is installed: each tick is an explicit invocation in the walkthrough database.

    .venv/Scripts/python.exe tools/s402d_tick_walkthrough.py run    # build, walk, write evidence + command log
    .venv/Scripts/python.exe tools/s402d_tick_walkthrough.py drop   # drop the database and work folder

Sequence (every read is a fresh process reading Postgres):
 0. SYSTEM price v1 (configuration, not a Leg B step).
 1. First delivery without the withheld mean; tick 1 builds S3, matches r1 and drains its consequence; tick 2 is
    idle (heartbeat advances, S4 skipped on an unchanged fence, no new pass row).
 2. The withheld mean is accepted late: the exact accepted ID, r1's EVIDENCE_ACCEPTED work, and the pre-tick
    `STALE / TECHNICAL_INPUT_CHANGED` read with that work queued; the seam is not CURRENT.
 3. Tick 3 (first post-release): S3 rebuilds, S4 appends r2 citing the late ID, the drain records r1's
    EVIDENCE_ACCEPTED attempt as the typed `FINDING_REVISION_SUPERSEDED` no-op and drains r2 to CURRENT PRICED.
    The same-revision `POWER_NOT_IN_ASSESSMENT_INPUTS` Leg A state is S4-02c's evidence and is not required here.
    If tick 3 does not complete S3 and S4, the tool reports what happened instead of asserting the r2 path (N6).
 4. Tick 4 replays nothing; then a stopped worker (tight DB-time thresholds) blocks the seam and tick 5 recovers.
The seam is asserted only for its upstream state; S5 money eligibility belongs to F1 (M5) and is recorded only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s402c_late_power_walkthrough as lw  # noqa: E402

s4, s2 = lw.s4, lw.s2
DB = "assetops_s402d3walk"
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s402d3-tick-walk"
EVIDENCE_NAME = "s402d-tick-walkthrough.json"
COMMAND_LOG = "s402d-tick-walkthrough-commands.log"
ENV = "walkthrough"
# A hand-run Leg B command, by CLI or by its Python entry point in a `-c` script (W4, N6).
HAND_RUN = re.compile(r"process-jobs|match-findings|recompute_consequences run|run_pending\(|FindingMatcher|"
                      r"build_finding_matcher|ConsequenceRecomputeWorker|build_consequence_recompute")

STOPPED = r'''
import json, sys, time
from datetime import datetime
from uuid import UUID
from assetops_backend.config import database_url
from assetops_backend.scheduling.composition import build_schedule_health, build_upstream_currentness
from assetops_backend.scheduling.health import HealthThresholds
t, s, w0, w1, env = sys.argv[1:6]
th = HealthThresholds(stop_after_seconds=1, site_stop_after_seconds=1)
time.sleep(2.5)
h, u = build_schedule_health(database_url(), th), build_upstream_currentness(database_url(), th)
try:
    rep = h.report(env)
    seam = u.window(UUID(t), UUID(s), datetime.fromisoformat(w0), datetime.fromisoformat(w1), env)
finally:
    h.dispose(); u.dispose()
site = next(x for x in rep["sites"] if x["site_id"] == s)
print(json.dumps({"thresholds": th.__dict__, "health_state": rep["state"],
                  "tick_alarms": [a["code"] for a in rep["tick"]["alarms"]], "site_state": site["state"],
                  "site_alarms": [a["code"] for a in site["alarms"]], "seam_eligibility": seam["eligibility"],
                  "seam_s3_jobs": len(seam["s3_jobs"]), "seam_consequence_work": len(seam["consequence_work"])},
                 default=str))
'''


class TickWalk(lw.LateWalk):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.cmdlog: list[str] = []
        self.out["environment"] = ENV
        self.out["ticks"] = []

    # Every subprocess this tool starts goes through `py` or `start`; both are logged verbatim.
    def py(self, *argv: str, cwd: Path | None = None, check: bool = True):
        self.cmdlog.append(f"{time.strftime('%H:%M:%S')} py {' '.join(argv)}")
        return super().py(*argv, cwd=cwd, check=check)

    def start(self, name: str, argv: list[str], cwd: Path, ready: str, env=None, timeout: float = 90) -> None:
        self.cmdlog.append(f"{time.strftime('%H:%M:%S')} start {name} {' '.join(argv)}")
        return super().start(name, argv, cwd, ready, env=env, timeout=timeout)

    # ------------------------------------------------------------------ schedule commands
    def sched(self, *argv: str) -> tuple[int, Any]:
        done = self.backend("-m", "assetops_backend.scheduling.run", *argv, check=False)
        lines = [x for x in done.stdout.splitlines() if x.strip().startswith("{")]
        if not lines:
            raise SystemExit(f"FAILED: scheduling.run {' '.join(argv)} exit {done.returncode}\n{done.stderr[-2000:]}")
        return done.returncode, json.loads(lines[-1])

    def window(self) -> tuple[str, str]:
        day = self.case["day"]
        lo = s4.instant(f"{day}T00:00:00Z")
        from datetime import timedelta

        return lo.isoformat(), (lo + timedelta(days=1)).isoformat()

    def seam(self, label: str) -> dict[str, Any]:
        w0, w1 = self.window()
        _, body = self.sched("upstream", "--tenant-id", self.identity["tenant_id"], "--site-id",
                             self.identity["site_id"], "--start", w0, "--end", w1, "--environment", ENV)
        e = body["eligibility"]
        day = (body.get("days") or [{}])[0]
        rec = {"label": label, "db_now": body["db_now"], "eligibility": e, "s3_status": day.get("s3_status"),
               "s3_status_reasons": day.get("s3_status_reasons"), "limitations": day.get("limitations"),
               "watermark": day.get("watermark"), "run_id": day.get("run_id"),
               "s3_jobs": [{k: j.get(k) for k in ("id", "status", "attempts", "last_error")} for j in body["s3_jobs"]],
               "match": [m for m in body["match"] if m.get("window_selection_seq") is not None],
               "findings": [{k: f.get(k) for k in ("finding_id", "finding_revision_id", "consequence_state",
                                                    "consequence_reasons", "head_consequence_revision_id")}
                            for f in body["findings"]],
               "consequence_work": [w.get("work_id") for w in body["consequence_work"]],
               "schedule": {k: (body.get("schedule") or {}).get(k) for k in (
                   "state", "heartbeat_at", "heartbeat_age_seconds", "site_last_completed_at")}}
        say(f"  seam {label}: {e['status']} stage={e['stage']} reasons={e['reasons']} s3={rec['s3_status']} "
            f"limits={[x.get('code', x) if isinstance(x, dict) else x for x in rec['limitations'] or []]}")
        self.out.setdefault("seam", []).append(rec)
        return rec

    def health(self, label: str) -> dict[str, Any]:
        code, body = self.sched("health", "--environment", ENV)
        site = next((x for x in body["sites"] if x["site_id"] == self.identity["site_id"]), {})
        rec = {"label": label, "exit": code, "state": body["state"], "db_now": body["db_now"],
               "tick": {k: body["tick"].get(k) for k in ("state", "heartbeat_at", "heartbeat_age_seconds")},
               "tick_alarms": [a["code"] for a in body["tick"]["alarms"]],
               "site_state": site.get("state"), "site_alarms": [a["code"] for a in site.get("alarms", [])],
               "backlog": {"s3": (site.get("s3") or {}).get("backlog"), "s4": (site.get("s4") or {}).get("backlog"),
                           "consequence": (site.get("consequence") or {}).get("pending"),
                           "match_pass_id": (site.get("s4") or {}).get("match_pass_id"),
                           "selection_seq": (site.get("s4") or {}).get("selection_seq")}}
        say(f"  health {label}: {rec['state']} site={rec['site_state']} alarms={rec['tick_alarms'] + rec['site_alarms']}"
            f" backlog={rec['backlog']} heartbeat={rec['tick']['heartbeat_at']}")
        self.out.setdefault("health", []).append(rec)
        return rec

    def tick(self, label: str) -> dict[str, Any]:
        code, body = self.sched("tick", "--environment", ENV, "--max-sites", "5", "--s3-jobs", "10",
                                "--consequence-items", "100")
        site = next((x for x in body["sites"] if x["site_id"] == self.identity["site_id"]), None)
        rec = {"label": label, "exit": code, "outcome": body["outcome"], "db_now": body["db_now"],
               "reconcile_ms": body["reconcile_ms"], "failure": body["failure"], "site": site}
        stages = {k: {x: v.get(x) for x in ("code", "processed", "deferred", "selected", "failed", "backlog",
                                            "revision_ids") if x in v} for k, v in (site or {}).get("stages", {}).items()}
        say(f"  tick {label}: exit {code} {body['outcome']} site={None if site is None else site['result']} "
            f"stages={json.dumps(stages)}")
        self.out["ticks"].append(rec)
        return rec

    def passes(self) -> list[tuple]:
        return [tuple(r) for r in self.pg(
            "SELECT id::text, selection_seq, revisions_written, completed_at::text FROM finding_match_pass "
            "WHERE site_id = %s ORDER BY completed_at", self.identity["site_id"])]

    def jobs(self) -> list[dict[str, Any]]:
        keys = ("id", "status", "window_start", "window_end", "attempts", "last_error")
        return [dict(zip(keys, r)) for r in self.pg(
            "SELECT id::text, status, window_start::text, window_end::text, attempts, last_error FROM recompute_job "
            "WHERE site_id = %s ORDER BY created_at", self.identity["site_id"])]

    def selections(self) -> list[tuple]:
        return [tuple(r) for r in self.pg(
            "SELECT seq, run_id::text, window_start::text FROM analytic_run_selection WHERE site_id = %s "
            "ORDER BY seq", self.identity["site_id"])]

    def snapshot(self, label: str) -> None:
        self.out.setdefault("snapshots", []).append({"label": label, "jobs": self.jobs(), "selections":
                                                     self.selections(), "match_passes": self.passes()})

    # ------------------------------------------------------------------ walk
    def walk(self) -> None:
        o = self.out
        step("0. SYSTEM diesel price v1 (configuration before both legs)")
        done = self.backend("-m", "assetops_backend.publish_assumption", "fixture", "--site", lw.SITE, "--file",
                            str(Path("conversions") / "demo-diesel-price-publications.json"), "--step", "v1")
        o["price_v1"] = json.loads(done.stdout.strip().splitlines()[-1])
        say(f"  price v1: revision {o['price_v1']['revision_id']}")

        step(f"1. {self.case['case_id']}: first delivery without [07:00, 07:05); schedule ticks only")
        first = {k: v for k, v in self.case.items() if k != "late"}
        first["steps"] = [st for st in self.case["steps"] if st["do"] == "deliver_power"]
        self.run_power_case(first)
        record = self.cases[-1]
        o["first_delivery"] = {"batch_ids": record["batch_ids"], "evidence_count": record["evidence_count"],
                               "evidence_id_sha256": record["evidence_id_sha256"],
                               "generator_power_ids": len(self.accepted(record["batch_ids"]))}
        self.snapshot("after first delivery, before any tick")
        self.seam("before tick 1")
        self.health("before tick 1")
        t1 = self.tick("1: first delivery")
        self.snapshot("after tick 1")
        stages = (t1["site"] or {}).get("stages", {})
        self.expect("tick 1 completed S3, matched S4 and drained the Site", t1["outcome"] == "COMPLETED"
                    and (t1["site"] or {}).get("result") == "COMPLETED" and stages.get("s4", {}).get("code") == "MATCHED",
                    t1)
        fids = [r[0] for r in self.pg("SELECT id::text FROM finding WHERE site_id = %s", self.identity["site_id"])]
        if not self.expect("tick 1 created exactly one Finding", len(fids) == 1, fids):
            o["stopped"] = "tick 1 did not create the Finding; nothing further is meaningful"
            return
        (fid,) = fids
        revs = self.revisions(fid)
        r1 = revs[-1][0]
        o["finding_id"], o["r1"] = fid, {"id": r1, "revision_no": revs[-1][1], "lifecycle": revs[-1][2],
                                         "transition": revs[-1][3]}
        o["r1"]["analytic_run_ids"] = [x[0] for x in self.pg(
            "SELECT DISTINCT analytic_run_id::text FROM finding_revision_assessment WHERE finding_revision_id = %s",
            r1)]
        pre = self.read("pre-late (r1)", fid, r1)
        o["pre_late_s3_result"] = {"quantity": pre["derived_now"]["quantity"], "reason": pre["derived_now"]["reason"],
                                   "candidate_spans": pre["candidate_spans"]}
        if not self.expect("N5 precondition: [07:00, 07:05) lies inside r1's observed Candidate time",
                           pre["withheld_inside_candidate"]
                           and pre["derived_now"]["reason"] != "CANDIDATE_SPAN_UNVERIFIED",
                           {"candidate_spans": pre["candidate_spans"], "reason": pre["derived_now"]["reason"]}):
            o["stopped"] = "N5 precondition failed; stopped without changing the fixture."
            return
        self.expect("pre-late: r1's consequence 1 is CURRENT after tick 1", pre["currentness"] == "CURRENT"
                    and (pre["consequence"] or {}).get("revision_no") == 1, pre["consequence"])
        s1 = self.seam("after tick 1")
        self.expect("after tick 1 the seam reads its true upstream state CURRENT (no live job, matched, drained)",
                    s1["eligibility"]["status"] == "CURRENT" and not s1["s3_jobs"], s1["eligibility"])
        h1 = self.health("after tick 1")
        passes1 = self.passes()
        t2 = self.tick("2: idle")
        h2 = self.health("after idle tick 2")
        self.expect("idle tick 2: S4 skipped on an unchanged fence, no new pass row, heartbeat advanced",
                    ((t2["site"] or {}).get("stages", {}).get("s4") or {}).get("code") == "SKIPPED_UNCHANGED_FENCE"
                    and self.passes() == passes1 and str(h2["tick"]["heartbeat_at"]) > str(h1["tick"]["heartbeat_at"]),
                    {"s4": ((t2["site"] or {}).get("stages", {}).get("s4")), "passes": len(self.passes())})

        step("2. The withheld mean is accepted late (same registered credential, TLS); no tick yet")
        late_batches = self.post(self.power_envelopes(self.late, s4.EPOCH_PREFIX + self.late["epoch"]))
        (late_id,) = self.accepted(late_batches)
        o["late"] = {"batch_ids": late_batches, "accepted_evidence_id": late_id,
                     "source_sequence": list(self.last_sequences)}
        say(f"  late accepted evidence {late_id}")
        ev = [w for w in self.work_rows() if w["cause"] == "EVIDENCE_ACCEPTED"]
        o["late_work_before_tick"] = ev
        self.expect("exactly one EVIDENCE_ACCEPTED work row, for the late ID and r1, not yet attempted",
                    len(ev) == 1 and ev[0]["accepted_evidence_id"] == late_id and ev[0]["finding_revision_id"] == r1
                    and ev[0]["attempts"] == [], ev)
        self.snapshot("after late acceptance, before tick 3")
        a0 = self.read("late, before tick 3 (r1)", fid, r1, late_id)
        self.expect("pre-tick: STALE / TECHNICAL_INPUT_CHANGED with the late mean's work queued",
                    a0["currentness"] == "STALE" and "TECHNICAL_INPUT_CHANGED" in a0["reasons"]
                    and [w["work_id"] for w in a0["pending_work"]] == [ev[0]["work_id"]] if ev else False,
                    {"reasons": a0["reasons"], "pending": a0["pending_work"]})
        sa = self.seam("late, before tick 3")
        self.expect("pre-tick: the seam is not CURRENT while the late work is queued",
                    sa["eligibility"]["status"] != "CURRENT", sa["eligibility"])
        self.health("late, before tick 3")

        step("3. Tick 3: the first post-release tick (S3 -> S4 -> consequence drain)")
        t3 = self.tick("3: first post-release")
        self.snapshot("after tick 3")
        st = (t3["site"] or {}).get("stages", {})
        s3_done = (st.get("s3") or {}).get("code") in (None, "OK", "COMPLETED") and not (st.get("s3") or {}).get(
            "deferred") and not [j for j in self.jobs() if j["status"] in ("PENDING", "LEASED")]
        s4_done = (st.get("s4") or {}).get("code") == "MATCHED"
        o["tick3_completed_s3_and_s4"] = bool(s3_done and s4_done)
        revs = self.revisions(fid)
        if not (s3_done and s4_done) or revs[-1][0] == r1:
            o["tick3_outcome_reported"] = {"stages": st, "revisions": revs, "jobs": self.jobs()}
            self.expect("tick 3 completed S3 and S4 (otherwise the actual state is reported, not the r2 path)",
                        False, o["tick3_outcome_reported"])
            self.read("tick 3 incomplete (r1)", fid, r1, late_id)
            self.seam("tick 3 incomplete")
            return
        r2 = revs[-1][0]
        o["r2"] = {"id": r2, "revision_no": revs[-1][1], "lifecycle": revs[-1][2], "transition": revs[-1][3],
                   "analytic_run_ids": [x[0] for x in self.pg(
                       "SELECT DISTINCT analytic_run_id::text FROM finding_revision_assessment "
                       "WHERE finding_revision_id = %s", r2)]}
        say(f"  FindingRevisions: {[(r[1], r[2], r[3]) for r in revs]}")
        self.expect("tick 3 appended a revised FindingRevision r2", revs[-1][1] == o["r1"]["revision_no"] + 1, revs)
        cites = self.pg("SELECT count(*) FROM finding_revision_assessment a JOIN analytic_run_evidence e ON "
                        "e.run_id = a.analytic_run_id WHERE a.finding_revision_id = %s AND a.scope = 'INTERVAL' "
                        "AND e.evidence_id = %s", r2, late_id)[0][0]
        self.expect("r2 cites the late ID (its analytic run includes it)", cites > 0, cites)
        work = self.work_rows()
        o["work_after_tick3"] = work
        ea = next(w for w in work if w["work_id"] == ev[0]["work_id"])
        self.expect("r1's EVIDENCE_ACCEPTED attempt is the typed FINDING_REVISION_SUPERSEDED no-op",
                    [(a["outcome"], a["no_op_reason"], a["consequence_revision_ids"]) for a in ea["attempts"]]
                    in ([("SUCCEEDED", "FINDING_REVISION_SUPERSEDED", [])],
                        [("SUCCEEDED", "FINDING_REVISION_SUPERSEDED", None)]), ea["attempts"])
        fra = [w for w in work if w["cause"] == "FINDING_REVISION_APPENDED" and w["finding_revision_id"] == r2]
        self.expect("r2's FINDING_REVISION_APPENDED work SUCCEEDED in tick 3", len(fra) == 1 and [
            a["outcome"] for a in fra[0]["attempts"]] == ["SUCCEEDED"], fra)
        b1 = self.read("after tick 3 (r2)", fid, r2, late_id)
        c = b1["consequence"] or {}
        self.expect("r2's consequence is CURRENT PRICED by price v1", b1["currentness"] == "CURRENT"
                    and c.get("state") == "PRICED" and c.get("price_revision_id") == o["price_v1"]["revision_id"], c)
        self.expect("r2 counts the late mean (late ID in run inputs and examined)",
                    b1["derived_now"]["late_in_run_inputs"] and b1["derived_now"]["late_examined"], b1["derived_now"])
        o["s5_money_eligible_recorded_only"] = b1["s5_money_eligible"]  # M5: F1 owns money eligibility
        hr1 = self.read("r1 after tick 3 (historical)", fid, r1, late_id)
        self.expect("r1 is HISTORICAL and keeps consequence 1 only (no same-revision Leg A append in this proof)",
                    hr1["currentness"] == "HISTORICAL" and len(hr1["history"]) == 1, hr1["history"])
        s3 = self.seam("after tick 3")
        self.expect("after tick 3 the seam is CURRENT only now that the work completed (no live job or work)",
                    s3["eligibility"]["status"] == "CURRENT" and not s3["s3_jobs"] and not s3["consequence_work"],
                    s3["eligibility"])
        self.expect("the seam's selected run is r2's run", s3["run_id"] in o["r2"]["analytic_run_ids"],
                    {"seam_run": s3["run_id"], "r2_runs": o["r2"]["analytic_run_ids"]})
        o["s3_limits_after_tick3"] = {"status": s3["s3_status"], "reasons": s3["s3_status_reasons"],
                                      "limitations": s3["limitations"]}
        self.health("after tick 3")

        step("4. Replay, stopped worker and recovery")
        before = (self.passes(), len(o["work_after_tick3"]), self.pg(
            "SELECT count(*) FROM financial_consequence_revision WHERE finding_id = %s", fid)[0][0])
        t4 = self.tick("4: replay")
        after = (self.passes(), len(self.work_rows()), self.pg(
            "SELECT count(*) FROM financial_consequence_revision WHERE finding_id = %s", fid)[0][0])
        self.expect("replay tick 4 appends no pass, work or consequence revision", before == after
                    and ((t4["site"] or {}).get("stages", {}).get("s4") or {}).get("code") == "SKIPPED_UNCHANGED_FENCE",
                    {"before": before, "after": after})
        w0, w1 = self.window()
        stopped = json.loads(self.py("-c", STOPPED, self.identity["tenant_id"], self.identity["site_id"], w0, w1, ENV,
                                     cwd=self.tree / "backend").stdout.strip().splitlines()[-1])
        o["stopped_worker"] = stopped
        say(f"  stopped worker (tight DB-time thresholds): {json.dumps(stopped)}")
        self.expect("stopped worker: health STOPPED and the seam blocks CURRENT with empty queues",
                    stopped["health_state"] == "STOPPED" and stopped["seam_eligibility"]["status"] != "CURRENT"
                    and "SCHEDULE_STOPPED" in stopped["seam_eligibility"]["reasons"]
                    and stopped["seam_s3_jobs"] == 0 and stopped["seam_consequence_work"] == 0, stopped)
        self.tick("5: recovery")
        s5 = self.seam("after recovery tick 5")
        self.expect("a completed tick recovers the seam to CURRENT", s5["eligibility"]["status"] == "CURRENT",
                    s5["eligibility"])
        self.health("after recovery tick 5")
        dup = self.pg("SELECT count(*) FROM (SELECT finding_revision_id, consequence_basis_sha256 FROM "
                      "financial_consequence_revision GROUP BY 1, 2 HAVING count(*) > 1) x")[0][0]
        self.expect("no duplicate consequence basis", dup == 0, dup)
        o["consequences"] = [dict(zip(("id", "finding_revision_id", "revision_no", "state", "reason"), r)) for r in
                             self.pg("SELECT id::text, finding_revision_id::text, revision_no, state, "
                                     "coalesce(quantity_reason, price_reason) FROM financial_consequence_revision "
                                     "WHERE finding_id = %s ORDER BY recorded_at", fid)]
        o["work_final"] = self.work_rows()

    def no_hand_run(self, path: Path) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        hits = [x for x in lines if HAND_RUN.search(x)]
        ticks = [x for x in lines if "assetops_backend.scheduling.run tick" in x]
        self.out["command_log"] = {"path": str(path), "lines": len(lines), "tick_invocations": len(ticks),
                                   "hand_run_hits": hits}
        self.expect("command log: no hand-run process-jobs / match-findings / recompute_consequences run "
                    "(nor their Python entry points); every step was a schedule tick",
                    not hits and len(ticks) >= 5, {"hits": hits, "ticks": len(ticks)})

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            self.walk()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
        log = Path(self.args_work) / COMMAND_LOG
        log.write_text("\n".join(self.cmdlog) + "\n", encoding="utf-8")
        self.no_hand_run(log)
        self.out["failures"] = list(self.failures)
        path = Path(self.args_work) / EVIDENCE_NAME
        path.write_text(json.dumps(self.out, indent=2, default=str), encoding="utf-8")
        say(f"Evidence: {path}; command log: {log} ({len(self.failures)} failed checks)")


def say(text: str) -> None:
    s4.say(text)


def step(text: str) -> None:
    s4.step(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s402d_tick_walkthrough.py")
    parser.add_argument("command", choices=("run", "drop"))
    parser.add_argument("--work", default=str(DEFAULT_WORK))
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--tls-port", type=int, default=8928)
    parser.add_argument("--http-port", type=int, default=8929)
    parser.add_argument("--cadence-seconds", type=int, default=60)
    parser.add_argument("--db", default=DB, help="own database (dropped and recreated by run)")
    args = parser.parse_args(argv)
    if not args.db.startswith("assetops_s402d3") or not args.db.replace("_", "").isalnum():
        raise SystemExit(f"Refusing database {args.db!r}: use an assetops_s402d3* database of its own.")
    s2.DEMO_DB = args.db
    if args.command == "drop":
        import psycopg

        admin = s2.PG_ADMIN.format(pw=os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev"),
                                   port=os.environ.get("ASSETOPS_PG_PORT", "55432"))
        with psycopg.connect(admin, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {args.db} WITH (FORCE)")
        print(f"dropped {args.db}")
        work = Path(args.work)
        if work.exists() and work.name.startswith("s402d3"):
            shutil.rmtree(work)
            print(f"removed {work}")
        return 0
    walk = TickWalk(args)
    walk.args_work = args.work
    walk.run()
    return 1 if walk.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
