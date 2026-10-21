"""W3-02 commit 3: Financials comparability - the shared group key, coverage precedence over NO_LINES, and the
persisted EV proof over the real W2-05b replay and W2-07 money worker.

The first two tests are pure (closure 3 Q19/C1 and the versioned group-key amendment) over the fake snapshot of
`test_w302_money_api.py`. The persisted tests need ASSETOPS_TEST_DATABASE_URL. The closure 2 N3 two-EV-Site
COMPARABLE fixture is not here: the reviewed EV producers install only EV-LAB-001 per database (see
`.agent/W3-02-pending-rulings.md` c3-q1).
"""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
