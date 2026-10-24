"""S4-02b phase 1: `fuel-cost-1` over real persisted inputs, the consequence store and durable dirty work.

A real Site runs through Batch V2 ingestion (generator-power interval means, not generator state, so the
assessment's own inputs carry the power), the S3 worker and the Finding matcher. The consequence is derived
from the exact persisted FindingRevision, assessment, accepted power and as-accepted Foundation/binding IDs,
priced over the whole window from the stored SYSTEM price series, appended idempotently, and re-derived after
a restart. An ordinary state-only Finding stays `QUANTITY_UNAVAILABLE`. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
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
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import SourceEnvelopeV3, _z, canonical_envelope_v3_text, v3_message_id
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_finding_store_postgres import SPEC, CaseRunner, block_rows

    from assetops_backend.financials import fuel_cost as fc
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore

UTC = timezone.utc
KEY = "diesel_price_per_litre"
POWER_DAY = datetime(2026, 10, 6, tzinfo=UTC)
STATE_DAY = datetime(2026, 10, 8, tzinfo=UTC)


def _at(day: datetime, hh: int, mm: int) -> datetime:
    return day + timedelta(hours=hh, minutes=mm)


class PowerSite:
    """One Site with a generator-power-only Candidate interval (08:05-08:30, open: no stop mean after) and an
    ordinary generator-state Candidate interval on another day."""

    def __init__(self, store, engine, capsys) -> None:  # noqa: F811
        self.runner = r = CaseRunner(store, engine)
        self.tenant, self.site = r.tenant, r.site
        rules = SPEC["reading_rules"]
        # Power day: a zero mean ending 08:00 (OFF), then 20 kW means ending 08:05..08:30; Candidate context rows
        # (three feeders, pv, discharge, soc) at each report time. No stop after: the dispatch interval is open.
        envelopes = [self.power(_at(POWER_DAY, 8, 0), "0")]
        t = _at(POWER_DAY, 8, 5)
        while t <= _at(POWER_DAY, 8, 30):
            envelopes.append(self.power(t, "20"))
            t += timedelta(minutes=5)
        context = block_rows({"from": "2026-10-06T08:00:00Z", "to": "2026-10-06T08:30:00Z", "pv": "40", "dis": "20",
                              "soc": "80", "only": ["load", "pv", "dis", "soc"]}, rules)
        now, _ = r.seal([(row, False) for row in sorted(context, key=lambda x: x[2])], "epoch-1")
        r.submit(envelopes + now, r.tick("2026-10-30T08:00:00Z"))
        # State day: the ordinary S4 shape (generator state only, no power means).
        r.step({"do": "deliver", "decided": "2026-10-30T09:00:00Z", "blocks": [
            {"from": "2026-10-08T08:00:00Z", "to": "2026-10-08T08:30:00Z", "pv": "40", "dis": "20", "soc": "80",
             "stop_before": True, "stop_after": True}]})
        r.step({"do": "assess"})
        r.step({"do": "match"})
        self.prices = PostgresAssumptionStore(URL)
        self.store = PostgresConsequenceStore(URL)
        self.capsys = capsys

    def power(self, end: datetime, kw: str) -> tuple[str, str]:
        kit, device, signal = self.runner.kit, "generator-controller", "ac-power"
        b = kit.binding(device, signal)
        key = (b["source_id"], "epoch-p")
        self.runner.seq[key] = self.runner.seq.get(key, 0) + 1
        seq = self.runner.seq[key]
        e = SourceEnvelopeV3(
            message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                     source_id=b["source_id"], sequence_epoch="epoch-p", sequence=seq),
            sequence_epoch="epoch-p", sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
            source_id=b["source_id"], device_id=device, signal_id=signal,
            binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
            source_time=_z(end), published_at=_z(end), interval_start=_z(end - timedelta(minutes=5)),
            interval_end=_z(end), family="MEASUREMENT", measurement="INTERVAL_MEAN", value=kw,
            unit=b["source_unit"], quality="GOOD", unavailable_reason=None)
        return device, canonical_envelope_v3_text(e)

    def finding_revisions(self) -> list[dict]:
        with self.runner.engine.connect() as c:
            return [dict(x._mapping) for x in c.execute(text(
                "SELECT r.id, r.finding_id, r.episode_start, r.episode_end, r.revision_no FROM finding_revision r "
                "WHERE r.site_id = :s AND r.revision_no = (SELECT max(revision_no) FROM finding_revision x "
                "WHERE x.finding_id = r.finding_id) ORDER BY r.episode_start"), {"s": self.site})]

    def on(self, day: datetime) -> dict:
        (rev,) = [r for r in self.finding_revisions() if r["episode_start"].date() == day.date()]
        return rev

    def derive(self, rev: dict, store=None) -> fc.Consequence:
        s = store or self.store
        f = s.load_input(self.tenant, self.site, rev["finding_id"], rev["id"])
        q = fc.quantify(f)
        snap = self.prices.snapshot(self.tenant, self.site, KEY, None, 0, 100)
        price = fc.select_window_price(snap["timeline"], snap["cited"], f.window_start, f.window_end)
        return fc.consequence(f, q, price)

    def publish(self, *steps: str) -> list[dict]:
        return run_fixture(self.prices, self.capsys, *steps)


@pytest.fixture()
def site(store, engine, capsys):  # noqa: F811
    s = PowerSite(store, engine, capsys)
    yield s
    s.prices.dispose()
    s.store.dispose()


@pytest.fixture()
def site_before_0029(store, engine, capsys):  # noqa: F811
    """W4-02 q1 ruling 2: the same MINIGRID PowerSite, seeded before 0029 is installed so it holds no mini history;
    for downgrade probes that cross 0029."""
    from alembic.config import Config
    from mini_depth_probe import assert_no_mini_history, seeded_before_0029
    from test_s1_bindings_postgres import BACKEND

    config = Config(str(BACKEND / "alembic.ini"))
    config.attributes["database_url"] = URL
    with seeded_before_0029(config, engine, store):
        s = PowerSite(store, engine, capsys)
        s.prices.dispose()
        s.store.dispose()
    assert_no_mini_history(engine)
    yield s
    s.prices.dispose()
    s.store.dispose()


class TestQuantityFromPersistedInputs:
    def test_power_finding_is_quantified_from_exact_accepted_ids_and_survives_restart(self, site, engine) -> None:  # noqa: F811
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        c = site.derive(rev)
        q = c.quantity
        assert q.state == "AVAILABLE", (q.reason, q.detail)
        # Five 20 kW means of 5 minutes inside [08:05, 08:30): 25/3 kWh x 0.3 L/kWh x 1.10 = 2.75 L.
        assert q.high_exact == Fraction(11, 4) and q.high == Decimal("2.75") and q.low == Decimal(0)
        assert [i.interval_start.strftime("%H:%M") for i in q.intervals] == ["08:05", "08:10", "08:15", "08:20",
                                                                            "08:25"]
        assert c.state == "PRICED" and c.price.value == Decimal("1.25") and c.amount_high == Decimal("3.4375")
        with engine.connect() as conn:
            stored = conn.execute(text(
                "SELECT CAST(e.id AS text) FROM accepted_evidence e WHERE e.site_id = :s AND e.role = "
                "'generator_power' AND e.interval_start >= :a AND e.interval_end <= :b ORDER BY e.interval_start"),
                {"s": site.site, "a": _at(POWER_DAY, 8, 5), "b": _at(POWER_DAY, 8, 30)}).scalars().all()
            interval = conn.execute(text(
                "SELECT v.result->'interval' FROM finding_revision_assessment a JOIN assessment_revision v "
                "ON v.id = a.assessment_revision_id WHERE a.finding_revision_id = :r AND a.is_primary "
                "AND a.scope = 'INTERVAL'"), {"r": rev["id"]}).scalar_one()
            linked = {str(x) for x in conn.execute(text(
                "SELECT assessment_revision_id FROM finding_revision_assessment WHERE finding_revision_id = :r "
                "AND scope = 'INTERVAL'"), {"r": rev["id"]}).scalars()}
        assert [i.evidence_id for i in q.intervals] == stored
        assert interval["upper_minutes"] is None and interval["off_after"] is None  # open: never read
        appended = site.store.append(c)
        assert appended.revision_no == 1 and not appended.replayed

        site.store.dispose()  # restart: new store, new engine, recompute from the persisted IDs only
        fresh = PostgresConsequenceStore(URL)
        again = site.derive(rev, fresh)
        assert again.basis_sha256 == c.basis_sha256 and again.technical_input_sha256 == c.technical_input_sha256
        replay = fresh.append(again)
        assert replay.replayed and replay.consequence_revision_id == appended.consequence_revision_id
        rows = fresh.rows(site.tenant, site.site)
        (row,) = rows["financial_consequence_revision"]
        assert (row["state"], row["basis_kind"], row["consequence_type"], row["model_id"]) == (
            "PRICED", "MODELLED_CONDITIONAL", "POTENTIAL_FUEL_COST", "fuel-cost-1")
        assert (row["quantity_low"], row["quantity_high"], row["quantity_high_exact"]) == (
            Decimal(0), Decimal("2.75"), "11/4")
        assert (row["amount_low"], row["amount_high"], row["currency"]) == (Decimal(0), Decimal("3.4375"), "USD")
        assert row["sfc_upper_multiplier"] == Decimal("1.10") and row["parameter_sha256"] == fc.PARAMETER_SHA256
        assert (row["window_start"], row["window_end"]) == (rev["episode_start"], rev["episode_end"])
        assert {str(x["assessment_revision_id"]) for x in rows["financial_consequence_assessment_revision"]} == linked
        (price_link,) = rows["financial_consequence_assumption_revision"]
        assert price_link["assumption_revision_id"] == row["price_revision_id"]
        assert [str(x["evidence_id"]) for x in rows["financial_consequence_power_interval"]] == stored
        assert all(x["mean_kw"] == Decimal("20") and x["duration_seconds"] == 300 and x["containment"] == "CONTAINED"
                   and x["sfc_l_per_kwh"] == Decimal("0.3") for x in rows["financial_consequence_power_interval"])
        fresh.dispose()

    def test_ordinary_state_only_finding_is_quantity_unavailable_with_no_number(self, site) -> None:
        site.publish("v1", "v2", "v3")
        c = site.derive(site.on(STATE_DAY))
        assert (c.state, c.quantity.reason) == ("QUANTITY_UNAVAILABLE", "POWER_MISSING")
        assert c.quantity.high is None and c.amount_high is None and c.price.state == "NOT_EVALUATED"
        site.store.append(c)
        (row,) = site.store.rows(site.tenant, site.site)["financial_consequence_revision"]
        assert row["quantity_high"] is None and row["amount_high"] is None and row["currency"] is None
        assert site.store.rows(site.tenant, site.site)["financial_consequence_assumption_revision"] == []

    def test_no_price_is_unpriced_never_zero(self, site) -> None:
        c = site.derive(site.on(POWER_DAY))
        assert (c.state, c.price.reason, c.amount_low, c.amount_high) == ("UNPRICED", "NO_PRICE", None, None)
        site.store.append(c)
        (row,) = site.store.rows(site.tenant, site.site)["financial_consequence_revision"]
        assert row["state"] == "UNPRICED" and row["quantity_high"] == Decimal("2.75") and row["amount_high"] is None


class TestRepricingAndIdempotentAppend:
    def test_v4_october_correction_appends_a_new_consequence_for_the_same_finding_revision(self, site) -> None:
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        first = site.store.append(site.derive(rev))
        (v4,) = site.publish("v4")
        assert v4["change_kind"] == "CORRECTION" and v4["revision_no"] == 4
        c2 = site.derive(rev)
        assert c2.price.value == Decimal("1.28") and c2.amount_high == Decimal("3.52")
        second = site.store.append(c2)
        assert (second.revision_no, second.replayed) == (2, False)
        rows = site.store.rows(site.tenant, site.site)["financial_consequence_revision"]
        old, new = rows
        assert old["id"] == first.consequence_revision_id and old["amount_high"] == Decimal("3.4375")
        assert new["prior_consequence_revision_id"] == old["id"] and new["finding_revision_id"] == rev["id"]
        assert new["technical_input_sha256"] == old["technical_input_sha256"]
        assert new["quantity_high"] == old["quantity_high"]
        assert str(new["price_revision_id"]) == v4["revision_id"]

    def test_concurrent_identical_appends_store_one_revision(self, site) -> None:
        site.publish("v1", "v2", "v3")
        c = site.derive(site.on(POWER_DAY))
        ids, errors = [], []

        def go() -> None:
            s = PostgresConsequenceStore(URL)
            try:
                ids.append(s.append(c).consequence_revision_id)
            except Exception as error:  # pragma: no cover - reported below
                errors.append(error)
            finally:
                s.dispose()

        threads = [threading.Thread(target=go) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors and len(set(ids)) == 1
        assert len(site.store.rows(site.tenant, site.site)["financial_consequence_revision"]) == 1


class TestDurableDirtyWork:
    def test_finding_revisions_and_publications_enqueue_work_transactionally(self, site) -> None:
        work = site.store.rows(site.tenant, site.site)["financial_consequence_work"]
        findings = {r["id"] for r in site.finding_revisions()}
        with site.runner.engine.connect() as c:
            every_revision = {x for x in c.execute(text("SELECT id FROM finding_revision WHERE site_id = :s"),
                                                   {"s": site.site}).scalars()}
        assert findings <= every_revision
        assert {w["finding_revision_id"] for w in work if w["cause"] == "FINDING_REVISION_APPENDED"} == every_revision
        out = site.publish("v1", "v2", "v3")
        site.publish("v1", "v2", "v3")  # replay: no new revision, so no new work
        out += site.publish("v4")
        work = site.store.rows(site.tenant, site.site)["financial_consequence_work"]
        published = [w for w in work if w["cause"] == "ASSUMPTION_PUBLISHED"]
        assert [str(w["assumption_revision_id"]) for w in published] == [o["revision_id"] for o in out]
        by_rev = {str(w["assumption_revision_id"]): w for w in published}
        v2, v4 = by_rev[out[1]["revision_id"]], by_rev[out[3]["revision_id"]]
        assert v2["affected_to"] is None  # a SUCCESSION changes everything after its start
        assert (v4["affected_from"], v4["affected_to"]) == (datetime(2026, 10, 1, tzinfo=UTC),
                                                            datetime(2026, 11, 1, tzinfo=UTC))

    def test_failed_then_succeeded_attempts_clear_pending_once(self, site) -> None:
        pending = site.store.pending_work(site.tenant, site.site)
        assert pending and all(p["attempts"] == 0 for p in pending)
        w = pending[0]["id"]
        assert site.store.record_attempt(site.tenant, site.site, w, succeeded=False, error_code="STORE_DOWN") == 1
        assert w in {p["id"] for p in site.store.pending_work(site.tenant, site.site)}
        assert site.store.record_attempt(site.tenant, site.site, w, succeeded=True) == 2
        assert w not in {p["id"] for p in site.store.pending_work(site.tenant, site.site)}
        with pytest.raises(DBAPIError, match="financial_consequence_attempt_one_success"):
            site.store.record_attempt(site.tenant, site.site, w, succeeded=True)


class TestDatabaseGuards:
    def test_history_and_number_rules_are_enforced_by_the_database(self, site, engine) -> None:  # noqa: F811
        site.publish("v1", "v2", "v3")
        rev = site.on(POWER_DAY)
        appended = site.store.append(site.derive(rev))
        cid = appended.consequence_revision_id
        for sql, message in (
            ("UPDATE financial_consequence_revision SET amount_high = 0", "append-only"),
            ("DELETE FROM financial_consequence_power_interval", "append-only"),
            ("DELETE FROM financial_consequence_work", "append-only"),
        ):
            with pytest.raises(DBAPIError, match=message):
                with engine.begin() as c:
                    c.execute(text(sql))

        def clone(**changes) -> str:
            cols = {"id": "CAST(:nid AS uuid)", "revision_no": "2", "prior_consequence_revision_id": "id",
                    "consequence_basis_sha256": "repeat('b', 64)", **changes}
            with engine.connect() as c:
                names = [r[0] for r in c.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = "
                    "'financial_consequence_revision' ORDER BY ordinal_position"))]
            select = ", ".join(cols.get(n, n) for n in names)
            return (f"INSERT INTO financial_consequence_revision ({', '.join(names)}) SELECT {select} "
                    "FROM financial_consequence_revision WHERE id = :id")

        for changes, message in (
            ({"amount_high": "amount_high + 0.01"}, "financial_consequence_priced_amount"),
            ({"amount_low": "0.01"}, "financial_consequence_priced_amount"),
            ({"state": "'UNPRICED'"}, "financial_consequence_unpriced"),
            ({"state": "'QUANTITY_UNAVAILABLE'", "quantity_state": "'QUANTITY_UNAVAILABLE'",
              "quantity_reason": "'POWER_MISSING'", "price_state": "'NOT_EVALUATED'", "price_revision_id": "NULL",
              "price_value": "NULL", "price_currency": "NULL", "amount_low": "NULL", "amount_high": "NULL",
              "currency": "NULL", "price_considered": "'[]'::jsonb"}, "financial_consequence_unavailable_has_no_number"),
            # Review L5: only `unpriced_has_no_amount` fails (UNPRICED with a valid reason but an amount).
            ({"state": "'UNPRICED'", "price_state": "'UNPRICED'", "price_reason": "'NO_PRICE'",
              "price_revision_id": "NULL", "price_value": "NULL", "price_currency": "NULL"},
             "financial_consequence_unpriced_has_no_amount"),
            # Review L6: a priced row's value must be its price revision's own.
            ({"price_value": "price_value + 1", "amount_high": "quantity_high * (price_value + 1)"},
             "not its price revision's value and currency"),
            ({"window_end": "window_end + interval '1 minute'"}, "not its FindingRevision window"),
            ({"revision_no": "3"}, "extend its chain by one"),
        ):
            with pytest.raises(DBAPIError, match=message):
                with engine.begin() as c:
                    c.execute(text(clone(**changes)), {"nid": str(uuid4()), "id": cid})
        # Review L6, at commit: a PRICED row without its PRICE link, or without its assessment links, is refused.
        with pytest.raises(DBAPIError, match="PRICED without its PRICE link"):
            with engine.begin() as c:
                c.execute(text(clone()), {"nid": str(uuid4()), "id": cid})
        # Review 2a L2: the assessment-completeness half on its own. An UNPRICED clone needs no PRICE link, so only
        # the missing assessment links can refuse it.
        with pytest.raises(DBAPIError, match="does not link every INTERVAL assessment of its FindingRevision"):
            with engine.begin() as c:
                c.execute(text(clone(state="'UNPRICED'", price_state="'UNPRICED'", price_reason="'NO_PRICE'",
                                     price_revision_id="NULL", price_value="NULL", price_currency="NULL",
                                     amount_low="NULL", amount_high="NULL", currency="NULL",
                                     price_considered="'[]'::jsonb")), {"nid": str(uuid4()), "id": cid})
        # A link to an assessment that is not one of the FindingRevision's INTERVAL assessments is refused.
        with engine.connect() as c:
            other = c.execute(text(
                "SELECT assessment_revision_id, analytic_run_id FROM finding_revision_assessment "
                "WHERE finding_revision_id <> :r AND scope = 'INTERVAL' LIMIT 1"), {"r": rev["id"]}).first()
        assert other is not None
        with pytest.raises(DBAPIError, match="not an INTERVAL assessment of its FindingRevision"):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO financial_consequence_assessment_revision VALUES (:c, :t, :s, :a, :run, false)"),
                    {"c": cid, "t": site.tenant, "s": site.site, "a": other[0], "run": other[1]})
        assert UUID(str(cid))


class TestReviewCarries:
    def test_a_later_succession_leaves_the_october_basis_unchanged_and_append_replays(self, site) -> None:
        """Review M1: v2 (SUCCESSION from 2030) re-IDs v1's assignment; October's consequence must replay."""
        site.publish("v1")
        rev = site.on(POWER_DAY)
        first_c = site.derive(rev)
        first = site.store.append(first_c)
        (v2,) = site.publish("v2")
        assert v2["change_kind"] == "SUCCESSION"
        again = site.derive(rev)
        assert again.price.assignment_id != first_c.price.assignment_id  # the assignment was re-issued
        assert again.price.considered == first_c.price.considered and again.basis_sha256 == first_c.basis_sha256
        replay = site.store.append(again)
        assert replay.replayed and replay.consequence_revision_id == first.consequence_revision_id
        (row,) = site.store.rows(site.tenant, site.site)["financial_consequence_revision"]
        assert row["price_considered"] == [[list(x) for x in again.price.considered][0]]

    def test_a_zero_width_finding_revision_is_not_blocked_by_its_work_row(self, site, engine) -> None:  # noqa: F811
        """Review L1: 0009 allows `episode_start = episode_end`; the dirty-work trigger must accept it."""
        rev = site.on(STATE_DAY)
        with engine.connect() as c:
            names = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding_revision' "
                "ORDER BY ordinal_position"))]
        cols = {"id": "CAST(:nid AS uuid)", "revision_no": "revision_no + 1000", "episode_end": "episode_start",
                "basis_sha256": "repeat('c', 64)"}
        nid = uuid4()
        with engine.begin() as c:
            c.execute(text(f"INSERT INTO finding_revision ({', '.join(names)}) SELECT "
                           f"{', '.join(cols.get(n, n) for n in names)} FROM finding_revision WHERE id = :id"),
                      {"nid": str(nid), "id": rev["id"]})
        (w,) = [w for w in site.store.rows(site.tenant, site.site)["financial_consequence_work"]
                if w["finding_revision_id"] == nid]
        assert w["affected_from"] == w["affected_to"] == rev["episode_start"]

    def test_upgrade_enqueues_finding_revisions_recorded_before_0011(self, site_before_0029, engine) -> None:  # noqa: F811
        """Review L4: a database upgraded from 0010 has work for every existing FindingRevision."""
        site = site_before_0029
        from alembic import command
        from alembic.config import Config
        from test_s1_bindings_postgres import BACKEND

        config = Config(str(BACKEND / "alembic.ini"))
        config.attributes["database_url"] = URL
        site.store.dispose()
        __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
        command.downgrade(config, "0010_financial_assumptions")
        command.upgrade(config, "head")
        with engine.connect() as c:
            revisions = set(c.execute(text("SELECT id FROM finding_revision WHERE site_id = :s"),
                                      {"s": site.site}).scalars())
        work = site.store.rows(site.tenant, site.site)["financial_consequence_work"]
        assert revisions and {w["finding_revision_id"] for w in work} == revisions
        assert all(w["cause"] == "FINDING_REVISION_APPENDED" for w in work)


class TestMigration0015Downgrade:
    """LR-01 fix round (review L2): the 0015 downgrade refuses to erase a returning basis."""

    @staticmethod
    def _config():
        from alembic.config import Config
        from test_s1_bindings_postgres import BACKEND

        config = Config(str(BACKEND / "alembic.ini"))
        config.attributes["database_url"] = URL
        return config

    @staticmethod
    def _basis_constraint(engine) -> bool:  # noqa: F811
        with engine.connect() as c:
            return bool(c.execute(text("SELECT 1 FROM pg_constraint WHERE conname = 'finding_revision_basis_unique'"))
                        .first())

    def test_downgrade_refuses_while_a_returning_basis_exists_and_keeps_history(self, site_before_0029, engine) -> None:  # noqa: F811
        site = site_before_0029
        from alembic import command
        from sqlalchemy.exc import DBAPIError

        rev = site.on(STATE_DAY)
        with engine.connect() as c:
            names = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'finding_revision' "
                "ORDER BY ordinal_position"))]
        cols = {"id": "CAST(:nid AS uuid)", "revision_no": "revision_no + 1"}  # the same basis and transition again
        with engine.begin() as c:
            c.execute(text(f"INSERT INTO finding_revision ({', '.join(names)}) SELECT "
                           f"{', '.join(cols.get(n, n) for n in names)} FROM finding_revision WHERE id = :id"),
                      {"nid": str(uuid4()), "id": rev["id"]})
        site.store.dispose()
        with pytest.raises(DBAPIError, match="returning basis"):
            __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
            command.downgrade(self._config(), "0014_source_clock_attestation")
        with engine.connect() as c:
            count = c.execute(text("SELECT count(*) FROM finding_revision WHERE finding_id = :f"),
                              {"f": rev["finding_id"]}).scalar_one()
            version = c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert count == 2 and version == "0035_w5_ev_work"
        assert not self._basis_constraint(engine)

    def test_downgrade_without_a_returning_basis_restores_the_constraint(self, site_before_0029, engine) -> None:  # noqa: F811
        site = site_before_0029
        from alembic import command

        site.on(STATE_DAY)
        site.store.dispose()
        config = self._config()
        try:
            __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
            command.downgrade(config, "0014_source_clock_attestation")
            assert self._basis_constraint(engine)
        finally:
            command.upgrade(config, "head")
        assert not self._basis_constraint(engine)
