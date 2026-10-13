"""S4-03 phase 1: Evidence/History child routes - status matrix and a >200-version page boundary (no database).

The page-boundary test uses an in-memory test store with 205 synthetic revisions. It is test-only: the ordinary
path would need 205 distinct S3 selections of one window, and the Postgres store returns a Finding's full ordered
revision list, so the paging under test is the service's own (exercised over real rows, in small pages, by
`test_s4_finding_evidence_history_postgres.py`). No product data is written.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.finding_read import FindingReadService
from assetops_backend.finding_api import build_finding_router

TENANT, SITE = uuid4(), uuid4()
SCOPE = {"KOBO-001": ("KOBO-001", TENANT, SITE)}
FID = uuid4()


class Down(RuntimeError):
    pass


def _revision(n: int) -> dict:
    at = datetime(2026, 10, 1, tzinfo=timezone.utc) + timedelta(minutes=n)
    return {"id": UUID(int=n), "revision_no": n, "created_at": at, "transition": "OPENED" if n == 1 else
            "BASIS_REFRESHED", "lifecycle": "SUPPORTED", "claim_level": "SUPPORTED", "model_version": "m",
            "matcher_version": "v", "episode_start": at, "episode_end": at, "candidate_minutes": 10,
            "necessary_minutes": 5, "indeterminate_minutes": 0, "basis_sha256": f"b{n}", "support_sha256": "s",
            "assessment_revision_id": uuid4(), "assessments": [], "cited_evidence_count": 0, "claim": {}}


class Store:
    """Test-only in-memory store: 205 revisions of one Finding."""

    def __init__(self, count: int = 205, error: Exception | None = None) -> None:
        self.revisions = [_revision(n) for n in range(1, count + 1)]
        self.error = error

    def finding_detail(self, tenant_id, site_id, finding_id):
        if self.error:
            raise self.error
        if (tenant_id, site_id, finding_id) != (TENANT, SITE, FID):
            return None
        root = {k: None for k in ("id", "finding_key", "domain", "mechanism", "analytic_id", "generator_asset_id",
                                  "anchor_start", "anchor_assessment_revision_id", "cohort_sha256",
                                  "matcher_version", "opened_at", "recurs_after_finding_id", "split_from_finding_id")}
        root["id"] = FID
        return {"finding": root, "revisions": self.revisions,
                "relations": {"merged_into": [], "merged_from": [], "split_parts": [], "recurred_by": []}}

    def revision_times(self, tenant_id, site_id, finding_id):
        return {}

    def revision_evidence(self, tenant_id, site_id, finding_revision_id):
        raise self.error or Down("lineage store failed")

    def revision_lineage(self, tenant_id, site_id, finding_revision_id, off_bounds):
        return {"evidence": [], "runs": [], "off_reports": []}


class Dispatch:
    def _annotate(self, ids):
        return []


def client(store: Store, access=None, gate_open: bool = True) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_finding_router(FindingReadService(store, Dispatch()), SCOPE.get, (Down,),
                                            gate=lambda c, t, s: (gate_open, "test gate"), **kwargs))
    return TestClient(app)


BASE = f"/api/sites/KOBO-001/findings/{FID}"


def test_more_than_200_versions_page_exhaustively_in_revision_order() -> None:
    c = client(Store())
    first = c.get(f"{BASE}/history").json()
    assert first["page"]["total"] == 205 and first["page"]["returned"] == 200
    assert first["page"]["next_after_revision_no"] == 200
    assert first["links"]["api_next_page"].endswith("after_revision_no=200&limit=200")
    second = c.get(f"{BASE}/history", params={"after_revision_no": 200}).json()
    numbers = [r["revision_no"] for r in first["revisions"] + second["revisions"]]
    assert numbers == list(range(1, 206)) and second["page"]["next_after_revision_no"] is None
    # BASIS_REFRESHED stays individually selectable even when grouped.
    assert sum(g["count"] for g in first["revision_groups"]) == 205
    assert first["revision_groups"][1]["kind"] == "BASIS_REFRESHED" and first["revision_groups"][1]["count"] == 204
    assert len(first["links"]["revisions"]) == 200
    # A pinned old revision stays selected; latest is marked separately.
    pinned = c.get(f"{BASE}/history", params={"revision_id": str(UUID(int=3))}).json()
    assert pinned["selection"]["selected_by"] == "EXACT_REVISION_ID" and not pinned["selection"]["is_latest"]
    assert [r["revision_no"] for r in pinned["revisions"] if r["is_selected"]] == [3]
    assert pinned["selection"]["latest_revision_no"] == 205
    assert "knowledge_at" not in pinned["selection"] and "no arbitrary" in pinned["selection"]["replay"]


def test_one_revision_states_no_earlier_versions() -> None:
    body = client(Store(count=1)).get(f"{BASE}/history").json()
    assert body["earlier_versions"] == "NONE" and body["page"]["total"] == 1


def test_access_scope_and_missing_refusals() -> None:
    for child in ("evidence", "history"):
        response = client(Store(), lambda request, code: 401).get(f"{BASE}/{child}")
        assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
        response = client(Store(), lambda request, code: 403).get(f"{BASE}/{child}")
        assert response.status_code == 403 and response.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
        assert client(Store()).get(f"{BASE.replace('KOBO-001', 'OTHER')}/{child}").status_code == 404
        assert client(Store()).get(f"/api/sites/KOBO-001/findings/{uuid4()}/{child}").status_code == 404
        assert client(Store()).get(f"{BASE}/{child}", params={"revision_id": str(uuid4())}).status_code == 404


def test_closed_cutover_refuses_unpinned_child_reads() -> None:
    for child in ("evidence", "history"):
        response = client(Store(), gate_open=False).get(f"{BASE}/{child}")
        assert response.status_code == 409 and response.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
    pinned = client(Store(), gate_open=False).get(f"{BASE}/history", params={"revision_id": str(UUID(int=2))})
    assert pinned.status_code == 200 and pinned.json()["audit_only"]["non_current"]


def test_store_or_lineage_failure_is_503_never_empty() -> None:
    for child in ("evidence", "history"):
        response = client(Store(error=Down("store down"))).get(f"{BASE}/{child}")
        assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"
    # The root resolves but the cited-evidence lineage read fails: unavailable, not an empty bundle.
    response = client(Store()).get(f"{BASE}/evidence")
    assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"


def test_no_store_configured_is_503() -> None:
    app = FastAPI()
    app.include_router(build_finding_router(None, SCOPE.get))
    for child in ("evidence", "history"):
        assert TestClient(app).get(f"{BASE}/{child}").status_code == 503
