"""3B3: the structure read over the real Postgres snapshot store and assumption store (spec §6).

World: the imported KOBO-001 Site (`test_s1_bindings_postgres.imported`), its Site-local October (Africa/Nairobi,
UTC+3) of stored `critical_served` day rows, and a diesel price revision whose `valid_from` (1 Sep 2026 00:00Z) is
before Kobo's local 1 October 00:00 (30 Sep 21:00Z), so it covers the whole Site-local month (P3). A Site with no
operating-calendar entry is stored as the snapshot builder writes it: a NOT_EXPECTED row each day
(`chain/builder.py`, `expected = bounds is not None`). The read goes through `build_structure_read`, the composition
the product uses. Needs ASSETOPS_TEST_DATABASE_URL (a routed `*_test` database), run under `heavy-slot.sh --db`.
"""

from __future__ import annotations

import hashlib
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401

    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.ports import SiteRef, SnapshotRow
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.sources import SOURCE_STATE

UTC = timezone.utc
TZ = "Africa/Nairobi"
OCT = [date(2026, 10, d) for d in range(1, 32)]
MONTH = "2026-10"


def _row(site: "SiteRef", day: date, grade: str = "COMPLETE", unserved: str | None = "2.5") -> "SnapshotRow":
    value = None if unserved is None else {"served_kwh": "40", "demand_kwh": "42.5", "unserved_kwh": unserved}
    return SnapshotRow(site.tenant_id, site.site_id, day, "SITE", "SITE", "critical_served", "MEASURED", 1,
                       grade != "NOT_EXPECTED", 86400, 86400 if grade == "COMPLETE" else 0, "0", grade, value, None,
                       "p1", "c1", 1, hashlib.sha256(f"{site.site_code}{day}".encode()).hexdigest())


def _site(store, code: str = "KOBO-001") -> "SiteRef":  # noqa: F811
    result = imported(store, code)
    return SiteRef(result.tenant.id, result.site.id, code, "MINIGRID", TZ)


def _snapshots(engine, rows) -> None:  # noqa: F811
    snaps = PostgresSnapshotStore(engine=engine)
    for row in rows:
        snaps.append(row)


def _price(site: "SiteRef", valid_from: datetime) -> None:
    prices = PostgresAssumptionStore(URL)
    try:
        prices.publish(site.tenant_id, site.site_id, Publication(
            assumption_key="diesel_price_per_litre", currency="USD", value=Decimal("1.30"),
            basis="AUTHORED_ESTIMATE", source_reference="3B3 fixture", valid_from=valid_from, valid_to=None,
            change_kind="INITIAL", correction_reason=None, expected_prior_revision_id=None,
            idempotency_key=f"3b3-{uuid4()}", channel="SYSTEM_CLI", provenance={"service": "test"}), SYSTEM_PUBLISHER)
    finally:
        prices.dispose()


@pytest.fixture()
def service():
    built = build_structure_read(URL)
    yield built
    built.dispose()


def test_a_closed_fully_covered_month_and_a_declared_price(store, engine, service):  # noqa: F811
    kobo = _site(store)
    _snapshots(engine, [_row(kobo, d) for d in OCT])
    _price(kobo, datetime(2026, 9, 1, tzinfo=UTC))
    result = service.read.site(kobo, MONTH)
    assert (result.structure_key, result.structure_version) == ("MINI_GRID", 4)  # 4a: registry v4
    unserved = result.values["unserved_critical_kwh"]
    assert unserved.value == Decimal("77.5") and unserved.evidence == "MEASURED"
    assert (unserved.coverage.covered, unserved.coverage.expected) == (31, 31)
    diesel = result.values["diesel_price"]
    assert diesel.value == Decimal("1.30") and diesel.evidence == "ESTIMATED" and diesel.currency == "USD"
    assert diesel.missing.carried_as == "ASSUMPTION" and diesel.sources[0].startswith("assumption:")
    assert diesel.missing.assumption == "Declared diesel price per litre, not a fuel invoice"
    assert result.values["period_days"].value == 31
    states = SOURCE_STATE["MINI_GRID"]
    for factor_id, state in states.items():
        if state == "NOT_CONNECTED":
            assert result.values[factor_id].value is None, factor_id
            assert result.values[factor_id].missing.cause == "NOT_CONNECTED", factor_id
    contribution = result.values["contribution"]
    assert contribution.value is None and contribution.evidence == "NOT_AVAILABLE"
    assert {"om", "staff", "tariff", "necessary_l"} <= set(contribution.missing_leaves)
    assert result.values["productive_tariff"].missing.note == "NO_PRICE"


def test_one_missing_day_leaves_the_month_without_a_value(store, engine, service):  # noqa: F811
    kobo = _site(store)
    _snapshots(engine, [_row(kobo, d) for d in OCT if d.day != 17])
    unserved = service.read.site(kobo, MONTH).values["unserved_critical_kwh"]
    assert unserved.value is None and unserved.missing.cause == "NOT_RECEIVED"
    assert (unserved.coverage.covered, unserved.coverage.expected) == (30, 31)
    assert unserved.coverage.grades["NO_DATA"] == 1


def test_a_mid_month_price_revision_gives_no_value(store, engine, service):  # noqa: F811
    kobo = _site(store)
    _price(kobo, datetime(2026, 10, 15, tzinfo=UTC))
    diesel = service.read.site(kobo, MONTH).values["diesel_price"]
    assert diesel.value is None and diesel.missing.note == "PRICE_SPANS_WINDOW"
    assert diesel.missing.cause == "NOT_CONNECTED" and diesel.missing.carried_as is None


def test_a_site_with_no_operating_calendar_is_not_connected(store, engine, service):  # noqa: F811
    other = _site(store, "MTO-001")
    _snapshots(engine, [_row(other, d, "NOT_EXPECTED", None) for d in OCT])
    unserved = service.read.site(other, MONTH).values["unserved_critical_kwh"]
    assert unserved.value is None and unserved.missing.cause == "NOT_CONNECTED"
    assert unserved.coverage.expected == 0


def test_window_price_selection_equals_the_diesel_port_on_the_same_rows(store):  # noqa: F811
    from assetops_backend.financials import fuel_cost
    from assetops_backend.financials.composition import build_trial_comparison_ports, build_window_price_selection

    kobo = _site(store)
    _price(kobo, datetime(2026, 9, 1, tzinfo=UTC))
    start, end = datetime(2026, 9, 30, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC)
    known = datetime.now(UTC)  # the revision is recorded now
    new = build_window_price_selection(URL)
    old = build_trial_comparison_ports(URL)
    try:
        got = new.select(kobo.tenant_id, kobo.site_id, fuel_cost.PRICE_KEY, start, end, known)
        assert got.state == "PRICED"
        assert got == old.price_selection(kobo.tenant_id, kobo.site_id, start, end, known)
    finally:
        new.dispose()
        old.store.dispose()
