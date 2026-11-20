"""5a (spec `specs/5a-targets/spec.md` §6 "Postgres"): the target read over the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Sites are inserted by 3A4's `NairobiSeeder`.
"""
from __future__ import annotations

import os
from decimal import Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import test_3a4_commercial_months as months_nodb
    import test_5a_targets as nodb
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.months import CommercialMonths
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.structure.targets.composition import build_target_read
    from test_3a1_commercial_service import Clock, make_world
    from test_3a4_commercial_months_postgres import NairobiSeeder


#: Workaround (mid-build Q2): Postgres refuses the fixture's step-1 `entered_by` `loader:ds3`
#: (`commercial_intake_entered_by_check`: `service:<name>` or `person:<uuid>`), so step 1 is entered under this name
#: here; the in-memory file keeps the spec's literal.
PG_LOADER = "service:ds3-loader"


@pytest.fixture()
def pgworld(store, engine):  # noqa: F811 - `store` empties the tenant closure, the commercial tables included
    owned = PostgresCommercialStore(URL)
    w = make_world(NairobiSeeder(engine))
    clock = Clock()
    w = dict(w, store=owned, clock=clock, svc=CommercialRecords(owned, clock=clock),
             tid=w["tenants"]["lakeside-power"], months=CommercialMonths(owned, clock=lambda: months_nodb.READ_AT))
    yield nodb.load(w, names={nodb.LOADER: PG_LOADER})
    owned.dispose()


def test_pg_1_kobo_budget_lines(pgworld) -> None:  # test 1(a)
    nodb.check_1a(pgworld, PG_LOADER)


def test_pg_3_site_targets(pgworld) -> None:  # test 3(a)
    for code in nodb.CODES:
        nodb.check_site_tables(pgworld, code)


def test_pg_6_portfolio(pgworld) -> None:  # test 6
    nodb.check_portfolio(pgworld)


def test_pg_composition(pgworld) -> None:  # build_target_read over the real wiring
    service = build_target_read(URL)
    try:
        st = service.read.site(nodb.refs(pgworld)["KOBO-001"], nodb.OCT)
    finally:
        service.dispose()
    fv = st.structure.values["contribution"]
    assert (fv.value, fv.evidence) == (Decimal("1445.00"), "DECLARED")
