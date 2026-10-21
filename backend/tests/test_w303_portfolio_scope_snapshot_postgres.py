"""W3-03 run 1a: the Portfolio scope/coverage/selection read over the persisted 0b four-Site fixture.

The one-day three-domain fixture (`build_portfolio_fixture`) is read through the unmounted Portfolio router and the
public Findings/Evidence/Financials roots at the one frozen clock: one snapshot and cutoff, F/E/M COMPLETE, the
lifecycle-filtered Finding IDs of the public root, the r0a L4 `site_coverage` call count, then the foreign-tenant,
added-empty-Site and changed-grant perturbations. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlencode
from uuid import uuid4

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_w301_estate_index_postgres import add_empty_site, iso
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import CODES, build_portfolio_fixture

    from assetops_backend.estate import coverage, evidence_money, financials, index
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router

MEMBERS = ("SUPPORTED", "UNCONFIRMED")


class Portfolio:
    """The unmounted Portfolio router over the W3-02 one-transaction reader, counting its snapshots."""

    def __init__(self, engine, tenant_id, admit=lambda code: True) -> None:
        self.read = evidence_read(engine)
        self.admit = admit
        self.snapshots = 0
        real = self.read.read

        def counted(work):
            self.snapshots += 1
            return real(work)

        self.read.read = counted
        app = FastAPI()
        app.include_router(build_estate_portfolio_router(
            EstatePortfolioService(self.read), lambda: tenant_id,
            access=lambda request, code: None if self.admit(code) else 403))
        self.client = TestClient(app)

    def get(self, **params):
        return self.client.get("/api/estate/portfolio?" + urlencode(params))

    def ok(self, **params) -> dict:
        response = self.get(**params)
        assert response.status_code == 200, response.text
        return response.json()


@pytest.fixture()
def portfolio_fixture(request, monkeypatch, capsys):
    return build_portfolio_fixture(request, monkeypatch, capsys)


def _count_site_coverage(monkeypatch) -> Counter:
    calls: Counter = Counter()
    real = coverage.site_coverage

    def counted(snapshot, tenant_id, site_id, domain, *args):
        calls[domain] += 1
        return real(snapshot, tenant_id, site_id, domain, *args)

    for module in (index, evidence_money, financials):
        monkeypatch.setattr(module, "site_coverage", counted)
    return calls


def _pairs(rows) -> list[tuple[str, str]]:
    return [(r["finding_id"], r["finding_revision_id"]) for r in rows]


def test_three_domains_same_window_cutoff_and_full_selection_ids(portfolio_fixture, monkeypatch) -> None:
    fx = portfolio_fixture
    calls = _count_site_coverage(monkeypatch)
    view = Portfolio(fx.engine, fx.tenant_id)
    body = view.ok(**fx.window, limit=100)
    # r0a L4: the three selectors call `site_coverage` at most once per Site/domain each, in one snapshot.
    measured = dict(calls)
    assert view.snapshots == 1
    assert sum(n for d, n in measured.items() if d != coverage.ACTIONS) <= 12, measured
    assert measured == {"mini_grid": 3, "cold_chain": 3, "ev_charging": 6, "actions": 1}, measured
    print(f"W3-03 1a L4 site_coverage calls: {measured}")

    estate, money_api = fx.estate(), fx.money()
    findings = estate.ok("findings", **fx.window, limit=100)
    evidence = money_api.ok("evidence", **fx.window, limit=100)
    financial = money_api.ok("financials", **fx.window, limit=100)
    code_of = {v: k for k, v in fx.site_ids.items()}

    # One window and one cutoff across the Portfolio and the public roots (B3); CURRENT and F/E/M COMPLETE.
    assert body["window"] == findings["window"] == evidence["window"] == financial["window"]
    assert body["window"]["known_at"] == iso(fx.frozen) and "known_at" not in fx.window
    assert body["schema_version"] == "estate-portfolio-1" and body["status"] == "CURRENT"
    assert body["coverage"]["state"] == "COMPLETE"
    assert (body["coverage"]["finding_state"], body["coverage"]["evidence_state"],
            body["coverage"]["money_state"]) == ("COMPLETE", "COMPLETE", "COMPLETE")
    assert body["scope"] == {**findings["scope"], "covered_site_count": 4}
    assert body["scope"]["authorized_site_count"] == 4
    # `coverage.sites` is exactly the Finding root's seven-key items, in its order.
    assert body["coverage"]["sites"] == findings["coverage"]["sites"]
    assert sorted(code_of[s["site_id"]] for s in body["coverage"]["sites"]) == sorted(CODES)

    # Exact selected IDs: the public Finding set after the lifecycle membership filter, in the Portfolio order.
    expected = [r for r in findings["rows"] if r["lifecycle"] in MEMBERS]
    assert sorted(_pairs(body["rows"])) == sorted(_pairs(expected)) and body["rows"]
    assert body["total_count"] == body["summary"]["finding_count"] == len(expected)
    starts = [r["episode_start"] for r in body["rows"]]
    assert starts == sorted(starts, reverse=True)
    public = {r["finding_revision_id"]: r for r in findings["rows"]}
    domains = {"KOBO-001": "MINIGRID", "COLD-LAB-001": "COLDCHAIN", "EV-LAB-001": "EV_CHARGING",
               "EV-LAB-002": "EV_CHARGING"}
    for row in body["rows"]:
        source = public[row["finding_revision_id"]]
        for key in ("site_id", "site_code", "site_name", "finding_label", "title", "lifecycle", "lens_flags",
                    "consequence", "source_provenance", "episode_start"):
            assert row[key] == source[key], key
        assert row["domain"] == domains[row["site_code"]] and row["mechanism"] is None
        # B4: the aligned 10-06 window selects no Action, so no row joins one.
        assert (row["action_id"], row["application_state"], row["resolution_state"],
                row["verification_outcome"], row["links"]["action"]) == (None,) * 5
        assert row["links"]["site"] == f"/sites/{row['site_code']}"
        assert (row["links"]["finding"] is not None) == (row["domain"] == "MINIGRID")
    assert {r["site_code"] for r in body["rows"]} >= {"KOBO-001", "COLD-LAB-001"}
    kobo = next(r for r in body["rows"] if r["site_code"] == "KOBO-001")
    assert kobo["links"]["finding"] == public[kobo["finding_revision_id"]]["links"]["finding"]
    assert kobo["consequence"]["state"] == "PRICED" and kobo["episode_end"] is not None

    # The full-scope token is stable at the one clock and fenced by the lens.
    again = view.ok(**fx.window, limit=100)
    assert again["selection_token"] == body["selection_token"] and again["rows"] == body["rows"]
    assert view.ok(**fx.window, lens="cost")["selection_token"] != body["selection_token"]
    assert body["selection_token"] not in (findings["selection_token"], evidence["selection_token"],
                                           financial["selection_token"])


def _add_foreign_site(engine, site_id, code: str) -> str:
    """TEST-SCOPED: a Site of a new tenant, copied from a fixture Site's stored rows with new identities."""
    tenant, new = str(uuid4()), str(uuid4())
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, default_currency, created_at) "
                       "SELECT CAST(:t AS uuid), 'w303-foreign', 'Foreign tenant', default_currency, created_at "
                       "FROM tenant WHERE id = (SELECT tenant_id FROM site WHERE id = :s)"), {"t": tenant, "s": site_id})
        for table, pick in (("site", {"id": "CAST(:new AS uuid)", "tenant_id": "CAST(:t AS uuid)",
                                      "site_code": ":code", "site_code_key": "lower(:code)"}),
                            ("site_import", {"id": "CAST(:imp AS uuid)", "site_id": "CAST(:new AS uuid)",
                                             "tenant_id": "CAST(:t AS uuid)"})):
            cols = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = :n ORDER BY ordinal_position"),
                {"n": table})]
            key = "id" if table == "site" else "site_id"
            c.execute(text(f"INSERT INTO {table} ({', '.join(cols)}) SELECT {', '.join(pick.get(x, x) for x in cols)} "
                           f"FROM {table} WHERE {key} = :s LIMIT 1"),
                      {"new": new, "t": tenant, "code": code, "imp": str(uuid4()), "s": site_id})
    return new


def test_foreign_tenant_missing_site_and_grant_fence(portfolio_fixture) -> None:
    fx = portfolio_fixture
    view = Portfolio(fx.engine, fx.tenant_id)
    one = view.ok(**fx.window, limit=1)
    assert one["status"] == "CURRENT" and one["total_count"] >= 2 and one["next_cursor"]
    cursor = one["next_cursor"]
    assert view.ok(**fx.window, cursor=cursor)["selection_token"] == one["selection_token"]

    # A foreign tenant reads an empty scope; no fixture Site, Finding or digest enters it.
    foreign = Portfolio(fx.engine, uuid4()).ok(**fx.window)
    assert foreign["status"] == "EMPTY_SCOPE" and foreign["rows"] == [] and foreign["total_count"] == 0
    assert foreign["coverage"] == {"state": "EMPTY", "finding_state": "EMPTY", "evidence_state": "EMPTY",
                                   "money_state": "EMPTY", "sites": []}
    assert not any(site_id in str(foreign) for site_id in fx.site_ids.values())
    # A foreign tenant's Site never enters this tenant's access basis, token or rows: page two still resumes.
    other = _add_foreign_site(fx.engine, fx.site_ids["KOBO-001"], "W303-FOREIGN-001")
    same = view.ok(**fx.window, limit=1)
    assert (same["scope"], same["selection_token"]) == (one["scope"], one["selection_token"])
    assert other not in str(same) and view.get(**fx.window, cursor=cursor).status_code == 200

    # An authorized empty Site (no selection) changes the access basis: the old cursor is 409, page one is partial.
    empty = add_empty_site(fx.engine, fx.site_ids["KOBO-001"], "W303-EMPTY-001")
    stale = view.get(**fx.window, cursor=cursor)
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "ESTATE_BASIS_CHANGED"
    assert stale.json()["detail"]["value_cards"] is None and "coverage" not in stale.json()["detail"]
    partial = view.ok(**fx.window, limit=100)
    states = {s["site_id"]: s["state"] for s in partial["coverage"]["sites"]}
    assert len(states) == 5 and states[empty] == "UNKNOWN"
    assert partial["scope"]["authorized_site_count"] == 5 and partial["scope"]["covered_site_count"] == 4
    assert partial["status"] == "UNKNOWN" and partial["coverage"]["state"] == "PARTIAL"
    assert (partial["coverage"]["finding_state"], partial["coverage"]["evidence_state"],
            partial["coverage"]["money_state"]) == ("PARTIAL", "PARTIAL", "PARTIAL")
    assert sorted(_pairs(partial["rows"])) == sorted(_pairs(view.ok(**fx.window, limit=100)["rows"]))
    assert empty not in {r["site_id"] for r in partial["rows"]} and other not in str(partial)

    # A changed grant (EV-LAB-002 denied) fences the cursor before its marker lookup.
    page = view.ok(**fx.window, limit=1)
    view.admit = lambda code: code != "EV-LAB-002"
    fenced = view.get(**fx.window, cursor=page["next_cursor"])
    assert fenced.status_code == 409 and fenced.json()["detail"]["code"] == "ESTATE_BASIS_CHANGED"
    narrowed = view.ok(**fx.window, limit=100)
    assert narrowed["scope"]["authorized_site_count"] == 4
    assert fx.site_ids["EV-LAB-002"] not in str(narrowed)
