"""5b (spec `specs/5b-attribution/spec.md` §6 "Postgres"): the bridge over the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Sites by 3A4's `NairobiSeeder`; the fixtures through
`PostgresCommercialStore` (3A4's `pgworld`, imported). Expected values are spec §5.2's literals, asserted by the
no-database file's checks (W2).
"""
from __future__ import annotations

import os
from decimal import Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_3a4_commercial_months_postgres import pgworld  # noqa: F401

    import test_5a_targets as t5a
    import test_5b_attribution as nodb
    from assetops_backend.structure.attribution.composition import build_bridge_read


def test_pg_1_site_bridges_and_portfolio(pgworld):  # noqa: F811 - tests 6 and 7, `BridgeRead` with clock READ_AT
    w = nodb.load_lakeside(pgworld)
    read = nodb.bridge_read(w)
    for code in nodb.CODES:
        nodb.check_site(read.site(nodb.ref(w, code), nodb.OCT), code, w)
    nodb.check_portfolio(nodb.lakeside_portfolio(w), w)


def test_pg_2_build_bridge_read(pgworld):  # noqa: F811 - the real wiring
    w = nodb.load_lakeside(pgworld)
    r = t5a.refs(w)
    service = build_bridge_read(URL)
    try:
        pb = service.read.portfolio(w["tid"], [r[c] for c in nodb.CODES], "2026-10")
    finally:
        service.dispose()
    effect = pb.rows["contribution"]["contribution"].effect
    assert (effect, format(effect, "f")) == (Decimal("-852.00"), "-852.00")
