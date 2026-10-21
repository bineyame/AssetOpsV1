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


@pytest.fixture(autouse=True)
def _cursor_key(monkeypatch):
    """r1b Q-1b-1: every Portfolio request needs the deployment key; a test-only value, never a default."""
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "3e" * 32)


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
        assert row["episode_end"] == source.get("episode_end", row["episode_end"])
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

    clean_rows = view.ok(**fx.window, limit=100)["rows"]
    clean_total = view.ok(**fx.window, limit=100)["summary"]["finding_count"]
    assert clean_total == len(clean_rows)
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
    assert sorted(_pairs(partial["rows"])) == sorted(_pairs(clean_rows))
    # r1a M1: partial Finding coverage withholds the estate count; null never renders as 0.
    assert partial["summary"]["finding_count"] is None and partial["total_count"] == len(clean_rows)
    assert empty not in {r["site_id"] for r in partial["rows"]} and other not in str(partial)

    # A changed grant (EV-LAB-002 denied) fences the cursor before its marker lookup.
    page = view.ok(**fx.window, limit=1)
    view.admit = lambda code: code != "EV-LAB-002"
    fenced = view.get(**fx.window, cursor=page["next_cursor"])
    assert fenced.status_code == 409 and fenced.json()["detail"]["code"] == "ESTATE_BASIS_CHANGED"
    narrowed = view.ok(**fx.window, limit=100)
    assert narrowed["scope"]["authorized_site_count"] == 4
    assert fx.site_ids["EV-LAB-002"] not in str(narrowed)


FULL_SCOPE = ("summary", "value_cards", "objectives", "evidence_prompt", "opportunity", "progress", "footer",
              "selected_lines", "money", "scope_disclosure", "coverage", "status", "total_count", "selection_token")


def test_page_size_does_not_change_cards_matrix_or_money(portfolio_fixture) -> None:
    """Run 1b (closure 2 N6 / r1b cards): limits 1 and 100 give equal full-scope projections; the clean fixture's
    five cards, matrix, prompt, progress, footer and money are the W3-02/W3-01 full-scope selections."""
    fx = portfolio_fixture
    view = Portfolio(fx.engine, fx.tenant_id)
    one, full = view.ok(**fx.window, limit=1), view.ok(**fx.window, limit=100)
    assert {k: one[k] for k in FULL_SCOPE} == {k: full[k] for k in FULL_SCOPE} and len(one["rows"]) == 1
    financial = fx.money().ok("financials", **fx.window, limit=100)
    evidence = fx.money().ok("evidence", **fx.window, limit=100)
    # Exact unpaged W3-02 line DTOs, groups, exclusions and diagnostics; no estate total (closure-1 declines).
    assert full["selected_lines"] == financial["rows"] and financial["next_cursor"] is None
    assert full["money"] == {"groups": financial["groups"], "exclusions": financial["exclusions"],
                             "diagnostics": financial["diagnostics"], "estate_total": None}
    assert full["scope_disclosure"]["exclusions"] == financial["exclusions"]
    assert full["summary"]["combined_value"] is None and full["summary"]["combined_value_state"] == "NOT_COMPARABLE"
    by_cat = {}
    for line in financial["rows"]:
        by_cat.setdefault(line["category"], []).append(line)
    w1 = by_cat["CANDIDATE_OPERATING_COST_EXPOSURE"]
    assert [x["eligibility"] for x in w1] == ["ELIGIBLE"]
    # Clean card states SITE_OWNED / UNKNOWN / UNSUPPORTED / UNSUPPORTED / NOT_ESTABLISHED, cost from W1 only.
    cards = full["value_cards"]
    assert [x["state"] for x in cards] == ["SITE_OWNED", "UNKNOWN", "UNSUPPORTED", "UNSUPPORTED", "NOT_ESTABLISHED"]
    assert cards[0]["line_keys"] == [w1[0]["line_key"]] and cards[0]["group_key"] == w1[0]["group_key"]
    assert cards[0]["currency"] == w1[0]["amount"]["currency"] and cards[0]["display_value"] is None
    ev = sorted(by_cat["GROSS_TARIFF_SCENARIO"], key=lambda x: x["line_key"])
    ev_group = next(g for g in financial["groups"] if g["category"] == "GROSS_TARIFF_SCENARIO")
    assert ev_group["state"] == "COMPARABLE" and sorted(ev_group["line_keys"]) == [x["line_key"] for x in ev]
    assert all(line["finding_id"] is None for line in ev)  # EV window money never attaches to a Finding
    # Matrix: one item per authorized Site, five fixed cells; cold/EV cost control N/A, W1 REVIEW.
    code_of = {v: k for k, v in fx.site_ids.items()}
    cells = {code_of[o["site_id"]]: {x["key"]: x["state"] for x in o["cells"]} for o in full["objectives"]}
    assert sorted(cells) == sorted(CODES)
    assert all([x["key"] for x in o["cells"]] == ["SERVICE_PRODUCT", "BACKUP", "ASSET_CONDITION", "COST_CONTROL",
                                                  "EVIDENCE"] for o in full["objectives"])
    assert cells["KOBO-001"]["COST_CONTROL"] == "REVIEW"
    assert {cells[c]["COST_CONTROL"] for c in CODES if c != "KOBO-001"} == {"NOT_APPLICABLE"}
    assert all(cells[c][k] == "UNKNOWN" for c in CODES for k in ("SERVICE_PRODUCT", "BACKUP", "ASSET_CONDITION"))
    readiness = {}
    for row in evidence["rows"]:
        readiness.setdefault(code_of[row["site_id"]], []).append(row["readiness"])
    for code, states in readiness.items():
        expected = "FULL" if all(s == "FULL" for s in states) else ("NONE" if "NONE" in states else "LIMITED")
        assert cells[code]["EVIDENCE"] == expected, (code, states)
    # Prompt: the first typed W3-02 gap with a nonnull step, else NO_GAP; CTA /evidence.
    stepped = [g for g in evidence["gaps"] if g["next_step"] is not None]
    prompt = full["evidence_prompt"]
    assert prompt["destination"] == "/evidence"
    if stepped:
        assert (prompt["state"], prompt["gap_code"], prompt["site_id"]) == (
            "AVAILABLE", stepped[0]["gap_code"], stepped[0]["site_ids"][0])
    else:
        assert prompt["state"] == "NO_GAP" and prompt["site_id"] is None
    assert full["summary"]["evidence_gap_site_count"] == len({s for g in evidence["gaps"] for s in g["site_ids"]})
    # B4: no selected Action in the 10-06 window; complete applicable Action coverage gives zero counts.
    assert full["progress"]["rows"] == [] and full["progress"]["pending_trial_count"] == 0
    assert full["summary"]["accepted_action_count"] == 0 and full["progress"]["recovered_value"] is None
    assert full["opportunity"] == {"state": "UNSUPPORTED", "finding_id": None, "scenario_amount": None,
                                   "headroom": None, "destination": None}
    # Footer: the first eligible EV gross-tariff line by (site_code_key, site_id, line_key).
    first = min(ev, key=lambda x: (x["site_code"].lower(), x["site_id"], x["line_key"]))
    assert full["footer"]["line_key"] == first["line_key"] and full["footer"]["destination"] == first["links"][
        "evidence"]
    # Scope disclosure: one item per authorized Site with the union of its selected IDs.
    sites = {code_of[s["site_id"]]: s for s in full["scope_disclosure"]["sites"]}
    assert sorted(sites) == sorted(CODES)
    assert w1[0]["consequence_revision_id"] in sites["KOBO-001"]["selected_revision_ids"]
    assert all(s["window"] == {"from": fx.window["from"], "to": fx.window["to"]} for s in sites.values())
