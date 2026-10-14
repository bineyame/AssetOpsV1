"""S4-02a phase 2: Site price read and Finding Financials bridge route matrix (no database).

Packet `tasks/S4-02a-site-assumptions.md` items 3-4. The stored selection semantics (half-open boundaries,
recorded cutoffs, exact IDs after later writes) are proved against PostgreSQL in
`test_s4_assumption_read_postgres.py`.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.finding_api import ACCESS_BASIS, bridge_consequence, build_finding_router
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


def bridge(reads, access=None, gate=None, consequences=None) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    if consequences is not None:
        kwargs.update(consequences=consequences, consequence_unavailable=(Down,))
    app.include_router(build_finding_router(reads, SCOPE.get, (Down,),
                                            gate=gate or (lambda c, t, s: (True, "comparison passed")), **kwargs))
    return TestClient(app)


FINDING = uuid4()
BRIDGE = f"/api/sites/KOBO-001/findings/{FINDING}/financials"


class TestFindingFinancialsBridge:
    def test_exact_revision_is_held_and_without_a_consequence_store_nothing_is_priced(self) -> None:
        reads = FindingReads(finding_body("r1"))
        body = bridge(reads).get(BRIDGE, params={"revision_id": str(uuid4())}).json()
        assert reads.calls[0][1] is not None
        assert body["revision"]["id"] == "r1" and body["window"]["start"].startswith("2026-10-19")
        assert body["consequence"] == {**body["consequence"], "state": "UNAVAILABLE", "amount": None,
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

    def test_the_bridge_summarises_the_stored_consequence_and_shows_an_amount_only_when_current(self) -> None:
        """S4-02b phase 2a replaced the S4-02a placeholder with the stored consequence read."""
        def result(currentness: str, state: str = "PRICED") -> dict:
            row = {"id": "c1", "state": state, "quantity": {"low": "0", "high": "2.75", "unit": "L", "reason": None},
                   "price": {"revision_id": "p1", "reason": None},
                   "amount": {"low": "0", "high": "3.4375", "currency": "USD"},
                   "display": {"state": "ROUNDED_OUTWARD", "amount_low": "0.00", "amount_high": "3.44"}}
            return {"currentness": {"state": currentness, "reasons": [], "pending_work": []}, "consequence": row}

        class Consequences:
            def __init__(self, out=None, error=None):
                self.out, self.error, self.calls = out, error, []

            def read(self, *args, **kw):
                self.calls.append(kw)
                if self.error:
                    raise self.error
                return self.out

        reads = FindingReads({**finding_body(), "selection": {"revision_id": str(uuid4()), "revision_no": 2,
                                                              "is_latest": True}})
        current = Consequences(result("CURRENT"))
        body = bridge(reads, consequences=current).get(BRIDGE).json()["consequence"]
        assert current.calls[0]["finding_revision_is_latest"] is True
        assert (body["state"], body["amount"], body["currency"], body["consequence_revision_id"]) == (
            "PRICED", {"low": "0.00", "high": "3.44"}, "USD", "c1")
        assert "not measured fuel saved" in body["reason"]
        for state in ("STALE", "PENDING", "HISTORICAL"):
            stale = bridge(reads, consequences=Consequences(result(state))).get(BRIDGE).json()["consequence"]
            assert (stale["state"], stale["amount"], stale["currency"], stale["quantity"]) == (state, None, None, None)
        down = bridge(reads, consequences=Consequences(error=Down("x"))).get(BRIDGE).json()["consequence"]
        assert (down["state"], down["amount"]) == ("UNAVAILABLE", None)
        unpriced = bridge_consequence(result("CURRENT", "UNPRICED"))
        assert (unpriced["state"], unpriced["amount"], unpriced["currency"]) == ("UNPRICED", None, None)


# ---- S4-02b phase 2b: review carries M1 (closed source), L1 (route refusals) and L4 (STALE wording) ----

CONSEQUENCES = f"/api/sites/KOBO-001/findings/{FINDING}/financial-consequences"


class Consequences:
    def __init__(self, out=None, error=None):
        self.out, self.error, self.calls = out, error, []

    def read(self, *args, **kw):
        self.calls.append(kw)
        if self.error:
            raise self.error
        return self.out

    def locate(self, *args):
        self.calls.append(("locate", args))
        if self.error:
            raise self.error
        return None


def latest_reads() -> FindingReads:
    return FindingReads({**finding_body(), "selection": {"revision_id": str(uuid4()), "revision_no": 2,
                                                         "is_latest": True}})


def stale(pending: list) -> dict:
    return {"currentness": {"state": "STALE", "reasons": ["PRICE_SELECTION_CHANGED"], "pending_work": pending},
            "consequence": {"id": "c1", "state": "PRICED"}}


class TestConsequenceRouteCarries:
    def test_l1_unauthenticated_and_forbidden_are_refused_before_any_lookup(self) -> None:
        reads, store = latest_reads(), Consequences(stale([]))
        for status in (401, 403):
            client = bridge(reads, access=lambda r, s, x=status: x, consequences=store)
            assert client.get(CONSEQUENCES).status_code == status
        assert reads.calls == [] and store.calls == []

    def test_l1_missing_or_failing_consequence_store_is_typed_503(self) -> None:
        for client in (bridge(latest_reads()), bridge(latest_reads(), consequences=Consequences(error=Down("gone")))):
            response = client.get(CONSEQUENCES)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "CONSEQUENCE_STORE_UNAVAILABLE"

    def test_m1_the_source_gate_is_passed_to_the_read_and_bridge(self) -> None:
        closed = lambda c, t, s: (False, "no comparison report")  # noqa: E731
        store = Consequences({"currentness": {"state": "AUDIT_ONLY", "reasons": ["SOURCE_CLOSED"],
                                              "pending_work": []}, "consequence": None,
                              "history": {"revisions": [], "page": {"next_after_revision_no": None}}})
        client = bridge(latest_reads(), gate=closed, consequences=store)
        assert client.get(BRIDGE, params={"revision_id": str(uuid4())}).status_code == 200
        assert client.get(CONSEQUENCES, params={"revision_id": str(uuid4())}).status_code == 200
        assert [c["source_open"] for c in store.calls] == [False, False]
        open_store = Consequences(stale([]))
        bridge(latest_reads(), consequences=open_store).get(BRIDGE)
        assert open_store.calls[0]["source_open"] is True

    def test_m1_audit_only_bridge_shows_no_amount(self) -> None:
        audit = bridge_consequence({"currentness": {"state": "AUDIT_ONLY", "reasons": ["SOURCE_CLOSED"],
                                                    "pending_work": []},
                                    "consequence": {"id": "c1", "state": "PRICED"}})
        assert (audit["state"], audit["amount"], audit["currency"], audit["quantity"]) == (
            "AUDIT_ONLY", None, None, None)
        assert audit["currentness_reasons"] == ["SOURCE_CLOSED"] and "for the record only" in audit["reason"]

    def test_l4_stale_claims_a_queued_recalculation_only_when_work_exists(self) -> None:
        idle = bridge_consequence(stale([]))
        queued = bridge_consequence(stale([{"work_id": "w1", "cause": "ASSUMPTION_PUBLISHED"}]))
        assert (idle["recalculation_queued"], queued["recalculation_queued"]) == (False, True)
        assert "not been recalculated yet" in idle["reason"] and "waiting" not in idle["reason"]
        assert "waiting to run" in queued["reason"]
        for body in (idle, queued):
            assert "being recalculated" not in body["reason"] and body["amount"] is None
