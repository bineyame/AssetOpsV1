"""DD1b2-R: the mill step of a three-Site prepare. A child of `Demo.after_children`, after all three Site children and
backfill step `a`, before steps `b,c,d`, so ACT-002/003 keep their codes and the thread opens from a story-dated study.

    python tools/demo_combined_mill.py build <url> <work>

In story time, instants from `kobo.mill` in `backend/conversions/demo-combined-story-v1.json`:
1. the one pinned study, S-19 to S-15: `reconcile` one window, then `run_pending(scan=False)` (Q3). Its revision and
   selection carry the story instant through the store's `story_clock` (Q2). It is a pin, not a scan (BL-32);
2. the Action, then the maintenance case, its record, ASSIGN, COMPLETE, then the case link (Action first: ACCEPTED is
   known before COMPLETE, so the thread reaches CHANGE_APPLIED);
3. the freeze, then the evaluation of the plan; the stored outcome is what the tick's evaluator replays.

**Disclosure (Q5):** freeze and evaluate read through `_AllKnown`, which drops `known_at`. `computed_at` on a snapshot
is build time, so an as-known read at a story clock would see nothing. The plan's `snapshots_known_at` is the story
instant; the rows read are as built. The days read are bounded to days that ended before the clock, and this is the
read the MILL-3 dry run made (`tools/dd1a2_mill3_dry_run.py`). Depot head pins stay wall-clock, a build-time fact.

Writes `<work>/mill.json`. Exits non-zero on: no eligible day, a refused Action, a short baseline, or a stored outcome
other than VERIFIED. A failed measure is reported with its table, never tuned.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SITE = "KOBO-001"
EFFECTIVE_OFFSET = -9
BASELINE_OFFSETS = (-13, -12, -11)
EXPECTED_OUTCOME = "VERIFIED"
PRINCIPAL = "service:w401-fixture"
ACTOR = {"kind": "SERVICE", "id": PRINCIPAL, "attestation": "service=w401-fixture;job=demo-mill;rule=dd1b2-r"}
KEY = "demo3-mill"
#: P1's measures as `frozen_result` stores them. It stores no `classification`: that only feeds its status.
STUDY_FIELDS = ("status", "assessed_days", "eligible_days", "headroom_kw", "window_hours", "limitations")


class Stop(SystemExit):
    """A ruled stop: `mill.json` is already written and names why."""


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def wire(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def instants_in_order(mill: dict) -> list[str]:
    """DD1b2-R Q6's required order: study known <= Action < the record steps < link < freeze < evaluate. The names of
    any instants out of order; empty when the story block holds."""
    chain = [("study.at", mill["study"]["at"]), ("action_at", mill["action_at"]),
             ("request", mill["request"]["occurred_at"]), ("record", mill["record"]["occurred_at"]),
             ("assign_at", mill["assign_at"]), ("complete_at", mill["complete_at"]),
             ("commands_recorded_from", mill["commands_recorded_from"]), ("case_link_at", mill["case_link_at"]),
             ("freeze_at", mill["freeze_at"]), ("evaluate_at", mill["evaluate_at"])]
    bad = [f"{a[0]} >= {b[0]}" for a, b in zip(chain, chain[1:]) if at(a[1]) >= at(b[1])]
    if at(mill["study"]["from"]) >= at(mill["study"]["to"]) or at(mill["study"]["to"]) >= at(mill["study"]["at"]):
        bad.append("study.from < study.to < study.at")
    return bad


class _AllKnown:
    """Q5: the tool's process-local reader. It reads the rows as built and ignores `known_at`; see the docstring."""

    def __init__(self, reader: Any) -> None:
        self.reader = reader

    def latest(self, tenant_id: Any, site_id: Any, from_day: date, to_day: date, measures: Any = None,
               known_at: Any = None) -> list:
        return self.reader.latest(tenant_id, site_id, from_day, to_day, measures)


def verification_service(store: Any, reader: Any, instant: datetime) -> Any:
    from assetops_backend.actions.verification import VerificationPorts, VerificationService

    return VerificationService(SimpleNamespace(store=store, clock=lambda: instant,
                                               verification_ports=VerificationPorts(snapshots=_AllKnown(reader))))


def pinned_study(url: str, tenant_id: Any, site_id: Any, mill: dict) -> dict:
    """Q3: one window, one job, on the job's, the lease's and the store's story clock."""
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions.worker import MiniOpportunityWorker
    from assetops_backend.mini_depth.read import MiniDepthRead

    instant = at(mill["study"]["at"])
    clock = lambda: instant  # noqa: E731
    jobs = build_postgres_assessment_store(url)
    jobs.test_clock_override = clock
    store = PostgresMiniDecisionStore.from_url(url, story_clock=clock)
    worker = MiniOpportunityWorker(jobs, store, MiniDepthRead.from_url(url, build_link_rows_reader()),
                                   test_lease_clock=clock)
    try:
        queued = worker.reconcile(SITE, at(mill["study"]["from"]), at(mill["study"]["to"]))
        outcomes = worker.run_pending(limit=10, tenant_id=tenant_id, site_id=site_id, scan=False)
    finally:
        store.dispose()
    return {"queued": len(queued), "outcomes": [o.as_json() for o in outcomes]}


def study_row(engine: Any, revision_id: str) -> dict:
    from sqlalchemy import text

    with engine.connect() as c:
        row = c.execute(text(
            "SELECT r.result, r.created_at, r.opportunity_id, o.first_day, o.last_day, s.selected_at "
            "FROM mini_opportunity_revision r JOIN mini_opportunity o ON o.id = r.opportunity_id "
            "JOIN mini_opportunity_selection s ON s.revision_id = r.id WHERE r.id = :r"), {"r": revision_id}).mappings().one()
    result = row["result"]
    return {**{k: result.get(k) for k in STUDY_FIELDS}, "first_day": str(row["first_day"]), "last_day": str(row["last_day"]),
            "created_at": wire(row["created_at"]), "selected_at": wire(row["selected_at"]),
            "opportunity_id": str(row["opportunity_id"]), "revision_id": str(revision_id),
            "day_rows": [{"local_day": d["local_day"], "decision": d["decision"], "window_hours": d.get("window_hours"),
                          "hours": [[h["decision"], h["constraints"], h["opportunity_kwh"]] for h in d.get("hours", [])]}
                         for d in result.get("day_rows", [])]}


def record_change(url: str, engine: Any, tenant_id: Any, site_id: Any, opportunity_id: str, revision_id: str,
                  mill: dict) -> dict:
    """The Action, the COMPLETE case and its link, each on its own story clock, in the order of Q6."""
    from sqlalchemy import text

    from assetops_backend.work.composition import build_domain_intent_service, build_work_service
    from demo_story_clock import StepClock

    domain, work = build_domain_intent_service(url), build_work_service(url)
    code = SITE
    try:
        action_at = at(mill["action_at"])
        domain._store.test_db_clock_override = lambda: action_at
        status, action = domain.create_action(tenant_id, site_id, code, {
            "domain": "MINI", "origin_opportunity_id": opportunity_id, "origin_opportunity_revision_id": revision_id,
            "title": mill["title"], "owner_label": mill["owner_label"], "due_at": None, "raised_at": wire(action_at),
            "actor": dict(ACTOR), "idempotency_key": f"{KEY}-action"}, PRINCIPAL)
        if status != 201:
            raise RuntimeError(f"create_action answered {status}: {action}")
        recorded = StepClock(at(mill["commands_recorded_from"]))
        work._store.test_db_clock_override = recorded
        request = {"kind": "MAINTENANCE_REQUEST", "occurred_at": mill["request"]["occurred_at"], "asset_id": None,
                   "finding_links": [], "action_links": [], "title": mill["request"]["title"],
                   "narrative": mill["request"]["narrative"], "cited_accepted_evidence_ids": [], "actor": dict(ACTOR),
                   "idempotency_key": f"{KEY}-request"}
        s, wr = work.create_case(tenant_id, site_id, request, PRINCIPAL)
        if s != 201:
            raise RuntimeError(f"create_case answered {s}: {wr}")
        case_id, rev_id = wr["id"], wr["revision"]["id"]
        s, rec = work.post_record(tenant_id, site_id, case_id, {
            "activity": mill["record"]["activity"], "outcome_note": None, "occurred_at": mill["record"]["occurred_at"],
            "actor": dict(ACTOR), "idempotency_key": f"{KEY}-record"}, PRINCIPAL)
        if s != 201:
            raise RuntimeError(f"post_record answered {s}: {rec}")
        for kind, payload, when in (("ASSIGN", {"assignee": mill["owner_label"]}, mill["assign_at"]),
                                    ("COMPLETE", {"maintenance_record_id": rec["id"]}, mill["complete_at"])):
            s, got = work.post_event(tenant_id, site_id, case_id, {
                "kind": kind, "occurred_at": when, "payload": payload, "actor": dict(ACTOR),
                "idempotency_key": f"{KEY}-{kind.lower()}"}, PRINCIPAL)
            if s != 201:
                raise RuntimeError(f"post_event {kind} answered {s}: {got}")
        link_at = at(mill["case_link_at"])
        if recorded.last >= link_at:
            raise RuntimeError(f"STORY_CLOCK_ORDER: last work command {recorded.last} is not before the link {link_at}")
        with engine.connect() as c:
            head = str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                      "LIMIT 1"), {"c": case_id}).scalar_one())
        domain._store.test_db_clock_override = lambda: link_at
        s, linked = domain.post_case_link(tenant_id, site_id, code, action["id"], {
            "case_id": case_id, "case_revision_id": rev_id, "case_event_id": head, "actor": dict(ACTOR),
            "idempotency_key": f"{KEY}-link"}, PRINCIPAL)
        if s != 201:
            raise RuntimeError(f"post_case_link answered {s}: {linked}")
        return {"id": action["id"], "code": action["action_code"], "recorded_at": action["recorded_at"],
                "case_id": case_id, "case_state": got.get("state"), "case_link_recorded_at": linked["recorded_at"],
                "last_work_recorded_at": wire(recorded.last)}
    finally:
        domain._store.dispose()
        work._store.dispose()


def baseline_table(reader: Any, tenant_id: Any, site_id: Any, effective_day: date) -> dict:
    """Read the grades BEFORE freezing: a frozen plan is never rebuilt (P3)."""
    from assetops_backend.actions import verification_families as vf

    candidates = vf.baseline_candidates(effective_day)
    rows = reader.latest(tenant_id, site_id, candidates[-1], candidates[0], [vf.MEASURE])
    return vf.baseline_selection(vf.day_grades(rows, candidates), effective_day)


def consume_and_drain(url: str, tenant_id: Any, site_id: Any) -> dict:
    """P3's one fallback: the `chain_snapshots` consume and drain in process, no opportunity or thread stage. No plan
    exists yet, so the stage's evaluator call has nothing to judge."""
    from assetops_backend.scheduling.stages import chain_snapshots

    done = chain_snapshots(url, {"tenant_id": str(tenant_id), "site_id": str(site_id), "items": 100000,
                                 "consume_limit": 100000})
    return {k: done.get(k) for k in ("code", "processed", "deferred", "consume", "drain")}


def grade_span(reader: Any, tenant_id: Any, site_id: Any, effective_day: date) -> dict:
    """The stop's grade table: a day's grade and productive kWh, from -14 to +14 of the change."""
    from assetops_backend.actions import verification_families as vf

    span = [effective_day + timedelta(days=n) for n in range(-vf.LOOK_DAYS, vf.LOOK_DAYS + 1)]
    rows = reader.latest(tenant_id, site_id, span[0], span[-1], [vf.MEASURE])
    grades, kwh = vf.judged_grades(rows, span), vf.day_kwh(rows, span)
    return {d.isoformat(): {"grade": grades[d], "productive_kwh": None if kwh[d] is None else str(kwh[d])} for d in span}


def build(url: str, work: Path, story: dict) -> dict:
    from sqlalchemy import create_engine, text

    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.chain.composition import build_snapshot_reader
    from assetops_backend.prepare_clock import require_prepare_database

    require_prepare_database(url)
    mill = story["kobo"]["mill"]
    bad = instants_in_order(mill)
    if bad:
        raise SystemExit(f"STORY_CLOCK_ORDER: {bad}")
    S = at(story["S"])
    doc: dict[str, Any] = {"site_code": SITE, "S": story["S"], "stop": None, "known_at_disclosure":
                           "freeze and evaluate read rows as built (_AllKnown); the plan's snapshots_known_at is the story instant"}
    path = work / "mill.json"

    def stop(code: str, **detail) -> Stop:
        doc["stop"] = {"code": code, **detail}
        path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
        return Stop(f"MILL STOP {code}: see {path}")

    engine = create_engine(url)
    reader = build_snapshot_reader(url)
    store = build_action_store(url)
    try:
        with engine.connect() as c:
            tenant_id, site_id, tz = c.execute(text("SELECT tenant_id, id, timezone FROM site WHERE site_code = :c"),
                                               {"c": SITE}).one()
        effective_day = (S + timedelta(days=EFFECTIVE_OFFSET)).date()
        expected_baseline = [(S + timedelta(days=n)).date().isoformat() for n in BASELINE_OFFSETS]

        # P1: the pinned study
        ran = pinned_study(url, tenant_id, site_id, mill)
        done = [o for o in ran["outcomes"] if o["status"] == "DONE"]
        if ran["queued"] != 1 or len(ran["outcomes"]) != 1 or len(done) != 1:
            raise stop("STUDY_NOT_ONE", ran=ran)
        study = study_row(engine, done[0]["revision_id"])
        doc["study"] = {k: v for k, v in study.items() if k != "day_rows"}
        if not study["eligible_days"]:
            raise stop("P1_NO_ELIGIBLE_DAY", day_rows=study["day_rows"])
        if study["status"] != "SUPPORTED":
            print("P1: the pinned study is", study["status"], "with", study["eligible_days"], "eligible days; goes on "
                  "with this pin (DD1b2-R probe table)", flush=True)

        # P2: the Action, the COMPLETE case and its link
        try:
            doc["action"] = record_change(url, engine, tenant_id, site_id, study["opportunity_id"], study["revision_id"],
                                          mill)
        except Exception as error:  # noqa: BLE001 - every refusal stops here with its text
            raise stop("P2_ACTION_REFUSED", error=f"{type(error).__name__}: {error}"[:600]) from error

        # P3: the grades, before the freeze
        table = baseline_table(reader, tenant_id, site_id, effective_day)
        doc["baseline_before_any_tick"] = table
        doc["baseline_fallback"] = None
        if table["state"] != "FULL":
            doc["baseline_fallback"] = consume_and_drain(url, tenant_id, site_id)
            table = baseline_table(reader, tenant_id, site_id, effective_day)
            doc["baseline_after_fallback"] = table
        if table["state"] != "FULL" or table["days"] != expected_baseline:
            raise stop("P3_BASELINE_SHORT", expected=expected_baseline, baseline=table,
                       grades=grade_span(reader, tenant_id, site_id, effective_day))
        status, frozen = verification_service(store, reader, at(mill["freeze_at"])).freeze_domain_plan(
            tenant_id, site_id, doc["action"]["id"])
        doc["plan"] = {"http": status, "selection": frozen["plan"].get("baseline_selection"),
                       "effective_day": effective_day.isoformat()}
        if (frozen["plan"].get("baseline_selection") or {}).get("state") != "FULL":
            raise stop("P3_PLAN_NOT_FULL", plan=doc["plan"])

        # P4: the verdict, in story time; the tick's evaluator only replays what this stores
        service = verification_service(store, reader, at(mill["evaluate_at"]))
        judged = service.evaluate_domain_plan(tenant_id, site_id, doc["action"]["id"])
        doc["evaluate"] = judged
        doc["summary"] = service.domain_summary(tenant_id, site_id, doc["action"]["id"])
        if judged.get("state") != EXPECTED_OUTCOME:
            raise stop("P4_NOT_VERIFIED", judged=judged, grades=grade_span(reader, tenant_id, site_id, effective_day))
        path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
        print("mill:", doc["action"]["code"], judged["state"], "study", study["status"], study["eligible_days"], "eligible")
        return doc
    finally:
        engine.dispose()
        getattr(store, "dispose", lambda: None)()
        store_of_reader = getattr(reader, "_store", None)
        getattr(store_of_reader, "dispose", lambda: None)()


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "build":
        raise SystemExit("usage: demo_combined_mill.py build <url> <work>")
    work_dir = Path(sys.argv[3])
    build(sys.argv[2], work_dir, json.loads((work_dir / "story.json").read_text(encoding="utf-8")))
