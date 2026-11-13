"""SR-12b (D-SR.34, D-SR.39; sequence doc rev 10b/10c): analytics readiness over the date range.

Only the readiness score follows `from`/`to`: it counts the active assessments that overlap
`[from, to)` (D-SR.74: half-open). Which analytics apply (the declaration) and the accepted-record check stay unranged. No DB: the
`/analytics` route is the file-backed declaration (`LegacySiteGate` refuses imported Sites), so there is no
Postgres path to pin.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from assetops_backend.analytics import dispatch, plain
from assetops_backend.analytics.adapters.json_assessment_store import JsonAssessmentStore
from assetops_backend.analytics.declaration import (
    READINESS_STATEMENT,
    READINESS_STATEMENT_RANGED,
    in_window,
    site_declaration,
)
from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.models import SiteEvidence
from assetops_backend.main import create_app
from run_fixtures import FakeSites
from test_t027_ingestion import SITE_ID
from test_t028_dispatch_analytic import BASE, SFC, between, minigrid, world

DAY = timedelta(days=1)


def _z(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def assessed(start: str, end: str) -> dict:
    return {"assessed_window": {"start": start, "end": end}}


def test_an_assessment_counts_when_its_window_overlaps_the_half_open_range():
    lo, hi = BASE, BASE + DAY
    assert not in_window(assessed(_z(BASE - DAY), _z(BASE)), lo, hi)  # edge 1: ends exactly at `from`: before
    assert not in_window(assessed(_z(BASE + DAY), _z(BASE + 2 * DAY)), lo, hi)  # edge 2: starts at `to`: after
    assert in_window(assessed(_z(BASE), _z(BASE)), lo, hi)  # edge 3: an instant at `from` is inside
    assert not in_window(assessed(_z(BASE + DAY), _z(BASE + DAY)), lo, hi)  # an instant at `to` is not
    assert in_window(assessed(_z(BASE + timedelta(hours=23)), _z(BASE + 2 * DAY)), lo, hi)
    assert not in_window(assessed(_z(BASE - 2 * DAY), _z(BASE - timedelta(seconds=1))), lo, hi)
    # No assessed window: the observed running bounds stand in and stay closed.
    assert in_window({"interval": {"first_running_observed": _z(BASE - DAY), "last_running_observed": _z(BASE)}},
                     lo, hi)  # edge 4: last observed = from: inside
    assert in_window({"interval": {"first_running_observed": _z(BASE), "last_running_observed": None}}, lo, hi)
    assert not in_window({}, lo, hi)


def _declaration(window):
    records = world(range(0, 151, 15), running=between(15, 120))
    assessments = [(f"a{i}", a) for i, a in enumerate(dispatch.assess(records, SFC))]
    assert len(assessments) == 1
    return site_declaration(minigrid(), SiteEvidence(SITE_ID, tuple(records)),
                            {dispatch.ANALYTIC_ID: assessments}, window)


def test_only_readiness_follows_the_range_and_the_declaration_list_stays_unranged():
    whole = _declaration(None)
    inside = _declaration((BASE, BASE + DAY))
    outside = _declaration((BASE + DAY, BASE + 2 * DAY))
    assert whole["readiness_window"] is None
    assert inside["readiness_window"] == {"from": _z(BASE), "to": _z(BASE + DAY)}
    for served in (inside, outside):  # which analytics apply, and their evidence check, do not change
        assert [a["analytic_id"] for a in served["analytics"]] == [a["analytic_id"] for a in whole["analytics"]]
        (row,), (base_row,) = served["analytics"], whole["analytics"]
        assert row["required_evidence"] == base_row["required_evidence"]
        assert {k: v for k, v in row.items() if k != "readiness"} == {
            k: v for k, v in base_row.items() if k != "readiness"}
    r_whole, r_in, r_out = (s["analytics"][0]["readiness"] for s in (whole, inside, outside))
    assert r_whole["assessed_intervals"] == r_in["assessed_intervals"] == 1
    assert r_out["assessed_intervals"] == 0
    assert r_whole["statement"] == READINESS_STATEMENT and r_whole["scope"] == plain.READINESS_SCOPE
    for r in (r_in, r_out):
        assert r["statement"] == READINESS_STATEMENT_RANGED != READINESS_STATEMENT
        assert r["scope"] == plain.READINESS_SCOPE_RANGED
        assert "not the selected window" not in r["statement"] and "not only the selected window" not in r["scope"]


@pytest.fixture()
def client(tmp_path):
    from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore

    return TestClient(create_app(
        FeatureFlags(simulator_lab_enabled=False),
        site_repository=FakeSites((minigrid(),)),
        evidence_store=JsonEvidenceStore(tmp_path / "evidence"),
        assessment_store=JsonAssessmentStore(tmp_path / "assessments"),
    ))


def test_the_route_takes_an_optional_window(client):
    base = f"/api/sites/{SITE_ID}/analytics"
    assert client.get(base).json()["readiness_window"] is None
    ranged = client.get(f"{base}?from=2026-11-02T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z")
    assert ranged.status_code == 200
    body = ranged.json()
    assert body["readiness_window"] == {"from": "2026-11-02T00:00:00Z", "to": "2026-11-09T00:00:00Z"}
    assert [a["analytic_id"] for a in body["analytics"]] == ["dispatch"]


@pytest.mark.parametrize("query", [
    "from=2026-11-02T00%3A00%3A00Z",  # one without the other
    "to=2026-11-09T00%3A00%3A00Z",
    "from=2026-11-02&to=2026-11-09",  # not instants
    "from=2026-11-09T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z",  # from after to
    "from=2026-11-02T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z",  # empty
])
def test_a_bad_window_is_422_invalid_window(client, query):
    response = client.get(f"/api/sites/{SITE_ID}/analytics?{query}")
    assert response.status_code == 422 and response.json()["detail"]["code"] == "INVALID_WINDOW"
