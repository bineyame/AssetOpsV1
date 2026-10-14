"""S4-02b phase 2a: the durable recompute worker and the exact consequence read over real persisted data.

Packet `tasks/S4-02b-fuel-consequence.md` phase row 2a: no price, future price, full-window backdated
correction, partial correction, boundary-crossing window; old/new consequence IDs inspected after a restart
and after a failed-then-retried worker. The Site is phase 1's `PowerSite` (a power-mean Candidate interval on
2026-10-06 [08:05, 08:30) and an ordinary state-only Finding on 2026-10-08). Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    """Each case builds several short-lived stores (CaseRunner, workers); collect their engines promptly so a
    full-suite run does not exhaust the server's connection slots."""
    yield
    import gc

    gc.collect()

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_assumptions_postgres import pub
    from test_s4_consequence_store_postgres import KEY, POWER_DAY, STATE_DAY, PowerSite

    from assetops_backend.analytics.composition import build_finding_read_service
    from assetops_backend.financials import fuel_cost as fc
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import (
        ConsequenceStoreUnavailable,
        PostgresConsequenceStore,
    )
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.consequence_read import ConsequenceReadService
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker
    from assetops_backend.finding_api import build_finding_router

UTC = timezone.utc


def _t(*a) -> datetime:
    return datetime(*a, tzinfo=UTC)


class Rig:
    def __init__(self, site) -> None:
        self.site = site
        self.worker = ConsequenceRecomputeWorker(site.store, site.prices, CONSEQUENCE_UNAVAILABLE)
        self.reads = ConsequenceReadService(site.store, site.prices)

    def run(self):
        return self.worker.run_pending(self.site.tenant, self.site.site)

    def read(self, day=POWER_DAY, **kw) -> dict:
        rev = self.site.on(day)
        return self.reads.read(self.site.tenant, self.site.site, rev["finding_id"], rev["id"],
                               finding_revision_is_latest=True, **kw)

    def chain(self, day=POWER_DAY) -> list[dict]:
        rev = self.site.on(day)
        return [r for r in self.site.store.rows(self.site.tenant, self.site.site)["financial_consequence_revision"]
                if r["finding_revision_id"] == rev["id"]]

    def correct(self, value: str, vf: datetime, vt: datetime, key: str):
        """A test-scoped SYSTEM CORRECTION on top of the current latest price revision."""
        snap = self.site.prices.snapshot(self.site.tenant, self.site.site, KEY, None, 0, 500)
        prior = snap["revisions"][-1]["id"]
        return self.site.prices.publish(self.site.tenant, self.site.site,
                                        pub(prior, key, "CORRECTION", vf, vt, value, "test-scoped correction"),
                                        SYSTEM_PUBLISHER)


@pytest.fixture()
def rig(store, engine, capsys):  # noqa: F811
    s = PowerSite(store, engine, capsys)
    yield Rig(s)
    s.prices.dispose()
    s.store.dispose()


class TestPriceCases:
    def test_no_price_is_unpriced_then_an_initial_price_makes_it_stale_until_recomputed(self, rig) -> None:
        assert all(o.succeeded for o in rig.run())
        r = rig.read()
        assert (r["currentness"]["state"], r["consequence"]["state"]) == ("CURRENT", "UNPRICED")
        assert r["consequence"]["price"]["reason"] == "NO_PRICE" and r["consequence"]["amount"]["high"] is None
        assert r["consequence"]["display"] is None and Decimal(r["consequence"]["quantity"]["high"]) == Decimal("2.75")
        state_day = rig.read(STATE_DAY)
        assert (state_day["currentness"]["state"], state_day["consequence"]["state"]) == (
            "CURRENT", "QUANTITY_UNAVAILABLE")
        assert state_day["consequence"]["quantity"]["reason"] == "POWER_MISSING"
        rig.site.publish("v1")
        stale = rig.read()
        assert stale["currentness"]["state"] == "STALE" and "PRICE_SELECTION_CHANGED" in stale["currentness"]["reasons"]
        assert stale["consequence"]["presented_as_current"] is False and stale["currentness"]["pending_work"]
        assert Decimal(stale["currentness"]["derived_now"]["price"]["value"]) == Decimal("1.25")
        rig.run()
        now = rig.read()
        c = now["consequence"]
        assert (now["currentness"]["state"], c["state"], c["revision_no"], c["presented_as_current"]) == (
            "CURRENT", "PRICED", 2, True)
        assert (Decimal(c["amount"]["low"]), Decimal(c["amount"]["high"]), c["amount"]["currency"]) == (
            0, Decimal("3.4375"), "USD")
        assert (c["display"]["amount_low"], c["display"]["amount_high"]) == ("0.00", "3.44")  # high rounded up
        assert len(rig.chain(STATE_DAY)) == 1  # an unavailable quantity ignores the price (Q5)

    def test_a_future_price_leaves_the_october_consequence_current(self, rig) -> None:
        rig.site.publish("v1")
        rig.run()
        first = rig.read()["consequence"]["id"]
        rig.site.publish("v2")  # SUCCESSION from 2030: re-IDs v1's assignment (review M1)
        r = rig.read()
        assert r["currentness"]["state"] == "CURRENT" and r["consequence"]["id"] == first
        outs = rig.run()
        assert outs and all(o.succeeded and not o.appended for o in outs)
        assert [x["id"] for x in rig.chain()] == [UUID(first)]

    def test_a_full_window_backdated_correction_appends_and_keeps_the_old_revision_inspectable(self, rig) -> None:
        rig.site.publish("v1", "v2", "v3")
        rig.run()
        old = rig.read()["consequence"]
        (v4,) = rig.site.publish("v4")
        assert rig.read()["currentness"]["state"] == "STALE"
        rig.run()
        new = rig.read()["consequence"]
        assert (new["revision_no"], new["prior_consequence_revision_id"]) == (2, old["id"])
        assert Decimal(new["amount"]["high"]) == Decimal("3.52")
        assert new["price"]["revision_id"] == v4["revision_id"]
        assert new["finding_revision_id"] == old["finding_revision_id"]
        assert new["digests"]["technical_input_sha256"] == old["digests"]["technical_input_sha256"]
        pinned = rig.read(consequence_revision_id=UUID(old["id"]))["consequence"]
        assert (pinned["id"], Decimal(pinned["amount"]["high"]), pinned["is_head"], pinned["historical"]) == (
            old["id"], Decimal("3.4375"), False, True)
        # Restart: new stores and worker; nothing is appended again and the IDs are unchanged.
        rig.site.store.dispose()
        rig.site.prices.dispose()
        again = Rig(rig.site)
        again.worker = ConsequenceRecomputeWorker(PostgresConsequenceStore(URL), PostgresAssumptionStore(URL),
                                                  CONSEQUENCE_UNAVAILABLE)
        assert again.run() == []
        after = again.read()
        assert after["currentness"]["state"] == "CURRENT" and after["consequence"]["id"] == new["id"]
        assert [str(x["id"]) for x in rig.chain()] == [old["id"], new["id"]]

    def test_a_partial_correction_changes_only_windows_whose_whole_window_price_changes(self, rig) -> None:
        rig.site.publish("v1")
        rig.run()
        first = rig.read()["consequence"]["id"]
        rig.correct("1.40", _t(2026, 10, 8), _t(2026, 10, 9), "partial-elsewhere")  # the state day only
        assert rig.read()["currentness"]["state"] == "CURRENT"
        assert all(o.succeeded and not o.appended for o in rig.run())
        assert [str(x["id"]) for x in rig.chain()] == [first]
        rig.correct("1.30", _t(2026, 10, 6), _t(2026, 10, 6, 12), "partial-whole-window")  # covers [08:05, 08:30)
        rig.run()
        c = rig.read()["consequence"]
        assert (c["revision_no"], Decimal(c["price"]["value"]), Decimal(c["amount"]["high"])) == (
            2, Decimal("1.30"), Decimal("3.575"))

    def test_a_correction_inside_the_window_appends_an_unpriced_revision(self, rig) -> None:
        rig.site.publish("v1")
        rig.run()
        boundary = rig.correct("1.30", _t(2026, 10, 6, 8, 15), _t(2026, 10, 7), "crossing")
        rig.run()
        r = rig.read()
        c = r["consequence"]
        assert (r["currentness"]["state"], c["state"], c["revision_no"]) == ("CURRENT", "UNPRICED", 2)
        assert (c["price"]["reason"], c["amount"]["high"], c["display"]) == ("PRICE_SPANS_WINDOW", None, None)
        assert [x[1:] for x in c["price"]["considered"]] == [
            [fc.iso(_t(2026, 10, 6, 8, 5)), fc.iso(_t(2026, 10, 6, 8, 15))],
            [fc.iso(_t(2026, 10, 6, 8, 15)), fc.iso(_t(2026, 10, 6, 8, 30))]]
        assert c["price"]["considered"][1][0] == str(boundary.revision_id)
        assert Decimal(c["quantity"]["high"]) == Decimal("2.75")  # the technical quantity is unchanged


class TestDurableFailureAndRetry:
    def test_a_failed_worker_leaves_typed_pending_work_and_the_retry_succeeds(self, rig, monkeypatch) -> None:
        rig.site.publish("v1")

        def down(*a, **k):
            raise ConsequenceStoreUnavailable("injected outage")

        monkeypatch.setattr(rig.site.store, "append", down)
        outs = rig.run()
        assert outs and all(not o.succeeded and o.error_code == "STORE_UNAVAILABLE" for o in outs)
        monkeypatch.undo()
        r = rig.read()
        assert r["currentness"]["state"] == "PENDING" and r["consequence"] is None
        assert {w["last_error_code"] for w in r["currentness"]["pending_work"]} == {"STORE_UNAVAILABLE"}
        retried = rig.run()
        assert retried and all(o.succeeded and o.attempt_no == 2 for o in retried)
        assert rig.read()["currentness"]["state"] == "CURRENT"
        assert rig.site.store.pending_work(rig.site.tenant, rig.site.site) == []

    def test_a_crash_between_append_and_record_replays_the_same_id(self, rig, monkeypatch) -> None:
        rig.site.publish("v1")
        real = rig.site.store.record_attempt

        def crash(*a, **k):
            raise RuntimeError("process killed after append")

        monkeypatch.setattr(rig.site.store, "record_attempt", crash)
        with pytest.raises(RuntimeError):
            rig.run()
        monkeypatch.setattr(rig.site.store, "record_attempt", real)
        (stored,) = rig.chain()
        outs = rig.run()
        assert stored["id"] in {x for o in outs for x in o.replayed}
        assert not any(stored["id"] in o.appended for o in outs) and rig.chain() == [stored]


class TestRoute:
    def client(self, site, consequences=True) -> TestClient:
        app = FastAPI()
        scope = {"KOBO-001": ("KOBO-001", site.tenant, site.site)}
        app.include_router(build_finding_router(
            build_finding_read_service(URL), scope.get, CONSEQUENCE_UNAVAILABLE,
            gate=lambda c, t, s: (True, "test gate open"),
            consequences=ConsequenceReadService(site.store, site.prices) if consequences else None,
            consequence_unavailable=CONSEQUENCE_UNAVAILABLE))
        return TestClient(app)

    def test_exact_current_historical_paged_and_refused_reads(self, rig) -> None:
        rig.site.publish("v1", "v2", "v3")
        rig.run()
        rig.site.publish("v4")
        rig.run()
        rev = rig.site.on(POWER_DAY)
        api = self.client(rig.site)
        base = f"/api/sites/KOBO-001/findings/{rev['finding_id']}/financial-consequences"
        body = api.get(base).json()
        assert body["selection"]["revision_id"] == str(rev["id"]) and body["currentness"]["state"] == "CURRENT"
        assert Decimal(body["consequence"]["amount"]["high"]) == Decimal("3.52") and body["history"]["total"] == 2
        assert body["consequence"]["lineage"]["evidence_ids"] and body["links"]["evidence_records"]
        page = api.get(base, params={"limit": 1}).json()
        assert [r["revision_no"] for r in page["history"]["revisions"]] == [1]
        assert page["history"]["page"]["next_after_revision_no"] == 1 and "api_next_page" in page["links"]
        old = page["history"]["revisions"][0]["id"]
        pinned = api.get(base, params={"consequence_revision_id": old}).json()
        assert pinned["consequence"]["id"] == old and pinned["consequence"]["historical"] is True
        assert pinned["selection"]["revision_id"] == str(rev["id"])  # the same FindingRevision
        assert api.get(base, params={"consequence_revision_id": str(uuid4())}).status_code == 404
        other = rig.site.on(STATE_DAY)
        assert api.get(base, params={"revision_id": str(other["id"])}).status_code == 404  # foreign revision
        state_base = f"/api/sites/KOBO-001/findings/{other['finding_id']}/financial-consequences"
        assert api.get(state_base, params={"revision_id": str(rev["id"]), "consequence_revision_id": old}
                       ).status_code == 404  # a consequence of another Finding never falls back
        (foreign,) = rig.chain(STATE_DAY)
        assert api.get(base, params={"revision_id": str(rev["id"]), "consequence_revision_id": str(foreign["id"])}
                       ).status_code == 404  # an exact consequence of another FindingRevision never falls back
        assert api.get(f"/api/sites/NOPE/findings/{rev['finding_id']}/financial-consequences").status_code == 404
        assert self.client(rig.site, consequences=False).get(base).status_code == 503
        bridge = api.get(f"/api/sites/KOBO-001/findings/{rev['finding_id']}/financials").json()["consequence"]
        assert (bridge["state"], bridge["amount"], bridge["currency"]) == (
            "PRICED", {"low": "0.00", "high": "3.52"}, "USD")
        assert Decimal(bridge["amount"]["high"]) >= Decimal(body["consequence"]["amount"]["high"])
