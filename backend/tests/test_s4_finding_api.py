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
        self.calls.append((tenant_id, site_id, finding_id, revision_id))
        if self.error:
            raise self.error
        return self.body


def client(reads, access=None) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    app.include_router(build_finding_router(reads, SCOPE.get, (Down,), **kwargs))
    return TestClient(app)


URL = f"/api/sites/KOBO-001/findings/{uuid4()}"


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
