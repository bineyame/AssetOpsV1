"""K10 v2 (build sheet DIESEL-1 §9t.3 item 3, ruling DIESEL-1-R3t): `PostgresChainRead.declared_none_days` on Postgres.

A day is declared absent only when exactly one Foundation revision (known at `k`) is in force at BOTH its local start
and its local end - 1 us, and neither declares a productive-use LOAD (`mini_depth.read.productive_loads`). Missing
or ambiguous setup, or a load at either bound, is never "none declared". One statement per call.
Authorized `*_test` database only (the `engine` fixture refuses anything else)."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_s1_bindings_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import event, text
    from test_s1_bindings_postgres import engine  # noqa: F401

    import pg_harness
    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead

ZONE = "Africa/Dar_es_Salaam"   # UTC+3, Kisiwa's zone shape
D1, D2, D3 = date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 28)
T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
K = datetime(2026, 11, 1, tzinfo=timezone.utc)
HOUSE = {"component_id": "HH-01", "component_type": "LOAD", "display_name": "Households",
         "properties": [{"property_key": "supply-use", "unit": "state", "value": "ESSENTIAL"}]}
MILL = {"component_id": "MILL-01", "component_type": "LOAD", "display_name": "Grain mill",
        "properties": [{"property_key": "supply-use", "unit": "state", "value": "PRODUCTIVE"}]}
NONE_DECLARED = {"components": [HOUSE]}
WITH_LOAD = {"components": [HOUSE, MILL]}


def local(d: date, hour: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, tzinfo=timezone.utc) - timedelta(hours=3)


@pytest.fixture(scope="module")
def world(engine):  # noqa: F811
    pg_harness.empty_tables(engine, ("foundation_revision", "source", "gateway", "asset", "site_import", "site",
                                     "tenant"))
    tenant = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:t, :slug, 'K10', now())"),
                  {"t": tenant, "slug": f"k10-{tenant.hex[:12]}"})
    port = PostgresChainRead(URL)
    try:
        yield engine, tenant, port
    finally:
        pg_harness.dispose(port)


def site(engine, tenant, *revisions) -> object:
    """A fresh MINIGRID Site with `revisions` = (content, valid_from, valid_to, recorded_at, superseded_at)."""
    s = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
            "origin, proposed_source_mode, created_at) VALUES (:s, :t, :code, lower(:code), 'Site', 'MINIGRID', "
            ":tz, 'ACTIVE', 'TEST', 'SIMULATED', now())"), {"s": s, "t": tenant, "code": f"K10-{s.hex[:8]}",
                                                             "tz": ZONE})
        for v, (content, vf, vt, rec, sup) in enumerate(revisions, start=1):
            c.execute(text(
                "INSERT INTO foundation_revision (id, tenant_id, site_id, version, valid_from, valid_to, recorded_at, "
                "superseded_at, schema_version, content, content_sha256, origin) VALUES (:id, :t, :s, :v, :vf, :vt, "
                ":rec, :sup, 1, CAST(:content AS jsonb), :sha, 'IMPORT')"),
                {"id": uuid4(), "t": tenant, "s": s, "v": v, "vf": vf, "vt": vt, "rec": rec, "sup": sup,
                 "content": json.dumps(content), "sha": hashlib.sha256(json.dumps(content).encode()).hexdigest()})
    return s


def call(port, tenant, s, days=(D1, D2, D3), measure="productive_kwh", known_at=K):
    return port.declared_none_days(tenant, s, measure, list(days), known_at)


def test_one_revision_without_productive_load_gives_the_days(world):
    engine, tenant, port = world
    s = site(engine, tenant, (NONE_DECLARED, T0, None, T0, None))
    assert call(port, tenant, s) == frozenset({D1, D2, D3})
    assert call(port, tenant, s, measure="critical_served") == frozenset()   # only productive_kwh


def test_one_revision_with_productive_load_gives_no_day(world):
    engine, tenant, port = world
    s = site(engine, tenant, (WITH_LOAD, T0, None, T0, None))
    assert call(port, tenant, s) == frozenset()


def test_no_revision_gives_no_day(world):
    engine, tenant, port = world
    s = site(engine, tenant)
    assert call(port, tenant, s) == frozenset()
    # a revision recorded after the cutoff is not known at k
    late = site(engine, tenant, (NONE_DECLARED, T0, None, K + timedelta(days=1), None))
    assert call(port, tenant, late) == frozenset()
    # validity starting mid-window: the earlier days have no covering revision
    mid = site(engine, tenant, (NONE_DECLARED, local(D2), None, T0, None))
    assert call(port, tenant, mid) == frozenset({D2, D3})


def test_two_overlapping_revisions_follow_r3t3(world):
    engine, tenant, port = world
    # A superseded after k and B current, both known at k, validity overlapping: R3t3 allows overlap, a mill vetoes
    s = site(engine, tenant, (NONE_DECLARED, T0, None, T0, K + timedelta(days=2)),
             (NONE_DECLARED, T0, None, T0 + timedelta(days=1), None))
    assert call(port, tenant, s) == frozenset({D1, D2, D3})
    m = site(engine, tenant, (NONE_DECLARED, T0, None, T0, K + timedelta(days=2)),
             (WITH_LOAD, T0, None, T0 + timedelta(days=1), None))
    assert call(port, tenant, m) == frozenset()


def test_r3t3_case_6_mid_day_mill_gives_no_day(world):
    engine, tenant, port = world
    s = site(engine, tenant, (NONE_DECLARED, T0, local(D2, 8), T0, None), (WITH_LOAD, local(D2, 8), local(D2, 14), T0, None),
             (NONE_DECLARED, local(D2, 14), None, T0, None))
    assert call(port, tenant, s, days=(D2,)) == frozenset()
    assert call(port, tenant, s) == frozenset({D1, D3})


def test_r3t3_case_7_mid_day_gap_gives_no_day(world):
    engine, tenant, port = world
    s = site(engine, tenant, (NONE_DECLARED, T0, local(D2, 8), T0, None), (NONE_DECLARED, local(D2, 14), None, T0, None))
    assert call(port, tenant, s, days=(D2,)) == frozenset()
    assert call(port, tenant, s) == frozenset({D1, D3})


def test_revision_change_inside_the_day_with_a_load_at_the_end_gives_no_day(world):
    engine, tenant, port = world
    change = local(D2, 12)   # midday local D2
    s = site(engine, tenant, (NONE_DECLARED, T0, change, T0, None), (WITH_LOAD, change, None, T0, None))
    assert call(port, tenant, s) == frozenset({D1})
    # the same change with no load on either side: each bound has exactly one revision declaring none
    t = site(engine, tenant, (NONE_DECLARED, T0, change, T0, None), (NONE_DECLARED, change, None, T0, None))
    assert call(port, tenant, t) == frozenset({D1, D2, D3})


def test_the_call_is_exactly_one_statement(world):
    engine, tenant, port = world
    s = site(engine, tenant, (NONE_DECLARED, T0, None, T0, None))
    seen: list[str] = []

    def count(conn, cursor, statement, *a):
        seen.append(statement)

    event.listen(port._engine, "before_cursor_execute", count)
    try:
        assert call(port, tenant, s) == frozenset({D1, D2, D3})
        assert len(seen) == 1, seen
        seen.clear()
        assert call(port, tenant, s, measure="avoidable_gen_min") == frozenset()
        assert seen == []   # a non-candidate measure reads nothing
        seen.clear()
        assert call(port, tenant, s, known_at=None) == frozenset({D1, D2, D3})   # k = clock_timestamp()
        assert len(seen) == 1
    finally:
        event.remove(port._engine, "before_cursor_execute", count)
