"""S4-01 phase 2: Finding route status matrix (no database).

`D-2026-10-09-pre-s3-claim-routes-and-actor`: 401 unauthenticated, 403 unauthorized known scope, 404 foreign
or unknown Site/root/revision, typed 503 when the store is unavailable or unconfigured.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics.finding_read import revision_groups
from assetops_backend.finding_api import ACCESS_BASIS, build_finding_router

TENANT, SITE = uuid4(), uuid4()
SCOPE = {"KOBO-001": ("KOBO-001", TENANT, SITE)}


class Down(RuntimeError):
    pass


class Reads:
    def __init__(self, body=None, error: Exception | None = None) -> None:
        self.body, self.error, self.calls = body, error, []

    def finding(self, tenant_id, site_id, finding_id, revision_id=None, **page):
        self.calls.append((tenant_id, site_id, finding_id, revision_id, page.get("source_open")))
        if self.error:
            raise self.error
        return self.body

    def window_state(self, tenant_id, site_id, day):
        self.calls.append((tenant_id, site_id, day))
        if self.error:
            raise self.error
        return self.body


def OPEN(code, tenant_id, site_id):
    return True, "comparison passed"


def CLOSED(code, tenant_id, site_id):
    return False, "Assessment lineage is broken: {'selected_heads_other_model': 1}"


def client(reads, access=None, gate=OPEN) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_finding_router(reads, SCOPE.get, (Down,), gate=gate, **kwargs))
    return TestClient(app)


URL = f"/api/sites/KOBO-001/findings/{uuid4()}"
WINDOW = "/api/sites/KOBO-001/finding-windows/2026-10-19"


def body(revision_id: str = "r1") -> dict:
    return {"selection": {"revision_id": revision_id}, "relations": {"canonical_finding_id": "f1"},
            "revision": {"assessments": [{"assessment_revision_id": "a1"}],
                         "currentness": {"windows": [{"day": "2026-10-06"}]}}}


def test_unauthenticated_is_401_before_any_lookup() -> None:
    reads = Reads()
    response = client(reads, lambda request, code: 401).get(URL)
    assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
    assert reads.calls == []


def test_unauthorized_known_scope_is_403() -> None:
    response = client(Reads(), lambda request, code: 403).get(URL)
    assert response.status_code == 403 and response.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"


def test_unknown_site_is_404_and_unknown_root_is_404() -> None:
    assert client(Reads()).get(URL.replace("KOBO-001", "OTHER")).status_code == 404
    reads = Reads(body=None)
    assert client(reads).get(URL, params={"revision_id": str(uuid4())}).status_code == 404
    assert reads.calls[0][:2] == (TENANT, SITE)  # resolved inside the configured tenant


def test_unavailable_store_is_typed_503() -> None:
    response = client(Reads(error=Down("database down"))).get(URL)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"
    response = client(None).get(URL)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"


def test_default_access_names_its_development_basis() -> None:
    assert ACCESS_BASIS.startswith("DEVELOPMENT_TENANT_OPERATOR_CONTEXT")


def test_consecutive_basis_refreshes_group_only_as_a_hint() -> None:
    kinds = ["OPENED", "BASIS_REFRESHED", "BASIS_REFRESHED", "SUPPORT_CHANGED", "BASIS_REFRESHED"]
    summaries = [{"id": f"r{n}", "revision_no": n, "transition": t, "support_changed": t != "BASIS_REFRESHED"}
                 for n, t in enumerate(kinds, start=1)]
    groups = revision_groups(summaries)
    assert [(g["kind"], g["count"]) for g in groups] == [("REVISION", 1), ("BASIS_REFRESHED", 2),
                                                         ("REVISION", 1), ("BASIS_REFRESHED", 1)]
    assert groups[1]["revision_ids"] == ["r2", "r3"] and groups[1]["support_changed"] is False
    assert sum(g["count"] for g in groups) == len(summaries)


class TestWindowRouteMatrix:
    """Review C3: the `/finding-windows/{day}` route has the same 401/403/404/503 matrix."""

    def test_unauthenticated_is_401_before_any_lookup(self) -> None:
        reads = Reads()
        response = client(reads, lambda request, code: 401).get(WINDOW)
        assert response.status_code == 401 and response.headers["www-authenticate"] == "Bearer"
        assert reads.calls == []

    def test_unauthorized_known_scope_is_403(self) -> None:
        reads = Reads()
        response = client(reads, lambda request, code: 403).get(WINDOW)
        assert response.status_code == 403 and response.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
        assert reads.calls == []

    def test_unknown_site_is_404(self) -> None:
        assert client(Reads()).get(WINDOW.replace("KOBO-001", "OTHER")).status_code == 404

    def test_unavailable_store_is_typed_503(self) -> None:
        response = client(Reads(error=Down("database down"))).get(WINDOW)
        assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"
        response = client(None).get(WINDOW)
        assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"


class TestPerformanceCutoverGate:
    """Q19: the S3 Performance cutover gate guards current Finding reads and the window read."""

    def test_closed_gate_refuses_the_window_read(self) -> None:
        reads = Reads(body={"state": "NO_FINDING"})
        response = client(reads, gate=CLOSED).get(WINDOW)
        assert response.status_code == 409 and response.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        assert "lineage is broken" in response.json()["detail"]["message"] and reads.calls == []

    def test_closed_gate_refuses_the_default_finding_read(self) -> None:
        reads = Reads(body=body())
        response = client(reads, gate=CLOSED).get(URL)
        assert response.status_code == 409 and response.json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
        assert reads.calls == []

    def test_closed_gate_serves_a_pinned_revision_as_audit_material_without_s3_links(self) -> None:
        reads = Reads(body=body())
        response = client(reads, gate=CLOSED).get(URL, params={"revision_id": str(uuid4())})
        assert response.status_code == 200
        out = response.json()
        assert reads.calls[0][-1] is False  # source_open=False: no S3 currentness read
        assert out["audit_only"]["non_current"] is True and out["source_gate"]["permitted"] is False
        assert out["links"]["assessment_revisions"] == {} and out["links"]["windows"] == {}
        assert out["links"]["performance"]["status"] == "CLOSED" and "409" in out["links"]["performance"]["note"]

    def test_open_gate_links_the_selected_s3_revision_and_window(self) -> None:
        out = client(Reads(body=body())).get(URL).json()
        assert out["audit_only"] is None and out["links"]["performance"]["status"] == "OPEN"
        assert out["links"]["assessment_revisions"]["a1"].endswith("/performance/dispatch/revisions/a1")
        assert out["links"]["windows"]["2026-10-06"].endswith("/performance/dispatch/windows/2026-10-06")

    def test_an_unconfigured_gate_is_closed(self) -> None:
        app = FastAPI()
        app.include_router(build_finding_router(Reads(body=body()), SCOPE.get, (Down,)))
        assert TestClient(app).get(WINDOW).status_code == 409

    def test_an_unreadable_gate_is_typed_503(self) -> None:
        def broken(code, tenant_id, site_id):
            raise Down("comparison store down")
        response = client(Reads(body=body()), gate=broken).get(URL)
        assert response.status_code == 503 and response.json()["detail"]["code"] == "FINDING_STORE_UNAVAILABLE"


def test_w301_source_provenance_wrappers_pass_public_blocks_and_keep_fail_closed_fallbacks() -> None:
    """W3-01 Run 3 q3: the Finding API wrappers carry the composed resolver's W1-compatible public block verbatim
    (the consequence block keeps its string Finding ID); unwired, failing or missing revisions keep the old
    fail-closed `unresolved` keys and never gain public keys."""
    from assetops_backend.evidence.provenance_read import consequence_provenance, finding_provenance

    t, s, fr, cid = uuid4(), uuid4(), uuid4(), uuid4()
    block = {"state": "REGISTERED_SIMULATION", "classification": "REGISTERED_SIMULATION", "source_ids": ["g"],
             "evidence_ids": ["e"], "basis_sha256": "sha256:" + "a" * 64, "reasons": [], "detail": {},
             "finding_revision_id": fr, "consequence_revision_id": cid}

    class Public:
        def finding_revision(self, *a):
            return block

        def consequence_revision(self, *a):
            return block

    class Broken:
        def finding_revision(self, *a):
            raise RuntimeError("down")

        consequence_revision = finding_revision

    class Missing:
        def finding_revision(self, *a):
            return None

        consequence_revision = finding_revision

    assert finding_provenance(Public(), t, s, fr) == block
    assert consequence_provenance(Public(), t, s, fr, cid) == {**block, "finding_revision_id": str(fr)}
    public_keys = {"classification", "source_ids", "evidence_ids", "basis_sha256", "detail"}
    for resolver, code in ((None, "PROVENANCE_NOT_WIRED"), (Broken(), "PROVENANCE_UNREADABLE"),
                           (Missing(), "PROVENANCE_REVISION_NOT_FOUND")):
        for fallback in (finding_provenance(resolver, t, s, fr), consequence_provenance(resolver, t, s, fr, cid)):
            assert fallback["state"] == "UNKNOWN" and fallback["reasons"][0]["code"] == code
            assert not (public_keys & set(fallback))
