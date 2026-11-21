"""5c unit 2 (spec sections 4.1 and 4.2, test 8; D-5C.7, PF6): `GET /api/portfolio/month` with injected reads.

The read is the real `DeepDiveRead` over World A's served snapshot (unit 1's `world("A")`, 3B7a in memory), a
reconciliation fake that answers unit 1's organisation standing and records how it was asked, and the not-connected
actions port. Every English literal is written by hand from spec section 2.5 (with PF5's example slot) and 3C0a's
`person.person_required`; the 200 body is unit 1's World A fixture.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from assetops_backend.accounts.model import COOKIE
from assetops_backend.deep_dive import composition as C
from assetops_backend.deep_dive.actions import NotConnectedActions
from assetops_backend.deep_dive.read import DeepDiveRead
from assetops_backend.deep_dive_api import build_deep_dive_router
from assetops_backend.sites.foundation_records import TenantRef
from assetops_backend.structure_snapshot.model import Served
from test_5c_deep_dive_view import AS_OF, FIXTURE, NAMES, NOT_MATCHED, world

ROUTE = "/api/portfolio/month"
LAKESIDE = TenantRef(UUID("5c000000-0000-4000-8000-00000000a001"), "lakeside-power", "Lakeside Power")
BAD_MONTH = {"code": "BAD_MONTH", "text": "Write the month as YYYY-MM, like 2026-10."}
UNAVAILABLE = {"code": "DEEP_DIVE_UNAVAILABLE", "text": "The month's figures cannot be read right now."}
PERSON_REQUIRED = {"code": "PERSON_REQUIRED", "text": "Sign in to continue."}


class Snapshots:
    """3B7a's `SnapshotRead.portfolio` over World A, served at the fixture's instant; records each ask."""

    def __init__(self, fault: Exception | None = None) -> None:
        self.asked: list = []
        self.fault = fault

    def portfolio(self, tenant_id, month):
        self.asked.append((tenant_id, month))
        if self.fault is not None:
            raise self.fault
        served, _, _ = world("A")
        return served if month == "2026-10" else Served("NO_SNAPSHOT", None, None, None)


class Reconciliation:
    def __init__(self) -> None:
        self.asked: list = []

    def standing(self, tenant_id, site_id, period, *, known_at=None):
        self.asked.append((tenant_id, site_id, period, known_at))
        return NOT_MATCHED


class Registry:
    def __init__(self, tenant: TenantRef | None) -> None:
        self._tenant = tenant

    def tenant(self):
        return self._tenant

    def imported_sites(self):
        return tuple(SimpleNamespace(site_code=c, name=n) for c, n in NAMES.items())


def principal(tenant_id: UUID):
    return SimpleNamespace(person_id=UUID(int=7), tenant_id=tenant_id, display_name="Fiona")


class Accounts:
    def __init__(self) -> None:
        self.people = {"ours": principal(LAKESIDE.id), "theirs": principal(UUID(int=99))}

    def resolve(self, token):
        return self.people.get(token) if token else None


def client(*, tenant: TenantRef | None = LAKESIDE, read="world", real_data: bool = False, snapshots=None,
           accounts=None) -> TestClient:
    snapshots = snapshots if snapshots is not None else Snapshots()
    recon = Reconciliation()
    if read == "world":
        read = DeepDiveRead(snapshots, recon, NotConnectedActions(), lambda: AS_OF)
    app = FastAPI()
    app.state.site_registry = Registry(tenant)
    app.include_router(build_deep_dive_router(read, accounts=accounts if accounts is not None else Accounts(),
                                              real_data=real_data, unavailable=(OperationalError,)))
    c = TestClient(app)
    c.snapshots, c.recon = snapshots, recon
    return c


def no_store(response) -> bool:
    return response.headers.get("cache-control") == "no-store"


def test_8_world_a_is_the_fixture() -> None:
    c = client()
    got = c.get(ROUTE, params={"month": "2026-10"})
    assert got.status_code == 200 and no_store(got)
    assert got.json() == json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Section 4.1: one organisation standing, read at the snapshot's `as_of` (D-3A7.9); no Site standing.
    assert c.recon.asked == [(LAKESIDE.id, None, "2026-10", AS_OF)]
    assert c.snapshots.asked == [(LAKESIDE.id, "2026-10")]


def test_8_no_month_is_the_month_before_the_clock() -> None:
    c = client()
    got = c.get(ROUTE)
    assert got.status_code == 200 and got.json()["month"] == "2026-10"
    jan = client(read=DeepDiveRead(Snapshots(), Reconciliation(), NotConnectedActions(),
                                   lambda: datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)))
    assert jan.get(ROUTE).json()["month"] == "2026-11"
    new_year = Snapshots()
    read = DeepDiveRead(new_year, Reconciliation(), NotConnectedActions(),
                        lambda: datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc))
    answer = client(read=read).get(ROUTE)
    assert answer.json()["month"] == "2026-12" and answer.json()["state"] == "NO_SNAPSHOT"


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "26-10", "2026-10-01", "2026/10", " 2026-10",
                                   "2026-10\n", ""])
def test_8_a_bad_month_is_422(month) -> None:
    c = client()
    got = c.get(ROUTE, params={"month": month})
    assert (got.status_code, got.json()) == (422, BAD_MONTH) and no_store(got)
    assert c.snapshots.asked == []


def test_8_no_tenant_or_no_read_is_503() -> None:
    for c in (client(tenant=None), client(read=None)):
        got = c.get(ROUTE, params={"month": "2026-10"})
        assert (got.status_code, got.json()) == (503, UNAVAILABLE) and no_store(got)


def test_8_a_store_fault_is_503() -> None:
    c = client(snapshots=Snapshots(fault=OperationalError("SELECT", {}, Exception("down"))))
    got = c.get(ROUTE, params={"month": "2026-10"})
    assert (got.status_code, got.json()) == (503, UNAVAILABLE) and no_store(got)


def test_8_real_data_needs_a_person_of_the_tenant() -> None:  # plant P10
    c = client(real_data=True)
    for cookies in ({}, {COOKIE: "nobody"}, {COOKIE: "theirs"}):
        c.cookies.clear()
        for name, value in cookies.items():
            c.cookies.set(name, value)
        got = c.get(ROUTE, params={"month": "2026-10"})
        assert (got.status_code, got.json()) == (401, PERSON_REQUIRED) and no_store(got), cookies
    assert c.snapshots.asked == []
    c.cookies.set(COOKIE, "ours")
    got = c.get(ROUTE, params={"month": "2026-10"})
    assert got.status_code == 200 and no_store(got)
    assert got.json() == json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_8_real_data_off_needs_no_person() -> None:  # RC7: the rehearsed tenant, the executive not signed in
    got = client(real_data=False).get(ROUTE, params={"month": "2026-10"})
    assert got.status_code == 200


def test_8_composition_disposes_all_three(monkeypatch) -> None:
    disposed: list[str] = []
    snapshot = SimpleNamespace(read="snapshots", dispose=lambda: disposed.append("snapshot"))
    monkeypatch.setattr(C, "build_structure_snapshot", lambda url: snapshot)
    monkeypatch.setattr(C, "build_commercial_reconciliation",
                        lambda url: ("reconciliation", lambda: disposed.append("reconciliation")))

    class Actions(NotConnectedActions):
        def dispose(self) -> None:
            disposed.append("actions")

    monkeypatch.setattr(C, "NotConnectedActions", Actions)
    read, dispose = C.build_deep_dive_read("postgresql://x/assetops_test")
    assert isinstance(read, DeepDiveRead)
    assert disposed == []
    dispose()
    assert sorted(disposed) == ["actions", "reconciliation", "snapshot"]
    disposed.clear()

    def broken(url):
        raise RuntimeError("no reconciliation")
    monkeypatch.setattr(C, "build_commercial_reconciliation", broken)
    with pytest.raises(RuntimeError):
        C.build_deep_dive_read("postgresql://x/assetops_test")
    assert disposed == ["snapshot"]  # never leak the first service when the second builder raises


def test_8_create_app_mounts_the_route(monkeypatch) -> None:
    from assetops_backend.main import create_app

    monkeypatch.delenv("DATABASE_URL", raising=False)
    got = TestClient(create_app()).get(ROUTE, params={"month": "2026-10"})
    assert (got.status_code, got.json()) == (503, UNAVAILABLE) and no_store(got)
