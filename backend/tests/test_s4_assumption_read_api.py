"""S4-02a phase 2: Site price read and Finding Financials bridge route matrix (no database).

Packet `tasks/S4-02a-site-assumptions.md` items 3-4. The stored selection semantics (half-open boundaries,
recorded cutoffs, exact IDs after later writes) are proved against PostgreSQL in
`test_s4_assumption_read_postgres.py`.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.finding_api import ACCESS_BASIS, build_finding_router, consequence_state
from assetops_backend.financial_api import build_financial_assumption_router
from assetops_backend.financial_read_api import build_financial_read_router
from assetops_backend.financials.assumption_read import AssumptionReadService

TENANT, SITE = uuid4(), uuid4()
SCOPE = {"KOBO-001": ("KOBO-001", TENANT, SITE)}
SERIES = "/api/sites/KOBO-001/financial-assumptions"


class Down(RuntimeError):
    pass


class Rows:
    def __init__(self, error: Exception | None = None) -> None:
        self.error, self.calls = error, []

    def snapshot(self, tenant_id, site_id, key, recorded_at, after_revision_no, limit):
        self.calls.append(("snapshot", tenant_id, site_id))
        if self.error:
            raise self.error
        return {"total": 0, "revisions": [], "timeline": [], "cited": {}}

    def revision_detail(self, tenant_id, site_id, revision_id):
        self.calls.append(("detail", tenant_id, site_id, revision_id))
        if self.error:
            raise self.error
        return None


def reader(rows=None, access=None, reads=True) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    service = AssumptionReadService(rows or Rows()) if reads else None
    app.include_router(build_financial_assumption_router(SCOPE.get))
    app.include_router(build_financial_read_router(service, SCOPE.get, (Down,), **kwargs))
    return TestClient(app)


class TestAssumptionReadMatrix:
    def test_unauthenticated_is_401_and_forbidden_is_403_before_any_lookup(self) -> None:
        rows = Rows()
        assert reader(rows, access=lambda r, s: 401).get(SERIES).status_code == 401
        response = reader(rows, access=lambda r, s: 403).get(f"{SERIES}/{uuid4()}")
        assert (response.status_code, response.json()["detail"]["code"]) == (403, "SITE_SCOPE_FORBIDDEN")
        assert rows.calls == []

    def test_unknown_site_is_404(self) -> None:
        assert reader().get("/api/sites/NOPE-001/financial-assumptions").status_code == 404

    def test_missing_or_failing_store_is_typed_503(self) -> None:
        for client in (reader(reads=False), reader(Rows(Down("db gone")))):
            for url in (SERIES, f"{SERIES}/{uuid4()}"):
                response = client.get(url)
                assert response.status_code == 503, url
                assert response.json()["detail"]["code"] == "ASSUMPTION_STORE_UNAVAILABLE"

    def test_unknown_or_malformed_revision_never_falls_back_to_latest(self) -> None:
        rows = Rows()
        missing = reader(rows).get(f"{SERIES}/{uuid4()}")
        assert (missing.status_code, missing.json()["detail"]["code"]) == (404, "ASSUMPTION_REVISION_NOT_FOUND")
        assert reader(rows).get(f"{SERIES}/latest").status_code == 422
        assert [c[0] for c in rows.calls] == ["detail"]

    def test_empty_series_is_no_price_not_a_default(self) -> None:
        body = reader().get(SERIES, params={"valid_at": "2026-10-01T00:00:00Z"}).json()
        assert body["state"] == "NO_PRICE" and body["timeline"] == [] and body["access_basis"] == ACCESS_BASIS
        assert body["selection"]["state"] == "NO_PRICE" and body["selection"]["revision_id"] is None

    def test_naive_instants_and_unknown_keys_are_refused(self) -> None:
        client = reader()
        assert client.get(SERIES, params={"valid_at": "2026-10-01T00:00:00"}).json()["detail"]["code"] == \
            "INSTANT_NOT_ZONED"
        assert client.get(SERIES, params={"key": "petrol"}).status_code == 422
        assert client.get(SERIES, params={"limit": 0}).status_code == 422

    def test_the_write_route_keeps_no_verified_principal_beside_the_reads(self) -> None:
        response = reader().post(SERIES, json={"value": "1.30"})
        assert (response.status_code, response.json()["detail"]["code"]) == (401, "UNAUTHENTICATED")


# ---- Finding Financials bridge ----

class FindingReads:
    def __init__(self, body=None, error: Exception | None = None) -> None:
        self.body, self.error, self.calls = body, error, []

    def finding(self, tenant_id, site_id, finding_id, revision_id=None, **page):
        self.calls.append((finding_id, revision_id, page.get("source_open")))
        if self.error:
            raise self.error
        return self.body


def finding_body(revision_id: str = "r2") -> dict:
    return {"finding": {"id": "f1"}, "selection": {"revision_id": revision_id, "revision_no": 2},
            "revision": {"title": "Generator ran while solar could carry the load", "lifecycle": "SUPPORTED",
                         "claim_level": "SUPPORTED", "episode": {"start": "2026-10-19T06:00:00+00:00",
                                                                 "end": "2026-10-19T09:00:00+00:00"}}}


def bridge(reads, access=None, gate=None) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_finding_router(reads, SCOPE.get, (Down,),
                                            gate=gate or (lambda c, t, s: (True, "comparison passed")), **kwargs))
    return TestClient(app)


FINDING = uuid4()
BRIDGE = f"/api/sites/KOBO-001/findings/{FINDING}/financials"


class TestFindingFinancialsBridge:
    def test_exact_revision_is_held_and_the_consequence_is_quantity_unavailable(self) -> None:
        reads = FindingReads(finding_body("r1"))
        body = bridge(reads).get(BRIDGE, params={"revision_id": str(uuid4())}).json()
        assert reads.calls[0][1] is not None
        assert body["revision"]["id"] == "r1" and body["window"]["start"].startswith("2026-10-19")
        assert body["consequence"] == {**body["consequence"], "state": "QUANTITY_UNAVAILABLE", "amount": None,
                                       "currency": None, "quantity": None, "price_revision_id": None}
        assert body["links"]["evidence"] == f"/sites/KOBO-001/findings/{FINDING}/evidence?revision_id=r1"
        assert body["links"]["financials"] == f"/sites/KOBO-001/financials?finding_id={FINDING}&revision_id=r1"

    def test_scope_refusals_and_store_failure(self) -> None:
        assert bridge(FindingReads(finding_body()), access=lambda r, s: 401).get(BRIDGE).status_code == 401
        assert bridge(FindingReads(finding_body()), access=lambda r, s: 403).get(BRIDGE).status_code == 403
        assert bridge(FindingReads(None)).get(BRIDGE).status_code == 404
        assert bridge(FindingReads(error=Down("x"))).get(BRIDGE).status_code == 503
        assert bridge(None).get(BRIDGE).status_code == 503

    def test_closed_gate_refuses_the_latest_and_serves_a_pinned_revision_as_audit(self) -> None:
        closed = lambda c, t, s: (False, "Assessment lineage is broken")  # noqa: E731
        assert bridge(FindingReads(finding_body()), gate=closed).get(BRIDGE).status_code == 409
        pinned = bridge(FindingReads(finding_body()), gate=closed).get(BRIDGE, params={"revision_id": str(uuid4())})
        assert pinned.status_code == 200 and pinned.json()["audit_only"]["non_current"] is True

    def test_unpriced_is_typed_and_a_priced_amount_does_not_exist_in_this_slice(self) -> None:
        unpriced = consequence_state(quantity_available=True, price_covers_window=False)
        assert (unpriced["state"], unpriced["amount"], unpriced["currency"]) == ("UNPRICED", None, None)
        try:
            consequence_state(quantity_available=True, price_covers_window=True)
        except NotImplementedError:
            pass
        else:
            raise AssertionError("S4-02a must never report a priced amount")
