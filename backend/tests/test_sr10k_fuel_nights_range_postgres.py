"""SR-10k (rev 10b.4, D-SR.45): the fuel-check nights list over the date range, on real Postgres.

Reuses K5's router harness (`test_k5_fuel_night_api_postgres.Api` and its `kobo` fixture: an imported Site with
synthetic stored windows). Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc

if URL:
    from test_k5_fuel_night_api_postgres import kobo  # noqa: F401
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401


def _z(at: datetime) -> str:
    return at.astimezone(UTC).isoformat().replace("+00:00", "Z")


def test_range_filters_stored_nights_by_site_local_day(kobo) -> None:  # noqa: F811
    nights = [date(2026, 10, 3), date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 9)]
    for night in nights:
        kobo.put(night, "WITHIN_MARGIN", "-24.343", "24.343")

    utc = kobo.get("/fuel-balance/nights", **{"from": "2026-10-05T00:00:00Z", "to": "2026-10-07T00:00:00Z"})
    assert utc.status_code == 200, utc.text
    assert utc.json()["mode"] == "NIGHTS"
    assert [n["night_date"] for n in utc.json()["nights"]] == ["2026-10-05", "2026-10-06"]

    zone = ZoneInfo(kobo.fuel.tz)
    lo = datetime(2026, 10, 6, tzinfo=zone)
    local = kobo.get("/fuel-balance/nights", **{"from": _z(lo), "to": _z(lo + timedelta(days=4))}).json()
    assert [n["night_date"] for n in local["nights"]] == ["2026-10-06", "2026-10-09"]

    empty = kobo.get("/fuel-balance/nights", **{"from": "2026-10-20T00:00:00Z", "to": "2026-10-27T00:00:00Z"})
    assert empty.status_code == 200 and empty.json()["mode"] == "NIGHTS" and empty.json()["nights"] == []

    bad = kobo.get("/fuel-balance/nights", **{"from": "2026-10-05T00:00:00Z"})
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "INVALID_WINDOW"

    # No parameters: unchanged (the latest 14 nights ending at the last stored night).
    assert [n["night_date"] for n in kobo.get("/fuel-balance/nights").json()["nights"]] == [
        "2026-10-03", "2026-10-05", "2026-10-06", "2026-10-09"]
