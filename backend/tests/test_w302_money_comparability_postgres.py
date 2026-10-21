"""W3-02 commit 3: Financials comparability - the shared group key, coverage precedence over NO_LINES, and the
persisted EV proof over the real W2-05b replay and W2-07 money worker.

The first two tests are pure (closure 3 Q19/C1 and the versioned group-key amendment) over the fake snapshot of
`test_w302_money_api.py`. The persisted tests need ASSETOPS_TEST_DATABASE_URL. The closure 2 N3 two-EV-Site proof
(build spec "Commit-3 rulings (c3)" c3-q1) uses the test-only second Site EV-LAB-002
(`tests/fixtures/w3/ev-lab-002.yaml`, `conversions/ev-lab-002-bindings.json`) in the same tenant and database as
EV-LAB-001, both driven through Host -> gateway -> accepted evidence -> EV assessment -> W2-07 money worker.
"""

from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from assetops_backend.estate.evidence_money import group_key_for_partition
from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture
from test_w302_evidence_api import A, WINDOW, FakeStore, client, site
from test_w302_money_api import MoneySnapshot, money_coverage, w1_head  # noqa: F401 - fixture

needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
COVERED_MG, UNCOVERED_MG = UUID("10000000-0000-4000-8000-000000000021"), UUID("10000000-0000-4000-8000-000000000022")
SIX = ("category", "currency", "window_start", "window_end", "period_kind", "assumption_fingerprint")


def financials(snap) -> dict:
    response = client(FakeStore(snap)).get("/api/estate/financials?" + urlencode({**WINDOW, "limit": 100}))
    assert response.status_code == 200, response.text
    return response.json()


def test_shared_group_key_matches_groups_and_exclusions(money_coverage) -> None:  # noqa: F811
    body = financials(MoneySnapshot())
    groups = [g for g in body["groups"] if g["line_keys"]]
    assert groups and body["exclusions"]
    for g in groups:
        assert g["group_key"] == group_key_for_partition(*(g[f] for f in SIX))
    by_group = {g["group_key"] for g in groups}
    for e in body["exclusions"]:
        assert e["group_key"] in by_group
        owner = next(g for g in groups if e["line_key"] in g["line_keys"])
        assert e["group_key"] == owner["group_key"]  # byte-identical with its partition
    assert all(g["group_key"] is None for g in body["groups"] if not g["line_keys"])
    base = {"category": "GROSS_TARIFF_SCENARIO", "currency": "KES", "window_start": "2026-10-13T08:00:00Z",
            "window_end": "2026-10-13T09:05:00Z", "period_kind": "SCENARIO_WINDOW",
            "assumption_fingerprint": "sha256:" + "a" * 64}
    key = group_key_for_partition(**base)
    assert key.startswith("sha256:") and len(key) == 71 and key == key.lower()
    for field in SIX:
        assert group_key_for_partition(**{**base, field: None}) != key, field
        assert group_key_for_partition(**{**base, field: str(base[field]) + "x"}) != key, field


def test_w302_money_unknown_coverage_precedes_no_lines(money_coverage) -> None:  # noqa: F811
    sites = [site(COVERED_MG, "MG-A", "MINIGRID"), site(UNCOVERED_MG, "MG-B", "MINIGRID")]
    money_coverage[UNCOVERED_MG] = "UNKNOWN"
    body = financials(MoneySnapshot(sites=sites, w1={}))
    assert body["rows"] == []
    assert body["groups"] == [{
        "group_key": None, "category": "CANDIDATE_OPERATING_COST_EXPOSURE", "currency": None,
        "window_start": None, "window_end": None, "period_kind": None, "assumption_fingerprint": None,
        "state": "UNKNOWN_COVERAGE", "line_keys": [], "amount": None,
        "reason_codes": ["NO_LINES", "UNKNOWN_COVERAGE"]}]
    with_head = financials(MoneySnapshot(sites=sites, w1={A[21]: w1_head(A[21], A[31])}))
    assert [r["site_code"] for r in with_head["rows"]] == ["MG-A"]
    assert [(g["state"], g["line_keys"]) for g in with_head["groups"]] == [
        ("UNKNOWN_COVERAGE", [f"mini_grid:{A[31]}"])]  # its actual partition; no NO_LINES sentinel
    assert "NO_LINES" not in with_head["groups"][0]["reason_codes"] and with_head["groups"][0]["amount"] is None
    money_coverage[UNCOVERED_MG] = "CURRENT"
    complete = financials(MoneySnapshot(sites=sites, w1={}))
    assert [(g["state"], g["reason_codes"]) for g in complete["groups"]] == [("NO_LINES", ["NO_LINES"])]


@needs_db
def test_w302_money_persisted_ev_single_site_line(chain) -> None:  # noqa: F811
    """The real EV replay, golden tariff and W2-07 money worker: the estate register line is the exact stored head
    with its session revision and accepted evidence IDs, ELIGIBLE, in a SINGLE_LINE partition (one EV Site)."""
    from test_w207_ev_money_postgres import ev_money_rows, golden_tariff, money, money_head
    from test_w301_estate_index_ev_postgres import settled
    from test_w301_estate_index_postgres import iso
    from assetops_backend.estate.composition import build_estate_evidence_service
    from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router

    built, _estate, day = settled(chain, "complete")
    tariff = golden_tariff(built)
    outcomes = money(built)
    assert outcomes and all(o.succeeded for o in outcomes), [(o.error_code, o.error_detail) for o in outcomes]
    rows = ev_money_rows(built)
    head = money_head(rows)
    assert head["state"] == "ESTIMATED"
    sessions = sorted(str(r["session_revision_id"]) for r in rows["ev_consequence_session"]
                      if r["consequence_revision_id"] == head["id"])
    evidence = sorted(str(r["evidence_id"]) for r in rows["ev_consequence_evidence"]
                      if r["consequence_revision_id"] == head["id"])
    service = build_estate_evidence_service(URL)
    try:
        app = FastAPI()
        app.include_router(build_estate_evidence_money_router(service, lambda: built.tenant_id))
        response = TestClient(app).get("/api/estate/financials", params={
            "from": iso(day), "to": iso(day + timedelta(days=1)), "limit": 100})
    finally:
        service.store.dispose()
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
    assert body["total_count"] == 1 and len(body["rows"]) == 1
    line = body["rows"][0]
    assert line["line_key"] == f"ev_charging:{head['id']}" and line["consequence_revision_id"] == str(head["id"])
    assert (line["category"], line["eligibility"], line["period_kind"]) == (
        "GROSS_TARIFF_SCENARIO", "ELIGIBLE", "SCENARIO_WINDOW")
    assert line["amount"] == {"low": str(head["amount"]), "high": str(head["amount"]), "currency": head["currency"]}
    assert line["assumption_revision_ids"] == [str(tariff)] and line["assumption_fingerprint"].startswith("sha256:")
    assert line["technical_interval_ids"] == sessions and line["basis_evidence_ids"] == evidence and evidence
    assert line["source_provenance"]["classification"] not in ("UNKNOWN", "MIXED")
    link = urlsplit(line["links"]["bridge"])
    assert link.path == "/sites/EV-LAB-001/ev/financials" and line["links"]["current_view_label"] is None
    assert parse_qs(link.query)["from"][0].startswith(line["window_start"][:16])
    group = next(g for g in body["groups"] if g["line_keys"])
    assert (group["state"], group["amount"], group["line_keys"]) == ("SINGLE_LINE", None, [line["line_key"]])
    assert body["summary"]["estate_total"] is None and body["summary"]["eligible_line_count"] == 1


# --- c3-q1: the persisted two-EV-Site comparable fixture ----------------------------------------------------------

SECOND_EV = "EV-LAB-002"
#: c3b (`.agent/W3-02-build-spec.md`, c3-q3): the second run uses the test-only scenario below. It parses only once
#: Lane A's `ev_parsing.py` admits (EV-LAB-002, 20518) for `ev-complete-lab-002`; until then the strict parser pins
#: EV-LAB-001/20517 and the path cannot run (`.agent/W3-02-pending-rulings.md`, c3b-q1). Commit 3 not done (N3).
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BACKEND)
SECOND_FIXTURE = os.path.join(BACKEND, "tests", "fixtures", "w3", "ev-lab-002.yaml")
SECOND_CONVERSION = os.path.join(BACKEND, "conversions", "ev-lab-002-bindings.json")
SHIPPED_EV_COMPLETE = os.path.join(ROOT, "config", "scenarios", "ev-complete.yaml")
SECOND_SCENARIO_ID = "ev-complete-lab-002"
SECOND_SCENARIO = os.path.join(BACKEND, "tests", "fixtures", "w3", "scenarios", f"{SECOND_SCENARIO_ID}.yaml")
#: The only lines the test-only scenario may change against the shipped `ev-complete` (c3b).
SECOND_SCENARIO_CHANGES = {"scenario_id: ev-complete": "scenario_id: ev-complete-lab-002",
                           "site_code: EV-LAB-001": "site_code: EV-LAB-002", "seed: 20517": "seed: 20518"}


def test_w302_second_ev_scenario_differs_from_shipped_only_in_three_fields() -> None:
    """c3b: the test-only `ev-complete-lab-002` is the shipped `ev-complete` line for line (comments included)
    except `scenario_id`, `site_code` and `seed`, so the fixture cannot drift from the shipped scenario silently."""
    import yaml

    with open(SHIPPED_EV_COMPLETE, encoding="utf-8") as f:
        shipped = f.read()
    with open(SECOND_SCENARIO, encoding="utf-8") as f:
        second = f.read()
    shipped_lines, second_lines = shipped.splitlines(), second.splitlines()
    assert len(shipped_lines) == len(second_lines)
    changed = {a: b for a, b in zip(shipped_lines, second_lines) if a != b}
    assert changed == SECOND_SCENARIO_CHANGES
    a, b = yaml.safe_load(shipped), yaml.safe_load(second)
    assert (b["scenario_id"], b["site_code"], b["seed"]) == (SECOND_SCENARIO_ID, SECOND_EV, 20518)
    assert {k: v for k, v in a.items() if k not in ("scenario_id", "site_code", "seed")} == {
        k: v for k, v in b.items() if k not in ("scenario_id", "site_code", "seed")}
    assert not os.path.exists(os.path.join(ROOT, "config", "scenarios", f"{SECOND_SCENARIO_ID}.yaml"))


def second_scenario_repository(root):
    """c3b: one test-scoped repository over a temporary root holding the six unchanged shipped EV documents plus
    the test-only `ev-complete-lab-002` (no duplicate IDs); the default production repository is untouched."""
    import glob
    import shutil

    from assetops_backend.scenarios.adapters.composite_scenario_repository import CompositeScenarioRepository
    from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import ReadOnlyYamlScenarioStore
    from assetops_backend.scenarios.adapters.yaml_user_scenario_store import UserYamlScenarioStore
    from scenario_cache import CachedScenarioRepository

    root.mkdir(parents=True)
    shipped = sorted(glob.glob(os.path.join(ROOT, "config", "scenarios", "ev-*.yaml")))
    assert len(shipped) == 6 and SECOND_SCENARIO_ID not in {os.path.basename(p)[:-5] for p in shipped}
    for path in (*shipped, SECOND_SCENARIO):
        shutil.copyfile(path, root / os.path.basename(path))
    # The ruled `CachedScenarioRepository(ReadOnlyYamlScenarioStore(root))` cannot serve `get_scenario` (the store
    # only lists), so the store is composed exactly as `build_scenario_repository()` does, over the test root and
    # an empty user root.
    (root.parent / "user-scenarios").mkdir()
    return CachedScenarioRepository(CompositeScenarioRepository(
        shipped=ReadOnlyYamlScenarioStore(root), user=UserYamlScenarioStore(root.parent / "user-scenarios")))


def install_second_ev_site(store):
    """c3-q1: import EV-LAB-002 into the same tenant and publish its complete `ev-roles-1` bindings at its original
    Foundation's `valid_from`, through the reviewed `import_site`, `plan_requests` and `BindingService.publish`."""
    from assetops_backend.sites.binding_conversion import plan_requests
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.composition import read_binding_conversion_fixture, read_site_import_source
    from assetops_backend.sites.foundation_service import ImportSource, import_site
    from test_s1_bindings_postgres import Clock
    from test_w205b_ev_replay_postgres import INSTALL_AT

    source = read_site_import_source(SECOND_FIXTURE)
    result = import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                         source=ImportSource(path="var/sites/ev-lab-002.yaml", sha256=source.sha256,
                                             record=source.record),
                         legacy_documents=(), clock=Clock(INSTALL_AT))
    fixture = read_binding_conversion_fixture(SECOND_CONVERSION)[0]
    original = next(r for r in store.revisions(result.tenant.id, result.site.id) if r.origin == "IMPORT")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(result.tenant.id, result.site.id).assets}
    requests, _declared, _rows = plan_requests(fixture, result.site, original.content.get("signal_mappings") or (),
                                               asset_ids)
    BindingService(store, Clock(INSTALL_AT)).publish(
        result.tenant, result.site, requests=requests, effective_from=original.valid_from, note=fixture["note"],
        role_set=fixture["role_set"])
    return result


@pytest.fixture()
def two_ev_sites(tmp_path, monkeypatch):
    """One `*_test` database, both Sites imported, both registered `complete` runs driven through the real chain;
    each Site's golden tariff (currency per call) and W2-07 money worker after its selected assessment settles."""
    from test_w205b_ev_replay_postgres import Chain, hold_uuids
    from test_w206_ev_store_postgres import run_worker
    from test_w207_ev_money_postgres import golden_tariff, money
    from test_w301_estate_index_ev_postgres import day_of
    from test_w301_estate_index_postgres import imported_before

    opened: list = []

    def make(currencies=("KES", "KES")):
        hold_uuids(monkeypatch, 0x3021)
        first = Chain("complete", tmp_path / "ev-lab-001")
        opened.append(first)
        first.open()  # the only fresh_database() call
        first.start_release_upload()
        run_worker(first)
        monkeypatch.undo()  # a separate allocator namespace for the second Site
        hold_uuids(monkeypatch, 0x3022)
        second = Chain("complete", tmp_path / "ev-lab-002", site_code=SECOND_EV, seed=20518)
        opened.append(second)
        second.open(fresh=False, install=install_second_ev_site,
                    scenarios=second_scenario_repository(tmp_path / "scenarios"), scenario_id=SECOND_SCENARIO_ID)
        second.start_release_upload()
        run_worker(second)
        assert first.tenant_id == second.tenant_id and first.site_id != second.site_id
        with first.engine.connect() as c:
            start = c.execute(text("SELECT min(window_start) FROM analytic_run_selection WHERE site_id = :s"),
                              {"s": first.site_id}).scalar_one()
        day = day_of(start)
        tariffs = {}
        for built, currency in zip((first, second), currencies):
            imported_before(built.engine, built.tenant_id, built.site_id, day - timedelta(days=1))
            tariffs[built.site_code] = golden_tariff(built, currency=currency)
            outcomes = money(built)
            assert outcomes and all(o.succeeded for o in outcomes), [(o.error_code, o.error_detail) for o in outcomes]
        return (first, second), day, tariffs

    yield make
    for built in opened:
        built.close()


def _read_financials(tenant_id, day, **params) -> dict:
    from test_w301_estate_index_postgres import iso
    from assetops_backend.estate.composition import build_estate_evidence_service
    from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router

    service = build_estate_evidence_service(URL)
    try:
        app = FastAPI()
        app.include_router(build_estate_evidence_money_router(service, lambda: tenant_id))
        response = TestClient(app).get("/api/estate/financials", params={
            "from": iso(day), "to": iso(day + timedelta(days=1)), "limit": 100, **params})
    finally:
        service.store.dispose()
    assert response.status_code == 200, response.text
    return response.json()


def _stored(built, tariff) -> dict:
    """The Site's stored head, its session revision and accepted evidence IDs, and its tariff, by scoped queries."""
    from test_w207_ev_money_postgres import ev_money_rows, money_head

    head = money_head(ev_money_rows(built))
    with built.engine.connect() as c:
        db_head = c.execute(text(
            "SELECT id, state, reason, amount, currency, tariff_revision_id FROM ev_consequence_revision "
            "WHERE tenant_id = :t AND site_id = :s ORDER BY revision_no DESC LIMIT 1"),
            {"t": built.tenant_id, "s": built.site_id}).one()
        sessions = sorted(str(x) for x in c.execute(text(
            "SELECT cs.session_revision_id FROM ev_consequence_session cs JOIN ev_session_revision sr "
            "ON sr.id = cs.session_revision_id WHERE cs.consequence_revision_id = :h AND sr.tenant_id = :t "
            "AND sr.site_id = :s"), {"h": db_head.id, "t": built.tenant_id, "s": built.site_id}).scalars())
        evidence = sorted(str(x) for x in c.execute(text(
            "SELECT ce.evidence_id FROM ev_consequence_evidence ce JOIN accepted_evidence ae ON ae.id = ce.evidence_id "
            "WHERE ce.consequence_revision_id = :h AND ae.tenant_id = :t AND ae.site_id = :s"),
            {"h": db_head.id, "t": built.tenant_id, "s": built.site_id}).scalars())
        price = c.execute(text(
            "SELECT id, currency, value FROM financial_assumption_revision WHERE id = :r AND tenant_id = :t "
            "AND site_id = :s"), {"r": tariff, "t": built.tenant_id, "s": built.site_id}).one()
    assert db_head.id == head["id"] and (db_head.state, db_head.reason) == ("ESTIMATED", "ELIGIBLE_COMPLETE_INTERVALS")
    assert db_head.tariff_revision_id == tariff and db_head.currency == price.currency
    assert sessions and evidence
    return {"head": db_head, "sessions": sessions, "evidence": evidence, "price": price}


def _line_matches(line: dict, built, stored: dict) -> None:
    head = stored["head"]
    assert line["site_code"] == built.site_code
    assert line["line_key"] == f"ev_charging:{head.id}" and line["consequence_revision_id"] == str(head.id)
    assert (line["category"], line["eligibility"], line["period_kind"]) == (
        "GROSS_TARIFF_SCENARIO", "ELIGIBLE", "SCENARIO_WINDOW")
    assert line["amount"] == {"low": str(head.amount), "high": str(head.amount), "currency": head.currency}
    assert line["assumption_revision_ids"] == [str(stored["price"].id)]
    assert line["technical_interval_ids"] == stored["sessions"]
    assert line["basis_evidence_ids"] == stored["evidence"]


@needs_db
def test_w302_money_persisted_ev_comparable_same_values(two_ev_sites) -> None:
    """c3-q1: two EV Sites, the same KES gross tariff rate and unit, one tenant and day: one COMPARABLE
    GROSS_TARIFF_SCENARIO group of exactly the two stored heads, summed unrounded, and still no estate total."""
    (first, second), day, tariffs = two_ev_sites(("KES", "KES"))
    stored = {b.site_code: _stored(b, tariffs[b.site_code]) for b in (first, second)}
    assert tariffs[first.site_code] != tariffs[second.site_code]
    assert {s["price"].currency for s in stored.values()} == {"KES"}
    assert stored[first.site_code]["price"].value == stored[second.site_code]["price"].value
    body = _read_financials(first.tenant_id, day)
    assert body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
    assert body["total_count"] == 2 and len(body["rows"]) == 2
    lines = {line["site_code"]: line for line in body["rows"]}
    assert set(lines) == {"EV-LAB-001", SECOND_EV}
    for built in (first, second):
        _line_matches(lines[built.site_code], built, stored[built.site_code])
    a, b = lines["EV-LAB-001"], lines[SECOND_EV]
    for field in ("category", "window_start", "window_end", "period_kind", "assumption_fingerprint"):
        assert a[field] == b[field], field
    assert a["amount"]["currency"] == b["amount"]["currency"] == "KES"
    assert a["assumption_fingerprint"] is not None and a["assumption_fingerprint"].startswith("sha256:")
    assert a["assumption_revision_ids"] != b["assumption_revision_ids"]  # distinct tariff revisions, one fingerprint
    for key in ("technical_interval_ids", "basis_evidence_ids"):
        assert a[key] and b[key] and not set(a[key]) & set(b[key]), key
    assert a["overlap_group"] is not None and b["overlap_group"] is not None
    assert a["overlap_group"] != b["overlap_group"]
    groups = [g for g in body["groups"] if g["line_keys"]]
    assert len(groups) == 1
    group = groups[0]
    assert group["state"] == "COMPARABLE" and group["category"] == "GROSS_TARIFF_SCENARIO"
    assert group["line_keys"] == sorted([a["line_key"], b["line_key"]])
    assert (group["currency"], group["window_start"], group["window_end"], group["period_kind"],
            group["assumption_fingerprint"]) == ("KES", a["window_start"], a["window_end"], a["period_kind"],
                                                 a["assumption_fingerprint"])
    total = sum((Decimal(str(s["head"].amount)) for s in stored.values()), Decimal(0))
    assert Decimal(group["amount"]["low"]) == total and Decimal(group["amount"]["high"]) == total
    assert group["amount"]["currency"] == "KES"
    assert not [e for e in body["exclusions"] if e["line_key"] in group["line_keys"]]
    assert body["summary"]["estate_total"] is None
    page = _read_financials(first.tenant_id, day, limit=1)
    assert len(page["rows"]) == 1 and page["next_cursor"]
    assert page["groups"] == body["groups"]
    rest = _read_financials(first.tenant_id, day, limit=1, cursor=page["next_cursor"])
    assert len(rest["rows"]) == 1
    assert {page["rows"][0]["line_key"], rest["rows"][0]["line_key"]} == set(group["line_keys"])
    assert rest["groups"] == body["groups"] and rest["selection_token"] == page["selection_token"]


@needs_db
def test_w302_money_persisted_ev_different_currency(two_ev_sites) -> None:
    """c3-q1: the same tariff rate and unit, KES on one Site and USD on the other: both lines stay ELIGIBLE in two
    SINGLE_LINE groups, no COMPARABLE group or numeric group amount, MIXED_CURRENCY names both, no estate total."""
    (first, second), day, tariffs = two_ev_sites(("KES", "USD"))
    stored = {b.site_code: _stored(b, tariffs[b.site_code]) for b in (first, second)}
    assert stored[first.site_code]["price"].currency == "KES" and stored[second.site_code]["price"].currency == "USD"
    assert stored[first.site_code]["price"].value == stored[second.site_code]["price"].value
    body = _read_financials(first.tenant_id, day)
    assert body["status"] == "CURRENT" and body["total_count"] == 2
    lines = {line["site_code"]: line for line in body["rows"]}
    for built in (first, second):
        _line_matches(lines[built.site_code], built, stored[built.site_code])
    assert lines["EV-LAB-001"]["amount"]["currency"] == "KES" and lines[SECOND_EV]["amount"]["currency"] == "USD"
    groups = [g for g in body["groups"] if g["line_keys"]]
    assert sorted((g["state"], g["currency"], g["line_keys"]) for g in groups) == sorted([
        ("SINGLE_LINE", "KES", [lines["EV-LAB-001"]["line_key"]]),
        ("SINGLE_LINE", "USD", [lines[SECOND_EV]["line_key"]])])
    assert all(g["state"] != "COMPARABLE" and g["amount"] is None for g in body["groups"])
    mixed = [d for d in body["diagnostics"] if d["code"] == "MIXED_CURRENCY"]
    assert mixed == [{"category": "GROSS_TARIFF_SCENARIO", "code": "MIXED_CURRENCY",
                      "line_keys": sorted(line["line_key"] for line in lines.values())}]
    assert body["summary"]["estate_total"] is None
