"""OUT-B4 review M1: `main.create_app` binds the outcome router's `work_access` to `site_read_access` (addendum 4 #2).
Composed through the product app, as `test_r373_request_access.py` does, so dropping the binding in `main.py` fails
this test. No database: the board route refuses before any lookup (`outcome_api.py`)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from assetops_backend import main
from test_r373_request_access import Grant


def test_board_route_refuses_a_site_the_site_read_grant_does_not_cover(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ASSETOPS_WORK_CURSOR_KEY_HEX", "a7" * 32)
    client = TestClient(main.create_app(site_read_access=Grant("COLD-LAB-001")))
    r = client.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
