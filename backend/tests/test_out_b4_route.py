"""OUT-B4 addendum 4 (#2, #7): the outcome routes admit a Site only when both the Site read seam (`access`) and the
Work read seam (`work_access`) admit it, and a cold or EV Site only when that domain's disclosure admits it. The
board answers the first refusal with its 401/403 (disclosure: the cold/EV gate's own 403 code); the estate summary
omits the refused Site. Fake registry, estate scope and board service; no database."""
from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.outcome_api import build_outcome_router

T = uuid4()
SITES = {code: SimpleNamespace(tenant_id=T, id=uuid4(), site_code=code, name=code, site_type=kind, timezone=None)
         for code, kind in (("KOBO-001", "MINIGRID"), ("COLD-LAB-001", "COLDCHAIN"), ("EV-LAB-001", "EV_CHARGING"))}
WINDOW = "from=2026-10-01T00:00:00Z&to=2026-10-08T00:00:00Z"


class Registry:
    def __init__(self) -> None:
        self.calls = 0

    def tenant(self):
        self.calls += 1
        return SimpleNamespace(id=T)

    def imported(self, code):
        self.calls += 1
        return SITES.get(code)


class Estate:
    def scope(self, tenant, parsed, admit):  # the estate convention: refused Sites are simply absent
        return {"sites": [{"site_code": c} for c in SITES if admit(c)]}


class Service:
    def __init__(self) -> None:
        self.boards: list[str] = []

    def board(self, ref, **kw):
        self.boards.append(ref.site_code)
        return {"site_code": ref.site_code, "read_state": "OK", "_short_values": {}}

    def summary(self, sites, lo, hi, known_at):
        return {"sites": [s.site_code for s in sites]}


def client(**kw) -> tuple[TestClient, Service]:
    service = Service()
    registry = Registry()
    app = FastAPI()
    app.include_router(build_outcome_router(service, registry, estate=Estate(), tenant=lambda: T, **kw))
    c = TestClient(app)
    c.registry = registry  # type: ignore[attr-defined]
    return c, service


def refuse(code: str):
    return lambda request, site_code: 403 if site_code == code else None


def test_defaults_admit_every_site() -> None:
    c, service = client()
    assert c.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06").status_code == 200
    assert c.get(f"/api/sites/COLD-LAB-001/outcome-board?{WINDOW}").status_code == 200
    assert c.get(f"/api/sites/EV-LAB-001/outcome-board?{WINDOW}").status_code == 200
    assert c.get(f"/api/estate/outcome-summary?{WINDOW}").json()["sites"] == list(SITES)


def test_work_access_refusal_is_403_before_lookup_and_omits_the_site() -> None:
    c, service = client(work_access=refuse("KOBO-001"))
    r = c.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
    assert service.boards == [] and c.registry.calls == 0  # L3: refused before any registry lookup
    assert c.get(f"/api/estate/outcome-summary?{WINDOW}").json()["sites"] == ["COLD-LAB-001", "EV-LAB-001"]
    # 401 from the Work seam while the Site seam admits
    c, _ = client(work_access=lambda request, code: 401)
    r = c.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06")
    assert r.status_code == 401 and r.json()["detail"]["code"] == "UNAUTHENTICATED"
    assert c.registry.calls == 0


def test_site_access_refusal_still_refuses() -> None:
    c, _ = client(access=refuse("EV-LAB-001"))
    assert c.get(f"/api/sites/EV-LAB-001/outcome-board?{WINDOW}").status_code == 403
    assert c.get(f"/api/estate/outcome-summary?{WINDOW}").json()["sites"] == ["KOBO-001", "COLD-LAB-001"]


def test_cold_disclosure_refusal_uses_the_cold_gate_code() -> None:
    c, service = client(cold_disclosure=lambda code, t, s: False)
    r = c.get(f"/api/sites/COLD-LAB-001/outcome-board?{WINDOW}")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "COLD_SOURCE_DISCLOSURE_FORBIDDEN"
    assert service.boards == []
    assert c.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06").status_code == 200
    assert c.get(f"/api/estate/outcome-summary?{WINDOW}").json()["sites"] == ["KOBO-001", "EV-LAB-001"]


def test_ev_disclosure_refusal_uses_the_ev_gate_code() -> None:
    seen = []
    c, service = client(ev_disclosure=lambda code, t, s: seen.append((code, t, s)) or False)
    r = c.get(f"/api/sites/EV-LAB-001/outcome-board?{WINDOW}")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "EV_SOURCE_DISCLOSURE_FORBIDDEN"
    assert seen[0] == ("EV-LAB-001", T, SITES["EV-LAB-001"].id)
    assert c.get(f"/api/estate/outcome-summary?{WINDOW}").json()["sites"] == ["KOBO-001", "COLD-LAB-001"]
