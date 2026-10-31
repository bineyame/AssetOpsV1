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


def test_board_services_get_the_apps_finding_read_service() -> None:
    """LINK-LINEAGE U2: `main.py` hands the board the same `finding_reads` it builds for the Finding routes, and the
    composition stores it on `BoardServices.finding_reads` (the history port's service)."""
    import ast
    from pathlib import Path

    from assetops_backend.site_outcomes.composition import build_outcome_board_service

    tree = ast.parse(Path(main.__file__).read_text(encoding="utf-8"))
    assigned = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "finding_reads" for t in n.targets)]
    assert len(assigned) == 1 and "build_finding_read_service" in ast.unparse(assigned[0].value)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and getattr(n.func, "id", None) == "build_outcome_board_service")
    kw = {k.arg: k.value for k in call.keywords}
    assert isinstance(kw.get("finding_reads"), ast.Name) and kw["finding_reads"].id == "finding_reads"
    sentinel = object()
    service, dispose = build_outcome_board_service(None, finding_reads=sentinel)
    try:
        assert service.s.finding_reads is sentinel
    finally:
        dispose()
