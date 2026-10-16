"""S4-02c phase 3: the two-leg late-power consequence walkthrough (tasks/S4-02c-evidence-consequence-work.md).

Runs the authored variant `backend/conversions/s4-power-late-demo-cases-v1.json` (`P02-power-late`, derived from
S4-02b's P01-power with the 20 kW mean [07:00, 07:05) withheld) in its OWN database through the same deployment
shape as `tools/s402b_power_cases.py`: a private code tree from git HEAD, migrations to head, the KOBO-001 import
and bindings, the registered gateway credential, and authored Batch V2 envelopes posted over TLS to
`POST /api/ingestion/batches`. No other spec is modified and no other database is touched.

    .venv/Scripts/python.exe tools/s402c_late_power_walkthrough.py run    # build, walk both legs, write evidence
    .venv/Scripts/python.exe tools/s402c_late_power_walkthrough.py drop   # drop the database and work folder

Sequence (every read is a fresh process reading Postgres, i.e. a reload):
 0. SYSTEM price v1 published first (re-review N2), so Leg B can be PRICED; its revision ID is recorded.
 1. First delivery without the withheld mean, S3 `process-jobs`, S4 `match-findings` -> FindingRevision r1; the
    consequence runner (`recompute_consequences run --tenant demo --site KOBO-001`) appends consequence 1.
    N5 precondition: [07:00, 07:05) must lie inside r1's observed Candidate time; otherwise the tool STOPS.
 2. Leg A: the withheld mean is accepted late. Before the drain: STALE / TECHNICAL_INPUT_CHANGED with its
    EVIDENCE_ACCEPTED work ID (bridge STALE_QUEUED). The runner drains it: the same r1 gains consequence 2,
    CURRENT QUANTITY_UNAVAILABLE / POWER_NOT_IN_ASSESSMENT_INPUTS; consequence 1 retained; not S5-eligible.
 3. Leg B: `process-jobs` + `match-findings` append a revised FindingRevision r2 whose analytic run includes the
    late ID; its FINDING_REVISION_APPENDED work drains to CURRENT PRICED (S5-eligible by the money predicate).
The wrong-asset no-op ("unrelated accepted input", re-review N7) is NOT exercised here: this Site binds one
generator, so it is proved by `backend/tests/test_s4_evidence_drain_postgres.py`, not by this fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s402b_power_cases as p  # noqa: E402

s4, s2 = p.s4, p.s2
DB = "assetops_s402c3walk"
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s402c3-late-power"
LATE_SPEC_PATH = "backend/conversions/s4-power-late-demo-cases-v1.json"
EVIDENCE_NAME = "s402c-late-power-walkthrough.json"
SITE = "KOBO-001"

# Runs in the private tree (fresh process): the exact consequence read, the bridge summary, and what the exact
# persisted inputs give now (examined IDs, Candidate time, run inputs). source_open=True: the Performance
# source gate is a file-backed comparison outside this slice; the read service is the same one the API uses.
READ = r'''
import hashlib, json, sys
from uuid import UUID
from assetops_backend.config import database_url
from assetops_backend.financials import fuel_cost as fc
from assetops_backend.financials.composition import build_consequence_read_service, build_consequence_store
from assetops_backend.finding_api import REASONS, bridge_consequence
t, s, f, r, latest, w0, w1, late = sys.argv[1:9]
url = database_url()
res = build_consequence_read_service(url).read(UUID(t), UUID(s), UUID(f), UUID(r),
                                                 finding_revision_is_latest=latest == "1", source_open=True)
fi = build_consequence_store(url).load_input(UUID(t), UUID(s), UUID(f), UUID(r))
q = fc.quantify(fi)
spans = fc.merge([(x.start, x.end) for x in fi.candidate_spans if x.start < x.end])
from datetime import datetime
lo, hi = (datetime.fromisoformat(x.replace("Z", "+00:00")) for x in (w0, w1))
runs = frozenset().union(*(a.run_evidence_ids for a in fi.assessments if a.scope == "INTERVAL"))
b = bridge_consequence(res)
key = next((k for k, v in REASONS.items() if v == b["reason"]), None)
cur, c = res["currentness"], res["consequence"]
ex = sorted(q.examined_evidence_ids)
print(json.dumps({
    "currentness": cur["state"], "reasons": cur["reasons"],
    "pending_work": [{"work_id": w["work_id"], "cause": w["cause"], "accepted_evidence_id": w["accepted_evidence_id"],
                      "finding_revision_id": w["finding_revision_id"]} for w in cur["pending_work"]],
    "head_consequence_revision_id": res["consequence_selection"]["head_consequence_revision_id"],
    "consequence": None if c is None else {
        "id": c["id"], "revision_no": c["revision_no"], "state": c["state"], "quantity": c["quantity"]["state"],
        "quantity_reason": c["quantity"]["reason"], "quantity_high": c["quantity"]["high"],
        "price_state": c["price"]["state"], "price_reason": c["price"]["reason"],
        "price_revision_id": c["price"]["revision_id"], "amount_high": c["amount"]["high"],
        "display_amount_high": (c["display"] or {}).get("amount_high"),
        "technical_input_sha256": c["digests"]["technical_input_sha256"],
        "consequence_basis_sha256": c["digests"]["consequence_basis_sha256"],
        "counted_power_evidence": len(c["lineage"]["evidence_ids"]),
        "counted_power_evidence_sha256": hashlib.sha256(",".join(sorted(c["lineage"]["evidence_ids"])).encode()).hexdigest(),
        "analytic_run_ids": sorted({a["analytic_run_id"] for a in c["lineage"]["assessments"]})},
    "history": [[h["id"], h["revision_no"], h["state"], h["quantity"]["reason"] or h["price"]["reason"]]
                for h in res["history"]["revisions"]],
    "bridge": {"state": b["state"], "reason_key": key, "recalculation_queued": b["recalculation_queued"],
               "recorded_consequence_revision_id": b.get("recorded_consequence_revision_id"),
               "amount": b["amount"], "currency": b["currency"], "currentness_reasons": b["currentness_reasons"]},
    # LR-01: the shared money gate (money-eligibility-1) is part of S5 eligibility; the API gates on it as well.
    "money_eligibility": {k: res["money_eligibility"].get(k) for k in (
        "state", "latest_finding_revision_id", "end_reason", "pending_reasons", "series_limits", "windows",
        "head_consequence_revision_id")},
    "current_amount_shown": cur["current_amount_shown"],
    "presented_as_current": None if c is None else c.get("presented_as_current"),
    "s5_money_eligible": cur["state"] == "CURRENT" and c is not None and c["state"] == "PRICED" and b["amount"] is not None
                         and res["money_eligibility"]["state"] == "ELIGIBLE",
    "derived_now": {"quantity": q.state, "reason": q.reason, "examined_count": len(ex),
                    "examined_sha256": hashlib.sha256(",".join(ex).encode()).hexdigest(),
                    "late_examined": late in ex, "late_in_run_inputs": late in runs,
                    "run_input_count": len(runs)},
    "candidate_spans": [[x[0].isoformat(), x[1].isoformat()] for x in spans],
    "withheld_inside_candidate": any(a <= lo and hi <= z for a, z in spans),
}))
'''


class LateWalk(p.PowerCases):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.power_spec = json.loads((s2.REPO / LATE_SPEC_PATH).read_text(encoding="utf-8"))
        self.case = self.power_spec["cases"][0]
        self.late = self.case["late"]
        self.out: dict[str, Any] = {"spec": self.power_spec["label"], "case_id": self.case["case_id"],
                                    "database": args.db, "commands": [], "checks": []}

    def power_envelopes(self, step: dict[str, Any], epoch: str) -> list[tuple[str, str]]:
        """The S4-02b envelopes, but numbered by the spec's SOURCE_ORDER rule: each mean's sequence is its
        position in source-time order among ALL the case's means (on-time and late), so the late mean fills the
        gap the first delivery left instead of being appended after the last sequence."""
        from datetime import timedelta

        mins = self.power_spec["power_rules"]["mean_minutes"]
        ends = []
        blocks = [b for st in self.case["steps"] if st["do"] == "deliver_power" for b in st["means"]]
        for block in blocks + self.late["means"]:
            end = s4.instant(block["first_end"])
            while end <= s4.instant(block["last_end"]):
                ends.append(end)
                end += timedelta(minutes=mins)
        order = {e: n for n, e in enumerate(sorted(ends), start=1)}
        out = super().power_envelopes(step, epoch)  # S4-02b envelopes; only the sequence is renumbered
        import dataclasses

        from assetops_contracts.source_envelope_v3 import (canonical_envelope_v3_text,
                                                           parse_canonical_envelope_v3_text,
                                                           v3_message_id)

        fixed, self.last_sequences = [], []
        for device, text_ in out:
            env = parse_canonical_envelope_v3_text(text_)
            seq = order[s4.instant(env.interval_end)]
            env = dataclasses.replace(env, sequence=seq, message_id=v3_message_id(
                site_id=env.site_id, gateway_id=env.gateway_id, source_id=env.source_id,
                sequence_epoch=env.sequence_epoch, sequence=seq))
            self.last_sequences.append(seq)
            fixed.append((device, canonical_envelope_v3_text(env)))
        return fixed

    # ------------------------------------------------------------------ helpers
    def expect(self, name: str, ok: bool, detail: Any = None) -> bool:
        self.out["checks"].append({"check": name, "ok": bool(ok), **({"detail": detail} if detail is not None else {})})
        say(f"  [{'ok' if ok else 'FAIL'}] {name}" + ("" if ok or detail is None else f": {detail}"))
        if not ok:
            self.failures.append(name)
        return bool(ok)

    def backend(self, *argv: str, check: bool = True):
        self.out["commands"].append("python " + " ".join(argv))
        return self.py(*argv, cwd=self.tree / "backend", check=check)

    def drain(self, label: str) -> dict[str, Any]:
        done = self.backend("-m", "assetops_backend.recompute_consequences", "run", "--tenant", "demo",
                            "--site", SITE, "--limit", "100", check=False)
        lines = [json.loads(x) for x in done.stdout.splitlines() if x.strip().startswith("{")]
        items = [x for x in lines if "work_id" in x]
        summary = next((x for x in lines if "work_id" not in x), None)
        say(f"  runner ({label}), exit {done.returncode}: " + json.dumps(
            {k: summary[k] for k in ("claimed", "selected", "appended", "replayed", "no_op", "failed", "deferred",
                                     "backlog")} if summary else done.stderr.strip()[-300:]))
        for i in items:
            say(f"    work {i['work_id']} {i['cause']} attempt {i['attempt_no']} succeeded={i['succeeded']} "
                f"appended={i['appended']} replayed={i['replayed']} no_op={i['no_op_reason']} "
                f"error={i['error_code']}")
        record = {"label": label, "exit": done.returncode, "items": items, "summary": summary}
        self.out.setdefault("drains", []).append(record)
        return record

    def read(self, label: str, finding_id: str, revision_id: str, late_id: str = "") -> dict[str, Any]:
        latest = self.pg("SELECT r.id::text FROM finding_revision r WHERE r.finding_id = %s ORDER BY r.revision_no "
                         "DESC LIMIT 1", finding_id)[0][0] == revision_id
        w0, w1 = self.late["withheld_interval"]
        done = self.py("-c", READ, self.identity["tenant_id"], self.identity["site_id"], finding_id, revision_id,
                       "1" if latest else "0", w0, w1, late_id or "-", cwd=self.tree / "backend")
        body = json.loads(done.stdout.strip().splitlines()[-1])
        c = body["consequence"] or {}
        say(f"  read {label}: {body['currentness']} {body['reasons']} head={body['head_consequence_revision_id']} "
            f"cons#{c.get('revision_no')} {c.get('state')} {c.get('quantity_reason') or c.get('price_reason')} "
            f"bridge={body['bridge']['reason_key']} queued={body['bridge']['recalculation_queued']} "
            f"pending={[w['work_id'] for w in body['pending_work']]} s5={body['s5_money_eligible']}")
        self.out.setdefault("reads", []).append({"label": label, "finding_id": finding_id,
                                                 "finding_revision_id": revision_id, "is_latest": latest, **body})
        return body

    def work_rows(self) -> list[dict[str, Any]]:
        rows = self.pg(
            "SELECT w.id::text, w.cause, w.finding_revision_id::text, w.accepted_evidence_id::text, "
            "w.affected_from::text, w.affected_to::text, w.enqueued_at::text, "
            "coalesce((SELECT json_agg(json_build_object('attempt_id', a.id::text, 'attempt_no', a.attempt_no, "
            "'outcome', a.outcome, 'no_op_reason', a.no_op_reason, 'error_code', a.error_code, "
            "'consequence_revision_ids', a.consequence_revision_ids) ORDER BY a.attempt_no) "
            "FROM financial_consequence_work_attempt a WHERE a.work_id = w.id), '[]') "
            "FROM financial_consequence_work w WHERE w.site_id = %s ORDER BY w.enqueued_at, w.id",
            self.identity["site_id"])
        keys = ("work_id", "cause", "finding_revision_id", "accepted_evidence_id", "affected_from", "affected_to",
                "enqueued_at", "attempts")
        return [dict(zip(keys, r)) for r in rows]

    def revisions(self, finding_id: str) -> list[tuple[str, int, str, str]]:
        return [tuple(r) for r in self.pg(
            "SELECT id::text, revision_no, lifecycle, transition FROM finding_revision WHERE finding_id = %s "
            "ORDER BY revision_no", finding_id)]

    def accepted(self, batch_ids: list[str]) -> list[str]:
        return [r[0] for r in self.pg("SELECT e.id::text FROM accepted_evidence e JOIN ingestion_batch b ON "
                                      "b.id = e.batch_id WHERE b.external_batch_id = ANY(%s) AND "
                                      "e.role = 'generator_power' ORDER BY e.interval_start", batch_ids)]

    # ------------------------------------------------------------------ walk
    def walk(self) -> None:
        o = self.out
        step("0. SYSTEM diesel price v1 (published before both legs; re-review N2)")
        done = self.backend("-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file",
                            str(Path("conversions") / "demo-diesel-price-publications.json"), "--step", "v1")
        o["price_v1"] = json.loads(done.stdout.strip().splitlines()[-1])
        say(f"  price v1: revision {o['price_v1']['revision_id']}")

        step(f"1. {self.case['case_id']}: first delivery without [07:00, 07:05), process-jobs, match-findings")
        self.run_power_case({k: v for k, v in self.case.items() if k != "late"})
        record = self.cases[-1]
        o["first_delivery"] = {"batch_ids": record["batch_ids"], "evidence_count": record["evidence_count"],
                               "evidence_id_sha256": record["evidence_id_sha256"],
                               "generator_power_ids": len(self.accepted(record["batch_ids"])),
                               "match_problems": [m["problems"] for m in record["matches"]]}
        self.expect("first match created exactly the expected Finding", not any(m["problems"] for m in record["matches"]),
                    [m["problems"] for m in record["matches"]])
        (fid,) = {f for m in record["matches"] for f in m["finding_ids"]}
        revs = self.revisions(fid)
        r1 = revs[-1][0]
        o["finding_id"], o["r1"] = fid, {"id": r1, "revision_no": revs[-1][1], "lifecycle": revs[-1][2],
                                         "transition": revs[-1][3]}
        o["r1"]["analytic_run_ids"] = [x[0] for x in self.pg(
            "SELECT DISTINCT analytic_run_id::text FROM finding_revision_assessment WHERE finding_revision_id = %s",
            r1)]
        self.drain("bootstrap: r1's FindingRevision work")
        pre = self.read("pre-late (r1)", fid, r1)
        o["pre_late_s3_result"] = {"quantity": pre["derived_now"]["quantity"], "reason": pre["derived_now"]["reason"],
                                   "candidate_spans": pre["candidate_spans"]}
        if not self.expect("N5 precondition: [07:00, 07:05) lies inside r1's observed Candidate time",
                           pre["withheld_inside_candidate"]
                           and pre["derived_now"]["reason"] != "CANDIDATE_SPAN_UNVERIFIED",
                           {"candidate_spans": pre["candidate_spans"], "reason": pre["derived_now"]["reason"]}):
            o["stopped"] = "N5 precondition failed: the withheld window is not observed Candidate time; Leg A cannot " \
                           "show TECHNICAL_INPUT_CHANGED. Stopped without changing the fixture."
            say("STOP: " + o["stopped"])
            return
        self.expect("pre-late: consequence 1 is CURRENT", pre["currentness"] == "CURRENT" and
                    (pre["consequence"] or {}).get("revision_no") == 1, pre["consequence"])

        step("2. Leg A: the withheld mean is accepted late (same registered credential, TLS)")
        late_batches = self.post(self.power_envelopes(self.late, s4.EPOCH_PREFIX + self.late["epoch"]),
                                 fixture=self.authored_fixture())
        late_sequences = list(self.last_sequences)
        (late_id,) = self.accepted(late_batches)
        o["late"] = {"batch_ids": late_batches, "accepted_evidence_id": late_id,
                     "decided_label": self.late["decided"],
                     "source_sequence": late_sequences}
        say(f"  late accepted evidence {late_id}")
        ev = [w for w in self.work_rows() if w["cause"] == "EVIDENCE_ACCEPTED"]
        o["leg_a_work_before"] = ev
        self.expect("exactly one EVIDENCE_ACCEPTED work row, for the late ID and r1, not yet attempted",
                    len(ev) == 1 and ev[0]["accepted_evidence_id"] == late_id and ev[0]["finding_revision_id"] == r1
                    and ev[0]["attempts"] == [], ev)
        a0 = self.read("Leg A before drain (r1)", fid, r1, late_id)
        self.expect("before drain: STALE / TECHNICAL_INPUT_CHANGED", a0["currentness"] == "STALE"
                    and "TECHNICAL_INPUT_CHANGED" in a0["reasons"], a0["reasons"])
        self.expect("before drain: the queued work ID is the late mean's EVIDENCE_ACCEPTED row; bridge STALE_QUEUED",
                    [w["work_id"] for w in a0["pending_work"]] == [ev[0]["work_id"]]
                    and a0["bridge"]["reason_key"] == "STALE_QUEUED" and a0["bridge"]["recalculation_queued"],
                    {"pending": a0["pending_work"], "bridge": a0["bridge"]})
        self.expect("before drain: the late ID is examined now but is not an input of r1's analytic run",
                    a0["derived_now"]["late_examined"] and not a0["derived_now"]["late_in_run_inputs"],
                    a0["derived_now"])
        self.drain("Leg A: EVIDENCE_ACCEPTED")
        a1 = self.read("Leg A after drain (r1)", fid, r1, late_id)
        c = a1["consequence"] or {}
        self.expect("after drain: same FindingRevision r1, consequence 2 CURRENT QUANTITY_UNAVAILABLE / "
                    "POWER_NOT_IN_ASSESSMENT_INPUTS", a1["currentness"] == "CURRENT" and c.get("revision_no") == 2
                    and c.get("state") == "QUANTITY_UNAVAILABLE"
                    and c.get("quantity_reason") == "POWER_NOT_IN_ASSESSMENT_INPUTS", c)
        self.expect("after drain: consequence 1 retained in history", [h[0] for h in a1["history"]][:1]
                    == [pre["consequence"]["id"]] and len(a1["history"]) == 2, a1["history"])
        self.expect("after drain: no S5 money (not CURRENT PRICED)", not a1["s5_money_eligible"]
                    and a1["bridge"]["amount"] is None, a1["bridge"])
        self.expect("after drain: the evidence work SUCCEEDED with consequence 2",
                    [(x["outcome"], x["consequence_revision_ids"]) for w in self.work_rows()
                     if w["work_id"] == ev[0]["work_id"] for x in w["attempts"]] == [("SUCCEEDED", [c.get("id")])])

        step("3. Leg B: S3 process-jobs and S4 match-findings re-evaluate the Finding")
        o["leg_b_process_jobs"] = self.cli("process-jobs")
        self.out["commands"].append("python -m assetops_backend.analytics.assess_dispatch process-jobs")
        o["leg_b_match"] = self.cli("match-findings", *self.site_args())
        self.out["commands"].append("python -m assetops_backend.analytics.assess_dispatch match-findings "
                                    "--tenant-id <tenant> --site-id <site>")
        revs = self.revisions(fid)
        r2 = revs[-1][0]
        o["r2"] = {"id": r2, "revision_no": revs[-1][1], "lifecycle": revs[-1][2], "transition": revs[-1][3],
                   "analytic_run_ids": [x[0] for x in self.pg(
                       "SELECT DISTINCT analytic_run_id::text FROM finding_revision_assessment "
                       "WHERE finding_revision_id = %s", r2)]}
        say(f"  FindingRevisions: {[(r[1], r[2], r[3]) for r in revs]}")
        self.expect("a revised FindingRevision r2 was appended", r2 != r1 and revs[-1][1] == o["r1"]["revision_no"] + 1,
                    revs)
        cites = self.pg("SELECT count(*) FROM finding_revision_assessment a JOIN analytic_run_evidence e ON "
                        "e.run_id = a.analytic_run_id WHERE a.finding_revision_id = %s AND a.scope = 'INTERVAL' "
                        "AND e.evidence_id = %s", r2, late_id)[0][0]
        self.expect("r2's analytic run includes the late ID", cites > 0, cites)
        fra = [w for w in self.work_rows() if w["cause"] == "FINDING_REVISION_APPENDED" and w["finding_revision_id"] == r2]
        o["leg_b_work_before"] = fra
        self.expect("r2 has exactly one FINDING_REVISION_APPENDED work row", len(fra) == 1, fra)
        b0 = self.read("Leg B before drain (r2)", fid, r2, late_id)
        self.expect("before drain: r2 PENDING with its queued work", b0["currentness"] == "PENDING"
                    and [w["work_id"] for w in b0["pending_work"]] == [fra[0]["work_id"]] if fra else False,
                    b0["pending_work"])
        self.drain("Leg B: r2's FindingRevision work")
        b1 = self.read("Leg B after drain (r2)", fid, r2, late_id)
        c = b1["consequence"] or {}
        self.expect("after drain: r2 CURRENT PRICED, priced by price v1", b1["currentness"] == "CURRENT"
                    and c.get("state") == "PRICED" and c.get("price_revision_id") == o["price_v1"]["revision_id"], c)
        self.expect("after drain: r2 counts the late mean (late ID in run inputs and examined)",
                    b1["derived_now"]["late_in_run_inputs"] and b1["derived_now"]["late_examined"], b1["derived_now"])
        self.expect("after drain: S5 money eligible (CURRENT PRICED, bridge amount shown)", b1["s5_money_eligible"],
                    b1["bridge"])
        h1 = self.read("Leg B: r1 after the revision (historical)", fid, r1, late_id)
        self.expect("r1 is HISTORICAL and keeps both consequence revisions", h1["currentness"] == "HISTORICAL"
                    and len(h1["history"]) == 2, h1["history"])
        replay = self.drain("replay: nothing left")
        self.expect("replay selects nothing and leaves no backlog", replay["summary"] is not None
                    and replay["summary"]["selected"] == 0 and replay["summary"]["backlog"] == 0, replay["summary"])
        o["work_after"] = self.work_rows()
        o["consequences"] = [dict(zip(("id", "finding_revision_id", "revision_no", "state", "reason",
                                       "technical_input_sha256", "consequence_basis_sha256"), r)) for r in self.pg(
            "SELECT id::text, finding_revision_id::text, revision_no, state, coalesce(quantity_reason, price_reason), "
            "technical_input_sha256, consequence_basis_sha256 FROM financial_consequence_revision WHERE "
            "finding_id = %s ORDER BY recorded_at", fid)]
        dup = self.pg("SELECT count(*) FROM (SELECT finding_revision_id, consequence_basis_sha256 FROM "
                      "financial_consequence_revision GROUP BY 1, 2 HAVING count(*) > 1) x")[0][0]
        self.expect("no duplicate consequence basis", dup == 0, dup)

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            self.walk()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
        self.out["failures"] = list(self.failures)
        path = Path(self.args_work) / EVIDENCE_NAME
        path.write_text(json.dumps(self.out, indent=2, default=str), encoding="utf-8")
        say(f"Evidence: {path} ({len(self.failures)} failed checks)")


# ---------------------------------------------------------------------------------------------------- LR-01
# The LR-01 extension (tasks/LR-01-late-reading-series-and-money-limit.md, owner walkthrough): its own private
# `assetops_lr01*` database and a matching work directory (default %LOCALAPPDATA%/AssetOps/<db>, the same root
# as this tool's S4-02c default), an explicit schedule tick (no timer installed), the SYSTEM-only attestation CLI
# and the file-backed Performance comparison that opens the source gate (re-review N1) after every step that
# moves a selection, so served Financials shows the real money states.
LR01_PREFIX = "assetops_lr01"
LR01_STATE = "lr01-state.json"
LR01_EVIDENCE = "lr01-walkthrough.json"
LR01_ENV = "lr01-walkthrough"
LR01_AUTHORITY = "lab-simulated-clock"
LR01_LABEL = "SIMULATED demonstration clock attestation (LR-01 walkthrough; not a real-source proof)"
RECORDED_USD, EXPECTED_USD = "7.5625", "15.8125"


def lr01_work(db: str, work: str | None) -> Path:
    return Path(work) if work else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / db


def tree_env(work: Path, db: str) -> dict[str, str]:
    """The private tree's environment, as `s2_demo_walkthrough.Demo.env` builds it, for the follow-up commands."""
    tree = work / "tree"
    env = dict(os.environ)
    env.pop("ASSETOPS_TEST_DATABASE_URL", None)
    env["PYTHONPATH"] = os.pathsep.join(str(tree / x) for x in ("backend", "gateway", "simulator", "contracts", "host"))
    env["DATABASE_URL"] = (f"postgresql+psycopg://assetops:{os.environ.get('ASSETOPS_PG_PASSWORD', 'assetops-local-dev')}"
                           f"@127.0.0.1:{os.environ.get('ASSETOPS_PG_PORT', '55432')}/{db}")
    env["PYTHONUNBUFFERED"] = "1"
    return env


def tree_py(work: Path, db: str, *argv: str, cwd: str = "backend", check: bool = True):
    import subprocess

    done = subprocess.run([str(s2.PY), *argv], cwd=work / "tree" / cwd, env=tree_env(work, db), capture_output=True,
                          text=True, timeout=900)
    if check and done.returncode:
        raise SystemExit(f"FAILED: {' '.join(argv)} exit {done.returncode}\n{done.stderr[-2000:]}")
    return done


def last_json(done) -> Any:
    lines = [x for x in done.stdout.splitlines() if x.strip().startswith("{")]
    return json.loads(lines[-1]) if lines else None


def performance_gate(work: Path, db: str) -> dict[str, Any]:
    """Re-review N1: the file-backed Performance comparison over the current selections (the source gate)."""
    done = tree_py(work, db, "-m", "assetops_backend.performance_migration", "run", "--tenant", "demo", "--site", SITE,
                   check=False)
    out = {"exit": done.returncode, "open": done.returncode == 0, "tail": (done.stdout or done.stderr)[-400:]}
    say(f"  Performance comparison (source gate): exit {done.returncode} -> gate {'OPEN' if out['open'] else 'CLOSED'}")
    return out


def schedule_tick(work: Path, db: str) -> dict[str, Any]:
    done = tree_py(work, db, "-m", "assetops_backend.scheduling.run", "tick", "--environment", LR01_ENV,
                   "--max-sites", "5", "--s3-jobs", "10", "--consequence-items", "100", check=False)
    body = last_json(done) or {"stderr": done.stderr[-800:]}
    say(f"  explicit schedule tick: exit {done.returncode} {body.get('outcome')}")
    return {"exit": done.returncode, "outcome": body.get("outcome"), "failure": body.get("failure")}


def record_attestation(work: Path, db: str, state: dict[str, Any], kind: str = "record") -> dict[str, Any]:
    argv = ["-m", "assetops_backend.record_clock_attestation", kind, "--site", SITE, "--source", state["source_id"],
            "--epoch", state["epoch"], "--idempotency-key", f"lr01-{kind}-{state['attestations']}"]
    if kind == "record":
        day = state["day"]
        argv += ["--authority", LR01_AUTHORITY, "--label", LR01_LABEL, "--max-error-seconds", "30",
                 "--valid-from", f"{day}T00:00:00Z", "--valid-to", f"{day}T23:59:59Z"]
    done = tree_py(work, db, *argv, check=False)
    body = last_json(done) or {"stderr": done.stderr[-800:]}
    say(f"  SYSTEM attestation {kind}: exit {done.returncode} {json.dumps(body)[:300]}")
    return {"exit": done.returncode, "body": body, "command": "python " + " ".join(argv)}


class Lr01Walk(LateWalk):
    """LR-01 outcome-table walk on the authored fixture: `admission` (run 1, the project gateway's numbering) or
    `on-time` (store-and-forward numbering) with a labelled simulated attestation."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.variant, self.through, self.db = args.variant, args.through, args.db
        self.state: dict[str, Any] = {"db": args.db, "variant": args.variant}
        self.out.update(lr01=True, variant=self.variant, through=self.through)

    def power_envelopes(self, step: dict[str, Any], epoch: str) -> list[tuple[str, str]]:
        if self.variant == "admission":
            # Admission-sequenced: each mean is numbered on intake, so the late mean follows the last sequence.
            out = p.PowerCases.power_envelopes(self, step, epoch)
            self.last_sequences = [v for k, v in self.seq.items() if k[1] == epoch]
            return out
        return super().power_envelopes(step, epoch)

    def latest(self, fid: str) -> dict[str, Any]:
        rid, no, life, trans, end_reason, es, ee = self.pg(
            "SELECT id::text, revision_no, lifecycle, transition, claim->>'end_reason', "
            "to_char(episode_start AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI'), "
            "to_char(episode_end AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI') FROM finding_revision "
            "WHERE finding_id = %s ORDER BY revision_no DESC LIMIT 1", fid)[0]
        return {"id": rid, "revision_no": no, "lifecycle": life, "transition": trans, "end_reason": end_reason,
                "episode": [es, ee], "analytic_run_ids": sorted(x[0] for x in self.pg(
                    "SELECT DISTINCT analytic_run_id::text FROM finding_revision_assessment "
                    "WHERE finding_revision_id = %s", rid))}

    def window_claim(self, body: dict[str, Any]) -> list[Any]:
        ids = [w["window_assessment_revision_id"] for w in body["money_eligibility"]["windows"]
               if w.get("window_assessment_revision_id")]
        return [list(r) for r in self.pg(
            "SELECT id::text, claim_level FROM assessment_revision WHERE id::text = ANY(%s)", ids)]

    def gate(self, label: str) -> None:
        self.out.setdefault("performance_gate", []).append({"label": label, **performance_gate(self.work, self.db)})

    def tick(self, label: str) -> None:
        self.out.setdefault("ticks", []).append({"label": label, **schedule_tick(self.work, self.db)})

    def money(self, label: str, fid: str, rid: str, late: str = "") -> dict[str, Any]:
        body = self.read(label, fid, rid, late)
        m = body["money_eligibility"]
        c = body["consequence"] or {}
        say(f"    money gate {m['state']} amount_shown={body['current_amount_shown']} cons={c.get('id')} "
            f"{c.get('state')} {c.get('amount_high')} bridge={body['bridge']['state']}")
        return body

    def walk(self) -> None:
        o, state = self.out, self.state
        step("0. SYSTEM diesel price v1")
        done = self.backend("-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file",
                            str(Path("conversions") / "demo-diesel-price-publications.json"), "--step", "v1")
        o["price_v1"] = json.loads(done.stdout.strip().splitlines()[-1])

        step(f"1. {self.case['case_id']} ({self.variant}-sequenced): first delivery without [07:00, 07:05)")
        self.run_power_case({k: v for k, v in self.case.items() if k != "late"})
        record = self.cases[-1]
        (fid,) = {f for m in record["matches"] for f in m["finding_ids"]}
        state.update(finding_id=fid, epoch=s4.EPOCH_PREFIX + self.late["epoch"], day=self.case["day"],
                     source_id=self.pg("SELECT source_id::text FROM accepted_evidence WHERE role = 'generator_power' "
                                       "LIMIT 1")[0][0], attestations=0, tenant_id=self.identity["tenant_id"],
                     site_id=self.identity["site_id"])
        self.drain("bootstrap: r1")
        self.gate("after the first delivery")
        o["r1"] = self.latest(fid)
        if self.variant == "on-time":
            step("1b. Labelled simulated clock attestation (SYSTEM CLI) before the late upload")
            o["attestation"] = record_attestation(self.work, self.db, state)
            state["attestations"] += 1
            self.expect("the SYSTEM attestation CLI recorded one event", o["attestation"]["exit"] == 0,
                        o["attestation"])
            self.tick("after the attestation")
            self.gate("after the attestation tick")

        step("2. The withheld 20 kW mean [07:00, 07:05) is accepted late")
        late_batches = self.post(self.power_envelopes(self.late, state["epoch"]),
                                 fixture=self.authored_fixture())
        (late_id,) = self.accepted(late_batches)
        state["late_id"] = late_id
        o["late"] = {"accepted_evidence_id": late_id, "sequence": list(self.last_sequences)}
        before = self.latest(fid)
        p0 = self.money("late accepted, before the tick", fid, before["id"], late_id)
        self.expect("late acceptance: PENDING_REASSESSMENT and no current amount",
                    p0["money_eligibility"]["state"] == "PENDING_REASSESSMENT" and not p0["current_amount_shown"],
                    p0["money_eligibility"]["pending_reasons"])

        step("3. Explicit schedule tick: S3, S4 and the consequence drain")
        self.tick("after late acceptance")
        self.gate("after the late tick")
        rx = self.latest(fid)
        o["after_late"] = rx
        b = self.money("after the late tick", fid, rx["id"], late_id)
        c = b["consequence"] or {}
        o["after_late_window_claims"] = self.window_claim(b)
        if self.variant == "admission":
            self.expect("row 1: S3 window INDETERMINATE",
                        any(x[1] == "INDETERMINATE" for x in o["after_late_window_claims"]),
                        o["after_late_window_claims"])
            lims = b["money_eligibility"]["series_limits"]
            self.expect("row 1: SEQUENCE_ORDER_INVERTED (no attestation) citing the late ID",
                        any(x["kind"] == "SEQUENCE_ORDER_INVERTED" and late_id in x["evidence_ids"]
                            and x.get("clock") == "NO_ATTESTATION" for x in lims), lims)
            self.expect("row 1: new SUPPORTED revision ending 07:00 with SERIES_LIMIT",
                        rx["revision_no"] > o["r1"]["revision_no"] and rx["lifecycle"] == "SUPPORTED"
                        and rx["end_reason"] == "SERIES_LIMIT" and rx["episode"][1] == f"{self.case['day']} 07:00", rx)
            self.expect(f"row 1: recorded {RECORDED_USD} USD (CURRENT PRICED basis) withheld, no current amount",
                        c.get("state") == "PRICED" and c.get("amount_high") == RECORDED_USD
                        and b["money_eligibility"]["state"] == "WITHHELD_GENERATOR_SERIES"
                        and not b["current_amount_shown"] and b["presented_as_current"] is False
                        and b["bridge"]["amount"] is None
                        and b["bridge"]["recorded_consequence_revision_id"] == c.get("id"), b["bridge"])
            state["withheld"] = {"finding_revision_id": rx["id"], "consequence_revision_id": c.get("id"),
                                 "analytic_run_ids": rx["analytic_run_ids"]}
            self.save()
            if self.through == "withheld":
                return
            self.attest_and_settle()
        else:
            self.expect(f"row 4: full episode, not SERIES_LIMIT, ELIGIBLE at {EXPECTED_USD} USD",
                        rx["end_reason"] != "SERIES_LIMIT" and rx["episode"][1] == f"{self.case['day']} 08:00"
                        and b["money_eligibility"]["state"] == "ELIGIBLE" and b["current_amount_shown"]
                        and c.get("amount_high") == EXPECTED_USD, {"revision": rx, "money": b["money_eligibility"]})
            state["eligible"] = {"finding_revision_id": rx["id"], "consequence_revision_id": c.get("id")}
        self.save()

    def attest_and_settle(self) -> None:
        o, state = self.out, self.state
        fid, w = state["finding_id"], state["withheld"]
        step("4. Labelled simulated clock attestation through the SYSTEM-only CLI")
        o["attestation"] = record_attestation(self.work, self.db, state)
        state["attestations"] += 1
        self.expect("the SYSTEM attestation CLI recorded one event", o["attestation"]["exit"] == 0, o["attestation"])
        self.gate("after the attestation")
        pend = self.money("after the attestation, before the tick", fid, w["finding_revision_id"], state["late_id"])
        self.expect(f"row 2: PENDING_REASSESSMENT; the {RECORDED_USD} head and old IDs retained, no current amount",
                    pend["money_eligibility"]["state"] == "PENDING_REASSESSMENT" and not pend["current_amount_shown"]
                    and (pend["consequence"] or {}).get("id") == w["consequence_revision_id"]
                    and (pend["consequence"] or {}).get("amount_high") == RECORDED_USD, pend["money_eligibility"])
        step("5. Explicit schedule tick: reassessment under the attestation")
        self.tick("after the attestation")
        self.gate("after the reassessment tick")
        rn = self.latest(fid)
        e = self.money("after reassessment", fid, rn["id"], state["late_id"])
        c = e["consequence"] or {}
        self.expect("row 3: new full-episode SUPPORTED revision, not SERIES_LIMIT",
                    rn["id"] != w["finding_revision_id"] and rn["lifecycle"] == "SUPPORTED"
                    and rn["end_reason"] != "SERIES_LIMIT" and rn["episode"][1] == f"{self.case['day']} 08:00", rn)
        self.expect(f"row 3: ELIGIBLE, exact-head CURRENT PRICED {EXPECTED_USD} USD shown, new run/consequence IDs",
                    e["money_eligibility"]["state"] == "ELIGIBLE" and e["current_amount_shown"]
                    and c.get("amount_high") == EXPECTED_USD and c.get("id") != w["consequence_revision_id"]
                    and not set(c.get("analytic_run_ids") or []) & set(w["analytic_run_ids"]), e["money_eligibility"])
        h = self.money("the withheld revision, now historical", fid, w["finding_revision_id"], state["late_id"])
        self.expect(f"row 3: the {RECORDED_USD} revision and its IDs stay as history",
                    h["currentness"] == "HISTORICAL" and (h["consequence"] or {}).get("id") == w["consequence_revision_id"]
                    and (h["consequence"] or {}).get("amount_high") == RECORDED_USD and not h["current_amount_shown"],
                    h["consequence"])
        state["eligible"] = {"finding_revision_id": rn["id"], "consequence_revision_id": c.get("id")}

    def save(self) -> None:
        (self.work / LR01_STATE).write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            self.walk()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
        self.out["failures"] = list(self.failures)
        self.out["state"] = self.state
        path = self.work / LR01_EVIDENCE
        path.write_text(json.dumps(self.out, indent=2, default=str), encoding="utf-8")
        say(f"Evidence: {path} ({len(self.failures)} failed checks)")


def lr01_followup(args: argparse.Namespace) -> int:
    """`attest` / `tick` / `serve` over a prepared LR-01 database and work directory."""
    import subprocess

    work = lr01_work(args.db, args.work)
    state_file = work / LR01_STATE
    if not state_file.exists():
        raise SystemExit(f"No {LR01_STATE} in {work}: run `run --db {args.db}` first.")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    if args.command == "attest":
        out = record_attestation(work, args.db, state, "record")
        state["attestations"] += 1
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        performance_gate(work, args.db)
        say("Financials now reads PENDING_REASSESSMENT until the next explicit tick.")
        return 0 if out["exit"] == 0 else 1
    if args.command == "tick":
        out = schedule_tick(work, args.db)
        performance_gate(work, args.db)
        return 0 if out["exit"] == 0 else 1
    performance_gate(work, args.db)
    log = work / "logs" / f"api-{args.api_port}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([str(s2.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                             str(args.api_port)], cwd=work / "tree" / "host", env=tree_env(work, args.db),
                            stdout=log.open("w"), stderr=subprocess.STDOUT)
    fid = state.get("finding_id")
    say(f"API for {args.db} on http://127.0.0.1:{args.api_port} (log {log}). From frontend/:")
    say(f'  $env:ASSETOPS_API_PORT="{args.api_port}"; npm.cmd run dev -- --port {args.web_port} --strictPort')
    say(f"Financials: http://localhost:{args.web_port}/sites/{SITE}/financials?finding_id={fid}")
    say(f"Finding:    http://localhost:{args.web_port}/sites/{SITE}/findings/{fid}")
    for key in ("withheld", "eligible"):
        if state.get(key):
            r = state[key]
            say(f"  {key}: finding revision {r['finding_revision_id']}, consequence {r['consequence_revision_id']}: "
                f"http://localhost:{args.web_port}/sites/{SITE}/financials?finding_id={fid}"
                f"&revision_id={r['finding_revision_id']}&consequence_revision_id={r['consequence_revision_id']}")
    say("Ctrl+C stops the API.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return 0


def say(text: str) -> None:
    s4.say(text)


def step(text: str) -> None:
    s4.step(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s402c_late_power_walkthrough.py")
    parser.add_argument("command", choices=("run", "drop", "attest", "tick", "serve"))
    parser.add_argument("--work", default=None, help="work folder (S4-02c default under %%LOCALAPPDATA%%/AssetOps; "
                                                     "LR-01 default %%LOCALAPPDATA%%/AssetOps/<db>)")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--tls-port", type=int, default=8918)
    parser.add_argument("--http-port", type=int, default=8919)
    parser.add_argument("--cadence-seconds", type=int, default=60)
    parser.add_argument("--db", default=DB, help="own database (dropped and recreated by run)")
    parser.add_argument("--variant", choices=("admission", "on-time"), default="admission",
                        help="LR-01: run 1 admission numbering, or the on-time-sequenced attested upload")
    parser.add_argument("--through", choices=("withheld", "eligible"), default="withheld",
                        help="LR-01 admission: stop at the withheld state (owner flow) or walk on to eligible")
    parser.add_argument("--api-port", type=int, default=8921)
    parser.add_argument("--web-port", type=int, default=5421)
    args = parser.parse_args(argv)
    lr01 = args.db.startswith(LR01_PREFIX)
    if not args.db.replace("_", "").isalnum() or args.db.endswith("_test") or not (
            lr01 or (args.db.startswith("assetops_s402c3walk") and args.command in ("run", "drop"))):
        raise SystemExit(f"Refusing database {args.db!r}: use an {LR01_PREFIX}* database (LR-01; the only prefix "
                         "attest/tick/serve accept) or an assetops_s402c3walk* database (S4-02c run/drop) of its own.")
    if lr01 and args.command in ("attest", "tick", "serve"):
        return lr01_followup(args)
    args.work = str(lr01_work(args.db, args.work)) if lr01 else (args.work or str(DEFAULT_WORK))
    s2.DEMO_DB = args.db
    if args.command == "drop":
        import psycopg

        admin = s2.PG_ADMIN.format(pw=os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev"),
                                   port=os.environ.get("ASSETOPS_PG_PORT", "55432"))
        with psycopg.connect(admin, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {args.db} WITH (FORCE)")
        print(f"dropped {args.db}")
        work = Path(args.work)
        # Drop rule (re-review N2): only this tool's own folders - the S4-02c default, or an LR-01 folder named
        # after its database or holding its LR-01 state file.
        if work.exists() and (work.name.startswith("s402c3") or (lr01 and (
                work.name == args.db or (work / LR01_STATE).exists()))):
            shutil.rmtree(work)
            print(f"removed {work}")
        return 0
    walk = Lr01Walk(args) if lr01 else LateWalk(args)
    walk.args_work = args.work
    walk.run()
    return 1 if walk.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
