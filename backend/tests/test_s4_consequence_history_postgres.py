"""S4-08 Site consequence history over real persisted rows (PowerSite: two Findings, recompute worker, prices).

The snapshot query, cutoff membership at microsecond boundaries, the real application/database clock skew of
FindingRevision `created_at` against consequence `recorded_at`, exact price lineage, the shared cutoff string with
the price read, equal-timestamp paging and a deterministically interleaved late commit (uncommitted during page
one, committed before page two: typed 409). Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    yield
    import gc

    gc.collect()


if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_recompute_postgres import Rig
    from test_s4_consequence_store_postgres import POWER_DAY, STATE_DAY, PowerSite
    from money_gate_stub import AUTHORED

    from assetops_backend.consequence_history_api import build_consequence_history_router
    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.financial_read_api import build_financial_read_router
    from assetops_backend.financials import consequence_history as ch
    from assetops_backend.financials.assumption_read import AssumptionReadService
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE


@pytest.fixture()
def rig(store, engine, capsys):  # noqa: F811
    s = PowerSite(store, engine, capsys)
    yield Rig(s)
    s.prices.dispose()
    s.store.dispose()


def history(rig, cutoff=None, after=None, limit=25, provenance=None, site=None):
    svc = ch.ConsequenceHistoryService(rig.site.store, provenance=provenance or AUTHORED)
    req = ch.parse_request(cutoff, after, str(limit))
    return svc.read(rig.site.tenant, site or rig.site.site, "KOBO-001", req, source_open=True, source_reason=None,
                    access_basis="dev")


def built(rig):
    """Power day: UNPRICED (no price yet) then PRICED after v1; state day: QUANTITY_UNAVAILABLE."""
    rig.run()
    rig.site.publish("v1")
    rig.run()
    rows = rig.site.store.rows(rig.site.tenant, rig.site.site)["financial_consequence_revision"]
    power = sorted((r for r in rows if r["finding_revision_id"] == rig.site.on(POWER_DAY)["id"]),
                   key=lambda r: r["revision_no"])
    (state,) = [r for r in rows if r["finding_revision_id"] == rig.site.on(STATE_DAY)["id"]]
    return power, state


def clone(engine, finding_revision_id, recorded_at, conn=None):  # noqa: F811
    """Append the next revision of a FindingRevision's consequence chain as a copy of its head (new ID, basis and
    `recorded_at`, same assessment links), as the append path would, without the price link a PRICED copy needs:
    callers clone the state-day QUANTITY_UNAVAILABLE chain."""
    with engine.connect() as c:
        names = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = "
            "'financial_consequence_revision' ORDER BY ordinal_position"))]
    cols = {"id": "CAST(:nid AS uuid)", "revision_no": "revision_no + 1", "prior_consequence_revision_id": "id",
            "consequence_basis_sha256": "md5(CAST(:nid AS text)) || md5(CAST(:nid AS text))",
            "recorded_at": "CAST(:ra AS timestamptz)"}
    head = ("(SELECT id FROM financial_consequence_revision WHERE finding_revision_id = :fr "
            "ORDER BY revision_no DESC LIMIT 1)")
    nid = str(uuid4())
    params = {"nid": nid, "ra": recorded_at, "fr": finding_revision_id}

    def work(c):
        prior = c.execute(text(f"SELECT {head}"), params).scalar_one()
        c.execute(text(f"INSERT INTO financial_consequence_revision ({', '.join(names)}) SELECT "
                       f"{', '.join(cols.get(n, n) for n in names)} FROM financial_consequence_revision "
                       "WHERE id = :prior"), {**params, "prior": prior})
        c.execute(text("INSERT INTO financial_consequence_assessment_revision (consequence_revision_id, tenant_id, "
                       "site_id, assessment_revision_id, analytic_run_id, is_primary) SELECT CAST(:nid AS uuid), "
                       "tenant_id, site_id, assessment_revision_id, analytic_run_id, is_primary FROM "
                       "financial_consequence_assessment_revision WHERE consequence_revision_id = :prior"),
                  {**params, "prior": prior})
    if conn is not None:
        work(conn)
    else:
        with engine.begin() as c:
            work(c)
    return nid


def ids(body):
    return [r["consequence_revision_id"] for r in body["rows"]]


class TestRealRows:
    def test_versions_lineage_currentness_and_recorded_amounts(self, rig) -> None:
        (unpriced, priced), state = built(rig)
        body = history(rig)
        assert body["cutoff"]["selected_by"] == "SERVER_DEFAULT" and body["current_amount_shown"] is False
        rows = {r["consequence_revision_id"]: r for r in body["rows"]}
        assert set(rows) == {str(unpriced["id"]), str(priced["id"]), str(state["id"])}
        p, u, q = rows[str(priced["id"])], rows[str(unpriced["id"])], rows[str(state["id"])]
        assert (p["at_cutoff"], u["at_cutoff"], q["at_cutoff"]) == (
            "CURRENT_AT_CUTOFF", "HISTORICAL_AT_CUTOFF", "CURRENT_AT_CUTOFF")
        assert p["price"]["state"] == "LINKED" and p["price"]["price_revision_id"] == str(priced["price_revision_id"])
        assert [a["used"] for a in p["price"]["assignments"]] == [True]
        assert p["change_from_prior"] == "PRICE_ONLY" and p["recorded_amount"]["disposition"] == "SHOWN"
        assert p["recorded_amount"]["is_current_amount"] is False and p["recorded_amount"]["label"] == ch.RECORDED_LABEL
        assert (u["price"]["state"], u["recorded_amount"]["amount"]) == ("NO_PRICE_LINK", None)
        assert (q["price"]["state"], q["recorded_amount"]["disposition"]) == ("NOT_EVALUATED", "QUANTITY_UNAVAILABLE")
        assert p["links"]["finding_financials"].endswith(f"&consequence_revision_id={priced['id']}")

    def test_cutoff_boundaries_and_the_real_clock_skew(self, rig) -> None:
        (unpriced, priced), _ = built(rig)
        eps = timedelta(microseconds=1)
        at_u = ch.instant(unpriced["recorded_at"])
        # The FindingRevision's application-clock created_at is later than its consequence's database clock.
        with rig.site.runner.engine.connect() as c:
            created = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"),
                                {"r": unpriced["finding_revision_id"]}).scalar_one()
        assert created > unpriced["recorded_at"]
        at = history(rig, at_u)
        assert {r["consequence_revision_id"]: r["at_cutoff"] for r in at["rows"]}[str(unpriced["id"])] == \
            "CURRENT_AT_CUTOFF"
        assert at["cutoff"]["recorded_at"] == at_u
        assert str(unpriced["id"]) not in ids(history(rig, ch.instant(unpriced["recorded_at"] - eps)))
        before_priced = history(rig, ch.instant(priced["recorded_at"] - eps))
        assert str(priced["id"]) not in ids(before_priced)
        after = history(rig, ch.instant(priced["recorded_at"] + eps))
        assert ids(after)[0] == str(priced["id"])

    def test_price_read_reports_the_identical_cutoff_string(self, rig) -> None:
        (_, priced), _ = built(rig)
        app = FastAPI()
        scope = (lambda code: (code, rig.site.tenant, rig.site.site))
        app.include_router(build_consequence_history_router(
            ch.ConsequenceHistoryService(rig.site.store, provenance=AUTHORED), scope, CONSEQUENCE_UNAVAILABLE,
            gate=lambda c, t, s: (True, "")))
        app.include_router(build_financial_read_router(AssumptionReadService(rig.site.prices), scope))
        client = TestClient(app)
        h = client.get("/api/sites/KOBO-001/financial-assumptions/consequences").json()
        cut = h["cutoff"]["recorded_at"]
        assert "." in cut  # database clock microseconds survive (review L-R1)
        prices = client.get(h["links"]["api_prices_at_cutoff"]).json()
        assert prices["cutoff"] == {**prices["cutoff"], "recorded_at": cut, "selected_by": "RECORDED_CUTOFF"}
        assert str(priced["price_revision_id"]) in {t["revision_id"] for t in prices["timeline"]}
        again = client.get("/api/sites/KOBO-001/financial-assumptions/consequences", params={"recorded_at": cut})
        assert again.json()["cutoff"]["recorded_at"] == cut and again.json()["fence"] == h["fence"]
        assert client.get("/api/sites/KOBO-001/financial-assumptions/consequences").json()["cutoff"][
            "recorded_at"] != cut  # a default reload fixes a new instant

    def test_real_resolver_without_published_evidence_withholds_every_amount(self, rig) -> None:
        built(rig)
        body = history(rig, provenance=build_source_provenance(URL))
        assert {r["recorded_amount"]["disposition"] for r in body["rows"] if r["state"] == "PRICED"} == {
            "MIXED_OR_UNKNOWN_SOURCE"}
        assert {r["source_provenance"]["state"] for r in body["rows"]} == {"UNKNOWN"}

    def test_foreign_site_reads_nothing_and_a_foreign_cursor_is_refused(self, rig) -> None:
        built(rig)
        cut = history(rig)["cutoff"]["recorded_at"]
        cursor = history(rig, cut, limit=1)["next_cursor"]
        other = uuid4()
        assert history(rig, cut, site=other)["rows"] == []
        with pytest.raises(ch.HistoryBasisChanged) as refused:
            history(rig, cut, cursor, limit=1, site=other)
        assert refused.value.detail["reason"] == "SCOPE_CHANGED"


class TestPagingOverTheSnapshot:
    def test_equal_timestamps_across_pages(self, rig, engine) -> None:  # noqa: F811
        (unpriced, _), state = built(rig)
        same = unpriced["recorded_at"] + timedelta(microseconds=7)
        made = {clone(engine, state["finding_revision_id"], same) for i in range(3)}
        cut = history(rig)["cutoff"]["recorded_at"]
        seen, after = [], None
        while True:
            page = history(rig, cut, after, limit=2)
            seen += ids(page)
            after = page["next_cursor"]
            if after is None:
                break
        assert len(seen) == len(set(seen)) == 6 and made <= set(seen)

    def test_interleaved_late_commit_refuses_page_two_and_page_one_reloads(self, rig, engine) -> None:  # noqa: F811
        (unpriced, _), state = built(rig)
        conn = engine.connect()
        tx = conn.begin()
        late = clone(engine, state["finding_revision_id"], unpriced["recorded_at"] + timedelta(microseconds=3), conn)
        try:
            first = history(rig, limit=1)  # the late row is uncommitted: outside this snapshot
            cut = first["cutoff"]["recorded_at"]
            assert late not in ids(first) and first["next_cursor"]
            tx.commit()
        finally:
            conn.close()
        with pytest.raises(ch.HistoryBasisChanged) as refused:
            history(rig, cut, first["next_cursor"], limit=1)
        assert refused.value.status == 409 and refused.value.detail["code"] == "CONSEQUENCE_HISTORY_BASIS_CHANGED"
        assert refused.value.detail["rows"] is None
        reloaded = history(rig, cut, limit=1)
        assert reloaded["fence"] != first["fence"]
        # A row stamped after the cutoff stays excluded and leaves the fence alone.
        from datetime import datetime
        clone(engine, state["finding_revision_id"], datetime.fromisoformat(cut) + timedelta(hours=1))
        seen, after = ids(reloaded), reloaded["next_cursor"]
        while after:
            page = history(rig, cut, after, limit=1)
            seen += ids(page)
            after = page["next_cursor"]
        assert late in seen and len(seen) == 4
