"""S4-04 phase 1: the Site Finding index read on real PostgreSQL (`D-2026-10-15-a-finding-index`,
`D-2026-10-15-s404-contract`).

Every fixture is produced through S2 ingestion, the S3 worker and the S4 matcher (`CaseRunner`); no row is
seeded. The assessed-empty fixture (`D-site-finding-index-empty`) and the positive fixture
(`D-site-finding-index-rows`) are independent tests. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner, _t, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_schedule_tick_postgres import import_site

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_index import (INDEX_CONTINUITY_LIMIT, FindingIndexService, IndexConflict,
                                                          discover, encode_cursor, sort_key)
    from assetops_backend.analytics.finding_read import FindingReadService
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.finding_api import build_finding_router
    from assetops_backend.finding_index_api import build_finding_index_router
    from assetops_backend.site_overview.composition import build_site_overview_read
    from assetops_backend.site_overview.read import choose

CLOSED = "test: Performance comparison has not passed"
DOMAIN = "mini-grid-dispatch"


def client_for(runner, *, gate_open: bool = True, access=None, extra: dict | None = None,
               continuity_limit: int | None = None) -> "TestClient":
    dispatch = DispatchReadService(PostgresAssessmentStore(URL))
    kwargs = {} if continuity_limit is None else {"continuity_limit": continuity_limit}
    index = FindingIndexService(PostgresFindingStore(URL), dispatch, **kwargs)
    scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site), **(extra or {})}
    gate = lambda code, t, s: (gate_open, "test: gate open" if gate_open else CLOSED)  # noqa: E731
    app = FastAPI()
    app.include_router(build_finding_index_router(index, scope.get, gate=gate,
                                                  **({} if access is None else {"access": access})))
    app.include_router(build_finding_router(FindingReadService(PostgresFindingStore(URL), dispatch), scope.get,
                                            gate=gate))
    return TestClient(app)


def call(client, site: str = "KOBO-001", **params):
    params.setdefault("domain", DOMAIN)
    if "frm" in params:
        params["from"] = params.pop("frm")
    return client.get(f"/api/sites/{site}/finding-index", params=params)


def ok(client, site: str = "KOBO-001", **params) -> dict:
    response = call(client, site, **params)
    assert response.status_code == 200, response.text
    return response.json()


def refused(response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    detail = response.json()["detail"]
    assert detail["code"] == code, detail
    # no refusal carries a status, rows or a count (never a CURRENT zero)
    assert "status" not in detail and not detail.get("rows") and detail.get("total_count") is None, detail
    return detail


def assert_no_claim(body: dict, status: str) -> None:
    assert body["status"] == status and not body["is_current"], body["status_reasons"]
    assert body["rows"] == [] and body["total_count"] is None and body["next_cursor"] is None
    assert "not a no-Findings verdict" in body["rows_statement"]


def set_jobs(engine, site, status: str) -> int:
    extra = {"LEASED": ", lease_until = now() + interval '1 hour'",
             "FAILED": ", attempts = 3, last_error = 'injected failure'"}.get(status, "")
    with engine.begin() as c:
        return c.execute(text(f"UPDATE recompute_job SET status = :st{extra} WHERE site_id = :s "
                              "AND status IN ('PENDING', 'LEASED')"), {"st": status, "s": site}).rowcount


def block(start: str, end: str, **kw) -> dict:
    return {"from": start, "to": end, **kw}


CANDIDATE = dict(pv="40", dis="20", soc="80", stop_before=True, stop_after=True)
NO_CANDIDATE = dict(pv="5", dis="5", soc="80", stop_before=True, stop_after=True)


class TestScopeValidationAndGate:
    def test_access_scope_validation_and_closed_gate_refuse_without_any_claim(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        other = import_site(store, "KOBO-902", tenant="other-tenant").site
        client = client_for(runner)
        window = {"frm": "2026-10-25T00:00:00Z", "to": "2026-10-26T00:00:00Z"}
        # 401 / 403 / 404 come before validation and never count anything
        r = call(client_for(runner, access=lambda req, code: 401), **window)
        assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"
        assert call(client_for(runner, access=lambda req, code: 403), **window).json()["detail"]["code"] == \
            "SITE_SCOPE_FORBIDDEN"
        assert call(client, "KOBO-902", **window).status_code == 404  # the other tenant's Site is not in scope
        assert call(client, "NOPE-1", domain="cold-chain").status_code == 404  # scope before validation
        assert other.id != runner.site
        # unsupported domains and invalid windows are a typed 422, never CURRENT zero
        for domain in (None, "", "cold-chain", "mini_grid", "dispatch", "MINI-GRID-DISPATCH"):
            params = {**window, "domain": domain} if domain is not None else dict(window)
            if domain is None:
                r = client.get("/api/sites/KOBO-001/finding-index",
                               params={"from": window["frm"], "to": window["to"]})
            else:
                r = call(client, **params)
            refused(r, 422, "UNSUPPORTED_DOMAIN")
        for bad in ({"frm": "2026-10-25T00:00:00", "to": "2026-10-26T00:00:00Z"},
                    {"frm": "2026-10-25T00:00:00+03:00", "to": "2026-10-26T00:00:00Z"},
                    {"frm": "2026-10-26T00:00:00Z", "to": "2026-10-25T00:00:00Z"},
                    {"frm": "2026-10-25T00:00:00Z", "to": "2026-10-25T00:00:00Z"},
                    {"frm": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:01Z"},
                    {"frm": "yesterday", "to": "2026-10-26T00:00:00Z"},
                    {"to": "2026-10-26T00:00:00Z"}):
            refused(call(client, **bad), 422, "INVALID_WINDOW")
        assert ok(client, frm="2026-10-01T00:00:00Z", to="2026-11-01T00:00:00Z")["window"]["to"] == \
            "2026-11-01T00:00:00Z"  # exactly 31 days is accepted
        for limit in ("0", "101", "ten"):
            refused(call(client, **window, limit=limit), 422, "INVALID_LIMIT")
        for cursor in ("%%%", "bm90LWpzb24", encode_cursor({"v": 1}), encode_cursor(
                {"v": 1, "tenant_id": "a", "site_id": "b", "domain": DOMAIN, "from": "x", "to": "y",
                 "selection_token": "t", "after": ["not-a-time", str(uuid4())]})):
            refused(call(client, **window, cursor=cursor), 422, "INVALID_CURSOR")
        # closed Performance gate: 409 with its reason, no rows, count or empty claim
        detail = refused(call(client_for(runner, gate_open=False), **window), 409, "PERFORMANCE_CUTOVER_CLOSED")
        assert detail["message"] == CLOSED and detail["rows"] is None


class TestAssessedEmpty:
    """`D-site-finding-index-empty`: an independently persisted, watermarked, assessed zero-row window."""

    def test_assessed_zero_with_watermarks_exclusions_and_non_current_variants(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        run_case(runner, SPEC["cases"][0])  # F01: one Finding 2026-10-06 08:00-09:00, for exclusion checks
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z",
                     "blocks": [block("2026-10-25T08:00:00Z", "2026-10-25T09:00:00Z", **NO_CANDIDATE)]})
        runner.step({"do": "assess"})
        sibling = import_site(store, "KOBO-903").site
        foreign = import_site(store, "KOBO-902", tenant="other-tenant").site
        client = client_for(runner, extra={"KOBO-903": ("KOBO-903", sibling.tenant_id, sibling.id),
                                           "KOBO-902": ("KOBO-902", foreign.tenant_id, foreign.id)})
        empty = {"frm": "2026-10-25T00:00:00Z", "to": "2026-10-26T00:00:00Z"}
        # S3 selected but no S4 pass through it yet: not a verdict
        pending = ok(client, **empty)
        assert_no_claim(pending, "PENDING")
        assert any("MATCH_PENDING" in r for r in pending["status_reasons"])
        runner.match()

        body = ok(client, **empty)
        assert body["status"] == "CURRENT" and body["is_current"] and body["rows_statement"] is None
        assert body["rows"] == [] and body["total_count"] == 0 and body["next_cursor"] is None
        assert body["domain"] == {"requested": DOMAIN, "finding_domain": "mini_grid", "analytic_id": "dispatch",
                                  "matcher_version": body["domain"]["matcher_version"]}
        assert body["window"]["from"] == "2026-10-25T00:00:00Z" and body["display_timezone"] == "UTC"
        assert body["discovery"]["days"] == ["2026-10-25"] and body["discovery"]["limit_days"] == 62
        [day] = body["watermarks"]["days"]
        assert day["status"] == "CURRENT" and day["s4"]["matched"]
        assert day["s3"]["selection_seq"] and day["s3"]["run_id"] and day["s3"]["window_assessment_revision_id"]
        assert day["s3"]["input_sha256"] and day["s3"]["configuration_sha256"] and day["s3"]["watermarks"]
        matcher = body["watermarks"]["matcher"]
        assert matcher["match_pass_id"] and matcher["matched_through_selection_seq"] >= day["s3"]["selection_seq"]
        assert body["selection_token"].startswith("sfi1-") and body["knowledge_at"] and body["built_at"]
        # the same assessed day under an unsupported token is a 422, never an assessed zero
        refused(call(client, **empty, domain="cold-chain"), 422, "UNSUPPORTED_DOMAIN")

        # strict half-open intersection on the F01 day: boundary touch excluded either side
        assert ok(client, frm="2026-10-06T09:00:00Z", to="2026-10-07T00:00:00Z")["total_count"] == 0
        assert ok(client, frm="2026-10-06T00:00:00Z", to="2026-10-06T08:00:00Z")["total_count"] == 0
        inside = ok(client, frm="2026-10-06T08:59:00Z", to="2026-10-06T09:01:00Z")
        assert inside["status"] == "CURRENT" and inside["total_count"] == 1
        # wrong window, sibling Site and other tenant's Site: Unknown, no rows, never zero
        assert_no_claim(ok(client, frm="2026-10-07T00:00:00Z", to="2026-10-08T00:00:00Z"), "UNASSESSED")
        assert_no_claim(ok(client, "KOBO-903", frm="2026-10-06T00:00:00Z", to="2026-10-07T00:00:00Z"), "UNASSESSED")
        assert_no_claim(ok(client, "KOBO-902", frm="2026-10-06T00:00:00Z", to="2026-10-07T00:00:00Z"), "UNASSESSED")
        # closed gate over the assessed-empty window: 409, no zero
        refused(call(client_for(runner, gate_open=False), **empty), 409, "PERFORMANCE_CUTOVER_CLOSED")

        # late evidence (dirty), leased and failed work: no snapshot, so no rows and no count
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-25T10:00:00Z", "2026-10-25T10:30:00Z", **NO_CANDIDATE)]})
        assert_no_claim(ok(client, **empty), "STALE_PROJECTION")
        assert set_jobs(engine, runner.site, "LEASED") >= 1
        assert_no_claim(ok(client, **empty), "STALE_PROJECTION")
        assert set_jobs(engine, runner.site, "FAILED") >= 1
        failed = ok(client, **empty)
        assert_no_claim(failed, "FAILED")
        assert any("RECOMPUTE_FAILED" in r for r in failed["status_reasons"])


class TestContinuity:
    def test_fixed_point_bridge_chain_dirty_neighbour_and_cap(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [
            block("2026-10-25T23:30:00Z", "2026-10-26T00:30:00Z", **CANDIDATE),
            block("2026-10-26T23:30:00Z", "2026-10-27T00:30:00Z", **CANDIDATE)]})
        runner.step({"do": "assess"})
        runner.match()
        heads = runner.reload()["revisions"]
        assert {(r["episode_start"], r["episode_end"]) for r in heads} == {
            (_t("2026-10-25T23:30:00Z"), _t("2026-10-26T00:30:00Z")),
            (_t("2026-10-26T23:30:00Z"), _t("2026-10-27T00:30:00Z"))}
        client = client_for(runner)
        window = {"frm": "2026-10-27T01:00:00Z", "to": "2026-10-28T00:00:00Z"}
        body = ok(client, **window)
        # the chain reaches two days beyond the requested one, through two actual cross-midnight episodes
        assert body["discovery"]["requested_days"] == ["2026-10-27"]
        assert body["discovery"]["days"] == ["2026-10-25", "2026-10-26", "2026-10-27"]
        assert [d["day"] for d in body["watermarks"]["days"]] == body["discovery"]["days"]
        assert body["status"] == "CURRENT" and body["total_count"] == 0  # both episodes end before 01:00
        assert all(d["s3"]["selection_seq"] and d["s4"]["matched"] for d in body["watermarks"]["days"])
        # the service cap: 409 with no rows, count or empty claim (2 days here; 62 by default, below)
        detail = refused(call(client_for(runner, continuity_limit=2), **window), 409, "INDEX_CONTINUITY_LIMIT")
        assert detail["limit_days"] == 2 and "does not mean continuity ends" in detail["message"]
        # a dirty, then failed, neighbour two days away blocks CURRENT for the requested day
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-25T10:00:00Z", "2026-10-25T10:30:00Z", **NO_CANDIDATE)]})
        dirty = ok(client, **window)
        assert_no_claim(dirty, "STALE_PROJECTION")
        assert all(r.startswith("2026-10-25") for r in dirty["status_reasons"]), dirty["status_reasons"]
        set_jobs(engine, runner.site, "FAILED")
        assert_no_claim(ok(client, **window), "FAILED")

    def test_s3_candidate_near_an_edge_reaches_a_neighbour_the_matcher_skipped(self, store, engine) -> None:  # noqa: F811
        """Phase-1 review H1: the matcher skips a Candidate cluster within 20 min of a UTC edge while the
        neighbouring day is not CURRENT, yet records a completed pass, so no stored episode reaches the edge.
        The selected S3 Candidate segment must pull the neighbour into discovery, whose state then blocks CURRENT."""
        runner = CaseRunner(store, engine)
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [
            block("2026-10-25T23:10:00Z", "2026-10-25T23:45:00Z", **CANDIDATE),
            block("2026-10-26T10:00:00Z", "2026-10-26T10:30:00Z", **NO_CANDIDATE)]})
        runner.step({"do": "assess"})
        # late evidence leaves D+1 stale; the matcher then skips D's cluster and writes nothing
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-26T12:00:00Z", "2026-10-26T12:30:00Z", **NO_CANDIDATE)]})
        runner.match()
        assert runner.reload()["revisions"] == []
        client = client_for(runner)
        day = {"frm": "2026-10-25T00:00:00Z", "to": "2026-10-26T00:00:00Z"}
        stale = ok(client, **day)
        assert stale["discovery"]["days"] == ["2026-10-25", "2026-10-26"]
        assert_no_claim(stale, "STALE_PROJECTION")
        assert all(r.startswith("2026-10-26") for r in stale["status_reasons"]), stale["status_reasons"]
        # the injected cap is reached through the S3 Candidate edge alone (no stored episode exists)
        detail = refused(call(client_for(runner, continuity_limit=1), **day), 409, "INDEX_CONTINUITY_LIMIT")
        assert detail["limit_days"] == 1
        # D+1 reassessed CURRENT, but no match pass through its new selection yet: still no claim
        runner.step({"do": "assess"})
        assert runner.reload()["revisions"] == []
        assert_no_claim(ok(client, **day), "PENDING")
        # after the rematch the Finding exists and the window reads CURRENT with it
        runner.match()
        body = ok(client, **day)
        assert body["status"] == "CURRENT" and body["total_count"] == 1, body["status_reasons"]
        assert body["rows"][0]["episode"]["start"] == "2026-10-25T23:10:00Z"

    def test_default_cap_is_62_distinct_days(self) -> None:
        assert INDEX_CONTINUITY_LIMIT == 62
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        chain = [{"episode_start": base + timedelta(days=n, hours=23, minutes=30),
                  "episode_end": base + timedelta(days=n + 1, minutes=30)} for n in range(70)]
        lo, hi = base + timedelta(days=69, hours=1), base + timedelta(days=70)
        with pytest.raises(IndexConflict) as raised:
            discover(chain, lo, hi)
        assert raised.value.detail["code"] == "INDEX_CONTINUITY_LIMIT"
        assert len(discover(chain[-61:], lo, hi)) == 62  # 61 bridges: exactly at the cap


class TestPositiveRows:
    """`D-site-finding-index-rows`: persisted canonical Findings with exact revision drill-down."""

    def test_rows_order_cursor_relations_lineage_and_s5_card_parity(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        for case in SPEC["cases"]:
            run_case(runner, case)
        stored = runner.reload()
        latest = {}
        for r in stored["revisions"]:
            latest[r["finding_id"]] = r
        merged_away = {m["superseded_finding_id"] for m in stored["merges"]}
        client = client_for(runner)
        day = {"frm": "2026-10-15T00:00:00Z", "to": "2026-10-16T00:00:00Z"}
        body = ok(client, **day)
        assert body["status"] == "CURRENT", body["status_reasons"]
        expected = sorted((f for f in stored["findings"] if f["id"] not in merged_away
                           and latest[f["id"]]["episode_start"] < _t(day["to"])
                           and latest[f["id"]]["episode_end"] > _t(day["frm"])),
                          key=lambda f: (-latest[f["id"]]["episode_start"].timestamp(), str(f["id"])))
        assert len(expected) >= 3 and body["total_count"] == len(expected)
        assert [r["finding_id"] for r in body["rows"]] == [str(f["id"]) for f in expected]
        for row in body["rows"]:
            head = latest[UUID(row["finding_id"])]
            assert row["finding_revision_id"] == str(head["id"]) and row["revision_no"] == head["revision_no"]
            assert row["key"] == {"tenant_id": str(runner.tenant), "site_id": str(runner.site),
                                  "finding_id": row["finding_id"]}
            assert row["links"]["selected_revision"] == \
                f"/sites/KOBO-001/findings/{row['finding_id']}?revision_id={row['finding_revision_id']}"
            assert row["amount"]["state"] == "UNAVAILABLE"
            cited = {str(e["evidence_id"]) for e in stored["evidence"] if e["finding_revision_id"] == head["id"]}
            assert set(row["cited"]["accepted_evidence_ids"]) == cited
            assert row["assessment"]["assessment_revision_id"] == str(head["assessment_revision_id"])
            assert row["cited"]["configuration"] and row["cited"]["configuration"][0]["configuration_sha256"]
        # merge canonicalization: merged-away IDs are relation links on the surviving row, never rows
        merged_rows = [r for r in body["rows"] if r["relations"]["merged_from"]]
        assert merged_rows and all(UUID(x) in merged_away for r in merged_rows for x in r["relations"]["merged_from"])
        assert any(r["relations"]["split_from"] for r in body["rows"])  # F06 split part

        # cursor pages reproduce the full order without splicing; reload gives the same page
        pages, cursor = [], None
        while True:
            page = ok(client, **day, limit="1", **({"cursor": cursor} if cursor else {}))
            assert page["selection_token"] == body["selection_token"] and page["total_count"] == len(expected)
            pages += page["rows"]
            cursor = page["next_cursor"]
            if cursor is None:
                break
        assert [r["finding_id"] for r in pages] == [r["finding_id"] for r in body["rows"]]
        again = ok(client, **day)
        assert [r["finding_revision_id"] for r in again["rows"]] == [r["finding_revision_id"] for r in body["rows"]]
        # exact pinned link resolves to the selected revision
        first = body["rows"][0]
        detail = client.get(first["links"]["api_selected_revision"])
        assert detail.status_code == 200 and detail.json()["selection"]["revision_id"] == first["finding_revision_id"]

        # S5-01 parity: the first index row is the Overview card Finding and revision on the same Site/day
        overview = build_site_overview_read(URL, PostgresEvidenceLedger(URL))
        card = overview.read("KOBO-001", runner.tenant, runner.site, _t(day["frm"]).date(),
                             access_basis="test", source_open=True, source_reason="test: gate open")["known_finding"]
        assert card is not None and (card["id"], card["revision_id"]) == (first["finding_id"],
                                                                          first["finding_revision_id"])

        # extension across midnight: one row, its latest revision; discovery includes the reached day
        f02 = ok(client, frm="2026-10-09T00:00:00Z", to="2026-10-10T00:00:00Z")
        assert f02["status"] == "CURRENT" and "2026-10-08" in f02["discovery"]["days"]
        [ext] = [r for r in f02["rows"] if r["episode"]["start"] == "2026-10-08T23:20:00Z"]
        # extended by F02's SUPPORT_CHANGED revision (later cases append provenance-only revisions on top)
        assert ext["episode"]["end"] == "2026-10-09T00:55:00Z" and ext["revision_no"] >= 2
        # a closed (no longer supported) episode stays an eligible row
        f05 = ok(client, frm="2026-10-21T00:00:00Z", to="2026-10-22T00:00:00Z")
        assert f05["status"] == "CURRENT" and [r["lifecycle"] for r in f05["rows"]] == ["NO_LONGER_SUPPORTED"]
        # relations equal the stored roots (recurrence links included)
        f03 = ok(client, frm="2026-10-11T00:00:00Z", to="2026-10-12T00:00:00Z")
        roots = {str(f["id"]): f for f in stored["findings"]}
        for r in f03["rows"] + body["rows"]:
            root = roots[r["finding_id"]]
            assert r["relations"]["recurs_after"] == (None if root["recurs_after_finding_id"] is None
                                                      else str(root["recurs_after_finding_id"]))
        assert len(f03["rows"]) == 2

    def test_order_ties_on_episode_start_break_by_uuid_like_the_s5_card(self) -> None:
        start = datetime(2026, 10, 15, 8, tzinfo=timezone.utc)
        ids = sorted(str(uuid4()) for _ in range(4))
        rows = [{"finding_id": i, "episode_start": start, "episode_end": start + timedelta(hours=1)}
                for i in reversed(ids)] + [{"finding_id": str(uuid4()), "episode_start": start - timedelta(hours=1),
                                           "episode_end": start}]
        assert sorted(rows, key=sort_key)[0]["finding_id"] == ids[0] == choose(rows)["finding_id"]


class TestInvalidation:
    def test_late_revision_invalidates_cursor_and_keeps_pinned_links(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        f06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
        for step in f06["steps"][:3]:
            runner.step(step)
        client = client_for(runner)
        day = {"frm": "2026-10-15T00:00:00Z", "to": "2026-10-16T00:00:00Z"}
        first = ok(client, **day, limit="1")
        assert first["status"] == "CURRENT" and first["total_count"] == 3 and first["next_cursor"]
        old = first["rows"][0]
        cursor = first["next_cursor"]
        # the cursor is bound to its scope
        moved = refused(call(client, frm="2026-10-15T00:00:00Z", to="2026-10-15T23:00:00Z", cursor=cursor),
                        409, "INDEX_BASIS_CHANGED")
        assert moved["reason"] == "SCOPE_CHANGED" and moved["instruction"] == "REQUEST_FIRST_PAGE_WITHOUT_CURSOR"
        assert moved["next_cursor"] is None
        # late evidence: the basis is no longer current, so the cursor restarts (409, not 422)
        runner.step(f06["steps"][3])  # release 'contradiction'
        assert refused(call(client, **day, cursor=cursor), 409, "INDEX_BASIS_CHANGED")["reason"] == \
            "BASIS_NOT_CURRENT"
        refused(call(client, **day, cursor=cursor[:-3] + "!!!"), 422, "INVALID_CURSOR")
        runner.step(f06["steps"][4])  # assess
        runner.step(f06["steps"][5])  # match: new revisions
        assert refused(call(client, **day, cursor=cursor), 409, "INDEX_BASIS_CHANGED")["reason"] == \
            "SELECTION_CHANGED"
        fresh = ok(client, **day)
        assert fresh["status"] == "CURRENT" and fresh["selection_token"] != first["selection_token"]
        assert old["finding_revision_id"] not in {r["finding_revision_id"] for r in fresh["rows"]}
        # the old pinned revision link survives the newer revision
        pinned = client.get(old["links"]["api_selected_revision"])
        assert pinned.status_code == 200 and pinned.json()["selection"]["revision_id"] == old["finding_revision_id"]

    def test_unconfirmed_episode_is_an_eligible_row(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        f05 = next(c for c in SPEC["cases"] if c["case_id"] == "F05")
        for step in f05["steps"][:6]:
            runner.step(step)
        body = ok(client_for(runner), frm="2026-10-21T00:00:00Z", to="2026-10-22T00:00:00Z")
        assert body["status"] == "CURRENT" and [r["lifecycle"] for r in body["rows"]] == ["UNCONFIRMED"]


class _MovingStore:
    """A store whose writer fence changes between the snapshot and the after-read (moving selection)."""

    def __init__(self, heads: list) -> None:
        self.heads, self.calls = heads, 0

    def index_snapshot(self, t, s, d, a):
        day = datetime(2026, 10, 25, tzinfo=timezone.utc)
        return {"heads": self.heads, "merges": [], "selection_seqs": {day: 7}, "fence": "before",
                "match_pass": {"match_pass_id": "p", "matched_through_selection_seq": 7}}

    def fence(self, t, s, a):
        return "after"

    def index_lineage(self, t, s, ids):
        return {"assessments": [], "evidence": [], "runs": []}


class _CurrentDispatch:
    def window(self, t, s, day):
        return {"status": "CURRENT", "status_reasons": [], "selection": {}, "window_assessment": None,
                "watermarks": {}, "coverage": None, "limitations": [], "current_basis": {"read_at": None}}


def test_selection_moving_during_the_read_is_never_current() -> None:
    from assetops_backend.analytics.finding_index import parse_request

    service = FindingIndexService(_MovingStore([]), _CurrentDispatch())
    body = service.read(uuid4(), uuid4(), "KOBO-001", parse_request(
        DOMAIN, "2026-10-25T00:00:00Z", "2026-10-26T00:00:00Z", None, None), access_basis="test")
    assert body["watermarks"]["days"][0]["status"] == "CURRENT"  # every day is current; only the fence moved
    assert body["status"] == "STALE_PROJECTION" and body["rows"] == [] and body["total_count"] is None
    assert any("SELECTION_MOVED_DURING_READ" in r for r in body["status_reasons"])
