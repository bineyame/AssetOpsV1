"""4b2 (spec `specs/4b-money-leaves/spec.md` §5 "Postgres"): the money leaves over the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Sites by 3A4's `NairobiSeeder` (imported; 3A4's file is not
edited). Expected values are spec §4.1's literals, asserted by the no-database file's checks (W2).

Mid-build Q2 (open; default applied): the fixture's `entered_by` `"test:4b"` is refused by migration 0063's
`commercial_intake_entered_by_check` (`service:<name>` or `person:<uuid>`), so Postgres ingests the same steps as
`PG_ENTERED_BY`. `entered_by` enters no figure; the no-database file keeps the spec's literal.
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

    import test_4b_money_leaves as nodb
    from assetops_backend.structure.composition import build_structure_read

PG_ENTERED_BY = "service:test-4b"


def _ingest(w) -> None:
    for step in nodb.fixture_steps():
        nodb.ingest(w, step["at"], step["batch"], PG_ENTERED_BY)


def test_pg_1_the_fixture_through_postgres(pgworld):  # noqa: F811
    _ingest(pgworld)
    nodb.check_kobo_october(pgworld)
    nodb.check_kisiwa_october(pgworld)
    nodb.check_mto_october(pgworld)
    nodb.check_portfolio(pgworld)


def test_pg_2_build_structure_read_reads_the_records(pgworld):  # noqa: F811
    _ingest(pgworld)
    service = build_structure_read(URL)
    try:
        values = service.read.site(nodb.site(pgworld, "KOBO-001"), "2026-10").values
    finally:
        service.dispose()
    revenue, contribution = values["revenue"], values["contribution"]
    assert (format(revenue.value, "f"), revenue.stated, revenue.evidence) == ("3458.00", True, "RECORDED")
    assert (contribution.value, format(contribution.value, "f"), contribution.evidence) == (
        Decimal("883.00"), "883.00", "RECORDED")
