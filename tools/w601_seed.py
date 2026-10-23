"""W6-01a (A1): the W6-01 global work fixture producer (`.agent/W6-01-build-spec.md` section 4).

    python tools/w601_seed.py --db assetops_w601_<unit>_test
        --fixture {incidents|zero|empty_scope|historical|cursor_change|stress|maintenance|preventive|detail|linked|
                   detail-linked|detail-history}
        --clock 2026-10-22T12:00:00Z [--append]

Creates (drops first) the private `*_test` database, migrates it to head, imports two tenants and their Sites
(`demo`: KOBO-001, KOBO-002; `w601-other`: KOBO-001) and writes work through the real W4 `WorkService` with the
server-side fixture SERVICE principal `service:w401-fixture` (A1Q Q9), never a browser-supplied actor. Each run has
one frozen fixture clock and an ordered write clock `11:59:00Z`, `11:59:01Z`, ... from `--clock` (successor writes
for `historical` and the `cursor_change --append` step use `12:00:01Z`, `12:00:02Z`). Incident roots occur at
`--clock` minus 2 days 3 hours, requests at minus 2 days 2 hours; a correction keeps its root and occurs one day
before `--clock`. Prints the stored IDs and codes read back from the database as JSON.

`stress` (W6-01a A2, A2Q2) writes six KOBO-001 incidents: incident 1 has a 200-character unbroken title and a
128-character unbroken assignee; incidents 2-6 are `Stress incident 2` ... `Stress incident 6` (five rows plus Next).
`empty_scope` seeds the same rows as `incidents`; the empty scope is the read's access callback denying every Site.
W6-01b (B1, `.agent/W6-01-build-spec.md` "B1-B3 pre-flight rulings" P-B1-1..9) adds `maintenance` (seven `demo`
requests over KOBO-001/KOBO-002 in every reachable state plus one other-tenant request), `preventive` (five `demo` DRAFT
plans, two RUN_HOURS, plus one other-tenant plan), `detail` (the C2-C4 request with CREATED, ASSIGN, COMMENT, a
record, COMPLETE, REOPEN and a case revision, and a second CANCELLED request), `linked` (a real S4 Finding and S6
Action, created by the merged test producers with an earlier F01 decision and accept clock (Q2), pinned to one incident and two requests),
the `stress` request/record/revision/plan and the `historical` plan root plus correction. B1 captures use
`--clock 2026-10-20T12:00:00Z` and the window `[2026-10-14, 2026-10-21)`. E1 adds `operational`.
W6-01c C1 ("C1-C3 pre-flight rulings"): `detail` also appends one OPERATOR_LOG linked to its first request (CL3-3,
occurrence `--clock` minus 2 days); `detail-linked` is `detail` on the `linked` producer's Site plus an incident
pinned to the real Finding/Action and a third request sourced from that incident with the same pins; `detail-history`
is `detail` plus one correction revision of the first request at `--clock + 2s` (the C2 historical capture reads at
`--clock + 1s`).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
for extra in (REPO, REPO / "backend", REPO / "contracts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from assetops_backend.evidence.composition import build_link_rows_reader  # noqa: E402
from assetops_backend.sites.adapters.import_files import read_import_source  # noqa: E402
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore  # noqa: E402
from assetops_backend.sites.foundation_service import ImportSource, import_site  # noqa: E402
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore  # noqa: E402
from assetops_backend.work.service import WorkService  # noqa: E402
from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID  # noqa: E402

PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
DB_NAME = re.compile(r"^assetops_w601_[a-z0-9_]{1,40}_test$")
KOBO_SOURCE = REPO / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
FIXTURES = ("incidents", "zero", "empty_scope", "historical", "cursor_change", "stress", "maintenance", "preventive",
            "detail", "linked", "detail-linked", "detail-history")
ACTOR = {"kind": "SERVICE", "id": W401_FIXTURE_SERVICE_PRINCIPAL_ID,
         "attestation": "service=w401-fixture;job=w601-seed;rule=w601/1"}
# A2Q2: 200 and 128 unbroken characters.
STRESS_TITLE = ("Backupgeneratorautomaticstartfailure" * 6)[:200]
STRESS_OWNER = ("Fieldmaintenancesupervisorteam" * 5)[:128]
SITES = (("demo", "KOBO-001"), ("demo", "KOBO-002"), ("w601-other", "KOBO-001"))
# X2 / P-B1-6/7: the B1 stress additions as ruled (the expressions store 4,000 and 500 characters).
STRESS_REQUEST_TITLE = ("Startermotorandcontrolpanelinspection" * 6)[:200]
STRESS_NARRATIVE = ("Inspection narrative " * 200)[:4000].rstrip()
STRESS_ACTIVITY = ("Replaced starter relay and tested " * 120)[:4000]
STRESS_REASON = ("Corrected the inspection scope " * 20)[:500].rstrip()
STRESS_PLAN_TITLE = ("Quarterlyfilterandbeltinspection" * 7)[:200]
# W6-01b build rulings (Q2) item 1: the linked fixture keeps the S4 setup, F01 day, readings and anchors (all inside
# the KOBO-001 Foundation period from 2026-09-29) and moves only F01's `deliver.decided` and the S6 accept clock earlier.
LINKED_SETUP_AT = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)
LINKED_DECIDED = "2026-10-19T08:00:00Z"  # original 2026-10-30T08:00:00Z
LINKED_ACCEPT_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
LINKED_FINDING_WINDOW = ("2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z")
# W6-01c C1: the CL3-3 linked REC body; the `detail-history` successor revision; the `detail-linked` titles.
DETAIL_REC_BODY = "Checked the starter after the inspection."
HISTORY_TITLE = "Inspect starter, control circuit and witnessed start"
HISTORY_NARRATIVE = "Repeat the starter check and record the witnessed start test."
HISTORY_REASON = "Witnessed start test added to the scope"
DETAIL_LINKED_INCIDENT = "Generator failed to start after the Finding"
DETAIL_LINKED_REQUEST = "Inspect starter for the failed start"


def db_url(db: str) -> str:
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != timedelta(0):
        raise SystemExit("--clock must be a UTC instant")
    return parsed.astimezone(timezone.utc)


def z(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class WriteClock:
    """The ordered fixture write clock: each W4 command takes the next instant, one second apart."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        value, self.now = self.now, self.now + timedelta(seconds=1)
        return value


def create_database(db: str) -> str:
    """Drop and recreate the private `*_test` database, then migrate it to head."""
    if not DB_NAME.match(db):
        raise SystemExit(f"--db must match {DB_NAME.pattern} (a private *_test database)")
    import psycopg
    from alembic import command
    from alembic.config import Config

    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
        admin.execute(f'CREATE DATABASE "{db}"')
    config = Config(str(REPO / "backend" / "alembic.ini"))
    config.attributes["database_url"] = db_url(db)
    command.upgrade(config, "head")
    return db_url(db)


def import_sites(url: str, clock: datetime) -> dict[tuple[str, str], dict[str, Any]]:
    """Two tenants, three imported Sites, each imported three days before `--clock` (before the window's `to`)."""
    source = read_import_source(str(KOBO_SOURCE))
    store = PostgresFoundationStore(url)
    out = {}
    try:
        for slug, code in SITES:
            record = source.record if code == "KOBO-001" else replace(source.record, site_id=code)
            result = import_site(store, tenant_slug=slug, configured_tenant_slug=slug,
                                 source=ImportSource(path=f"var/sites/{slug}-{code.lower()}.yaml",
                                                     sha256=source.sha256, record=record),
                                 legacy_documents=(), clock=lambda: clock - timedelta(days=3))
            out[(slug, code)] = {"tenant": result.tenant.id, "site": result.site.id, "site_code": code}
    finally:
        engine = getattr(store, "_engine", None)
        if engine is not None:
            engine.dispose()
    return out


class Writer:
    """W4 `WorkService` commands with the injected fixture principal and the ordered write clock."""

    def __init__(self, url: str, clock: WriteClock, sites: dict[tuple[str, str], dict[str, Any]],
                 fixture_clock: datetime) -> None:
        self.svc = WorkService(PostgresWorkStore(url, link_rows=build_link_rows_reader(),
                                                 test_db_clock_override=clock))
        self.sites, self.clock, self.write_clock = sites, fixture_clock, clock
        self.written: list[dict[str, Any]] = []
        # B1: events, records and revisions (the case/plan rows stay in `written`, whose shape A1 tests read).
        self.commands: list[dict[str, Any]] = []

    def _key(self) -> str:
        """Unique per command: each command takes exactly one write-clock instant, the next one."""
        return f"w601-{self.write_clock.now:%Y%m%dT%H%M%S%f}"

    def incident(self, site: tuple[str, str], title: str, *, finding_links: list | None = None,
                 action_links: list | None = None) -> dict[str, Any]:
        s = self.sites[site]
        body = {"kind": "INCIDENT", "occurred_at": z(self.clock - timedelta(days=2, hours=3)), "asset_id": None,
                "finding_links": finding_links or [], "action_links": action_links or [], "title": title,
                "narrative": "Operator reported a stop; cause not established.", "cited_accepted_evidence_ids": [],
                "actor": dict(ACTOR), "idempotency_key": self._key()}
        _, made = self.svc.create_case(s["tenant"], s["site"], body, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.written.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": made["id"],
                             "code": made["code"], "kind": "INCIDENT", "revision_id": made["revision"]["id"]})
        return made

    def request(self, site: tuple[str, str], incident_id: str | None, title: str, *,
                narrative: str = "Inspection requested.", finding_links: list | None = None,
                action_links: list | None = None) -> dict[str, Any]:
        s = self.sites[site]
        body = {"kind": "MAINTENANCE_REQUEST", "occurred_at": z(self.clock - timedelta(days=2, hours=2)),
                "asset_id": None, "finding_links": finding_links or [], "action_links": action_links or [],
                "title": title, "narrative": narrative, "cited_accepted_evidence_ids": [], "actor": dict(ACTOR),
                "idempotency_key": self._key(), **({} if incident_id is None else {"incident_id": incident_id})}
        _, made = self.svc.create_case(s["tenant"], s["site"], body, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.written.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": made["id"],
                             "code": made["code"], "kind": "MAINTENANCE_REQUEST", "incident_id": incident_id})
        return made

    def assign(self, site: tuple[str, str], case_id: str, assignee: str) -> None:
        self.event(site, case_id, "ASSIGN", {"assignee": assignee})

    def event(self, site: tuple[str, str], case_id: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        s = self.sites[site]
        _, made = self.svc.post_event(s["tenant"], s["site"], case_id, {
            "kind": kind, "occurred_at": z(self.clock - timedelta(days=1)), "payload": payload,
            "actor": dict(ACTOR), "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.commands.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": case_id,
                             "event": kind, "event_id": _event_id(made)})
        return made

    def record(self, site: tuple[str, str], case_id: str, activity: str, outcome_note: str | None) -> str:
        s = self.sites[site]
        _, made = self.svc.post_record(s["tenant"], s["site"], case_id, {
            "activity": activity, "outcome_note": outcome_note, "occurred_at": z(self.clock - timedelta(days=1)),
            "actor": dict(ACTOR), "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.commands.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": case_id,
                             "record_id": made["id"]})
        return made["id"]

    def complete(self, site: tuple[str, str], case_id: str, activity: str, outcome_note: str | None) -> str:
        """A performed record, then COMPLETE referring to that stored record (W4 `record_in_case`)."""
        record_id = self.record(site, case_id, activity, outcome_note)
        self.event(site, case_id, "COMPLETE", {"maintenance_record_id": record_id})
        return record_id

    def revise(self, site: tuple[str, str], case_id: str, revision_id: str, title: str, narrative: str,
               reason: str) -> dict[str, Any]:
        s = self.sites[site]
        _, made = self.svc.post_revision(s["tenant"], s["site"], case_id, {
            "supersedes_revision_id": revision_id, "title": title, "narrative": narrative, "reason": reason,
            "occurred_at": z(self.clock - timedelta(days=1)), "actor": dict(ACTOR),
            "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.commands.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": case_id,
                             "revision_id": made["revision_id"], "reason": reason})
        return made

    def plan(self, site: tuple[str, str], title: str, trigger: str, *, due_at: datetime | None = None,
             due_hours: str | None = None, occurred_at: datetime | None = None,
             correction: dict[str, str] | None = None) -> dict[str, Any]:
        """A DRAFT plan (root occurrence `--clock` minus 2 days 1 hour) or, with `correction`, its successor."""
        s = self.sites[site]
        at = self.clock - timedelta(days=2, hours=1) if occurred_at is None else occurred_at
        _, made = self.svc.post_plan(s["tenant"], s["site"], {
            "asset_id": None, "title": title, "trigger_kind": trigger,
            "next_due_at": None if due_at is None else z(due_at), "next_due_hours": due_hours,
            "occurred_at": z(at), "actor": dict(ACTOR), "idempotency_key": self._key(), **(correction or {})},
            W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.written.append({"tenant": slug_of(site), "site_code": s["site_code"], "plan_id": made["id"],
                             "code": made["public_code"], "kind": "PLAN", "title": title,
                             "supersedes_plan_id": (correction or {}).get("supersedes_plan_id")})
        return made

    def post_operational_record(self, site: tuple[str, str], case_id: str | None, body: str, *,
                                kind: str = "OPERATOR_LOG", occurred_at: datetime | None = None,
                                correction: dict[str, str] | None = None) -> dict[str, Any]:
        """C1 (CL3-3): an authored SUBMITTED operational record (root occurrence `--clock` minus 2 days) or, with
        `correction`, its successor; the next write-clock instant and the fixture SERVICE principal."""
        s = self.sites[site]
        at = self.clock - timedelta(days=2) if occurred_at is None else occurred_at
        _, made = self.svc.post_operational_record(s["tenant"], s["site"], {
            "kind": kind, "body": body, "occurred_at": z(at), "period_end": None, "unit": None, "quantity": None,
            "source_document_sha256": None, "case_id": case_id, "actor": dict(ACTOR),
            "idempotency_key": self._key(), **(correction or {})}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.commands.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": case_id,
                              "operational_record_id": made["id"], "canonical_record_id": made["canonical_record_id"],
                              "code": made["public_code"], "recorded_at": made["recorded_at"]})
        return made

    def correct(self, site: tuple[str, str], case_id: str, revision_id: str, title: str) -> dict[str, Any]:
        s = self.sites[site]
        _, made = self.svc.post_revision(s["tenant"], s["site"], case_id, {
            "supersedes_revision_id": revision_id, "title": title, "narrative": "Corrected after review.",
            "reason": "Title corrected", "occurred_at": z(self.clock - timedelta(days=1)), "actor": dict(ACTOR),
            "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        return made

    def close(self) -> None:
        self.svc._store.dispose()


def slug_of(site: tuple[str, str]) -> str:
    return site[0]


def _event_id(made: dict[str, Any]) -> str | None:
    event = made.get("event") if isinstance(made, dict) else None
    return None if not isinstance(event, dict) else event.get("id")


A, B, OTHER = ("demo", "KOBO-001"), ("demo", "KOBO-002"), ("w601-other", "KOBO-001")


def seed(url: str, fixture: str, clock: datetime, *, append: bool = False) -> dict[str, Any]:
    """Write one fixture into an already migrated database whose Sites `import_sites` created."""
    if fixture not in FIXTURES:
        raise SystemExit(f"--fixture must be one of {', '.join(FIXTURES)}")
    if fixture in ("linked", "detail-linked"):
        if append:
            raise SystemExit("--append applies only to --fixture cursor_change")
        return seed_linked(url, clock) if fixture == "linked" else seed_detail_linked(url, clock)
    sites = import_sites(url, clock) if not append else _existing_sites(url)
    base = clock - timedelta(minutes=1)
    if append:
        if fixture != "cursor_change":
            raise SystemExit("--append applies only to --fixture cursor_change")
        writer = Writer(url, WriteClock(clock + timedelta(seconds=2)), sites, clock)
        try:
            writer.incident(A, "Late incident appended after page one")
        finally:
            writer.close()
        return {"fixture": fixture, "append": True, "written": writer.written, **_ids(sites)}
    writer = Writer(url, WriteClock(base), sites, clock)
    try:
        if fixture == "stress":
            # A2Q2: the A2 capture stress rows, all in tenant one at Site KOBO-001.
            first = writer.incident(A, STRESS_TITLE)
            for n in range(2, 7):
                writer.incident(A, f"Stress incident {n}")
            writer.assign(A, first["id"], STRESS_OWNER)
            # X2 / P-B1-4/6/7: one long request (owner, narrative, record) with a case revision, and one long plan.
            long = writer.request(A, None, STRESS_REQUEST_TITLE, narrative=STRESS_NARRATIVE)
            writer.assign(A, long["id"], STRESS_OWNER)
            writer.record(A, long["id"], STRESS_ACTIVITY, "Authored note")
            writer.revise(A, long["id"], long["revision"]["id"], STRESS_REQUEST_TITLE, STRESS_NARRATIVE,
                          STRESS_REASON)
            writer.plan(A, STRESS_PLAN_TITLE, "CALENDAR")
        elif fixture == "maintenance":
            seed_maintenance(writer)
        elif fixture == "preventive":
            seed_preventive(writer)
        elif fixture in ("detail", "detail-history"):
            made = seed_detail(writer)
        elif fixture != "zero":
            first = writer.incident(A, "Generator stopped")
            second = writer.incident(A, "Inverter fault reported")
            writer.incident(A, "Battery alarm acknowledged")
            writer.incident(A, "Feeder breaker tripped")
            writer.incident(B, "Pump stopped")
            writer.incident(B, "Panel door open")
            writer.incident(OTHER, "Other tenant incident")
            writer.assign(A, first["id"], "Field team A")
            writer.request(A, first["id"], "Inspect starter")
            writer.correct(A, second["id"], second["revision"]["id"], "Inverter fault confirmed")
        if fixture == "historical":
            later = Writer(url, WriteClock(clock + timedelta(seconds=1)), sites, clock)
            try:
                later.correct(A, first["id"], first["revision"]["id"], "Generator stopped twice")
                later.incident(B, "Late incident after the historical cutoff")
            finally:
                later.close()
            writer.written.extend(later.written)
            # CL3-4 as ruled by P-B1-8: the plan root at `--clock + 3s` and its correction at `+4s`.
            plans = Writer(url, WriteClock(clock + timedelta(seconds=3)), sites, clock)
            try:
                root = plans.plan(A, "Inspect filters", "CALENDAR", due_at=clock + timedelta(days=7))
                plans.plan(A, "Inspect filters", "CALENDAR", due_at=clock + timedelta(days=14),
                           occurred_at=clock - timedelta(days=1),
                           correction={"supersedes_plan_id": root["id"], "canonical_plan_id": root["id"],
                                       "correction_reason": "Due date corrected after review"})
            finally:
                plans.close()
            writer.written.extend(plans.written)
        if fixture == "detail-history":
            # C2 historical capture (ruling "For the required 403 capture ..."): one explicit write at
            # `--clock + 2s` that changes the first request's selected revision; read at `--clock + 1s` for history.
            later = Writer(url, WriteClock(clock + timedelta(seconds=2)), sites, clock)
            try:
                later.revise(A, made["first"]["id"], made["revision"]["revision_id"], HISTORY_TITLE,
                             HISTORY_NARRATIVE, HISTORY_REASON)
            finally:
                later.close()
            writer.commands.extend(later.commands)
    finally:
        writer.close()
    return {"fixture": fixture, "clock": z(clock), "written": writer.written, "commands": writer.commands,
            **_ids(sites)}


def seed_maintenance(writer: Writer) -> None:
    """P-B1-4: seven `demo` requests (OPEN 4, IN_PROGRESS 1, COMPLETED 1, CANCELLED 1) and one other-tenant one."""
    made = [writer.request(site, None, title) for site, title in (
        (A, "Inspect starter"), (A, "Inspect transfer switch"), (A, "Replace breaker"), (A, "Check feeder contacts"),
        (B, "Inspect pump"), (B, "Check panel door"))]
    writer.event(A, made[3]["id"], "CANCEL", {"reason": "Work withdrawn after scope review"})
    writer.assign(B, made[4]["id"], "Field team B")
    writer.assign(B, made[5]["id"], "Field team C")
    writer.complete(B, made[5]["id"], "Inspected panel door contacts.", "Operation not verified.")
    writer.request(A, None, "Inspect inverter relay")
    writer.request(OTHER, None, "Other tenant inspection")


def seed_preventive(writer: Writer) -> None:
    """P-B1-4/9: five `demo` DRAFT plans (root occurrence October 18 for the B1 clock) and one other-tenant plan."""
    writer.plan(A, "Inspect filters", "CALENDAR", due_at=utc("2026-10-29T00:00:00Z"))
    writer.plan(A, "Generator 500-hour service", "RUN_HOURS", due_hours="500")
    writer.plan(A, "Check battery cabinet", "CALENDAR", due_at=utc("2026-11-01T00:00:00Z"))
    writer.plan(B, "Inspect pump seals", "CALENDAR", due_at=utc("2026-10-25T00:00:00Z"))
    writer.plan(B, "Review switchgear", "RUN_HOURS", due_hours="750")
    writer.plan(OTHER, "Other tenant plan", "CALENDAR", due_at=utc("2026-10-29T00:00:00Z"))


def seed_detail(writer: Writer) -> dict[str, Any]:
    """P-B1-5 / X9: the C2-C4 request and its second, cancelled request; each command takes the next second.
    C1 (CL3-3) appends one OPERATOR_LOG on the first request at the next write-clock instant."""
    first = writer.request(A, None, "Inspect starter and control circuit",
                           narrative="Inspect the failed start path before returning the generator to service.")
    writer.assign(A, first["id"], "Maintenance lead")
    writer.event(A, first["id"], "COMMENT", {"text": "Starter relay inspection scheduled."})
    writer.complete(A, first["id"], "Inspected starter relay and control wiring.",
                    "Witnessed start test still required.")
    writer.event(A, first["id"], "REOPEN", {"reason": "Witnessed start test was not recorded"})
    revision = writer.revise(A, first["id"], first["revision"]["id"], "Inspect starter and control circuit again",
                             "Repeat the starter check and record the witnessed test.", "Inspection scope corrected")
    second = writer.request(A, None, "Check spare relay", narrative="Spare relay check requested.")
    writer.event(A, second["id"], "CANCEL", {"reason": "Duplicate request; first inspection covers the relay"})
    rec = writer.post_operational_record(A, first["id"], DETAIL_REC_BODY)
    return {"first": first, "second": second, "revision": revision, "rec": rec}


def _linked_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Q2 item 1: a private copy of the S4 SPEC whose only change is F01's `deliver.decided`."""
    out = copy.deepcopy(spec)
    [f01] = [c for c in out["cases"] if c["case_id"] == "F01"]
    delivers = [step for step in f01["steps"] if "decided" in step]
    if len(delivers) != 1:
        raise SystemExit("linked: the S4 F01 case no longer has exactly one decided step")
    delivers[0]["decided"] = LINKED_DECIDED
    return out


def _linked_producer(url: str) -> dict[str, Any]:
    """Q2 item 1: a real S4 Finding and S6 Action through the merged test producers on the ruled clocks."""
    os.environ["ASSETOPS_TEST_DATABASE_URL"] = url  # before the producer modules read their module-level URL
    tests = REPO / "backend" / "tests"
    if str(tests) not in sys.path:
        sys.path.insert(0, str(tests))
    from sqlalchemy import create_engine

    import test_s4_finding_store_postgres as s4
    import test_s6_action_store_postgres as s6
    import test_w401_work_service_postgres as w401
    from test_s4_finding_index_postgres import client_for, ok

    spec = _linked_spec(s4.SPEC)
    f01 = {c["case_id"]: c for c in spec["cases"]}["F01"]
    saved = (s4.SPEC, s4.SETUP_AT, s6.T_ACCEPT)
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    runner = None
    try:
        s4.SPEC, s4.SETUP_AT, s6.T_ACCEPT = spec, LINKED_SETUP_AT, LINKED_ACCEPT_AT
        runner = s4.CaseRunner(store, engine)
        s4.run_case(runner, f01)
        body = ok(client_for(runner), frm=LINKED_FINDING_WINDOW[0], to=LINKED_FINDING_WINDOW[1], limit=50)
        if body["status"] != "CURRENT" or not body["rows"]:
            raise SystemExit(f"linked: no public F01 Finding in {LINKED_FINDING_WINDOW}")
        row = body["rows"][0]
        fid, frev = row["finding_id"], row["finding_revision_id"]
        action_id, action_event = w401.accepted_action(runner, fid, "w601-linked-accept-001")
        tenant, site = runner.tenant, runner.site
    finally:
        s4.SPEC, s4.SETUP_AT, s6.T_ACCEPT = saved
        for owned in ((runner.findings,) if runner is not None else ()) + (store,):
            owned_engine = getattr(owned, "_engine", None)
            if owned_engine is not None:
                owned_engine.dispose()
        engine.dispose()
    return {"tenant": tenant, "site": site, "finding_id": fid, "finding_revision_id": frev, "action_id": action_id,
            "action_event_id": action_event}


def seed_linked(url: str, clock: datetime) -> dict[str, Any]:
    """Q2 item 1: the real Finding and Action, then one incident and two requests through `WorkService` pinned to
    them, read back through the global roots."""
    made = _linked_producer(url)
    tenant, site, fid, frev = made["tenant"], made["site"], made["finding_id"], made["finding_revision_id"]
    action_id, action_event = made["action_id"], made["action_event_id"]
    sites = {A: {"tenant": tenant, "site": site, "site_code": "KOBO-001"}}
    finding = [{"finding_id": fid, "finding_revision_id": frev}]
    action = [{"action_id": action_id, "action_event_id": action_event}]
    writer = Writer(url, WriteClock(utc("2026-10-20T11:59:00Z")), sites, clock)
    try:
        incident = writer.incident(A, "Generator stopped after the Finding", finding_links=finding,
                                   action_links=action)
        first = writer.request(A, None, "Inspect starter for the Finding", finding_links=finding,
                               action_links=action)
        writer.request(A, None, "Follow up the accepted Action", action_links=action)
    finally:
        writer.close()
    hrefs = _linked_hrefs(url, tenant, fid, action_id, incident["id"], first["id"])
    return {"fixture": "linked", "clock": z(clock), "written": writer.written, "commands": writer.commands,
            "tenant_id": str(tenant), "site_id": str(site), "finding_id": fid, "finding_revision_id": frev,
            "action_id": action_id, "action_event_id": action_event, "hrefs": hrefs,
            "sites": [{"tenant": "demo", "site_code": "KOBO-001", "tenant_id": str(tenant), "site_id": str(site)}]}


def seed_detail_linked(url: str, clock: datetime) -> dict[str, Any]:
    """C1 (P-C1-11): `detail` on the `linked` producer's Site, then an incident pinned to the real Finding and Action
    and a third request sourced from that incident with the same pins. Fails unless the C1 detail of that request
    carries the source incident and lineage-true Finding and Action links."""
    made = _linked_producer(url)
    tenant, site = made["tenant"], made["site"]
    sites = {A: {"tenant": tenant, "site": site, "site_code": "KOBO-001"}}
    finding = [{"finding_id": made["finding_id"], "finding_revision_id": made["finding_revision_id"]}]
    action = [{"action_id": made["action_id"], "action_event_id": made["action_event_id"]}]
    writer = Writer(url, WriteClock(clock - timedelta(minutes=1)), sites, clock)
    try:
        seed_detail(writer)
        incident = writer.incident(A, DETAIL_LINKED_INCIDENT, finding_links=finding, action_links=action)
        third = writer.request(A, incident["id"], DETAIL_LINKED_REQUEST, finding_links=finding, action_links=action)
    finally:
        writer.close()
    links = _detail_links(url, tenant, site, third["id"])
    return {"fixture": "detail-linked", "clock": z(clock), "written": writer.written, "commands": writer.commands,
            "tenant_id": str(tenant), "site_id": str(site),
            **{k: v for k, v in made.items() if k not in ("tenant", "site")},
            "incident_id": incident["id"], "request_id": third["id"], "detail_links": links,
            "sites": [{"tenant": "demo", "site_code": "KOBO-001", "tenant_id": str(tenant), "site_id": str(site)}]}


def _detail_links(url: str, tenant: Any, site: Any, request_id: str) -> dict[str, Any]:
    """The C1 outer links of the incident-sourced request at the current read time (no explicit cutoff)."""
    from assetops_backend.work.composition import build_global_work_read
    from assetops_backend.work.global_detail import GlobalWorkDetailService

    read = build_global_work_read(url)
    try:
        body = GlobalWorkDetailService(read).detail(tenant, site, "KOBO-001", request_id, [])
    finally:
        read.dispose()
    links = body["links"]
    if (links["source_incident"] is None or not any(x["href"] for x in links["findings"])
            or not any(x["href"] for x in links["actions"])):
        raise SystemExit(f"detail-linked: the request detail lacks its source incident or a lineage-true Finding "
                         f"or Action link: {links}")
    return {"code": body["selected"]["case_code"], "known_at": body["selected"]["known_at"],
            "source_incident": links["source_incident"], "findings": links["findings"], "actions": links["actions"]}


def _linked_hrefs(url: str, tenant: Any, fid: str, action_id: str, incident_id: str, request_id: str
                  ) -> dict[str, Any]:
    """Fail unless the persisted incident and first request expose lineage-true Finding and Action hrefs on the
    global roots (current read, window `[2026-10-14, 2026-10-21)`). A missing cursor key gets a process-local one."""
    from assetops_backend.work.composition import build_global_work_read
    from assetops_backend.work.global_index import CURSOR_KEY_ENV, GlobalWorkIndexService, parse_global_request

    if not os.environ.get(CURSOR_KEY_ENV):
        os.environ[CURSOR_KEY_ENV] = os.urandom(32).hex()
    read = build_global_work_read(url)
    out = {}
    try:
        service = GlobalWorkIndexService(read)
        for kind, case_id in (("incidents", incident_id), ("maintenance", request_id)):
            request = parse_global_request(kind, [("from", "2026-10-14T00:00:00Z"), ("to", "2026-10-21T00:00:00Z")])
            body = service.read(tenant, kind, request, lambda code: True)
            [row] = [r for r in body["rows"] if r["case_id"] == case_id]
            finding = [x for x in row["finding_links"] if x["label"] == f"Finding {fid[:8]}" and x["href"]]
            act = [x for x in row["action_links"] if x["label"] == f"Action {action_id[:8]}" and x["href"]]
            if not finding or not act:
                raise SystemExit(f"linked: /api/work/{kind} row {row['code']} lacks a lineage-true Finding or Action "
                                 f"href: {row['finding_links']} {row['action_links']}")
            out[kind] = {"code": row["code"], "finding": finding[0], "action": act[0], "known_at": body["known_at"]}
    finally:
        read.dispose()
    return out


def _existing_sites(url: str) -> dict[tuple[str, str], dict[str, Any]]:
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT t.slug, s.site_code, t.id, s.id FROM site s JOIN tenant t "
                                  "ON t.id = s.tenant_id")).all()
    finally:
        engine.dispose()
    return {(r[0], r[1]): {"tenant": r[2], "site": r[3], "site_code": r[1]} for r in rows}


def _ids(sites: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    return {"sites": [{"tenant": slug, "site_code": code, "tenant_id": str(v["tenant"]), "site_id": str(v["site"])}
                      for (slug, code), v in sorted(sites.items())]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--fixture", required=True, choices=FIXTURES)
    parser.add_argument("--clock", required=True)
    parser.add_argument("--append", action="store_true", help="cursor_change: append one row at --clock + 2 s")
    args = parser.parse_args(argv)
    clock = utc(args.clock)
    if args.append:
        if not DB_NAME.match(args.db):
            raise SystemExit(f"--db must match {DB_NAME.pattern}")
        url = db_url(args.db)
    else:
        url = create_database(args.db)
    print(json.dumps(seed(url, args.fixture, clock, append=args.append), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
