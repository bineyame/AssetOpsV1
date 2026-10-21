"""W4-03 unit 5: the persisted opportunity list/detail reads over Postgres (`.agent/W4-03-build-spec.md` "API, exact
wire, ordering and errors"; closure 1 Q1-Q16; closure 4 S5/S7-S10/S14/S20; u4b read-side ownership; "Unit-5..12
rulings (u5)" unit 5 rulings 1-7).

Studies are projected by the unit-4 worker over the MG-W402-001 authored cases (`test_w403_opportunity_worker_postgres`
helpers). Live jobs are inserted directly, as the unit-4 tests do. A root with no selection is the store's own insert.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w402_reads_postgres import CODE, DAYS, ZONE, _midnight, _read, _reconcile, _setup
    from test_w403_opportunity_worker_postgres import project, revisions, worker
    from test_w403_scenarios_postgres import (
        _Registry,
        db_now,
        load_command,
        mg,
        mg_published,
        principal_for,
        selected_pins,
        tariff_command,
    )

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_decisions.model import DecisionRefused
    from assetops_backend.mini_decisions.opportunities import OpportunityService, decode_cursor, parse_opportunity_list
    from assetops_backend.mini_decisions.scenarios import ScenarioService, _instant, encode_cursor, parse_list
    from assetops_backend.mini_decisions.store import MiniDecisionStoreUnavailable, PostgresMiniDecisionStore
    from assetops_backend.mini_decisions_api import build_mini_decisions_router
    from assetops_backend.mini_depth.inputs import local_noon
    from assetops_backend.mini_depth.read import MiniDepthRead, iso, renewable_revisions

FROM, TO = "2026-10-05T21:00:00.000000Z", "2026-10-10T21:00:00.000000Z"
ROW_KEYS = {"opportunity", "status", "currentness", "source_provenance", "selected_source_provenance",
            "pending_source_provenance", "limitations"}
OBJECT_KEYS = {"id", "code", "revision_id", "revision_no", "first_day", "last_day", "model_version", "study_days",
               "eligible_days", "assessed_days", "headroom_kw", "proposed_load_kw", "gross_sales_scenario",
               "demand_state", "collection_state", "scenario_id", "day_rows"}
LIST_KEYS = {"schema_version", "window", "status", "currentness", "source_provenance", "selected_source_provenance",
             "pending_source_provenance", "total_count", "rows", "next_cursor", "selection_token"}
DAY_KEYS = {"local_day", "decision", "opportunity_kwh", "constraints", "evidence_ids", "selection_seq",
            "mini_revision_id"}
READ_CODES = {"SELECTION_CHANGED", "RECOMPUTE_PENDING", "SOURCE_STALE", "SCENARIO_BASIS_MISMATCH"}


def service(engine) -> "OpportunityService":
    return OpportunityService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))


def page(svc, t, s, frm=FROM, to=TO, limit=None, known=None, cursor=None):
    return svc.list(t, s, parse_opportunity_list(frm, to, limit, [known] if known else [], cursor), "basis")


def detail(svc, t, s, oid, known=None):
    return svc.detail(t, s, str(oid), [known] if known else [])


def now(engine) -> str:
    return iso(db_now(engine))


def job(engine, t, s, lo, hi, status="PENDING", domain="mini_opportunity") -> str:
    with engine.begin() as c:
        return str(c.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, available_at, "
            "created_at) VALUES (gen_random_uuid(), :t, :s, :d, :lo, :hi, :st, clock_timestamp(), clock_timestamp()) "
            "RETURNING id"), {"t": t, "s": s, "d": domain, "lo": lo, "hi": hi, "st": status}).scalar_one())


def settle(engine, job_id) -> None:
    with engine.begin() as c:
        c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE id = :j"), {"j": job_id})


def renewable_job(engine, t, s, day) -> None:
    noon = local_noon(day, ZONE)
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_renewable', :lo, :hi, NULL, clock_timestamp())"),
                  {"t": t, "s": s, "lo": noon.start, "hi": noon.end})


def bare_root(engine, t, s, first, last):
    """A root the store holds with no selection (closure 1 Q4-Q6: a root and its rows can be UNKNOWN)."""
    oid = uuid4()
    store_ = PostgresMiniDecisionStore(engine)
    with store_.transaction() as c:
        store_.insert_opportunity(c, {"id": oid, "tenant_id": t, "site_id": s, "first_day": first, "last_day": last,
                                      "model_version": "mini-opportunity/1"})
    return oid


def stale_foundation(engine, s) -> None:
    """The unit-2b stale-digest vector: an ambiguous covering Foundation (test-only replica edit, no job)."""
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in ("CREATE TEMP TABLE f_copy ON COMMIT DROP AS SELECT * FROM foundation_revision "
                    "WHERE site_id = :s AND superseded_at IS NULL",
                    "UPDATE f_copy SET id = gen_random_uuid(), version = version + 1000, "
                    "recorded_at = clock_timestamp(), superseded_at = '2999-01-01Z', origin = 'PUBLISH'",
                    "INSERT INTO foundation_revision SELECT * FROM f_copy"):
            c.execute(text(sql), {"s": s})


def codes(body) -> list[str]:
    return [x["code"] for x in body["limitations"]]


def positive(body) -> bool:
    """The u5 ruling 1 green-display inputs (unit 7 renders the chip from these)."""
    selected = body["selected_source_provenance"] or {}
    return (body["status"] == "SUPPORTED" and (body["opportunity"]["eligible_days"] or 0) > 0
            and body["currentness"]["state"] == "CURRENT"
            and selected.get("classification") not in (None, "MIXED", "UNKNOWN"))


def test_list_status_uses_all_roots_before_paging_and_zero_rows_unknown(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    svc = service(engine)
    empty = page(svc, t, s)
    assert (empty["total_count"], empty["rows"], empty["status"], empty["next_cursor"]) == (0, [], "UNKNOWN", None)
    assert empty["currentness"] == {"state": "UNKNOWN", "job_state": "NONE"}
    assert empty["selected_source_provenance"] is None and empty["pending_source_provenance"] is None
    project(engine)
    one = page(svc, t, s)
    [row] = one["rows"]
    stored = revisions(engine)[0].result["status"]
    assert stored in ("SUPPORTED", "LIMITED") and one["status"] == row["status"] == stored
    # A root with no visible selection contributes UNKNOWN to the envelope, though page one holds only the projected
    # study (first_day DESC).
    bare = bare_root(engine, t, s, date(2026, 10, 2), date(2026, 10, 6))
    first = page(svc, t, s, limit="1")
    assert first["total_count"] == 2 and [r["opportunity"]["first_day"] for r in first["rows"]] == ["2026-10-06"]
    assert first["rows"][0]["status"] == stored and first["status"] == "UNKNOWN"
    second = page(svc, t, s, limit="1", cursor=first["next_cursor"])
    assert [r["opportunity"]["id"] for r in second["rows"]] == [str(bare)] and second["next_cursor"] is None
    assert second["rows"][0]["status"] == "UNKNOWN" and second["status"] == "UNKNOWN"
    assert second["total_count"] == 2
    # The weakest order is UNKNOWN < LIMITED < SUPPORTED: without the bare root in the window the stored status wins.
    late = page(svc, t, s, frm="2026-10-09T21:00:00.000000Z")
    assert late["total_count"] == 1 and late["status"] == stored


def test_pending_stale_missing_historical_current_precedence_and_jobs(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    w = worker(engine)
    w.reconcile(CODE, _midnight(date(2026, 10, 5)), _midnight(date(2026, 10, 11)))
    assert len(w.run_pending(scan=False)) == 2  # the 5-9 Oct study misses 5 Oct; the 6-10 Oct study is complete
    svc = service(engine)

    def states(**q):
        body = page(svc, t, s, frm="2026-10-04T21:00:00.000000Z", **q)
        rows = {r["opportunity"]["first_day"]: r["currentness"] for r in body["rows"]}
        return body["currentness"], rows["2026-10-05"], rows["2026-10-06"]

    env, missing, full = states()
    assert (full["state"], full["job_state"]) == ("CURRENT", "SETTLED")
    assert (missing["state"], missing["job_state"]) == ("UNKNOWN", "NONE")  # an unchanged missing day stays UNKNOWN
    assert env == {"state": "UNKNOWN", "job_state": "NONE"}
    assert [w_["local_day"] for w_ in full["windows"]] == [d.isoformat() for d in DAYS]
    assert full["selection_seq"] is not None and full["selected_at"].endswith("Z")
    k_clean = now(engine)
    # An explicit past cutoff is HISTORICAL only below the missing-day UNKNOWN.
    _, missing, full = states(known=k_clean)
    assert (full["state"], missing["state"]) == ("HISTORICAL", "UNKNOWN")

    # An overlapping FAILED opportunity job (a one-day window inside 10 Oct only) is pending, not a stored failure.
    failed = job(engine, t, s, _midnight(DAYS[-1]), _midnight(DAYS[-1] + timedelta(days=1)), "FAILED")
    env, missing, full = states()
    assert (full["state"], full["job_state"]) == ("PENDING_RECOMPUTE", "FAILED")
    assert (missing["state"], missing["job_state"]) == ("UNKNOWN", "NONE")
    assert env == {"state": "PENDING_RECOMPUTE", "job_state": "FAILED"}
    settle(engine, failed)

    # A live W4-02 job on the missing day: pending beats the missing day.
    renewable_job(engine, t, s, date(2026, 10, 5))
    env, missing, full = states()
    assert (missing["state"], missing["job_state"]) == ("PENDING_RECOMPUTE", "PENDING")
    assert full["state"] == "CURRENT" and env["state"] == "PENDING_RECOMPUTE"
    # The day is selected now: the pinned missing day changed, which is STALE_SOURCE, above UNKNOWN.
    _reconcile(engine, [date(2026, 10, 5)])
    env, missing, full = states()
    assert (missing["state"], missing["job_state"]) == ("STALE_SOURCE", "SETTLED")
    assert full["state"] == "CURRENT" and env == {"state": "STALE_SOURCE", "job_state": "SETTLED"}

    # A pending renewable job on a day both studies pin, then its new selected revision.
    renewable_job(engine, t, s, DAYS[1])
    env, missing, full = states()
    assert (full["state"], full["job_state"]) == ("PENDING_RECOMPUTE", "PENDING")
    assert missing["state"] == "PENDING_RECOMPUTE" and env == {"state": "PENDING_RECOMPUTE", "job_state": "PENDING"}
    _reconcile(engine, [DAYS[1]])
    _, _, full = states()
    assert (full["state"], full["job_state"]) == ("STALE_SOURCE", "SETTLED")
    # The clean cutoff still replays its own heads and jobs.
    _, missing, full = states(known=k_clean)
    assert (full["state"], missing["state"]) == ("HISTORICAL", "UNKNOWN")


def test_stored_supported_result_unchanged_through_s9_pending_and_stale_reads(store, engine, tmp_path,
                                                                             capsys) -> None:  # noqa: F811
    """u4b: the persisted SUPPORTED revision read through the shared S9 basis at an exact cutoff, with pending newer
    evidence and a stale digest; the frozen result never changes and no positive display input survives either."""
    t, s = mg_published(store, engine, tmp_path, capsys)
    project(engine)
    [rev] = revisions(engine)
    frozen = rev.result
    assert (frozen["status"], frozen["eligible_days"]) == ("SUPPORTED", 4)
    svc = service(engine)
    oid = page(svc, t, s)["rows"][0]["opportunity"]["id"]
    reader = MiniDepthRead(engine, link_rows_on)

    def at(known):
        """W4-03 detail, the W4-02 read and the shared S9 basis, all at one explicit cutoff."""
        k = _instant(known, "INVALID_KNOWN_AT")
        mine = detail(svc, t, s, oid, known)
        w4 = _read(engine, t, s, "renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)), known_at=k)
        with PostgresMiniDecisionStore(engine).snapshot() as c:
            basis = reader.read_selected_renewable_basis(c, tenant_id=t, site_id=s, days=DAYS, known=k,
                                                         historical=True)
        return mine, w4, basis

    k0 = now(engine)
    clean, w4, basis = at(k0)
    assert clean["status"] == "SUPPORTED" and clean["currentness"]["state"] == "HISTORICAL"
    current = detail(svc, t, s, oid)
    assert current["currentness"]["state"] == "CURRENT" and positive(current)
    assert current["selected_source_provenance"]["classification"] == "AUTHORED_DEMONSTRATION"
    assert current["selected_source_provenance"] == basis["selected_source_provenance"]
    assert current["limitations"] == frozen["limitations"]

    # Pending newer evidence on an ELIGIBLE pinned day.
    day = next(d for d, r in zip(DAYS, frozen["day_rows"]) if r["decision"] == "ELIGIBLE")
    renewable_job(engine, t, s, day)
    k1 = now(engine)
    pending, w4, basis = at(k1)
    assert basis["currentness"]["state"] == w4["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert pending["status"] == "SUPPORTED" and pending["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert pending["pending_source_provenance"] is not None
    assert pending["pending_source_provenance"] == w4["pending_source_provenance"]
    assert pending["selected_source_provenance"] == w4["selected_source_provenance"]
    assert "RECOMPUTE_PENDING" in codes(pending) and not positive(pending)
    assert revisions(engine)[0].result == frozen
    with engine.begin() as c:
        c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE domain = 'mini_renewable' AND status = 'PENDING'"))

    # A stale digest: the same heads, a changed covering Foundation.
    stale_foundation(engine, s)
    k2 = now(engine)
    stale, w4, basis = at(k2)
    assert basis["currentness"]["state"] == w4["currentness"]["state"] == "STALE_SOURCE"
    assert stale["status"] == "SUPPORTED" and stale["currentness"]["state"] == "STALE_SOURCE"
    assert codes(stale)[len(frozen["limitations"]):] == ["SOURCE_STALE"] and not positive(stale)
    assert stale["opportunity"]["revision_id"] == str(rev.id)
    assert revisions(engine)[0].result == frozen and len(revisions(engine)) == 1
    # The earlier cutoffs replay. Job status is not versioned, so k1 after the job settled agrees with W4-02's k1.
    replay, w4, _ = at(k1)
    assert replay["currentness"]["state"] == w4["currentness"]["state"] == "HISTORICAL"
    assert at(k0)[0] == clean


def test_read_limitations_are_ordered_and_frozen_result_survives(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    [rev] = revisions(engine)
    stored = rev.result["limitations"]
    svc = service(engine)
    oid = page(svc, t, s)["rows"][0]["opportunity"]["id"]
    who = principal_for(t, s)
    scenarios = ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))
    _, tariff = scenarios.create(t, s, who, tariff_command("w403-u5-lim-01"))
    status, _ = svc.link_scenario(t, s, who, oid, link_body("w403-u5-lim-02", oid, tariff["id"]))
    assert status == 201
    mismatch = detail(svc, t, s, oid)
    assert codes(mismatch) == [x["code"] for x in stored] + ["SCENARIO_BASIS_MISMATCH"]

    # A new W4-02 head on 7 Oct and an overlapping FAILED opportunity job: changed, pending, mismatch, in that order.
    _reconcile(engine, [DAYS[1]])
    failed = job(engine, t, s, _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)), "FAILED")
    body = detail(svc, t, s, oid)
    assert body["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert body["limitations"][:len(stored)] == stored
    assert codes(body)[len(stored):] == ["SELECTION_CHANGED", "RECOMPUTE_PENDING", "SCENARIO_BASIS_MISMATCH"]
    assert all(x["evidence_ids"] == [] for x in body["limitations"][len(stored):])
    # Only an opportunity job is live: no new accepted IDs, so no pending block though currentness is pending.
    assert body["pending_source_provenance"] is None
    settle(engine, failed)
    body = detail(svc, t, s, oid)
    assert codes(body)[len(stored):] == ["SELECTION_CHANGED", "SOURCE_STALE", "SCENARIO_BASIS_MISMATCH"]
    assert len(codes(body)) == len(set(codes(body)))
    assert not READ_CODES & {x["code"] for x in stored}
    assert revisions(engine)[0].result == rev.result and body["status"] == rev.result["status"]


def link_body(key, oid, scenario_id, **actor):
    return {"schema_version": "mini-opportunity-scenario-command-1", "idempotency_key": key,
            "actor": {"kind": "SERVICE", "id": "service:w403-fixture",
                      "attestation": "service=w403-fixture;job=positive-decisions;rule=w403/1", **actor},
            "opportunity_id": str(oid), "scenario_id": str(scenario_id)}


def test_selection_and_scenario_link_history_at_two_cutoffs(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    _, [done] = project(engine)
    svc = service(engine)
    oid = page(svc, t, s)["rows"][0]["opportunity"]["id"]
    who = principal_for(t, s)
    scenarios = ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))
    _, fits = scenarios.create(t, s, who, load_command("w403-u5-his-01", selected_pins(engine, t, s)))
    _, other = scenarios.create(t, s, who, tariff_command("w403-u5-his-02"))
    _, first_link = svc.link_scenario(t, s, who, oid, link_body("w403-u5-his-03", oid, fits["id"]))
    k1 = now(engine)
    one = detail(svc, t, s, oid, k1)
    assert [(x["scenario_id"], x["selected"], x["compatible"]) for x in one["scenario_links"]] == [
        (fits["id"], True, True)]
    assert one["opportunity"]["scenario_id"] == fits["id"] and one["opportunity"]["proposed_load_kw"] == "0.001"
    assert "SCENARIO_BASIS_MISMATCH" not in codes(one)
    # Money comes only from the compatible link, under the same gate as the scenario row at that cutoff.
    row = next(r for r in scenarios.list(t, s, parse_list(None, None, None, [k1], None), "basis")["rows"]
               if r["id"] == fits["id"])
    assert one["opportunity"]["gross_sales_scenario"] == row["gross_sales"]
    _, second_link = svc.link_scenario(t, s, who, oid, link_body("w403-u5-his-04", oid, other["id"]))
    k2 = now(engine)
    two = detail(svc, t, s, oid, k2)
    assert [(x["id"], x["selected"], x["compatible"]) for x in two["scenario_links"]] == [
        (second_link["id"], True, False), (first_link["id"], False, True)]
    assert set(two["scenario_links"][0]) == {"id", "scenario_id", "created_at", "selected", "compatible"}
    # The newer incompatible association is selected: never a fallback to the older compatible one.
    o = two["opportunity"]
    assert (o["scenario_id"], o["proposed_load_kw"], o["gross_sales_scenario"]) == (None, None, None)
    assert codes(two)[-1] == "SCENARIO_BASIS_MISMATCH"

    # Late change: a new W4-02 head, then revision 2 and its selection.
    _reconcile(engine, [DAYS[1]])
    project(engine)
    r1, r2 = revisions(engine)
    head = detail(svc, t, s, oid)
    assert [(h["revision_id"], h["revision_no"], h["current"]) for h in head["history"]] == [
        (str(r2.id), 2, True), (str(r1.id), 1, False)]
    assert set(head["history"][0]) == {"revision_id", "revision_no", "input_sha256", "created_at", "selection_seq",
                                       "selected_at", "job_id", "status", "current"}
    assert head["history"][1]["job_id"] == str(done.job_id) and head["history"][0]["input_sha256"] == r2.input_sha256
    assert head["history"][0]["selected_at"] >= head["history"][1]["selected_at"]
    assert head["currentness"]["selection_seq"] == head["history"][0]["selection_seq"]
    # At k2 only the first selection was visible; both links remain inspectable at both cutoffs.
    old = detail(svc, t, s, oid, k2)
    assert [(h["revision_id"], h["current"]) for h in old["history"]] == [(str(r1.id), True)]
    assert old["opportunity"]["revision_id"] == str(r1.id) and len(old["scenario_links"]) == 2
    assert len(detail(svc, t, s, oid, k1)["scenario_links"]) == 1
    # The compatible scenario pins revision 1's selection, so it is incompatible with revision 2.
    assert [x["compatible"] for x in head["scenario_links"]] == [False, False]


def test_list_detail_shape_full_count_pins_decimals_and_provenance(store, engine) -> None:  # noqa: F811
    t, s = mg(store, engine)
    project(engine)
    [rev] = revisions(engine)
    svc = service(engine)
    bare = bare_root(engine, t, s, date(2026, 10, 2), date(2026, 10, 6))
    body = page(svc, t, s)
    assert set(body) == LIST_KEYS and body["schema_version"] == "mini-opportunities-1"
    assert body["window"] == {"from": FROM, "to": TO, "known_at": body["window"]["known_at"]}
    assert set(body["currentness"]) == {"state", "job_state"} and body["total_count"] == 2
    row, empty = body["rows"]
    assert set(row) == ROW_KEYS and set(row["opportunity"]) == OBJECT_KEYS
    o = row["opportunity"]
    import re
    assert re.fullmatch(r"OPP-\d{6,}", o["code"]) and o["revision_id"] == str(rev.id) and o["revision_no"] == 1
    assert (o["first_day"], o["last_day"], o["model_version"], o["study_days"]) == (
        "2026-10-06", "2026-10-10", "mini-opportunity/1", 5)
    assert (o["eligible_days"], o["assessed_days"]) == (rev.result["eligible_days"], rev.result["assessed_days"])
    assert o["headroom_kw"] == rev.result["headroom_kw"]
    assert (o["demand_state"], o["collection_state"]) == ("UNVERIFIED", "UNVERIFIED")
    assert (o["proposed_load_kw"], o["gross_sales_scenario"], o["scenario_id"]) == (None, None, None)
    assert [d["local_day"] for d in o["day_rows"]] == [d.isoformat() for d in DAYS]
    for d, pin, frozen in zip(o["day_rows"], rev.selected_hours, rev.result["day_rows"]):
        assert set(d) == DAY_KEYS and {k: d[k] for k in frozen} == frozen
        assert (d["selection_seq"], d["mini_revision_id"]) == (pin["selection_seq"], pin["mini_revision_id"])
        bound = d["opportunity_kwh"]
        assert bound is None or all(isinstance(bound[k], str) and "e" not in bound[k].lower() for k in ("low", "high"))
    assert set(row["currentness"]) == {"state", "job_state", "selection_seq", "selected_at", "windows"}
    assert row["currentness"]["windows"] == [{"local_day": p["local_day"], "selection_seq": p["selection_seq"],
                                              "mini_revision_id": p["mini_revision_id"]} for p in rev.selected_hours]
    # S20: the five pinned mini revisions and their accepted-ID union, never the opportunity revision ID.
    with PostgresMiniDecisionStore(engine).snapshot() as c:
        found = renewable_revisions(c, t, s, [p["mini_revision_id"] for p in rev.selected_hours])
    union = sorted({i for r in found.values() for i in r["evidence_ids"]})
    selected = row["selected_source_provenance"]
    assert selected["evidence_ids"] == union and str(rev.id) not in selected["source_ids"]
    assert row["source_provenance"] == selected and row["pending_source_provenance"] is None
    assert body["selected_source_provenance"]["evidence_ids"] == union
    # The root with no visible selection.
    assert empty["opportunity"]["id"] == str(bare) and empty["status"] == "UNKNOWN"
    e = empty["opportunity"]
    assert (e["revision_id"], e["revision_no"], e["eligible_days"], e["assessed_days"], e["headroom_kw"],
            e["scenario_id"], e["day_rows"], e["study_days"]) == (None, None, None, None, None, None, [], 5)
    assert empty["currentness"] == {"state": "UNKNOWN", "job_state": "NONE", "selection_seq": None,
                                    "selected_at": None, "windows": []}
    assert empty["selected_source_provenance"] is None and empty["source_provenance"]["classification"] == "UNKNOWN"
    # Detail: the same siblings plus history, scenario links and links; never a one-row list.
    one = detail(svc, t, s, o["id"])
    assert set(one) == ROW_KEYS | {"schema_version", "history", "scenario_links", "links"}
    assert one["schema_version"] == "mini-opportunity-detail-1" and one["opportunity"] == o
    assert one["links"]["renewable"].startswith(f"/sites/{s}/performance/renewable?from={FROM}&to={TO}&known_at=")
    k = now(engine)
    assert iso_k(detail(svc, t, s, o["id"], k)) == k and one["links"]["scenario"] is None
    for unknown in (uuid4(), "not-a-uuid"):
        with pytest.raises(DecisionRefused) as refused:
            detail(svc, t, s, unknown)
        assert (refused.value.status, refused.value.code) == (404, "DECISION_NOT_FOUND")
    with pytest.raises(DecisionRefused) as refused:  # a foreign Site never reads this root
        detail(svc, t, uuid4(), o["id"])
    assert refused.value.code == "DECISION_NOT_FOUND"


def iso_k(body) -> str:
    """The detail's own read cutoff, as its renewable link carries it."""
    return body["links"]["renewable"].rsplit("known_at=", 1)[1]


def test_local_midnight_intersection_cursor_and_basis_change(store, engine) -> None:  # noqa: F811
    _, t, s = _setup(store, engine)
    svc = service(engine)
    a = bare_root(engine, t, s, DAYS[0], DAYS[-1])
    c_ = bare_root(engine, t, s, DAYS[0], DAYS[2])  # a second root on the same first day (id ASC)
    b = bare_root(engine, t, s, date(2026, 10, 2), DAYS[0])
    # Nairobi 6-10 Oct is exactly this UTC pair; both bounds are required and must be Site-local midnights.
    assert page(svc, t, s)["total_count"] == 3
    for frm, to in ((None, TO), (FROM, None), ("2026-10-05T22:00:00.000000Z", TO), (FROM, "2026-10-10T20:00:00Z"),
                    (TO, FROM), (FROM, FROM), ("yesterday", TO)):
        with pytest.raises(DecisionRefused) as refused:
            page(svc, t, s, frm=frm, to=to)
        assert refused.value.code == "INVALID_WINDOW", (frm, to)
    assert page(svc, t, s, frm="2026-10-06T00:00:00+03:00", to="2026-10-11T00:00:00+03:00")["total_count"] == 3
    # Intersection on [first_day, last_day + 1 day): 10 Oct alone holds A; 11 Oct holds nothing; 1-5 Oct holds
    # only the 2-6 Oct root (a study starting 6 Oct does not intersect it).
    only_10 = page(svc, t, s, frm="2026-10-09T21:00:00.000000Z", to=TO)
    assert [r["opportunity"]["id"] for r in only_10["rows"]] == [str(a)]
    assert page(svc, t, s, frm=TO, to="2026-10-11T21:00:00.000000Z")["total_count"] == 0
    early = page(svc, t, s, frm="2026-09-30T21:00:00.000000Z", to=FROM)
    assert [r["opportunity"]["id"] for r in early["rows"]] == [str(b)]
    # Ordering (first_day DESC, id ASC), count before paging, cursor `after = [first_day, id]`.
    lead, follow = sorted([str(a), str(c_)])
    first = page(svc, t, s, limit="1")
    assert [r["opportunity"]["id"] for r in first["rows"]] == [lead] and first["total_count"] == 3
    assert decode_cursor(first["next_cursor"])["after"] == ["2026-10-06", lead]
    second = page(svc, t, s, limit="1", cursor=first["next_cursor"])
    third = page(svc, t, s, limit="1", cursor=second["next_cursor"])
    assert [second["rows"][0]["opportunity"]["id"], third["rows"][0]["opportunity"]["id"]] == [follow, str(b)]
    assert third["next_cursor"] is None and third["total_count"] == 3
    assert second["selection_token"] == first["selection_token"]
    for bad, code in (("!!", "INVALID_CURSOR"), (encode_cursor({"v": 1}), "INVALID_CURSOR")):
        with pytest.raises(DecisionRefused) as refused:
            page(svc, t, s, limit="1", cursor=bad)
        assert refused.value.code == code
    with pytest.raises(DecisionRefused) as refused:
        page(svc, t, s, limit="0")
    assert refused.value.code == "INVALID_LIMIT"
    with pytest.raises(DecisionRefused) as refused:  # page two under different bounds
        page(svc, t, s, frm="2026-10-04T21:00:00.000000Z", limit="1", cursor=first["next_cursor"])
    assert refused.value.code == "DECISION_BASIS_CHANGED"
    # The cursor keeps page one's cutoff: a root created later is not visible, so page two still answers.
    bare_root(engine, t, s, DAYS[1], DAYS[-1] + timedelta(days=1))
    assert page(svc, t, s, limit="1", cursor=first["next_cursor"])["rows"] == second["rows"]
    # A live opportunity job in page one's token that settles before page two changes the selected basis.
    live = job(engine, t, s, _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    fresh = page(svc, t, s, limit="1")
    assert fresh["selection_token"] != first["selection_token"] and fresh["total_count"] == 4
    settle(engine, live)
    with pytest.raises(DecisionRefused) as refused:
        page(svc, t, s, limit="1", cursor=fresh["next_cursor"])
    assert (refused.value.status, refused.value.code) == (409, "DECISION_BASIS_CHANGED")


def new_case(engine, t, s, kind):
    """A W4-01 work case with its typed child (test-only schema insert, as `test_w401_migration_postgres.new_case`)."""
    case_id, prefix = uuid4(), "INC" if kind == "INCIDENT" else "WR"
    key = f"u5-{case_id.hex[:12]}"
    with engine.begin() as c:
        no = c.execute(text("SELECT nextval('work_public_no_seq')")).scalar_one()
        c.execute(text(
            "INSERT INTO work_case (id, tenant_id, site_id, kind, public_no, public_code, asset_id, occurred_at, "
            "actor_kind, actor_id, authorization_basis, attestation, create_key, create_payload_sha256) VALUES "
            "(:i, :t, :s, :k, :n, :code, NULL, '2026-10-06T16:11:00Z', 'SERVICE', 'service:w401-fixture', "
            "'SITE_WORK_WRITE', 'service=w401-fixture;job=j;rule=r', :key, :h)"),
            {"i": case_id, "t": t, "s": s, "k": kind, "n": no, "code": f"{prefix}-{no:06d}", "key": key,
             "h": "a" * 64})
        child = "incident (tenant_id, site_id, id, incident_key)" if kind == "INCIDENT" else (
            "maintenance_work_request (tenant_id, site_id, id, request_key)")
        c.execute(text(f"INSERT INTO {child} VALUES (:t, :s, :i, :key)"), {"t": t, "s": s, "i": case_id, "key": key})
    return case_id


def work_link(engine, t, s, case_id, oid, key) -> None:
    store_ = PostgresMiniDecisionStore(engine)
    with store_.transaction() as c:
        store_.insert_work_link(c, {
            "id": uuid4(), "tenant_id": t, "site_id": s, "case_id": case_id, "opportunity_id": oid,
            "actor_kind": "SERVICE", "actor_id": "service:w403-fixture",
            "authorization_basis": "SITE_DECISION_WRITE:service:w403-fixture",
            "attestation": "service=w403-fixture;job=positive-decisions;rule=w403/1", "idempotency_key": key,
            "payload_sha256": "b" * 64})


def test_site_work_link_uses_case_kind_and_never_actions_root(store, engine) -> None:  # noqa: F811
    _, t, s = _setup(store, engine)
    svc = service(engine)
    oid = bare_root(engine, t, s, DAYS[0], DAYS[-1])
    plain = detail(svc, t, s, oid)
    assert plain["links"]["site_work"] is None and plain["links"]["scenario"] is None
    assert plain["links"]["renewable"].startswith(f"/sites/{s}/performance/renewable?from={FROM}&to={TO}&known_at=")
    k0 = now(engine)
    work_link(engine, t, s, new_case(engine, t, s, "MAINTENANCE_REQUEST"), oid, "w403-u5-work-01")
    maintenance = detail(svc, t, s, oid)["links"]["site_work"]
    assert maintenance == f"/sites/{s}/work/maintenance"
    k1 = now(engine)
    work_link(engine, t, s, new_case(engine, t, s, "INCIDENT"), oid, "w403-u5-work-02")
    both = detail(svc, t, s, oid)["links"]
    assert both["site_work"] == f"/sites/{s}/work/incidents" and both["scenario"] is None
    assert detail(svc, t, s, oid, k1)["links"]["site_work"] == maintenance
    assert detail(svc, t, s, oid, k0)["links"]["site_work"] is None
    for link in (maintenance, both["site_work"]):
        assert not link.endswith("/work") and link != f"/sites/{s}/work"
    # Another opportunity's association never leaks.
    other = bare_root(engine, t, s, DAYS[1], DAYS[-1] + timedelta(days=1))
    assert detail(svc, t, s, other)["links"]["site_work"] is None


class _FailingStore:
    def snapshot(self):
        raise MiniDecisionStoreUnavailable("down")


def _client(registry, opportunities=None, **kw) -> TestClient:
    app = FastAPI()
    app.include_router(build_mini_decisions_router(None, registry, opportunities=opportunities, **kw))
    return TestClient(app)


def test_role_cutover_scope_and_store_refusals(store, engine, monkeypatch) -> None:  # noqa: F811
    route = f"/api/sites/{CODE}/opportunities"
    query = {"from": FROM, "to": TO}
    item = f"{route}/{uuid4()}"
    opened = {"gate": lambda code, t, s: (True, "open")}
    # Non-MINIGRID: the 200 UNKNOWN envelope before the (closed) gate, with no store.
    cold = _client(_Registry(site_type="COLD_ROOM"))
    envelope = cold.get(route).json()
    assert envelope["schema_version"] == "mini-opportunities-1" and envelope["rows"] == []
    assert envelope["status"] == "UNKNOWN" and envelope["limitations"] == [
        {"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}]
    one = cold.get(item)
    assert one.status_code == 200 and one.json()["schema_version"] == "mini-opportunity-detail-1"
    assert one.json()["opportunity"] is None and one.json()["limitations"][0]["code"] == "SITE_ROLE_UNSUPPORTED"
    # MINIGRID with the default (closed) gate: 409 before query parsing.
    closed = _client(_Registry())
    for path, listing in ((route, True), (item, False)):
        r = closed.get(path)
        assert r.status_code == 409 and r.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        assert ("rows" in r.json()["detail"]) is listing
    # Gate failure and missing/failing store are 503, never a 200 empty result.
    from assetops_backend.sites.ports import SiteStoreUnavailable

    def broken(code, t, s):
        raise SiteStoreUnavailable("down")

    assert _client(_Registry(), gate=broken).get(route, params=query).status_code == 503
    for client_ in (_client(_Registry(), **opened),
                    _client(_Registry(), OpportunityService(_FailingStore(), None), **opened)):  # type: ignore[arg-type]
        for path in (route, item):
            r = client_.get(path, params=query)
            assert r.status_code == 503 and r.json()["detail"]["code"] == "DECISION_STORE_UNAVAILABLE"
    # Query validation after scope and gate.
    assert _client(_Registry(), **opened).get(route).json()["detail"]["code"] == "INVALID_WINDOW"
    # Scope precedes everything.
    assert _client(_Registry(), access=lambda r, c: 403, **opened).get(route).json()["detail"]["code"] == (
        "SITE_SCOPE_FORBIDDEN")
    assert _client(_Registry(), access=lambda r, c: 401, **opened).get(item).status_code == 401
    assert _client(_Registry(), **opened).get("/api/sites/NOPE-1/opportunities").status_code == 404
    assert _client(_Registry(down=True), **opened).get(route).status_code == 503

    # The composed app wires the Performance gate: a fresh request on an imported MINIGRID Site is gated.
    _, t, s = _setup(store, engine)
    from assetops_backend import main

    monkeypatch.setenv("DATABASE_URL", URL)
    app = TestClient(main.create_app())
    r = app.get(route, params=query)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED", r.json()
    # Through the router with an open gate, the same persisted store answers (a fresh request).
    live = _client(SimpleNamespace(tenant=lambda: SimpleNamespace(id=t),
                                   imported=lambda code: SimpleNamespace(id=s, site_code=CODE, site_type="MINIGRID")
                                   if code == CODE else None),
                   service(engine), **opened)
    body = live.get(route, params=query).json()
    assert body["schema_version"] == "mini-opportunities-1" and body["total_count"] == 0
    assert live.get(item).json()["detail"]["code"] == "DECISION_NOT_FOUND"
