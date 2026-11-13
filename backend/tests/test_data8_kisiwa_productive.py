"""DATA-8 (D-17N.4, K10/K11; owner "both" 2026-11-12): Kisiwa's cold store and water pump are productive users, and the
Site has a declared price per kWh. No database: the declaration is pinned on the in-memory Foundation store by
`test_k1_kisiwa_fixtures.py::test_register_in_on_the_in_memory_store`; here the price publication's commands. The
Postgres proof is the VPS scratch prepare named in `.agent/DATA-17N-packet.md`."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import demo_combined_kisiwa as kis

AT = datetime(2026, 10, 29, 10, 30, tzinfo=timezone.utc)


def test_the_productive_users_are_the_cold_store_and_the_pump() -> None:
    assert kis.SUPPLY_USES == {"load-clinic": "PRODUCTIVE", "load-res": "HOUSEHOLD", "load-mill": "PRODUCTIVE"}


def test_the_price_fixture_is_kobos_productive_price() -> None:
    import demo_combined_kobo as kobo

    assert kis.FIXTURE_PRODUCTIVE_PRICE == kobo.FIXTURE_PRODUCTIVE_PRICE
    doc = json.loads(kis.FIXTURE_PRODUCTIVE_PRICE.read_text(encoding="utf-8"))
    assert doc["assumption_key"] == "productive_use_price_per_kwh"
    [v1] = [s for s in doc["steps"] if s["step"] == "v1"]
    assert (v1["currency"], v1["value"]) == ("USD", "0.25")


def test_publish_price_publishes_diesel_then_productive_for_kisiwa(monkeypatch) -> None:
    calls: list[list[str]] = []
    clocks: list[datetime] = []

    class Store:
        def __init__(self, url, test_recorded_clock_override):
            clocks.append(test_recorded_clock_override())

    import assetops_backend.financials.adapters.postgres_assumption_store as pas
    import assetops_backend.publish_assumption as pa
    import pg_harness

    monkeypatch.setattr(pas, "PostgresAssumptionStore", Store)
    monkeypatch.setattr(pa, "main", lambda argv, store: calls.append(argv) or 0)
    monkeypatch.setattr(pg_harness, "dispose", lambda *a, **k: None)
    kis.publish_price("postgresql://unused", AT)
    assert clocks == [AT]
    assert calls == [["fixture", "--site", "KISIWA-001", "--file", str(f), "--step", "v1"]
                     for f in (kis.FIXTURE_PRICES, kis.FIXTURE_PRODUCTIVE_PRICE)]


def test_a_failed_productive_price_stops_the_build(monkeypatch) -> None:
    import pytest

    import assetops_backend.financials.adapters.postgres_assumption_store as pas
    import assetops_backend.publish_assumption as pa
    import pg_harness

    monkeypatch.setattr(pas, "PostgresAssumptionStore", lambda url, test_recorded_clock_override: object())
    monkeypatch.setattr(pa, "main", lambda argv, store: 2 if "productive" in argv[4] else 0)
    monkeypatch.setattr(pg_harness, "dispose", lambda *a, **k: None)
    with pytest.raises(SystemExit, match="productive-use price v1 publication failed"):
        kis.publish_price("postgresql://unused", AT)
