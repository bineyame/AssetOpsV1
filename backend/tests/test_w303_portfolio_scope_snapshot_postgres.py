"""W3-03 run 1a: the Portfolio scope/coverage/selection read over the persisted 0b four-Site fixture.

The one-day three-domain fixture (`build_portfolio_fixture`) is read through the unmounted Portfolio router and the
public Findings/Evidence/Financials roots at the one frozen clock: one snapshot and cutoff, F/E/M COMPLETE, the
lifecycle-filtered Finding IDs of the public root, the r0a L4 `site_coverage` call count, then the foreign-tenant,
added-empty-Site and changed-grant perturbations. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import pytest

from test_w301_estate_index_postgres import URL
from assetops_backend.estate.evidence_money import CURRENT_VIEW

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    import pg_harness
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4 mini-grid fixtures (one variant)
    from test_w301_estate_index_postgres import add_empty_site, db_now, imported_before, iso
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import (
        CODES, _stamped_tables, build_portfolio_fixture, pin_snapshots)

    from assetops_backend.estate import coverage, evidence_money, financials, index, portfolio
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.estate.money_invariants import double_count_violations

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
        body = response.json()
        # CC-R1: every persisted Portfolio body read here satisfies the no-double-count invariant.
        assert double_count_violations(body) == [], double_count_violations(body)
        return body


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
    proven_queries: dict[str, set[str]] = {}
    for item in evidence["rows"]:
        if item["links"]["site_readiness_label"] is None:
            proven_queries.setdefault(item["site_id"], set()).add(item["links"]["site_readiness"].split("?", 1)[1])
    linked: set[str] = set()
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
        # Post-W6 W3-estate Q2/Q9/Q10: the EV Site home; mini-grid keeps its exact `revision_id` Finding route; a
        # cold/EV Finding opens over a proven selected Site window (one of that Site's proven Evidence windows,
        # never episode bounds) or stays null. The Findings index emits the same link.
        home = f"/sites/{row['site_code']}" + ("/ev" if row["domain"] == "EV_CHARGING" else "")
        assert row["links"]["site"] == home == source["links"]["site"]
        link = row["links"]["finding"]
        assert link == source["links"]["finding"]
        if row["domain"] == "MINIGRID":
            assert link == (f"/sites/{row['site_code']}/findings/{row['finding_id']}?revision_id="
                            f"{row['finding_revision_id']}")
        elif link is not None:
            path, query = link.split("?", 1)
            assert path == f"/sites/{row['site_code']}/findings/{row['finding_id']}" and "revision_id" not in query
            assert query in proven_queries.get(row["site_id"], set()), (link, proven_queries)
            linked.add(row["domain"])
    assert "COLDCHAIN" in linked, linked  # non-vacuous: the selected cold Finding row emits a live windowed link
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


def test_page_size_does_not_change_cards_matrix_or_money(portfolio_fixture, monkeypatch) -> None:
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

    # Post-W6 W3-estate Q10 (supersedes r1b2 R7's null destinations): mounted Site routes per domain; cold/EV Cost
    # control and Evidence reuse the Site's selected-window links (else its home); EV Backup has no configured
    # objective. An unknown physical configuration is UNKNOWN for cost and evidence, never N/A, and has no
    # destination (no persisted producer: the real `objective` over a NOT_APPLICABLE domain).
    to = {code_of[o["site_id"]]: {x["key"]: x["destination"] for x in o["cells"]} for o in full["objectives"]}
    assert to["KOBO-001"] == {
        "SERVICE_PRODUCT": "/sites/KOBO-001/performance/service", "BACKUP": "/sites/KOBO-001/performance/backup",
        "ASSET_CONDITION": "/sites/KOBO-001/health", "COST_CONTROL": "/sites/KOBO-001/financials",
        "EVIDENCE": "/sites/KOBO-001/evidence"}
    cold_to = to["COLD-LAB-001"]
    assert (cold_to["SERVICE_PRODUCT"], cold_to["BACKUP"], cold_to["ASSET_CONDITION"]) == (
        "/sites/COLD-LAB-001/performance/temperature", "/sites/COLD-LAB-001/performance/backup",
        "/sites/COLD-LAB-001/health")
    assert cold_to["EVIDENCE"].startswith("/sites/COLD-LAB-001/evidence?from=")
    assert cold_to["COST_CONTROL"] == "/sites/COLD-LAB-001/financials?" + cold_to["EVIDENCE"].split("?", 1)[1]
    for code in ("EV-LAB-001", "EV-LAB-002"):
        ev_to = to[code]
        assert (ev_to["SERVICE_PRODUCT"], ev_to["BACKUP"], ev_to["ASSET_CONDITION"]) == (
            f"/sites/{code}/performance/sessions", None, f"/sites/{code}/health")
        if ev_to["EVIDENCE"] == f"/sites/{code}/ev":
            assert ev_to["COST_CONTROL"] == f"/sites/{code}/ev"
        else:
            assert ev_to["EVIDENCE"].startswith(f"/sites/{code}/ev/evidence?from=")
            assert ev_to["COST_CONTROL"] == f"/sites/{code}/ev/financials?" + ev_to["EVIDENCE"].split("?", 1)[1]
    assert all(len(o["cells"]) == 5 for o in full["objectives"]) and len(full["objectives"]) == 4
    odd = {"site_id": "s", "site_code": "X", "site_name": "X", "site_type": "WIND"}
    cells = {x["key"]: x["state"] for x in portfolio.objective(
        odd, (odd, coverage.NOT_APPLICABLE, {}, []), (odd, coverage.NOT_APPLICABLE, {}, []), False)["cells"]}
    assert cells["COST_CONTROL"] == cells["EVIDENCE"] == "UNKNOWN" and "NOT_APPLICABLE" not in cells.values()

    # r1b2 R11: one batched provenance read per request, constant at limits 1 and 100; each Site DTO equals the
    # existing single-Site `cited_provenance` truth for the same IDs.
    from sqlalchemy import event
    from assetops_backend.estate.adapters import postgres_estate_read as per

    statements: list[str] = []
    calls: list = []
    base = getattr(per.EstateSnapshot, "_real", per.EstateSnapshot)  # the unpinned class (the pin subclasses it)
    real_many = base.cited_provenance_many

    def many(self, t, items):
        calls.append([(str(s), list(c), list(sel)) for s, c, sel in items])
        return real_many(self, t, items)

    monkeypatch.setattr(base, "cited_provenance_many", many)
    # Review L2: the batched link rows must serve every Site; any `_Prefetched` fallback to the per-Site
    # `link_rows` read is recorded and fails the test (equal per-Site counts at both limits would hide it).
    fallback_links: list = []
    prefetched: list = []
    real_init = per._Prefetched.__init__

    class _FallbackSpy:
        def __init__(self, inner) -> None:
            self._inner = inner

        def link_rows(self, *a):
            fallback_links.append(a)
            return self._inner.link_rows(*a)

        def __getattr__(self, name):
            return getattr(self._inner, name)

    def spied_init(self, rows, site, fallback) -> None:
        prefetched.append(site)
        real_init(self, rows, site, _FallbackSpy(fallback))

    monkeypatch.setattr(per._Prefetched, "__init__", spied_init)
    listener = lambda conn, cursor, sql, *a: statements.append(sql)  # noqa: E731
    event.listen(fx.engine, "before_cursor_execute", listener)
    try:
        counts = []
        for limit in (1, 100):
            statements.clear()
            body = view.ok(**fx.window, limit=limit)
            counts.append((sum("AS q(site_id, id)" in x for x in statements),
                           sum("AS q(id)" in x for x in statements)))
        assert counts[0] == counts[1] and counts[0][0] == 1, counts
        assert prefetched and fallback_links == [], fallback_links
    finally:
        event.remove(fx.engine, "before_cursor_execute", listener)
    assert len(calls) == 2 and calls[0] == calls[1] and len(calls[0]) == 4
    truth = view.read.read(lambda snap: [snap.cited_provenance(fx.tenant_id, s, c, sel) for s, c, sel in calls[0]])
    by_site = {s["site_id"]: s["source_provenance"] for s in body["scope_disclosure"]["sites"]}
    assert [by_site[s] for s, _, _ in calls[0]] == truth and all(truth)


# --- run 1b: the successful Q9 variants (closure 2 Q9 table as amended by NQ1, r1a2 items 1/2, r1b Q-1b-3) --------

VARIANTS = ("a_lineless_cold", "b_historical", "c1_unbound", "c2_mixed", "mg_historical_marker")
OPERATING_COST = "CANDIDATE_OPERATING_COST_EXPOSURE"
CARD_TAIL = ["UNKNOWN", "UNSUPPORTED", "UNSUPPORTED", "NOT_ESTABLISHED"]


def _declined(body: dict) -> None:
    """The closure-1 decline assertions every success body carries (the visible pulse note is run 2's)."""
    assert body["summary"]["combined_value"] is None and body["summary"]["combined_value_state"] == "NOT_COMPARABLE"
    assert body["money"]["estate_total"] is None


def _fem(body: dict) -> tuple[str, str, str]:
    c = body["coverage"]
    return c["finding_state"], c["evidence_state"], c["money_state"]


def _same_money(body: dict, financial: dict) -> None:
    """The exact W3-02 full-scope money: lines, groups, exclusions and diagnostics, never an invented row."""
    assert body["selected_lines"] == financial["rows"]
    assert {k: body["money"][k] for k in ("groups", "exclusions", "diagnostics")} == {
        k: financial[k] for k in ("groups", "exclusions", "diagnostics")}


def _site_state(body: dict, site_id: str) -> dict:
    return next(s for s in body["coverage"]["sites"] if s["site_id"] == site_id)


def _w1_withheld(request, monkeypatch, capsys, source: str, reason: str) -> None:
    """(c1)/(c2): the W1 Finding's selected source is UNKNOWN or MIXED through the reviewed S4-05 publication path;
    the W1 line is WITHHELD with that reason and no current amount; the card is WITHHELD; coverage stays COMPLETE."""
    fx = build_portfolio_fixture(request, monkeypatch, capsys, w1_source=source)
    body = Portfolio(fx.engine, fx.tenant_id).ok(**fx.window, limit=100)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    _same_money(body, financial)
    (w1,) = [x for x in financial["rows"] if x["category"] == OPERATING_COST]
    assert w1["eligibility"] == "WITHHELD" and reason in w1["reason_codes"] and w1["amount"] is None
    assert body["status"] == "CURRENT" and _fem(body) == ("COMPLETE", "COMPLETE", "COMPLETE")
    assert [c["state"] for c in body["value_cards"]] == ["WITHHELD", *CARD_TAIL]
    assert body["value_cards"][0]["line_keys"] == [w1["line_key"]] and body["value_cards"][0]["currency"] is None
    kobo = {x["key"]: x["state"] for x in next(o for o in body["objectives"]
                                              if o["site_id"] == fx.site_ids["KOBO-001"])["cells"]}
    assert kobo["COST_CONTROL"] == "UNKNOWN"
    _declined(body)


@pytest.mark.parametrize("variant", VARIANTS)
def test_late_revision_pending_historical_and_mixed_source(variant, request, monkeypatch, capsys) -> None:
    if variant == "c1_unbound":
        return _w1_withheld(request, monkeypatch, capsys, "UNBOUND", "UNKNOWN_SOURCE")
    if variant == "c2_mixed":
        return _w1_withheld(request, monkeypatch, capsys, "MIXED", "MIXED_SOURCE")
    if variant == "mg_historical_marker":
        return _minigrid_historical_marker(request, monkeypatch)

    fx = build_portfolio_fixture(request, monkeypatch, capsys, cold_drain=variant != "a_lineless_cold")
    view = Portfolio(fx.engine, fx.tenant_id)
    cold = fx.site_ids["COLD-LAB-001"]
    if variant == "b_historical":
        # NQ1: the explicit cutoff 2026-09-30 precedes every fixture head; the one-day request is kept.
        k = datetime(2026, 9, 30, tzinfo=timezone.utc)
        heads = [(t, stamp) for t, stamp in _stamped_tables(fx.engine, "site_id")
                 if any(w in t for w in ("assessment", "finding", "consequence", "evidence"))]
        assert len(heads) >= 4, heads
        with fx.engine.connect() as c:
            early = {t: c.execute(text(f"SELECT count(*) FROM {t} WHERE site_id = ANY(CAST(:s AS uuid[])) "
                                       f"AND {stamp} <= :k"), {"s": list(fx.site_ids.values()), "k": k}).scalar_one()
                     for t, stamp in heads}
        assert not any(early.values()), early  # every fixture head is recorded after the cutoff
        body = view.ok(**fx.window, known_at=iso(k), limit=100)
        assert body["status"] == "HISTORICAL" and _fem(body) == ("UNKNOWN", "UNKNOWN", "UNKNOWN")
        assert {s["state"] for s in body["coverage"]["sites"]} == {"UNKNOWN"}
        assert body["rows"] == [] and body["selected_lines"] == []
        assert [c["state"] for c in body["value_cards"]] == ["WITHHELD", *CARD_TAIL]
        assert {x["state"] for o in body["objectives"] for x in o["cells"] if x["key"] == "EVIDENCE"} == {"UNKNOWN"}
        # Finding/Evidence coverage is incomplete, so their counts are withheld; Action coverage is complete as of
        # the cutoff (mini-grid selected, cold/EV not applicable), so its true zero stands.
        assert body["summary"]["finding_count"] is None and body["summary"]["evidence_gap_site_count"] is None
        assert body["summary"]["accepted_action_count"] == 0 and body["progress"]["rows"] == []
        _declined(body)
        return

    body = view.ok(**fx.window, limit=100)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    site = _site_state(body, cold)
    _same_money(body, financial)
    # Pending money wins over UNKNOWN for overall status; the cold category's M unit is U beside covered Sites.
    assert body["status"] == "PENDING" and body["coverage"]["money_state"] == "PARTIAL"
    cold_lines = [x for x in body["selected_lines"] if x["domain"] == "cold_chain"]
    assert all(x["amount"] is None for x in cold_lines)  # no current cold amount
    # r1b Q-1b-3: a line-less guard; no selected cold line and no invented exclusion row. The cold Site's own
    # coverage is still CURRENT: the guard, not the Site state, makes the status PENDING (r1a2 item 2).
    # r1b3 P-1b-1: this is the persisted cold line-less pending path only. The late-cold reduction and status rule
    # (uncovered cold unit with a selected PENDING line) is the pure `test_money_table`; `fx.cold.advance_late()`
    # after the drained excursion selects a settled cold head and is not a later-record/unsettled-job proof.
    assert site["state"] == "CURRENT" and _fem(body) == ("COMPLETE", "COMPLETE", "PARTIAL")
    assert cold_lines == []
    assert not [x for x in body["money"]["exclusions"] if x["line_key"].startswith("cold_chain:")]
    # W1 operating cost stays covered and Site-owned while an unrelated category is pending.
    assert [c["state"] for c in body["value_cards"]] == ["SITE_OWNED", *CARD_TAIL]
    (w1,) = [x for x in body["selected_lines"] if x["category"] == OPERATING_COST]
    assert w1["eligibility"] == "ELIGIBLE" and body["value_cards"][0]["line_keys"] == [w1["line_key"]]
    _declined(body)


def _minigrid_historical_marker(request, monkeypatch) -> None:
    """r1a2 item 1 persisted control (r1b3 P-1b-2): the S4 F01 chain and its late delivery (W3-01 `LATE`) at an
    explicit cutoff with a pre-cutoff PENDING recompute job. Its selected-as-of head is STALE, so the Site stays U;
    the before-head cutoff stays UNKNOWN. The positive covered-marker rule is the pure
    `test_settled_current_and_historical_bases`; this control is not a positive covered marker."""
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4_CASES
    from test_w301_estate_index_postgres import LATE, WIDE

    runner = CaseRunner(request.getfixturevalue("store"), request.getfixturevalue("engine"))
    request.addfinalizer(lambda: pg_harness.dispose(runner.findings))
    eng = runner.engine
    run_case(runner, S4_CASES["F01"])
    imported_before(eng, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    pin_snapshots(monkeypatch, lambda: max(runner.now + timedelta(minutes=1), db_now(eng)))
    view = Portfolio(eng, runner.tenant)
    runner.step(LATE)
    k = runner.now
    with eng.connect() as c:
        assert c.execute(text("SELECT count(*) FROM recompute_job WHERE site_id = :s AND status = 'PENDING' "
                              "AND created_at <= :k"), {"s": runner.site, "k": k}).scalar_one() >= 1
    body = view.ok(**WIDE, known_at=iso(k), limit=100)
    (site,) = body["coverage"]["sites"]
    assert body["status"] == "HISTORICAL" and site["state"] == "HISTORICAL" and site["job_state"] == "PENDING"
    # r1b3 P-1b-2: this reviewed producer's selected-as-of head is STALE at its own cutoff, so the stale-source
    # rule (not the job marker) keeps the Site U. The positive "covered despite the marker" rule is proved by the
    # pure `test_settled_current_and_historical_bases`; it is not claimed here.
    assert site["source_freshness"] == "STALE" and _fem(body) == ("UNKNOWN", "UNKNOWN", "UNKNOWN")
    assert body["summary"]["finding_count"] is None
    _declined(body)
    # The before-head cutoff: no selected as-of head, so the Site is UNKNOWN (never covered by the marker rule).
    early = view.ok(**WIDE, known_at=iso(datetime(2026, 10, 1, tzinfo=timezone.utc)), limit=100)
    (none,) = early["coverage"]["sites"]
    assert early["status"] == "HISTORICAL" and none["state"] == "UNKNOWN"
    assert _fem(early) == ("UNKNOWN", "UNKNOWN", "UNKNOWN") and early["rows"] == []
    _declined(early)


# --- run 1b: the Evidence prompt over a fake snapshot (no persisted null-step producer) ----------------------------

def _gap_row(site: dict, capability: str, gaps: list[tuple[str, str | None]], readiness: str = "LIMITED") -> dict:
    """One fake W3-02 Evidence row whose `_gaps` feed the real `evidence_money._groups` (the Portfolio's gap list)."""
    sid = str(site["site_id"])
    return {"site_id": sid, "site_code": site["site_code"], "site_name": site["site_name"],
            "capability_key": capability, "_key": (site["site_code_key"], sid, capability),
            "raw_state": readiness, "readiness": readiness, "selected_revision_ids": [f"rev-{sid}"],
            "_assessments": [f"rev-{sid}"], "_cited": [], "_token_cited": [],
            # Real rows always carry `links`; a fake row has no proven window, so it takes the label-carrying fallback.
            "links": {"site": f"/sites/{site['site_code']}", "site_readiness": f"/sites/{site['site_code']}",
                      "site_readiness_label": CURRENT_VIEW},
            "_gaps": [{"key": ("mini_grid", code, "role"), "domain": "mini_grid", "gap_code": code,
                       "missing_role": "role", "label": f"label {code}", "next_step": step} for code, step in gaps]}


def test_evidence_prompt_null_steps_and_coverage_precedence(monkeypatch) -> None:
    """r1b Matrix and prompt over the fake one-transaction store of `test_w303_portfolio_api` (real `_portfolio`,
    real gap grouping): null-step gaps are skipped for the prompt but counted in `evidence_gap_site_count`; the first
    stepped gap names its first Site in the group's `(site_code_key, site_id)` order; incomplete Evidence coverage
    wins over any gap and withholds the count."""
    from test_w303_portfolio_api import CO, MG, SITES, WINDOW, World, client, get

    mg, co = SITES
    world = World(monkeypatch)
    rows: dict[str, list[dict]] = {}
    states: dict[str, str] = {}

    def select_evidence_scope(snap, t, req, scope):
        per = []
        for s in scope["sites"]:
            sid = str(s["site_id"])
            domain = "mini_grid" if s["site_type"] == "MINIGRID" else "cold_chain"
            per.append((s, domain, {**_fake_cov(states.get(sid, "CURRENT"))}, rows.get(sid, [])))
        return per, [r for s in scope["sites"] for r in rows.get(str(s["site_id"]), [])]

    monkeypatch.setattr(portfolio, "select_evidence_scope", select_evidence_scope)
    c = client(world)

    # A null-step gap at Kobo and a stepped gap at both Sites: the prompt skips the null step and names Cold-1
    # (`cold-1` < `kobo 001`); the count covers every typed gap, null-step included.
    rows.update({MG: [_gap_row(mg, "backup", [("G-A-NULL", None), ("G-B", "Upload a log")])],
                 CO: [_gap_row(co, "product", [("G-B", "Upload a log")])]})
    body = get(c, {**WINDOW, "limit": 1}).json()
    assert body["coverage"]["evidence_state"] == "COMPLETE"
    assert body["evidence_prompt"] == {
        "state": "AVAILABLE", "text": "Upload a log at Cold to address the selected evidence gap.", "site_id": CO,
        "site_code": "COLD-1", "gap_code": "G-B", "destination": "/evidence"}
    assert body["summary"]["evidence_gap_site_count"] == 2
    assert get(c, {**WINDOW, "limit": 4}).json()["evidence_prompt"] == body["evidence_prompt"]

    # r1b2 R8: the EVIDENCE cell reduces the Site's rows: all FULL -> FULL, any NONE -> NONE, else LIMITED;
    # CONTRADICTORY or no row -> UNKNOWN.
    def cell(site_id: str) -> str:
        body = get(c, WINDOW).json()
        item = next(o for o in body["objectives"] if o["site_id"] == site_id)
        return next(x["state"] for x in item["cells"] if x["key"] == "EVIDENCE")

    for readiness, expected in ((["FULL", "FULL"], "FULL"), (["FULL", "NONE", "LIMITED"], "NONE"),
                                (["FULL", "LIMITED"], "LIMITED"), (["FULL", "CONTRADICTORY"], "UNKNOWN"),
                                ([], "UNKNOWN")):
        rows[MG] = [_gap_row(mg, f"cap-{i}", [], readiness=r) for i, r in enumerate(readiness)]
        assert cell(MG) == expected, (readiness, expected)

    # Only a null-step gap: NO_GAP, while the gap Site still counts.
    rows.update({MG: [_gap_row(mg, "backup", [("G-A-NULL", None)])], CO: [_gap_row(co, "product", [])]})
    body = get(c, WINDOW).json()
    assert body["evidence_prompt"] == {"state": "NO_GAP", "text": "No selected decision-changing evidence step",
                                       "site_id": None, "site_code": None, "gap_code": None,
                                       "destination": "/evidence"}
    assert body["summary"]["evidence_gap_site_count"] == 1

    # Incomplete Evidence coverage (Cold-1 UNKNOWN) wins over a stepped gap and withholds the count.
    rows.update({MG: [_gap_row(mg, "backup", [("G-B", "Upload a log")])]})
    states[CO] = "UNKNOWN"
    body = get(c, WINDOW).json()
    assert body["coverage"]["evidence_state"] == "PARTIAL"
    assert body["evidence_prompt"] == {"state": "COVERAGE_INCOMPLETE", "text": "Evidence coverage incomplete",
                                       "site_id": None, "site_code": None, "gap_code": None,
                                       "destination": "/evidence"}
    assert body["summary"]["evidence_gap_site_count"] is None


def _fake_cov(state: str) -> dict:
    from test_w303_portfolio_api import cov
    return cov(state)


# --- run 1b: the EV footer ----------------------------------------------------------------------------------------

def test_ev_footer_first_eligible_and_coverage_warning(portfolio_fixture) -> None:
    """Closure 1 / R12: the footer is the first eligible EV gross-tariff line with exact quantity and amount and a
    reviewed EV route, by `(site_code_key, site_id, line_key)`, never a group or a Finding. After an authorized
    empty EV Site joins, the same line stays the footer while that Site's coverage is UNKNOWN: the page's
    "other Sites may lack coverage" warning reads `coverage.sites`, not the footer."""
    fx = portfolio_fixture
    view = Portfolio(fx.engine, fx.tenant_id)
    body = view.ok(**fx.window, limit=1)
    financial = fx.money().ok("financials", **fx.window, limit=100)
    keys = {fx.site_ids[c]: c.lower() for c in CODES}

    def exact(b) -> bool:
        return b is not None and b["low"] is not None and b["low"] == b["high"]

    eligible = [x for x in financial["rows"] if x["domain"] == "ev_charging"
                and x["category"] == "GROSS_TARIFF_SCENARIO" and x["eligibility"] == "ELIGIBLE"
                and exact(x["quantity"]) and exact(x["amount"]) and x["links"].get("current_view_label") is None]
    assert len({x["site_id"] for x in eligible}) == 2, "both EV Sites carry an eligible exact line"
    first = min(eligible, key=lambda x: (keys[x["site_id"]], x["site_id"], x["line_key"]))
    assert first["site_code"] == "EV-LAB-001" and first["finding_id"] is None
    assert body["footer"] == {"line_key": first["line_key"], "site_name": first["site_name"],
                              "quantity_display": None, "amount_display": None,
                              "source_provenance": first["source_provenance"],
                              "window_start": first["window_start"], "window_end": first["window_end"],
                              "destination": first["links"]["evidence"]}
    assert body["footer"]["destination"]
    assert all(s["state"] == "CURRENT" for s in body["coverage"]["sites"])
    # r1b2 R12: an otherwise eligible exact line without a reviewed `links.evidence` target is skipped; the next
    # eligible line (EV-LAB-002) is the footer. Derived from the persisted DTOs through the real `footer`.
    m_sites = [({"site_id": sid, "site_code_key": code.lower()}, None, None, None) for code, sid in fx.site_ids.items()]
    unrouted = [{**x, "links": {**x["links"], "evidence": None}} if x["line_key"] == first["line_key"] else x
                for x in body["selected_lines"]]
    second = min((x for x in eligible if x["line_key"] != first["line_key"]),
                 key=lambda x: (keys[x["site_id"]], x["site_id"], x["line_key"]))
    assert portfolio.footer(m_sites, body["selected_lines"])["line_key"] == first["line_key"]
    assert portfolio.footer(m_sites, unrouted)["line_key"] == second["line_key"]
    assert portfolio.footer(m_sites, [{**x, "links": {**x["links"], "evidence": None}} for x in eligible]) is None

    empty = add_empty_site(fx.engine, fx.site_ids["EV-LAB-001"], "W303-EMPTY-001")
    later = view.ok(**fx.window, limit=1)
    assert later["footer"] == body["footer"]
    assert _site_state(later, empty)["state"] == "UNKNOWN"
    assert later["coverage"]["money_state"] == "PARTIAL" and later["status"] == "UNKNOWN"
    (tariff,) = [g for g in later["money"]["groups"] if g["category"] == "GROSS_TARIFF_SCENARIO" and g["line_keys"]]
    assert tariff["state"] == "UNKNOWN_COVERAGE" and tariff["amount"] is None
    _declined(later)
