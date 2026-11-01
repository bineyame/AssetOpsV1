"""IDX-GAPS U4: `finding-index/2` on real PostgreSQL (build sheet IDX-GAPS §2 U4, P1-P5, and the residual-risk probe).

Every Finding here is produced through S2 ingestion, the S3 worker and the S4 matcher (`CaseRunner`); no row is
seeded, so withholding is proved on real matcher output. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import date

import pytest

from test_s4_finding_index_postgres import CANDIDATE, NO_CANDIDATE, assert_no_claim, block, client_for, ok
from test_s4_finding_store_postgres import SPEC, URL, CaseRunner, _t, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_index import FindingIndexService, parse_request

DOMAIN = "mini-grid-dispatch"


def day(d: str, n: int = 1) -> dict:
    """The window `[d, d + n days)`."""
    lo = date.fromisoformat(d)
    hi = date.fromordinal(lo.toordinal() + n)
    return {"frm": f"{lo.isoformat()}T00:00:00Z", "to": f"{hi.isoformat()}T00:00:00Z"}


def f01(runner) -> None:
    run_case(runner, SPEC["cases"][0])  # F01: one Finding 2026-10-06 08:00-09:00, assessed and matched


def gap_map(body: dict) -> dict:
    return {g["day"]: (g["state"], g["reason"]) for g in body["gaps"]}


def assess_empty(runner, d: str, decided: str) -> None:
    """Deliver one non-candidate hour on `d`, so that day is assessed (with no Finding) once assessed and matched."""
    runner.step({"do": "deliver", "decided": decided,
                 "blocks": [block(f"{d}T08:00:00Z", f"{d}T09:00:00Z", **NO_CANDIDATE)]})


class TestPartial:
    def test_p1_one_missing_day_lists_the_assessed_finding_and_names_the_gap(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        f01(runner)
        body = ok(client_for(runner), **day("2026-10-06", 2))
        assert body["status"] == "PARTIAL" and not body["is_current"], body["status_reasons"]
        assert body["policy_version"] == "finding-index/2" and body["selection_token"].startswith("sfi2-")
        assert [r["episode"]["start"] for r in body["rows"]] == ["2026-10-06T08:00:00Z"]
        assert body["total_count"] == 1 and body["withheld"] is False
        assert body["rows_statement"].startswith("Rows from assessed days only")
        assert body["gaps"] == [{"day": "2026-10-07", "state": "UNASSESSED", "reason": "NOT_CURRENT"}]
        # v1 is unchanged on the assessed day alone; the missing day alone stays the v1 no-claim body
        alone = ok(client_for(runner), **day("2026-10-06"))
        assert alone["status"] == "CURRENT" and alone["is_current"] and alone["gaps"] == []
        assert_no_claim(ok(client_for(runner), **day("2026-10-07")), "UNASSESSED")

    def test_p2_one_pending_day_lists_the_finding_and_names_the_pending_day(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        f01(runner)
        assess_empty(runner, "2026-10-07", "2026-10-30T08:00:00Z")
        assess_empty(runner, "2026-10-08", "2026-10-30T08:05:00Z")
        runner.step({"do": "assess"})
        runner.match()
        client = client_for(runner)
        assert ok(client, **day("2026-10-06", 3))["status"] == "CURRENT"
        # late evidence on 10-08, not assessed: that day is no longer CURRENT
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-08T10:00:00Z", "2026-10-08T10:30:00Z", **NO_CANDIDATE)]})
        body = ok(client, **day("2026-10-06", 3))
        assert body["status"] == "PARTIAL" and not body["is_current"], body["status_reasons"]
        assert [r["episode"]["start"] for r in body["rows"]] == ["2026-10-06T08:00:00Z"]
        assert body["total_count"] == 1 and body["withheld"] is False
        assert gap_map(body) == {"2026-10-08": ("STALE_PROJECTION", "NOT_CURRENT")}
        # assessed again but not matched through: PENDING, still a gap
        runner.step({"do": "assess"})
        pending = ok(client, **day("2026-10-06", 3))
        assert pending["status"] == "PARTIAL" and gap_map(pending) == {"2026-10-08": ("PENDING", "NOT_CURRENT")}
        assert pending["total_count"] == 1
        runner.match()
        assert ok(client, **day("2026-10-06", 3))["status"] == "CURRENT"

    def test_p3_an_edge_candidate_next_to_a_gap_day_is_withheld(self, store, engine) -> None:  # noqa: F811
        """Sheet form: a Candidate block 10-06 23:45-23:59 next to a 10-07 that is not CURRENT. Observed: delivering
        that block also assesses 10-07 (no evidence there) CURRENT, so 10-07 is made a gap by late evidence before
        the match; the matcher then skips the edge cluster and leaves 10-06 PENDING (not matched through its selection),
        so 10-06 is itself a NOT_CURRENT gap."""
        runner = CaseRunner(store, engine)
        assess_empty(runner, "2026-10-05", "2026-10-30T08:00:00Z")
        runner.step({"do": "deliver", "decided": "2026-10-30T08:05:00Z",
                     "blocks": [block("2026-10-06T23:45:00Z", "2026-10-06T23:59:00Z", **CANDIDATE)]})
        runner.step({"do": "assess"})
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-07T12:00:00Z", "2026-10-07T12:30:00Z", **NO_CANDIDATE)]})
        runner.match()
        assert runner.reload()["revisions"] == []  # the matcher skipped the edge cluster
        client = client_for(runner)
        late = ok(client, **day("2026-10-06"))
        # every requested day is in G: the v1 status, no claim
        assert_no_claim(late, "STALE_PROJECTION")
        assert gap_map(late) == {"2026-10-06": ("PENDING", "NOT_CURRENT"),
                                 "2026-10-07": ("STALE_PROJECTION", "NOT_CURRENT")}
        two = ok(client, **day("2026-10-05", 2))
        assert two["status"] == "PARTIAL" and two["rows"] == [] and two["total_count"] == 0
        assert gap_map(two) == {"2026-10-06": ("PENDING", "NOT_CURRENT"),
                                "2026-10-07": ("STALE_PROJECTION", "NOT_CURRENT")}

    def test_p3b_matched_cross_midnight_finding_withheld_when_next_day_stale(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [
            block("2026-10-05T08:00:00Z", "2026-10-05T09:00:00Z", **CANDIDATE),
            block("2026-10-06T23:30:00Z", "2026-10-07T00:30:00Z", **CANDIDATE),
            block("2026-10-07T10:00:00Z", "2026-10-07T10:30:00Z", **NO_CANDIDATE)]})
        runner.step({"do": "assess"})
        runner.match()
        heads = {(r["episode_start"], r["episode_end"]) for r in runner.reload()["revisions"]}
        assert (_t("2026-10-06T23:30:00Z"), _t("2026-10-07T00:30:00Z")) in heads, heads  # a real matched Finding
        client = client_for(runner)
        full = ok(client, **day("2026-10-05", 3))
        assert full["status"] == "CURRENT" and full["total_count"] == 2
        # late evidence on 10-07: the cross-midnight Finding touches a gap and is withheld; 10-05's stays
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-07T12:00:00Z", "2026-10-07T12:30:00Z", **NO_CANDIDATE)]})
        body = ok(client, **day("2026-10-05", 2))
        assert body["status"] == "PARTIAL" and body["withheld"] is True, body["status_reasons"]
        assert [r["episode"]["start"] for r in body["rows"]] == ["2026-10-05T08:00:00Z"]
        assert body["total_count"] == 1
        gaps = gap_map(body)
        assert gaps["2026-10-07"] == ("STALE_PROJECTION", "NOT_CURRENT")
        assert gaps == {"2026-10-06": ("CURRENT", "EDGE_NEXT_TO_GAP"),
                        "2026-10-07": ("STALE_PROJECTION", "NOT_CURRENT")}


class _FenceMovesAfterSnapshot:
    """The real Postgres store, except the writer fence read after the snapshot differs (a write during the read)."""

    def __init__(self, inner) -> None:
        self.inner = inner

    def index_snapshot(self, *a):
        return self.inner.index_snapshot(*a)

    def fence(self, *a):
        return ("moved", self.inner.fence(*a))

    def index_lineage(self, *a):
        return self.inner.index_lineage(*a)

    def __getattr__(self, name):
        return getattr(self.inner, name)


class TestMovingAndBoard:
    def test_p4_a_change_during_the_read_gives_no_rows_even_with_a_gap(self, store, engine) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        f01(runner)
        dispatch = DispatchReadService(PostgresAssessmentStore(URL))
        real = FindingIndexService(PostgresFindingStore(URL), dispatch)
        moving = FindingIndexService(_FenceMovesAfterSnapshot(PostgresFindingStore(URL)), dispatch)
        w = day("2026-10-06", 2)
        req = parse_request(DOMAIN, w["frm"], w["to"], None, None)
        assert real.read(runner.tenant, runner.site, "KOBO-001", req, access_basis="test")["status"] == "PARTIAL"
        body = moving.read(runner.tenant, runner.site, "KOBO-001", req, access_basis="test")
        assert body["status"] not in ("CURRENT", "PARTIAL") and not body["is_current"]
        assert body["rows"] == [] and body["total_count"] is None and body["next_cursor"] is None
        assert any("SELECTION_MOVED_DURING_READ" in r for r in body["status_reasons"])

    def test_p5_board_settles_on_partial_off_its_own_day_and_names_the_gaps(self, store, engine) -> None:  # noqa: F811
        from fastapi.encoders import jsonable_encoder

        from assetops_backend.site_outcomes import mini

        runner = CaseRunner(store, engine)
        f01(runner)
        index = FindingIndexService(PostgresFindingStore(URL), DispatchReadService(PostgresAssessmentStore(URL)))

        def finding_index(lo, hi, cursor):  # as site_outcomes/read.py binds the port
            req = parse_request(DOMAIN, lo.isoformat().replace("+00:00", "Z"),
                                hi.isoformat().replace("+00:00", "Z"), None, cursor)
            return jsonable_encoder(index.read(runner.tenant, runner.site, "KOBO-001", req, access_basis="test"))

        def refuse(*a):
            raise RuntimeError("not bound in this test")

        ports = mini.MiniPorts(overview=refuse, depth=refuse, dispatch=refuse, assumption=refuse,
                               finding_index=finding_index, estate=refuse, action_index=refuse,
                               verification=refuse, action=refuse, work=refuse, plans=refuse, readiness=refuse)
        board = mini.compose(ports, site_code="KOBO-001", day=date(2026, 10, 6), site_timezone=None)
        assert "finding_index" not in board.failed, board.failed  # PARTIAL, board day 10-06 not a gap: settled
        gaps = board.facts.finding_gaps
        assert gaps["text"] == "30 of the last 31 days have no checked readings yet"
        assert len(gaps["days"]) == 30 and "2026-10-06" not in gaps["days"] and gaps["days"][0] == "2026-09-06"
        # the board day itself a gap (10-07, no evidence): the Finding source is not settled
        later = mini.compose(ports, site_code="KOBO-001", day=date(2026, 10, 7), site_timezone=None)
        assert "finding_index" in later.failed
        assert later.facts.finding_gaps["text"] == "30 of the last 31 days have no checked readings yet"


class TestResidualRiskProbe:
    """Recorded, not fixed (U4 residual-risk probe): an unmatched cross-midnight Candidate block whose START day is
    a gap. The matcher skips a cluster next to a non-CURRENT day; the question is what the END day reads alone."""

    def test_probe_unmatched_cross_midnight_block_gap_start_day(self, store, engine, capsys) -> None:  # noqa: F811
        runner = CaseRunner(store, engine)
        runner.step({"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [
            block("2026-10-06T23:30:00Z", "2026-10-07T00:30:00Z", **CANDIDATE),
            block("2026-10-07T10:00:00Z", "2026-10-07T10:30:00Z", **NO_CANDIDATE)]})
        runner.step({"do": "assess"})
        # late evidence leaves the START day 10-06 stale; the matcher then skips the cluster
        runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z",
                     "blocks": [block("2026-10-06T10:00:00Z", "2026-10-06T10:30:00Z", **NO_CANDIDATE)]})
        runner.match()
        revisions = runner.reload()["revisions"]
        client = client_for(runner)
        end_day = ok(client, **day("2026-10-07"))
        two = ok(client, **day("2026-10-07", 2))
        record = {"revisions": len(revisions), "end_day": (end_day["status"], end_day["total_count"],
                                                           end_day["discovery"]["days"], end_day["gaps"]),
                  "end_plus_one": (two["status"], two["total_count"], two["gaps"])}
        with capsys.disabled():
            print(f"\nIDX-GAPS probe record: {record}")
        # RESIDUAL RISK, recorded and pinned as observed (not a desired behaviour; IDX-GAPS packet): the matcher wrote
        # no Finding, and the END day alone reads CURRENT with a zero count. Its own dispatch read lists no Candidate
        # segment in its first minutes, so no edge pulls the gap START day into discovery. v1 reads it the same way.
        assert revisions == []
        assert (end_day["status"], end_day["total_count"], end_day["discovery"]["days"], end_day["gaps"]) == (
            "CURRENT", 0, ["2026-10-07"], [])
        assert two["status"] == "PARTIAL" and two["total_count"] == 0
        assert two["gaps"] == [{"day": "2026-10-08", "state": "UNASSESSED", "reason": "NOT_CURRENT"}]
