"""5c unit 2 (spec section 4.1, test 9; D-3A7.9, D-5C.4): the month read over the Postgres stores.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. World A (5b section 5.2) through 3A4's `pgworld` and 3A1's service;
3A7's statements through `CommercialReconciliation.record`; 3B7a's builder and read over
`PostgresStructureSnapshotStore`. One settable clock is 3A7's `months.clock()`, the snapshot builder's and the read's.
Expected values are unit 1's World A fixture and hand-written literals (W2).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_3a4_commercial_months_postgres import pgworld  # noqa: F401

    import test_3b7a_structure_snapshot as t3
    import test_5b_attribution as t5b
    from assetops_backend.commercial.months import CommercialMonths
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.deep_dive.actions import NotConnectedActions
    from assetops_backend.deep_dive.composition import build_deep_dive_read
    from assetops_backend.deep_dive.read import DeepDiveRead
    from assetops_backend.sites.foundation_records import TenantRef
    from assetops_backend.structure.reconciliation import CommercialReconciliation
    from assetops_backend.structure_snapshot.adapters.postgres_structure_snapshot_store import \
        PostgresStructureSnapshotStore
    from assetops_backend.structure_snapshot.build import SnapshotBuilder
    from assetops_backend.structure_snapshot.composition import build_structure_snapshot
    from assetops_backend.structure_snapshot.kinds import StoreHeldKinds
    from assetops_backend.structure_snapshot.read import SnapshotRead
    from test_3a7_reconciliation import FIONA
    from test_5c_deep_dive_view import FIXTURE, NAMES


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 19, hour, minute, tzinfo=timezone.utc)


#: Keys of the payload that name the read's instants; every other key is World A's fixture.
TIMED = ("as_of", "as_of_text", "status_line")
A_WORDS = ["Estimated, not yet reconciled", "Estimated, not yet reconciled", None, None,
           "Emulated, not yet reconciled", "Emulated, not yet reconciled", "Estimated, not yet reconciled",
           "Emulated, not yet reconciled", "Estimated, not yet reconciled", "Emulated, not yet reconciled",
           "Estimated, not yet reconciled", None, None]
B_WORDS = ["Estimated", "Estimated", None, None, "Emulated", "Emulated", "Estimated", "Emulated", "Estimated",
           "Emulated", "Estimated", None, None]


def money_words(v: dict) -> list:
    """Every `word` of the tiles, the bridge's steps, the cash line and the outcome cards, in that order."""
    return ([t["word"] for t in v["tiles"]] + [s["word"] for g in v["bridge"]["groups"] for s in g["steps"]]
            + [v["cash"]["word"]] + [o["word"] for o in v["outcomes"]])


@pytest.fixture()
def lakeside(pgworld):  # noqa: F811
    clock = t3.Clock(t3.AS_OF)
    w = dict(pgworld, clock=clock, svc=CommercialRecords(pgworld["store"], clock=clock),
             months=CommercialMonths(pgworld["store"], clock=clock))
    t5b.load_lakeside(w)
    snapshots = PostgresStructureSnapshotStore(URL)
    r = t3.fresh(w)
    kinds = StoreHeldKinds(w["store"])
    recon = CommercialReconciliation(w["months"], w["store"])
    builder = SnapshotBuilder(r.actual, r.targets, r.lines, snapshots, kinds, t3.RULES_A, clock)
    read = DeepDiveRead(SnapshotRead(snapshots, w["months"], kinds, t3.RULES_A, clock), recon, NotConnectedActions(),
                        clock)
    tenant = TenantRef(w["tid"], "lakeside-power", "Lakeside Power")
    yield dict(w=w, clock=clock, recon=recon, builder=builder, read=read, tenant=tenant)
    snapshots.dispose()


def record(x, when: datetime, *, revenue: str, fuel: str):
    x["clock"].now = when
    return x["recon"].record(x["w"]["tid"], FIONA, site_code=None, period="2026-10", currency="USD", revenue=revenue,
                             fuel_cost=fuel, source_ref="Management accounts, October 2026", by_script=True)


def build(x, when: datetime) -> None:
    x["clock"].now = when
    x["builder"].build(x["w"]["tid"], t3.refs(x["w"])[:3], t3.OCT, built_by=t3.BY)


def read(x, when: datetime) -> dict:
    x["clock"].now = when
    return x["read"].month(x["tenant"], "2026-10", NAMES)


def test_9_the_standing_is_read_at_the_snapshots_instant(lakeside) -> None:  # plant P3
    x = lakeside
    record(x, at(10), revenue="9700.00", fuel="5100.00")  # S1, the finance lead
    build(x, at(11))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    # (a) read at 11:30: World A's standing and money words, as of the build.
    a = read(x, at(11, 30))
    assert (a["state"], a["as_of"]) == ("SERVED", "2026-11-19T11:00:00Z")
    assert a["as_of_text"] == "Figures as of 19 November 2026, 11:00 UTC."
    assert a["status_line"] == ("Figures as of 19 November 2026, 11:00 UTC. Not yet reconciled with the management "
                                "accounts. Kisiwa's budget disagrees with its own lines.")
    assert a["standing"] == {
        "reconciled": False, "reason": "THIS_MONTH_NOT_MATCHED",
        "text": "Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1%.",
        "details": ["Fuel cost (Recorded and Emulated): the accounts say $5,100.00 and the records say $4,995.00, "
                    "$105.00 less (2.06%), beyond the $51.00 allowed (1%)."]}
    assert money_words(a) == A_WORDS
    assert {k: v for k, v in a.items() if k not in TIMED} == {k: v for k, v in fixture.items() if k not in TIMED}

    # (b) S2 (fuel 5,000.00) recorded at 12:00, after `as_of`; read at 12:30: still A's words (D-3A7.9).
    record(x, at(12), revenue="9700.00", fuel="5000.00")
    b = read(x, at(12, 30))
    assert b == a

    # (c) rebuilt at 13:00, read at 13:30: B's words.
    build(x, at(13))
    c = read(x, at(13, 30))
    assert (c["as_of"], c["standing"]["reconciled"], c["standing"]["reason"]) == (
        "2026-11-19T13:00:00Z", True, "RECONCILED")
    assert c["standing"]["details"] == []
    assert c["status_line"] == ("Figures as of 19 November 2026, 13:00 UTC. Reconciled with the management accounts. "
                                "Kisiwa's budget disagrees with its own lines.")
    assert money_words(c) == B_WORDS
    assert c["outcomes"][3]["value"] == "Reconciled"


def test_9_the_composition_reads_the_database(lakeside) -> None:
    x = lakeside
    read_, dispose = build_deep_dive_read(URL)
    try:
        assert read_.month(x["tenant"], "2026-10", NAMES)["state"] == "NO_SNAPSHOT"
        service = build_structure_snapshot(URL)
        try:
            service.builder.build(x["w"]["tid"], t3.refs(x["w"])[:3], t3.OCT, built_by=t3.BY)
        finally:
            service.dispose()
        served = read_.month(x["tenant"], "2026-10", NAMES)
    finally:
        dispose()
    assert served["state"] == "SERVED" and served["operator"] == "Lakeside Power"
    assert served["actions"]["connected"] is False
