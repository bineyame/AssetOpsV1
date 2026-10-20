"""W3-01 Run 6 (q6) Lane A prerequisites `0a`/`0b`: the connection-taking W1 money reads at an explicit cutoff.

A real power Site (the S4-02b `PowerSite` shape: Batch V2 ingestion, the S3 worker, the S4 matcher, the stored
SYSTEM price series and the consequence worker; no row is seeded) is read through the `*_on` helpers on ONE
caller-owned REPEATABLE READ connection. The fixture clock is set one day behind the database clock, so every
Finding/evidence row precedes the wall-clocked price and consequence rows and a cutoff taken between two of
those rows still sees the Finding. Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from test_s4_consequence_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_consequence_recompute_postgres import supersede
    from test_s4_consequence_store_postgres import POWER_DAY, STATE_DAY, PowerSite, _at
    from test_s4_finding_store_postgres import SPEC, CaseRunner, block_rows

    import test_s4_finding_store_postgres as s4_findings
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.consequence_read import ConsequenceReadService
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker


def db_now(engine) -> datetime:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def _iso(at: datetime) -> str:
    return at.isoformat().replace("+00:00", "Z")


class EarlySite(PowerSite):
    """`PowerSite` with its fixture clock one day behind the database clock (same rows, same order)."""

    def __init__(self, store, engine, capsys, monkeypatch) -> None:  # noqa: F811
        base = db_now(engine) - timedelta(days=1)
        assert base > STATE_DAY + timedelta(days=2), "the database clock must run after the fixture's data days"
        monkeypatch.setattr(s4_findings, "SETUP_AT", base)
        self.runner = r = CaseRunner(store, engine)
        self.tenant, self.site = r.tenant, r.site
        rules = SPEC["reading_rules"]
        envelopes = [self.power(_at(POWER_DAY, 8, 0), "0")]
        t = _at(POWER_DAY, 8, 5)
        while t <= _at(POWER_DAY, 8, 30):
            envelopes.append(self.power(t, "20"))
            t += timedelta(minutes=5)
        context = block_rows({"from": "2026-10-06T08:00:00Z", "to": "2026-10-06T08:30:00Z", "pv": "40", "dis": "20",
                              "soc": "80", "only": ["load", "pv", "dis", "soc"]}, rules)
        sealed, _ = r.seal([(row, False) for row in sorted(context, key=lambda x: x[2])], "epoch-1")
        r.submit(envelopes + sealed, r.tick(_iso(base + timedelta(hours=1))))
        r.step({"do": "deliver", "decided": _iso(base + timedelta(hours=2)), "blocks": [
            {"from": "2026-10-08T08:00:00Z", "to": "2026-10-08T08:30:00Z", "pv": "40", "dis": "20", "soc": "80",
             "stop_before": True, "stop_after": True}]})
        r.step({"do": "assess"})
        r.step({"do": "match"})
        self.prices = PostgresAssumptionStore(URL)
        self.store = PostgresConsequenceStore(URL)
        self.capsys = capsys


class Rig:
    def __init__(self, site: EarlySite, engine) -> None:  # noqa: F811
        self.site, self.engine = site, engine
        self.t, self.s = site.tenant, site.site
        self.worker = ConsequenceRecomputeWorker(site.store, site.prices, CONSEQUENCE_UNAVAILABLE)
        self.reads = ConsequenceReadService(site.store, site.prices)

    def run(self) -> None:
        assert all(o.succeeded for o in self.worker.run_pending(self.t, self.s))

    def now(self) -> datetime:
        return db_now(self.engine)

    def on(self, finding_revision_id, known_at, site_id=None) -> dict:
        with caller_snapshot(self.engine) as c:
            return self.reads.select_consequence_on(c, self.t, site_id or self.s, finding_revision_id, known_at)


@pytest.fixture()
def rig(store, engine, capsys, monkeypatch):  # noqa: F811
    s = EarlySite(store, engine, capsys, monkeypatch)
    yield Rig(s, engine)
    s.prices.dispose()
    s.store.dispose()


@contextmanager
def caller_snapshot(engine):  # noqa: F811
    """The caller's one REPEATABLE READ transaction; every helper must run inside it and leave it open."""
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a helper ended the caller's transaction"


def test_consequence_on_excludes_later_revision_and_price(rig) -> None:
    rig.run()  # no price yet: revision 1 is UNPRICED
    rev = rig.site.on(POWER_DAY)
    k1 = rig.now()
    rig.site.publish("v1")
    k2 = rig.now()
    rig.run()  # revision 2 is PRICED at v1
    live = rig.on(rev["id"], rig.now())
    at1, at2 = rig.on(rev["id"], k1), rig.on(rev["id"], k2)
    assert (live["revision_no"], live["consequence_state"], live["currentness"]["state"]) == (2, "PRICED", "CURRENT")
    assert (Decimal(live["amount_low"]), Decimal(live["amount_high"]), live["currency"]) == (
        0, Decimal("3.4375"), "USD")
    assert live["cited"]["price_revision_id"] is not None and len(live["cited"]["power_evidence_ids"]) == 5
    assert live["cited"]["assessment_revision_ids"]
    # k1: the later revision and the later price are both absent; the UNPRICED head is current at k1.
    assert (at1["revision_no"], at1["consequence_state"], at1["currentness"]) == (
        1, "UNPRICED", {"state": "CURRENT", "reasons": []})
    assert at1["consequence_revision_id"] != live["consequence_revision_id"]
    assert (at1["amount_high"], at1["currency"], at1["cited"]["price_revision_id"]) == (None, None, None)
    # k2: the price is known, its consequence is not: the same revision 1, stale at k2, never repriced.
    assert at2["consequence_revision_id"] == at1["consequence_revision_id"]
    assert at2["currentness"]["state"] == "STALE" and "PRICE_SELECTION_CHANGED" in at2["currentness"]["reasons"]
    assert (at2["amount_high"], at2["currency"]) == (None, None)


def test_consequence_on_exact_finding_pin_and_stale_basis(rig, monkeypatch) -> None:
    rig.site.publish("v1", "v2", "v3")
    rig.run()
    power, state_day = rig.site.on(POWER_DAY), rig.site.on(STATE_DAY)
    before = rig.now()
    rig.site.publish("v4")  # a full-window backdated correction: the stored basis is stale until recomputed
    live = rig.now()
    current, stale = rig.on(power["id"], before), rig.on(power["id"], live)
    assert current["currentness"]["state"] == "CURRENT" and current["consequence_state"] == "PRICED"
    assert stale["consequence_revision_id"] == current["consequence_revision_id"]
    assert stale["currentness"]["state"] == "STALE" and "PRICE_SELECTION_CHANGED" in stale["currentness"]["reasons"]
    assert Decimal(stale["amount_high"]) == Decimal(current["amount_high"])  # the stored amount, not repriced
    # The exact pin selects only that FindingRevision's own chain.
    other = rig.on(state_day["id"], live)
    assert other["consequence_state"] == "QUANTITY_UNAVAILABLE" and other["currentness"]["state"] == "CURRENT"
    assert other["consequence_revision_id"] != stale["consequence_revision_id"]
    assert other["finding_id"] == str(state_day["finding_id"]) and other["cited"]["power_evidence_ids"] == []
    # A revision that is not this Site's, or not yet created at the cutoff, is UNKNOWN with no amount.
    with rig.engine.connect() as c:
        created = c.execute(text("SELECT created_at FROM finding_revision WHERE id = :r"),
                            {"r": power["id"]}).scalar_one()
    for refused in (rig.on(uuid4(), live), rig.on(power["id"], live, site_id=uuid4()),
                    rig.on(power["id"], created - timedelta(microseconds=1))):
        assert refused["currentness"] == {"state": "UNKNOWN", "reasons": ["FINDING_REVISION_NOT_AT_CUTOFF"]}
        assert (refused["consequence_revision_id"], refused["amount_high"], refused["currency"]) == (None, None, None)
    # Created but nothing recorded by the cutoff: PENDING, never an amount.
    pending = rig.on(power["id"], created)
    assert pending["currentness"] == {"state": "PENDING", "reasons": ["NO_CONSEQUENCE_AT_CUTOFF"]}
    assert pending["consequence_revision_id"] is None and pending["amount_high"] is None
    # A FindingRevision superseded by the cutoff keeps its stored amount as HISTORICAL record.
    old, new = supersede(rig, monkeypatch)
    hist = rig.on(old["id"], rig.now())
    assert hist["currentness"] == {"state": "HISTORICAL", "reasons": ["FINDING_REVISION_SUPERSEDED"]}
    assert hist["consequence_revision_id"] == stale["consequence_revision_id"] and hist["amount_high"] is not None
