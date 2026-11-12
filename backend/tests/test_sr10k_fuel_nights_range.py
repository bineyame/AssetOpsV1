"""SR-10k (architect sequence rev 10b.4, D-SR.45): the Kisiwa fuel-check nights list over the date range, no database.

The nights route takes the date range's UTC instants `from`/`to` (both or neither, else 422 `INVALID_WINDOW`) and
lists the nights whose Site-local `night_date` is one of `chain.read.window_days(from, to, tz)`. The legacy date form
and the no-parameter default are unchanged. The store is an in-memory stub of the fuel-balance store's read methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.fuel_balance.night_read import FuelNightRead
from assetops_backend.fuel_balance_api import build_fuel_balance_router

UTC = timezone.utc
TANK = str(uuid4())
TENANT, SITE = uuid4(), uuid4()


@dataclass(frozen=True)
class Window:
    night_date: date
    state: str = "WITHIN_MARGIN"
    revision: int = 1


class Store:
    def __init__(self, nights: list[date], tz: str = "Africa/Dar_es_Salaam") -> None:
        self.every = [Window(d) for d in sorted(nights)]
        self.tz = tz
        self.calls: list[tuple[date, date]] = []

    def night_context(self, tenant_id: UUID, site_id: UUID):
        return self.tz, TANK, datetime(2026, 11, 12, tzinfo=UTC)

    def has_windows(self, tenant_id: UUID, site_id: UUID, known: datetime) -> bool:
        return bool(self.every)

    def windows(self, tenant_id, site_id, tank, lo: date, hi: date, known):
        self.calls.append((lo, hi))
        return [w for w in self.every if lo <= w.night_date < hi]

    def night_records_and_provenance(self, tenant_id, site_id, windows, known, records_of, link_rows):
        return [], {"source_provenance": [], "selected_source_provenance": [], "pending_source_provenance": []}

    def dispose(self) -> None:
        pass


def client(store: Store) -> TestClient:
    read = FuelNightRead(store=store, link_rows=None)
    app = FastAPI()
    scope = {"kisiwa-001": ("KISIWA-001", TENANT, SITE)}
    app.include_router(build_fuel_balance_router(read, lambda code: scope.get(code.lower())))
    return TestClient(app)


NIGHTS = [date(2026, 10, d) for d in (1, 5, 6, 7, 20)]
URL = "/api/sites/KISIWA-001/fuel-balance/nights"


def dates(body: dict) -> list[str]:
    return [n["night_date"] for n in body["nights"]]


def test_utc_midnight_range_lists_the_nights_of_its_days() -> None:
    store = Store(NIGHTS)
    r = client(store).get(URL, params={"from": "2026-10-05T00:00:00Z", "to": "2026-10-08T00:00:00Z"})
    assert r.status_code == 200, r.text
    assert r.json()["mode"] == "NIGHTS" and dates(r.json()) == ["2026-10-05", "2026-10-06", "2026-10-07"]
    assert store.calls == [(date(2026, 10, 5), date(2026, 10, 8))]


def test_site_local_midnight_range_names_the_site_local_days() -> None:
    # Kisiwa is UTC+3: local midnight 6 Oct is 21:00Z on 5 Oct; [6 Oct, 7 Oct) local is the one night of 6 Oct.
    store = Store(NIGHTS)
    r = client(store).get(URL, params={"from": "2026-10-05T21:00:00Z", "to": "2026-10-06T21:00:00Z"})
    assert r.status_code == 200, r.text
    assert dates(r.json()) == ["2026-10-06"]


def test_range_with_no_night_is_night_mode_with_an_empty_list() -> None:
    r = client(Store(NIGHTS)).get(URL, params={"from": "2026-10-10T00:00:00Z", "to": "2026-10-17T00:00:00Z"})
    assert r.status_code == 200 and r.json()["mode"] == "NIGHTS" and r.json()["nights"] == []


def test_site_without_windows_stays_none_under_a_range() -> None:
    r = client(Store([])).get(URL, params={"from": "2026-10-05T00:00:00Z", "to": "2026-10-08T00:00:00Z"})
    assert r.status_code == 200 and r.json()["mode"] == "NONE" and r.json()["nights"] == []


def test_31_days_allowed_and_32_refused() -> None:
    c = client(Store(NIGHTS))
    ok = c.get(URL, params={"from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z"})
    assert ok.status_code == 200 and dates(ok.json()) == [d.isoformat() for d in NIGHTS]
    r = c.get(URL, params={"from": "2026-10-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_WINDOW"


def test_range_refusals_are_invalid_window() -> None:
    c = client(Store(NIGHTS))
    for params in ({"from": "2026-10-05T00:00:00Z"}, {"to": "2026-10-05T00:00:00Z"},
                   {"from": "2026-10-05T00:00:00Z", "to": "2026-10-05T00:00:00Z"},
                   {"from": "2026-10-06T00:00:00Z", "to": "2026-10-05T00:00:00Z"},
                   {"from": "2026-10-05T00:00:00", "to": "2026-10-06T00:00:00Z"},
                   {"from": "2026-10-0xT00:00:00Z", "to": "2026-10-06T00:00:00Z"},
                   {"from": "2026-10-05T00:00:00Z", "to": "2026-10-06"}):
        r = c.get(URL, params=params)
        assert r.status_code == 422, params
        assert r.json()["detail"] == {"code": "INVALID_WINDOW",
                                      "message": "Choose up to 31 nights, with the first night before the last."}


def test_no_params_and_date_form_unchanged() -> None:
    store = Store(NIGHTS)
    c = client(store)
    default = c.get(URL).json()  # the latest 14 nights ending at the last stored night
    assert dates(default) == ["2026-10-07", "2026-10-20"]
    legacy = c.get(URL, params={"from": "2026-10-05", "to": "2026-10-07"}).json()
    assert dates(legacy) == ["2026-10-05", "2026-10-06"]
    r = c.get(URL, params={"from": "2026-10-05"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "FUEL_BALANCE_RANGE_INVALID"


def test_known_at_still_checked_in_range_form() -> None:
    r = client(Store(NIGHTS)).get(URL, params={"from": "2026-10-05T00:00:00Z", "to": "2026-10-08T00:00:00Z",
                                               "known_at": "not-a-time"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "INVALID_KNOWN_AT"
