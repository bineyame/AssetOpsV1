"""W4-01 commit 4: the Site Incident/Maintenance lists over real Postgres (`site-work-index-1`).

`.agent/W4-01-build-spec.md` B1/B8/B9/B10, closure 2 Q8/Q11, Run 5 r1-r5, Run 6 rulings 1-2 and Run 7 q7-1..q7-5
with the commit-4 dry-read. Cases are written through the W4 command service (the q2 private command clock where
a fixed instant is needed); lists read through `WorkIndexService` over `PostgresWorkRead` with the q4-1 private read
clock. Tests on the shared `runner` fixture come before the cold/EV `chain` test, whose fresh-database reset
invalidates that pool. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, Harness, runner  # noqa: F401
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 cold replay fixture
    from test_w203_cold_replay_postgres import opened, run
    from test_w205b_ev_replay_postgres import chain as ev_chain  # noqa: F401 - the W2-05b EV replay fixture
    from test_w206_ev_store_postgres import run_worker as run_ev_worker
    from test_w401_work_service_postgres import (POSITIVE_NOW, PRINCIPAL, Ctx, VirtualDbClock, accepted_action,
                                                  event, incident, public_finding, record, request)

    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.actions.site_index import ActionIndexService
    from assetops_backend.actions.site_index import parse_request as action_index_request
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.finding_api import ACCESS_BASIS
    from assetops_backend.work import model as m
    from assetops_backend.work.adapters import postgres_work_store
    from assetops_backend.work.adapters.postgres_work_read import PostgresWorkRead
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.composition import _link_read_ports, build_work_service
    from assetops_backend.work.model import WorkRefused
    from assetops_backend.work.service import WorkService
    from assetops_backend.work.site_index import WorkIndexService, parse_list_request, select

COMMON = {"case_id", "revision_id", "code", "title", "narrative", "occurred_at", "recorded_at", "state", "asset_id",
          "asset_label", "finding_links", "action_links", "url", "source_provenance"}
MAINTENANCE = COMMON | {"activity", "outcome_note", "outcome_state", "next_evidence", "next_evidence_copy",
                        "request_state", "record_id", "incident_id"}
DAY = ("2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z")
MISSING = {"code": "LINK_SELECTION_MISSING", "accepted_evidence_ids": []}


class Lists:
    """The list service over a private reader; `at` is the q4-1 private read instant (None: DB time)."""

    def __init__(self, at: datetime | None = None) -> None:
        self.at = at
        self.read = PostgresWorkRead(URL, link_rows=build_link_rows_reader(), ports=_link_read_ports(),
                                     test_read_clock_override=None if at is None else (lambda: self.at))
        self.svc = WorkIndexService(self.read)

    def get(self, t, s, kind, window=DAY, code="KOBO-001", *, limit=None, known_at=None, cursor=None) -> dict:
        req = parse_list_request(window[0], window[1], limit, [] if known_at is None else [known_at], cursor)
        return self.svc.read(t, s, code, kind, req, access_basis=ACCESS_BASIS)

    def select(self, t, s, kind, window=DAY, code="KOBO-001", known_at: datetime | None = None) -> dict:
        lo, hi = (datetime.fromisoformat(x.replace("Z", "+00:00")) for x in window)
        return self.read.snapshot(t, s, code, lambda rx: select(
            rx, t, s, code, kind, lo, hi, rx.read_at if known_at is None else known_at, ACCESS_BASIS))

    def close(self) -> None:
        self.read.dispose()


def refused(code: str, call, *args, **kwargs) -> None:
    with pytest.raises(WorkRefused) as caught:
        call(*args, **kwargs)
    assert caught.value.code == code, caught.value.code


def iso(value: datetime) -> str:
    return m.iso(value)


def test_site_window_cutoff_and_empty_count(runner) -> None:  # noqa: F811
    """B10/r4/r5: Incident membership by root occurrence, request membership by root creation, the K cutoff,
    equal-time UUID order, latest activity at K and the null fallbacks; an empty window is an exact zero."""
    t, s = runner.tenant, runner.site
    clock = VirtualDbClock(POSITIVE_NOW)
    ctx = Ctx(runner, clock)
    try:
        _, a = ctx.case(incident("w401-ix-a", occurred_at="2026-10-06T10:00:00Z"))
        _, b = ctx.case(incident("w401-ix-b", occurred_at="2026-10-06T12:00:00Z"))
        _, c = ctx.case(incident("w401-ix-c", occurred_at="2026-10-06T12:00:00Z"))
        _, out = ctx.case(incident("w401-ix-out", occurred_at="2026-10-05T23:59:59Z"))
        _, r1 = ctx.case(request("w401-ix-r1", occurred_at="2026-10-05T08:00:00Z"))
        _, r2 = ctx.case(request("w401-ix-r2", occurred_at="2026-10-07T08:00:00Z"))
        _, rec1 = ctx.record(r1["id"], record("w401-ix-rec1", activity="First inspection",
                                              occurred_at="2026-11-01T00:30:00Z"))
        _, rec2 = ctx.record(r1["id"], record("w401-ix-rec2", activity="Second inspection",
                                              outcome_note="Connector reseated", occurred_at="2026-11-01T00:31:00Z"))
        k = POSITIVE_NOW + timedelta(seconds=7, microseconds=500_000)  # after rec2 (+7 s), before `late` (+8 s)
        _, late = ctx.case(incident("w401-ix-late", occurred_at="2026-10-06T09:00:00Z"))
        _, rec3 = ctx.record(r1["id"], record("w401-ix-rec3", activity="Third inspection",
                                              occurred_at="2026-11-01T00:32:00Z"))
    finally:
        ctx.close()
    assert late["event"]["recorded_at"] > iso(k) > rec2["recorded_at"], (late, rec2)
    lists = Lists(POSITIVE_NOW + timedelta(minutes=1))
    maint = ("2026-11-01T00:00:00Z", "2026-11-02T00:00:00Z")
    try:
        at_k = lists.get(t, s, "incidents", known_at=iso(k))
        now = lists.get(t, s, "incidents")
        m_k = lists.get(t, s, "maintenance", maint, known_at=iso(k))
        m_now = lists.get(t, s, "maintenance", maint)
        by_creation = lists.get(t, s, "incidents", maint)
        empty = lists.get(t, s, "incidents", ("2026-10-01T00:00:00Z", "2026-10-02T00:00:00Z"))
    finally:
        lists.close()
    tie = sorted([b["id"], c["id"]])
    assert [r["case_id"] for r in at_k["rows"]] == [*tie, a["id"]]  # occurred DESC, equal time UUID ASC
    assert at_k["total_count"] == 3 and at_k["known_at"] == iso(k) and at_k["status"] == "HISTORICAL"
    assert out["id"] not in {r["case_id"] for r in now["rows"]}
    assert [r["case_id"] for r in now["rows"]] == [*tie, a["id"], late["id"]] and now["total_count"] == 4
    assert now["status"] == "CURRENT" and now["coverage"] == {"state": "COMPLETE", "reason": None}
    row = at_k["rows"][-1]
    assert set(row) == COMMON and row["url"] is None and row["asset_label"] is None and row["state"] == "OPEN"
    assert row["code"].startswith("INC-") and row["occurred_at"] == "2026-10-06T10:00:00.000000Z"
    assert row["title"] == "Witnessed start request failed" and row["finding_links"] == [] == row["action_links"]
    assert at_k["site_code"] == "KOBO-001" and isinstance(at_k["site_name"], str) and at_k["site_name"]
    assert at_k["window"] == {"from": "2026-10-06T00:00:00.000000Z", "to": "2026-10-07T00:00:00.000000Z",
                              "bounds": "[from, to)"}
    # Maintenance membership is request creation (r1 occurred 5 Oct, created 1 Nov); incidents never by creation.
    assert by_creation["total_count"] == 0 and by_creation["rows"] == []
    assert [r["case_id"] for r in m_k["rows"]] == [r2["id"], r1["id"]] and m_k["total_count"] == 2
    w2, w1 = m_k["rows"]
    assert set(w1) == MAINTENANCE == set(w2)
    assert (w1["record_id"], w1["activity"], w1["outcome_note"]) == (rec2["id"], "Second inspection",
                                                                     "Connector reseated")
    assert rec1["id"] != w1["record_id"]
    assert (w2["record_id"], w2["activity"], w2["outcome_note"], w2["incident_id"]) == (None, None, None, None)
    for w in (w1, w2):
        assert w["outcome_state"] == "UNVERIFIED" and w["next_evidence"] is None
        assert w["next_evidence_copy"] == "No next evidence recorded" and w["request_state"] == w["state"] == "OPEN"
    [now_r1] = [r for r in m_now["rows"] if r["case_id"] == r1["id"]]
    assert (now_r1["record_id"], now_r1["activity"]) == (rec3["id"], "Third inspection")
    # r3: zero eligible cases is an exact CURRENT/COMPLETE zero with UNKNOWN/EMPTY_CITATION_SET provenance.
    assert empty["total_count"] == 0 and empty["rows"] == [] and empty["next_cursor"] is None
    assert empty["status"] == "CURRENT" and empty["coverage"] == {"state": "COMPLETE", "reason": None}
    prov = empty["source_provenance"]
    assert (prov["classification"], prov["state"]) == ("UNKNOWN", "UNKNOWN") and "detail" not in prov
    assert [x["code"] for x in prov["reasons"]] == ["EMPTY_CITATION_SET"]
    assert empty["selection_token"].startswith("sha256:") and len(empty["selection_token"]) == 71


def test_pending_link_and_missing_source_keep_gap(runner, monkeypatch) -> None:  # noqa: F811
    """B9/r3: a valid pinned mini-grid Action whose dispatch selection is beyond the matcher pass is
    PENDING_RECOMPUTE / PARTIAL / LINK_WORK_PENDING; a pinned Finding revision absent at K is UNKNOWN /
    LINK_SELECTION_MISSING with the q7-4 provenance guard on its row and on the list, even off-page."""
    run_case(runner, CASES["F01"])
    t, s = runner.tenant, runner.site
    row = public_finding(runner)
    fid, frev = row["finding_id"], row["finding_revision_id"]
    action_id, action_event = accepted_action(runner, fid, "w401-ix-accept-002")
    ctx = Ctx(runner, VirtualDbClock(POSITIVE_NOW))
    try:
        _, pending = ctx.case(incident("w401-ix-pend", occurred_at="2026-10-06T16:11:00Z",
                                       action_links=[{"action_id": action_id, "action_event_id": action_event}]))
    finally:
        ctx.close()
    with runner.engine.begin() as c:  # TEST-SCOPED: reselect the dispatch day after the matcher pass
        added = c.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) SELECT tenant_id, site_id, analytic_id, window_start, window_end, run_id, NULL, "
            "clock_timestamp() FROM analytic_run_selection WHERE site_id = :s AND analytic_id = 'dispatch' "
            "AND window_start = '2026-10-06T00:00:00Z' ORDER BY seq DESC LIMIT 1"), {"s": s}).rowcount
    assert added == 1
    lists = Lists(POSITIVE_NOW + timedelta(minutes=1))
    try:
        body = lists.get(t, s, "incidents")
        chosen = lists.select(t, s, "incidents")
    finally:
        lists.close()
    [fence] = chosen["linked_selection_fences"]
    assert fence["kind"] == "ACTION" and fence["selection_token"].startswith("sai1-"), fence
    assert fence["state"] == "PENDING_RECOMPUTE", fence
    assert body["status"] == "PENDING_RECOMPUTE" and body["total_count"] == 1
    assert body["coverage"] == {"state": "PARTIAL", "reason": "LINK_WORK_PENDING"}
    [link] = body["rows"][0]["action_links"]
    assert (link["action_id"], link["action_event_id"], link["label"]) == (
        action_id, action_event, f"Action {action_id[:8]}")
    assert link["href"] == f"/sites/KOBO-001/actions/{action_id}?event_id={action_event}"

    # Missing lineage: a case pinned to the F01 revision is written at an instant before that revision existed
    # (TEST-SCOPED bypass of the q4-2 command cutoff; the scoped junction FK still holds) and read at K between.
    with runner.engine.connect() as c:
        made = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"), {"r": frev}).scalar_one()
    early = made.astimezone(timezone.utc) - timedelta(hours=1)
    monkeypatch.setattr(postgres_work_store._Tx, "finding_pairs_in_scope", lambda self, pairs: set(pairs))
    svc = WorkService(PostgresWorkStore(URL, link_rows=build_link_rows_reader(),
                                        test_db_clock_override=VirtualDbClock(early)))
    try:
        _, broken = svc.create_case(t, s, incident(
            "w401-ix-missing", occurred_at="2026-10-06T08:00:00Z",
            finding_links=[{"finding_id": fid, "finding_revision_id": frev}]), PRINCIPAL)
        _, plain = svc.create_case(t, s, incident("w401-ix-plain", occurred_at="2026-10-06T20:00:00Z"), PRINCIPAL)
    finally:
        svc._store.dispose()
    k = early + timedelta(seconds=5)
    assert k < made
    lists = Lists(POSITIVE_NOW + timedelta(minutes=1))
    try:
        page = lists.get(t, s, "incidents", known_at=iso(k), limit="1")
        full = lists.get(t, s, "incidents", known_at=iso(k))
        chosen = lists.select(t, s, "incidents", known_at=k)
    finally:
        lists.close()
    assert page["total_count"] == 2 and [r["case_id"] for r in page["rows"]] == [plain["id"]]  # broken is off-page
    assert page["status"] == "UNKNOWN" and page["coverage"] == {"state": "UNKNOWN", "reason": "LINK_SELECTION_MISSING"}
    prov = page["source_provenance"]
    assert (prov["classification"], prov["state"]) == ("UNKNOWN", "UNKNOWN") and MISSING in prov["reasons"]
    assert prov["basis_sha256"].startswith("sha256:") and "detail" not in prov
    assert MISSING not in page["rows"][0]["source_provenance"]["reasons"]  # the unaffected row keeps its own DTO
    [bad] = [r for r in full["rows"] if r["case_id"] == broken["id"]]
    assert MISSING in bad["source_provenance"]["reasons"] and bad["source_provenance"]["state"] == "UNKNOWN"
    assert bad["finding_links"] == [{"finding_id": fid, "finding_revision_id": frev, "label": f"Finding {fid[:8]}",
                                     "href": None}]
    assert chosen["linked_selection_fences"] == [{"kind": "FINDING", "root_id": fid, "selected_id": frev,
                                                  "selection_token": None, "state": "UNKNOWN"}]


def test_cursor_fence_and_full_count(runner) -> None:  # noqa: F811
    """B8/r2/r4: equal-time UUID ties, exact full count, full-set provenance including an off-page citation, a
    stable page two at the cursor's fixed K, and 409 on a changed off-page event or a changed cutoff."""
    run_case(runner, CASES["F01"])
    t, s = runner.tenant, runner.site
    cited = public_finding(runner)["cited"]["accepted_evidence_ids"]
    ctx = Ctx(runner, VirtualDbClock(POSITIVE_NOW))
    try:
        _, i1 = ctx.case(incident("w401-cur-1", occurred_at="2026-10-06T12:00:00Z"))
        _, i2 = ctx.case(incident("w401-cur-2", occurred_at="2026-10-06T12:00:00Z"))
        _, i3 = ctx.case(incident("w401-cur-3", occurred_at="2026-10-06T08:00:00Z",
                                  cited_accepted_evidence_ids=cited))
    finally:
        ctx.close()
    lists = Lists(POSITIVE_NOW + timedelta(minutes=1))
    try:
        before_i3 = lists.get(t, s, "incidents", known_at=iso(POSITIVE_NOW + timedelta(seconds=1, microseconds=1)))
        one = lists.get(t, s, "incidents", limit="2")
        lists.at = POSITIVE_NOW + timedelta(minutes=2)  # page two reads later; the cursor's K stays fixed
        two = lists.get(t, s, "incidents", limit="2", cursor=one["next_cursor"])
        refused("WORK_BASIS_CHANGED", lists.get, t, s, "incidents", limit="2", cursor=one["next_cursor"],
                known_at=iso(POSITIVE_NOW + timedelta(seconds=30)))
        refused("WORK_BASIS_CHANGED", lists.get, t, s, "incidents", ("2026-10-06T00:00:00Z", "2026-10-08T00:00:00Z"),
                limit="2", cursor=one["next_cursor"])
    finally:
        lists.close()
    assert [r["case_id"] for r in one["rows"]] == sorted([i1["id"], i2["id"]]) and one["total_count"] == 3
    assert [r["case_id"] for r in two["rows"]] == [i3["id"]] and two["next_cursor"] is None
    assert two["total_count"] == 3 and two["known_at"] == one["known_at"] == iso(POSITIVE_NOW + timedelta(minutes=1))
    assert two["selection_token"] == one["selection_token"] and two["source_provenance"] == one["source_provenance"]
    assert two["status"] == one["status"] == "CURRENT"
    # The off-page citation is in the full-set provenance and basis; page-one rows cite nothing.
    assert set(cited) <= set(one["source_provenance"]["evidence_ids"])
    assert all(r["source_provenance"]["evidence_ids"] == [] for r in one["rows"])
    assert before_i3["total_count"] == 2 and not set(cited) & set(before_i3["source_provenance"]["evidence_ids"])
    assert before_i3["source_provenance"]["basis_sha256"] != one["source_provenance"]["basis_sha256"]
    # A COMMENT on the off-page case recorded before the fixed K changes the whole-set basis: page two is 409.
    ctx = Ctx(runner, VirtualDbClock(POSITIVE_NOW + timedelta(seconds=30)))
    try:
        status, _ = ctx.event(i3["id"], event("COMMENT", {"text": "Seen again"}, "w401-cur-cmt",
                                              occurred_at="2026-11-01T01:00:20Z"))
    finally:
        ctx.close()
    assert status == 201
    lists = Lists(POSITIVE_NOW + timedelta(minutes=3))
    try:
        refused("WORK_BASIS_CHANGED", lists.get, t, s, "incidents", limit="2", cursor=one["next_cursor"])
        again = lists.get(t, s, "incidents", limit="2", known_at=one["known_at"])
    finally:
        lists.close()
    assert again["total_count"] == 3 and again["selection_token"] != one["selection_token"]
    assert [r["case_id"] for r in again["rows"]] == [r["case_id"] for r in one["rows"]]  # same page, new basis


def test_pinned_link_survives_later_finding_and_action_heads(runner) -> None:  # noqa: F811
    """r1/q6-2/q7-2/q7-3: exact pins stay after a later Action head; the mini-grid Action fence is the exact W1
    `sai1-` window token (the Action itself created outside the window); the mini-grid Finding has no full
    `sfi1-` port, so its fence is null/UNKNOWN and the list never claims CURRENT."""
    run_case(runner, CASES["F01"])
    t, s = runner.tenant, runner.site
    row = public_finding(runner)
    fid, frev = row["finding_id"], row["finding_revision_id"]
    action_id, action_event = accepted_action(runner, fid, "w401-ix-accept-004")
    ctx = Ctx(runner, VirtualDbClock(POSITIVE_NOW))
    try:
        _, case = ctx.case(incident(
            "w401-ix-pinned", occurred_at="2026-10-06T16:11:00Z",
            finding_links=[{"finding_id": fid, "finding_revision_id": frev}],
            action_links=[{"action_id": action_id, "action_event_id": action_event}]))
    finally:
        ctx.close()
    h = Harness(runner)
    try:  # a later Action head: a backdated OBSERVED event through the existing Action route
        later = h.observe(action_id, h.clock.at, "w401-ix-observe")
        assert later.status_code == 201, later.text
        head = later.json()["event"]["id"]
    finally:
        h.close()
    with runner.engine.connect() as c:
        created, newest = c.execute(text(
            "SELECT a.created_at, max(e.recorded_at) FROM action a JOIN action_event e ON e.action_id = a.id "
            "WHERE a.id = :a GROUP BY a.created_at"), {"a": action_id}).one()
    assert head != action_event
    assert not (datetime(2026, 10, 6, tzinfo=timezone.utc) <= created < datetime(2026, 10, 7, tzinfo=timezone.utc))
    read_at = max(newest, POSITIVE_NOW).astimezone(timezone.utc) + timedelta(minutes=1)
    lists = Lists(read_at)
    try:
        body = lists.get(t, s, "incidents")
        chosen = lists.select(t, s, "incidents")
    finally:
        lists.close()
    store = build_action_store(URL)
    try:
        w1 = ActionIndexService(store).read(t, s, "KOBO-001", action_index_request(*DAY, None, None),
                                            access_basis=ACCESS_BASIS)
    finally:
        store.dispose()
    [wire] = body["rows"]
    assert wire["case_id"] == case["id"]
    assert wire["finding_links"] == [{"finding_id": fid, "finding_revision_id": frev, "label": f"Finding {fid[:8]}",
                                      "href": f"/sites/KOBO-001/findings/{fid}?revision_id={frev}"}]
    assert [(x["action_id"], x["action_event_id"]) for x in wire["action_links"]] == [(action_id, action_event)]
    fences = {f["kind"]: f for f in chosen["linked_selection_fences"]}
    assert fences["FINDING"] == {"kind": "FINDING", "root_id": fid, "selected_id": frev, "selection_token": None,
                                 "state": "UNKNOWN"}
    assert fences["ACTION"]["selected_id"] == action_event  # never the later head
    assert fences["ACTION"]["selection_token"] == chosen["action_index_token"] == w1["fence"]["token"]
    assert fences["ACTION"]["selection_token"].startswith("sai1-") and w1["total_count"] == 0
    assert fences["ACTION"]["state"] in ("CURRENT", "PENDING_RECOMPUTE")
    assert body["status"] == "UNKNOWN" and body["coverage"] == {"state": "UNKNOWN", "reason": "LINK_SELECTION_MISSING"}
    assert MISSING not in wire["source_provenance"]["reasons"]  # lineage exists; only the list fence is missing
    assert body["total_count"] == 1


def _pin(built, domain: str) -> tuple[str, str]:
    with built.engine.connect() as c:
        pin = c.execute(text(
            "SELECT CAST(finding_id AS text), CAST(id AS text) FROM finding_revision WHERE site_id = :s "
            "AND domain = :d ORDER BY created_at DESC, id LIMIT 1"), {"s": built.site_id, "d": domain}).first()
    assert pin is not None, f"the replay wrote no {domain} Finding"
    return pin[0], pin[1]


def _db_now(built) -> datetime:
    with built.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)


def _window(now: datetime) -> tuple[str, str]:
    return iso(now - timedelta(days=1)), iso(now + timedelta(hours=1))


def test_cold_ev_pinned_list_fence_and_reselection(chain, ev_chain, monkeypatch) -> None:  # noqa: F811
    """Run 6 ruling 1: exact cold and EV Finding pins carry non-null `wce1-` list fences; a later reselection
    leaves the earlier-cutoff fence and pinned IDs unchanged while the newer selected basis changes the fence and
    the list token; a pin missing at K is null/UNKNOWN."""
    built = opened("excursion", chain)
    run(built)
    t, s, code = built.tenant_id, built.site_id, "COLD-LAB-001"
    fid, frev = _pin(built, "cold_chain")
    svc = build_work_service(URL)
    try:
        status, case = svc.create_case(t, s, incident(
            "w401-ix-cold", finding_links=[{"finding_id": fid, "finding_revision_id": frev}]), PRINCIPAL)
    finally:
        svc._store.dispose()
    assert status == 201, case
    k = _db_now(built)
    window = _window(k)
    with built.engine.begin() as c:  # TEST-SCOPED reselection of the same old run, as the W3/W4 proofs do
        analytic = c.execute(text("SELECT analytic_id FROM finding_revision WHERE id = :r"), {"r": frev}).scalar_one()
        c.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) SELECT tenant_id, site_id, analytic_id, window_start, window_end, run_id, NULL, "
            "clock_timestamp() FROM analytic_run_selection WHERE site_id = :s AND analytic_id = :a "
            "ORDER BY seq DESC LIMIT 1"), {"s": s, "a": analytic})
    lists = Lists()
    try:
        old = lists.select(t, s, "incidents", window, code, known_at=k)
        again = lists.select(t, s, "incidents", window, code, known_at=k)
        new = lists.select(t, s, "incidents", window, code)
        body = lists.get(t, s, "incidents", window, code, known_at=iso(k))
    finally:
        lists.close()
    [f_old], [f_again], [f_new] = (x["linked_selection_fences"] for x in (old, again, new))
    assert f_old["selection_token"].startswith("wce1-") and f_old["state"] != "UNKNOWN", f_old
    assert (f_old["root_id"], f_old["selected_id"]) == (fid, frev) == (f_new["root_id"], f_new["selected_id"])
    assert f_again == f_old and again["selection_token"] == old["selection_token"]
    assert f_new["selection_token"].startswith("wce1-") and f_new["selection_token"] != f_old["selection_token"]
    assert new["selection_token"] != old["selection_token"]
    assert body["selection_token"] == old["selection_token"] and body["total_count"] == 1
    assert body["status"] != "UNKNOWN" and body["coverage"]["state"] != "UNKNOWN"
    # A pin written before its Finding revision existed (TEST-SCOPED q4-2 bypass) is null/UNKNOWN at K.
    with built.engine.connect() as c:
        made = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"), {"r": frev}).scalar_one()
    early = made.astimezone(timezone.utc) - timedelta(minutes=10)
    monkeypatch.setattr(postgres_work_store._Tx, "finding_pairs_in_scope", lambda self, pairs: set(pairs))
    early_svc = WorkService(PostgresWorkStore(URL, link_rows=build_link_rows_reader(),
                                              test_db_clock_override=VirtualDbClock(early)))
    try:
        _, missing = early_svc.create_case(t, s, incident(
            "w401-ix-cold-missing", occurred_at=iso(early - timedelta(minutes=5)),
            finding_links=[{"finding_id": fid, "finding_revision_id": frev}]), PRINCIPAL)
    finally:
        early_svc._store.dispose()
    lists = Lists()
    try:
        gap = lists.select(t, s, "incidents", _window(early), code, known_at=early + timedelta(seconds=1))
    finally:
        lists.close()
    assert gap["linked_selection_fences"] == [{"kind": "FINDING", "root_id": fid, "selected_id": frev,
                                               "selection_token": None, "state": "UNKNOWN"}]
    assert MISSING in gap["source_provenance"]["reasons"]
    built.close()

    ev = ev_chain("interrupted")
    ev.start_release_upload()
    run_ev_worker(ev)
    t, s, code = ev.tenant_id, ev.site_id, "EV-LAB-001"
    fid, frev = _pin(ev, "ev_charging")
    svc = build_work_service(URL)
    try:
        status, case = svc.create_case(t, s, incident(
            "w401-ix-ev", finding_links=[{"finding_id": fid, "finding_revision_id": frev}]), PRINCIPAL)
    finally:
        svc._store.dispose()
    assert status == 201, case
    lists = Lists()
    try:
        chosen = lists.select(t, s, "incidents", _window(_db_now(ev)), code)
    finally:
        lists.close()
    [fence] = chosen["linked_selection_fences"]
    assert (fence["root_id"], fence["selected_id"]) == (fid, frev)
    assert fence["selection_token"].startswith("wce1-") and fence["state"] != "UNKNOWN", fence
