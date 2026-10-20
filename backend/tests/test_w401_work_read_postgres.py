"""W4-01 commit 3: the work read adapter's pinned link coverage over real Postgres (Run 3 rulings 6-8, q3 test
placement; W3-01 Run 7 q7-1 cross-reference).

- Mini-grid: the F01 Finding and its accepted Action (closure 3 Q7) pinned on a case; the detail and Q9 coverage
  read every link on the adapter's one read-only REPEATABLE READ connection.
- Cold: a pinned cold Finding link at an explicit cutoff keeps the exact seq selected then, after a later
  reselection of the same old run; a later read may select the later seq, never another assessment.

Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, runner  # noqa: F401
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, run
    from test_w401_work_service_postgres import PRINCIPAL, accepted_action, incident, public_finding

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.composition import _link_read_ports, build_work_service
    from assetops_backend.work.detail import WorkDetailService
    from assetops_backend.work.link_coverage import linked_coverage


class Recorded:
    """The composition's shared read ports, recording the connection each call receives."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object, bool]] = []
        ports = _link_read_ports()

        def wrap(name, fn):
            def call(c, *args, **kwargs):
                self.calls.append((name, c, c.in_transaction()))
                return fn(c, *args, **kwargs)
            return call

        self.ports = replace(ports, **{n: wrap(n, getattr(ports, n)) for n in (
            "cold_snapshot", "ev_snapshot", "selected_windows", "dispatch_days", "finding_index")})


def reader(recorded: Recorded) -> PostgresWorkRead:
    return PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=recorded.ports)


def coverage_at(read: PostgresWorkRead, t, s, code: str, revision_id: str, known_at: datetime | None = None):
    def work(rx):
        k = rx.read_at if known_at is None else known_at
        rows = rx.link_selections(revision_id, None, None, k)
        return rx._c, rows, linked_coverage(rx, t, s, revision_id, None, None, k)
    return read.snapshot(t, s, code, work)


def test_minigrid_pinned_finding_and_action_coverage_on_one_connection(runner) -> None:  # noqa: F811
    run_case(runner, CASES["F01"])
    row = public_finding(runner)
    fid, frev = row["finding_id"], row["finding_revision_id"]
    action_id, action_event = accepted_action(runner, fid, "w401-read-accept-001")
    svc = build_work_service(URL)
    try:
        status, created = svc.create_case(runner.tenant, runner.site, incident(
            "w401-read-incident-001", finding_links=[{"finding_id": fid, "finding_revision_id": frev}],
            action_links=[{"action_id": action_id, "action_event_id": action_event}]), PRINCIPAL)
    finally:
        svc._store.dispose()
    assert status == 201
    revision_id = created["revision"]["id"]
    # The F01 runner writes on its virtual clock (from 2026-10-29), so the coverage cutoff is the runner's last
    # recorded instant, not the wall-clock read time (see the handoff's F01 virtual-clock note).
    with runner.engine.connect() as c:
        k = c.execute(text(
            "SELECT greatest((SELECT created_at FROM finding_revision WHERE id = :r), "
            "(SELECT recorded_at FROM action_event WHERE id = :e))"), {"r": frev, "e": action_event}).scalar_one()
    recorded = Recorded()
    read = reader(recorded)
    try:
        conn, rows, coverage = coverage_at(read, runner.tenant, runner.site, "KOBO-001", revision_id, k)
        detail = WorkDetailService(read).detail(runner.tenant, runner.site, "KOBO-001", created["id"], [])
    finally:
        read.dispose()
    # Every pinned link resolved its exact pinned row; none fell back to a head.
    assert [(r["kind"], r["id"], r["selected_id"], r["domain"]) for r in rows] == [
        ("FINDING", fid, frev, "mini_grid"), ("ACTION", action_id, action_event, "mini_grid")]
    assert all(r["pin"] is not None and r["pin"]["days"] for r in rows), rows
    links = {x["kind"]: x for x in coverage["links"]}
    assert set(links) == {"FINDING", "ACTION"}
    assert {x["state"] for x in coverage["links"]} <= {"CURRENT", "PENDING_RECOMPUTE"}
    assert all(x["selection_token"].startswith("sha256:") for x in coverage["links"])
    assert coverage["state"] in ("COMPLETE", "PARTIAL") and (coverage["state"] == "COMPLETE") == (
        coverage["reason"] is None)
    # Same connection: every shared read ran on the snapshot's own connection, inside its transaction.
    assert {name for name, _, _ in recorded.calls} == {"dispatch_days", "finding_index"}
    assert all(c is conn and inside for _, c, inside in recorded.calls)
    # Detail carries the pinned links and Q11 provenance over them.
    assert detail["finding_links"] == [{"finding_id": fid, "finding_revision_id": frev}]
    assert detail["action_links"] == [{"action_id": action_id, "action_event_id": action_event}]
    assert set(detail["coverage"]) == {"state", "reason"}


def test_missing_pin_is_unknown_never_a_head(runner) -> None:  # noqa: F811
    """A pinned Finding revision that did not exist at the cutoff is UNKNOWN / LINK_SELECTION_MISSING."""
    run_case(runner, CASES["F01"])
    row = public_finding(runner)
    svc = build_work_service(URL)
    try:
        _, created = svc.create_case(runner.tenant, runner.site, incident(
            "w401-read-incident-002", finding_links=[{"finding_id": row["finding_id"],
                                                      "finding_revision_id": row["finding_revision_id"]}]),
            PRINCIPAL)
    finally:
        svc._store.dispose()
    with runner.engine.connect() as c:
        made = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"),
                         {"r": row["finding_revision_id"]}).scalar_one()
    read = reader(Recorded())
    try:
        _, rows, coverage = coverage_at(read, runner.tenant, runner.site, "KOBO-001", created["revision"]["id"],
                                        made - timedelta(microseconds=1))
    finally:
        read.dispose()
    assert rows[0]["pin"] is None
    assert coverage["state"] == "UNKNOWN" and coverage["reason"] == "LINK_SELECTION_MISSING"
    assert coverage["links"][0]["state"] == "UNKNOWN" and coverage["links"][0]["selection_token"] is None


def test_cold_pinned_link_keeps_its_seq_after_reselection(chain) -> None:  # noqa: F811
    """W3-01 Run 7 q7-1 through W4: a pinned cold link read at explicit cutoff K keeps the seq selected by K
    after a later reselection of the same old run (TEST-SCOPED direct append, as the W3 proof does)."""
    built = opened("excursion", chain)
    run(built)
    t, s = built.tenant_id, built.site_id
    with built.engine.connect() as c:
        pin = c.execute(text(
            "SELECT CAST(finding_id AS text), CAST(id AS text), analytic_id FROM finding_revision WHERE site_id = :s "
            "AND domain = 'cold_chain' ORDER BY created_at DESC, id LIMIT 1"), {"s": s}).first()
    assert pin is not None, "the cold excursion replay wrote no cold Finding"
    fid, frev, analytic = pin
    svc = build_work_service(URL)
    try:
        status, created = svc.create_case(t, s, incident(
            "w401-cold-incident-001", finding_links=[{"finding_id": fid, "finding_revision_id": frev}]), PRINCIPAL)
    finally:
        svc._store.dispose()
    assert status == 201, created
    revision_id = created["revision"]["id"]
    with built.engine.connect() as c:
        k = c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)
    with built.engine.begin() as c:
        c.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) SELECT tenant_id, site_id, analytic_id, window_start, window_end, run_id, NULL, "
            "clock_timestamp() FROM analytic_run_selection WHERE site_id = :s AND analytic_id = :a "
            "ORDER BY seq DESC LIMIT 1"), {"s": s, "a": analytic})
    recorded = Recorded()
    read = reader(recorded)
    try:
        conn, old_rows, old = coverage_at(read, t, s, "COLD-READ", revision_id, k)
        _, again_rows, again = coverage_at(read, t, s, "COLD-READ", revision_id, k)
        _, new_rows, new = coverage_at(read, t, s, "COLD-READ", revision_id)
    finally:
        read.dispose()
    old_pin, new_pin = old_rows[0]["pin"], new_rows[0]["pin"]
    assert old_pin is not None and new_pin is not None, (old_rows, new_rows)
    assert new_pin["seq"] > old_pin["seq"]  # the later read may select the reselection
    assert new_pin["assessment_revision_id"] == old_pin["assessment_revision_id"]  # the same old run
    assert old_pin["evidence_cutoff"] <= k  # q7-1: the W2 snapshot is bounded by the evidence watermark
    assert again == old and again_rows == old_rows  # a repeat at K: the first seq, identical token
    assert old["links"][0]["state"] in ("HISTORICAL", "PENDING_RECOMPUTE", "STALE_SOURCE")
    assert old["links"][0]["selection_token"] != new["links"][0]["selection_token"]
    assert {name for name, c, inside in recorded.calls} == {"selected_windows", "cold_snapshot"}
    assert all(inside for _, _, inside in recorded.calls)
