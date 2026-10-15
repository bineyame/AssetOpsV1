"""S4-02a phase 1: assumption store and SYSTEM publication (PostgreSQL, migration 0010).

Fixture v1 (INITIAL, backdated, open-ended) -> v2 (SUCCESSION, future) -> v3 (middle-only CORRECTION) through the
server-side CLI, then a fresh store/engine (restart) re-reads persisted IDs, exact value text and set-once
`recorded_to`. One negative per change_kind, idempotent retry, prior mismatch, concurrency and the
database-level guards (exclusion, containment, set-once, append-only, finite nonnegative value).
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication, PublicationRefused
    from assetops_backend.publish_assumption import main as publish_main

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = BACKEND / "conversions" / "demo-diesel-price-publications.json"
KEY = "diesel_price_per_litre"
UTC = timezone.utc


def _t(y: int, m: int, d: int = 1) -> datetime:
    return datetime(y, m, d, tzinfo=UTC)


# The future SUCCESSION's start, read from the fixture rather than repeated here (review M2).
V2_START = datetime.fromisoformat(
    json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"][1]["valid_from"].replace("Z", "+00:00"))


@pytest.fixture()
def site(store):  # noqa: F811
    result = imported(store)
    return result.tenant.id, result.site.id


@pytest.fixture()
def prices():
    s = PostgresAssumptionStore(URL)
    yield s
    s.dispose()


# The S4-02a history these tests prove. S4-02b appends v4 (an October 2026 correction, carry C3); a run of the
# whole fixture is proved separately in `test_v4_october_correction_appends_and_replays_safely`.
S4_02A_STEPS = ("v1", "v2", "v3")


def run_fixture(prices, capsys, *steps: str, file: Path = FIXTURE, every_step: bool = False) -> list[dict]:
    args = ["fixture", "--site", "KOBO-001", "--file", str(file)]
    for step in steps or (() if every_step else S4_02A_STEPS):
        args += ["--step", step]
    code = publish_main(args, store=prices)
    out = capsys.readouterr()
    assert code == 0, out.err
    return [json.loads(line) for line in out.out.splitlines()]


def pub(prior, key, kind="INITIAL", vf=_t(2026, 1), vt=None, value="1.25", reason=None) -> Publication:
    return Publication(assumption_key=KEY, currency="USD", value=Decimal(value), basis="AUTHORED_ESTIMATE",
                       source_reference="test source", valid_from=vf, valid_to=vt, change_kind=kind,
                       correction_reason=reason, expected_prior_revision_id=prior, idempotency_key=key,
                       channel="SYSTEM_CLI", provenance={"service": "test"})


def counts(engine):  # noqa: F811
    with engine.connect() as c:
        return (c.execute(text("SELECT count(*) FROM financial_assumption_revision")).scalar_one(),
                c.execute(text("SELECT count(*) FROM financial_assumption_assignment")).scalar_one())


def selected(rows, valid_at: datetime, recorded_at: datetime | None = None):
    """The revision assigned at `valid_at` as known at `recorded_at` (None: current). Half-open on both axes."""
    hits = [r for r in rows
            if r["valid_from"] <= valid_at and (r["valid_to"] is None or valid_at < r["valid_to"])
            and (r["recorded_to"] is None if recorded_at is None
                 else r["recorded_from"] <= recorded_at and (r["recorded_to"] is None or recorded_at < r["recorded_to"]))]
    assert len(hits) <= 1
    return hits[0]["revision_id"] if hits else None


def refused(work) -> PublicationRefused:
    with pytest.raises(PublicationRefused) as caught:
        work()
    return caught.value


class TestFixtureHistorySurvivesRestart:
    def test_v1_initial_v2_succession_v3_middle_correction(self, site, prices, engine, capsys) -> None:  # noqa: F811
        tenant_id, site_id = site
        out = run_fixture(prices, capsys)
        assert [(o["step"], o["change_kind"], o["revision_no"], o["replayed"]) for o in out] == [
            ("v1", "INITIAL", 1, False), ("v2", "SUCCESSION", 2, False), ("v3", "CORRECTION", 3, False)]
        v1, v2, v3 = (o["revision_id"] for o in out)

        prices.dispose()  # restart: a new engine and a new store read only what was persisted
        fresh = PostgresAssumptionStore(URL)
        revisions = fresh.revisions(tenant_id, site_id, KEY)
        assignments = fresh.assignments(tenant_id, site_id, KEY)
        assert [str(r["id"]) for r in revisions] == [v1, v2, v3]
        assert [str(r["value"]) for r in revisions] == ["1.25", "1.32", "1.19"]
        assert all(r["actor_kind"] == "SYSTEM" and r["actor_id"] == SYSTEM_PUBLISHER.actor_id
                   and r["author_id"] is None and r["channel"] == "SYSTEM_FIXTURE" for r in revisions)
        assert [r["prior_revision_id"] for r in revisions] == [None, revisions[0]["id"], revisions[1]["id"]]
        assert revisions[2]["correction_reason"].startswith("Demonstration correction")
        assert revisions[0]["provenance"]["fixture_step"] == "v1"
        with engine.connect() as c:
            assert c.execute(text("SELECT array_agg(value::text ORDER BY revision_no) FROM "
                                  "financial_assumption_revision")).scalar_one() == ["1.25", "1.32", "1.19"]
        r1, r2, r3 = (r["recorded_at"] for r in revisions)
        assert r1 < r2 < r3

        shape = sorted(((str(a["revision_id"]), a["valid_from"], a["valid_to"], a["recorded_from"],
                         a["recorded_to"]) for a in assignments), key=str)
        assert shape == sorted([
            (v1, _t(2026, 1), None, r1, r2),                 # original v1, closed by the succession
            (v1, _t(2026, 1), V2_START, r2, r3),          # v1 truncated at v2, closed by the correction
            (v2, V2_START, None, r2, None),               # future v2, still current
            (v1, _t(2026, 1), _t(2026, 6), r3, None),        # left remainder keeps v1
            (v1, _t(2026, 7), V2_START, r3, None),        # right remainder keeps v1
            (v3, _t(2026, 6), _t(2026, 7), r3, None),        # corrected middle
        ], key=str)
        ids = {str(r["id"]): r["id"] for r in revisions}
        # Current selection, both boundaries half-open.
        assert selected(assignments, _t(2026, 5, 31)) == ids[v1]
        assert selected(assignments, _t(2026, 6)) == ids[v3]
        assert selected(assignments, _t(2026, 7)) == ids[v1]
        assert selected(assignments, V2_START - timedelta(microseconds=1)) == ids[v1]
        assert selected(assignments, V2_START) == ids[v2]
        assert selected(assignments, _t(2025, 12, 31)) is None
        # Older recorded cutoffs still select what was known then.
        assert selected(assignments, _t(2026, 6, 15), r1) == ids[v1]
        assert selected(assignments, V2_START + timedelta(days=31), r1) == ids[v1]
        assert selected(assignments, V2_START + timedelta(days=31), r2) == ids[v2]
        assert selected(assignments, _t(2026, 6, 15), r2) == ids[v1]
        assert selected(assignments, _t(2026, 6, 15), r3) == ids[v3]
        assert selected(assignments, _t(2026, 6, 15), r1 - timedelta(microseconds=1)) is None

        # Re-running the whole fixture replays every step: same IDs, nothing new, recorded_to unchanged.
        before = counts(engine)
        again = run_fixture(PostgresAssumptionStore(URL), capsys)
        assert [o["revision_id"] for o in again] == [v1, v2, v3] and all(o["replayed"] for o in again)
        assert counts(engine) == before
        assert sorted(map(str, (a["recorded_to"] for a in fresh.assignments(tenant_id, site_id, KEY)))) == \
            sorted(map(str, (a["recorded_to"] for a in assignments)))
        fresh.dispose()

    def test_v4_october_correction_appends_and_replays_safely(self, site, prices, engine, capsys) -> None:  # noqa: F811
        """S4-02a carry C3: a Site already published with v1-v3 takes the appended v4 Finding-window correction;
        every earlier step replays with its stored ID and a second full run writes nothing."""
        tenant_id, site_id = site
        earlier = run_fixture(prices, capsys)
        full = run_fixture(prices, capsys, every_step=True)
        assert [o["step"] for o in full] == ["v1", "v2", "v3", "v4"]
        assert [o["revision_id"] for o in full[:3]] == [o["revision_id"] for o in earlier]
        assert [o["replayed"] for o in full] == [True, True, True, False]
        assert (full[3]["change_kind"], full[3]["revision_no"]) == ("CORRECTION", 4)
        before = counts(engine)
        again = run_fixture(prices, capsys, every_step=True)
        assert all(o["replayed"] for o in again) and counts(engine) == before
        v1, v4 = UUID(full[0]["revision_id"]), UUID(full[3]["revision_id"])
        current = sorted((a["revision_id"], a["valid_from"], a["valid_to"])
                         for a in prices.assignments(tenant_id, site_id, KEY) if a["recorded_to"] is None
                         if _t(2026, 7) <= a["valid_from"] < V2_START)
        assert current == sorted([(v1, _t(2026, 7), _t(2026, 10)), (v4, _t(2026, 10), _t(2026, 11)),
                                  (v1, _t(2026, 11), V2_START)])
        assert selected(prices.assignments(tenant_id, site_id, KEY), datetime(2026, 10, 6, 8, tzinfo=UTC)) == v4

    def test_replay_from_a_modified_fixture_copy_returns_the_stored_ids(self, site, prices, engine, capsys,  # noqa: F811
                                                                         tmp_path) -> None:
        """Review M1: an appended step, a bumped version and CRLF line endings do not break replay."""
        out = run_fixture(prices, capsys)
        before = counts(engine)
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc["version"] += 1
        doc["steps"] = doc["steps"][:3]
        doc["steps"].append({**doc["steps"][2], "step": "v4", "expected_prior_step": "v3",
                             "idempotency_key": "demo-diesel-price-v4-test", "value": "1.21",
                             "valid_from": "2026-08-01T00:00:00Z", "valid_to": "2026-09-01T00:00:00Z"})
        copy = tmp_path / "modified.json"
        copy.write_bytes(json.dumps(doc, indent=2).replace("\n", "\r\n").encode("utf-8"))
        assert b"\r\n" in copy.read_bytes()
        again = run_fixture(prices, capsys, "v1", "v2", "v3", file=copy)
        assert [o["revision_id"] for o in again] == [o["revision_id"] for o in out]
        assert all(o["replayed"] for o in again)
        assert counts(engine) == before
        # The appended step publishes normally after the replayed ones.
        (v4,) = run_fixture(prices, capsys, "v4", file=copy)
        assert (v4["revision_no"], v4["replayed"]) == (4, False)

    def test_closing_a_current_row_before_the_series_latest_start_is_refused(self, site, prices, engine,  # noqa: F811
                                                                              capsys) -> None:
        """Review L1: a retroactive close at recorded_from + 1us would rewrite what earlier cutoffs select."""
        run_fixture(prices, capsys)
        with pytest.raises(DBAPIError, match="not later than the series"):
            with engine.begin() as c:
                c.execute(text("UPDATE financial_assumption_assignment SET recorded_to = recorded_from "
                               "+ interval '1 microsecond' WHERE recorded_to IS NULL"))
        with pytest.raises(DBAPIError, match="not later than the series"):
            with engine.begin() as c:
                c.execute(text("UPDATE financial_assumption_assignment SET recorded_to = (SELECT max(recorded_from) "
                               "FROM financial_assumption_assignment) WHERE recorded_to IS NULL"))

    def test_database_refuses_rewrites_of_history(self, site, prices, engine, capsys) -> None:  # noqa: F811
        run_fixture(prices, capsys)
        for sql, message in (
            ("UPDATE financial_assumption_revision SET value = 9 WHERE revision_no = 1", "append-only"),
            ("DELETE FROM financial_assumption_revision WHERE revision_no = 3", "append-only"),
            # Moving a closed recorded_to earlier overlaps nothing, so only the set-once trigger refuses it.
            ("UPDATE financial_assumption_assignment SET recorded_to = recorded_to - interval '1 microsecond' "
             "WHERE recorded_to IS NOT NULL", "already closed"),
            ("UPDATE financial_assumption_assignment SET valid_to = valid_to - interval '1 day' "
             "WHERE recorded_to IS NULL AND valid_to IS NOT NULL", "immutable"),
            ("DELETE FROM financial_assumption_assignment", "DELETE refused"),
        ):
            with pytest.raises(DBAPIError, match=message):
                with engine.begin() as c:
                    c.execute(text(sql))


class TestNegativePerChangeKind:
    def test_initial_overlapping_a_current_assignment_is_409(self, site, prices, engine) -> None:  # noqa: F811
        v1 = prices.publish(*site, pub(None, "a"), SYSTEM_PUBLISHER)
        before = counts(engine)
        error = refused(lambda: prices.publish(*site, pub(v1.revision_id, "b", vf=_t(2026, 3), vt=_t(2026, 4)),
                                               SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (409, "INITIAL_OVERLAPS_CURRENT")
        assert counts(engine) == before
        # INITIAL into time with no current price is accepted (backdated, bounded).
        gap = prices.publish(*site, pub(v1.revision_id, "c", vf=_t(2025, 6), vt=_t(2026, 1)), SYSTEM_PUBLISHER)
        assert gap.revision_no == 2

    def test_succession_overlapping_more_than_the_open_ended_assignment_is_409(self, site, prices, engine,  # noqa: F811
                                                                                capsys) -> None:
        out = run_fixture(prices, capsys, "v1", "v2")
        before = counts(engine)
        # Before v2's start, so it overlaps the truncated v1 as well as v2's open tail.
        soon = V2_START - timedelta(days=30)
        assert soon > datetime.now(UTC) + timedelta(days=1), "fixture v2 must start well in the future"
        error = refused(lambda: prices.publish(*site, pub(UUID(out[1]["revision_id"]), "s",
                                                          kind="SUCCESSION", vf=soon), SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (409, "SUCCESSION_OVERLAP_NOT_PERMITTED")
        backdated = refused(lambda: prices.publish(*site, pub(UUID(out[1]["revision_id"]), "s2",
                                                              kind="SUCCESSION", vf=_t(2026, 2)), SYSTEM_PUBLISHER))
        assert backdated.code == "SUCCESSION_NOT_FUTURE"
        assert counts(engine) == before

    def test_correction_without_a_reason_is_refused(self, site, prices, engine) -> None:  # noqa: F811
        v1 = prices.publish(*site, pub(None, "a"), SYSTEM_PUBLISHER)
        before = counts(engine)
        error = refused(lambda: prices.publish(*site, pub(v1.revision_id, "c", kind="CORRECTION", vf=_t(2026, 6),
                                                          vt=_t(2026, 7)), SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (422, "CORRECTION_REASON_REQUIRED")
        nothing = refused(lambda: prices.publish(*site, pub(v1.revision_id, "d", kind="CORRECTION", vf=_t(2025, 1),
                                                            vt=_t(2025, 2), reason="r"), SYSTEM_PUBLISHER))
        assert (nothing.status, nothing.code) == (409, "CORRECTION_NOTHING_TO_CORRECT")
        assert counts(engine) == before


class TestRetryPriorAndConcurrency:
    def test_exact_retry_returns_the_same_id_and_conflicting_retry_is_refused(self, site, prices, engine) -> None:  # noqa: F811
        first = prices.publish(*site, pub(None, "k1"), SYSTEM_PUBLISHER)
        again = prices.publish(*site, pub(None, "k1"), SYSTEM_PUBLISHER)
        assert (again.revision_id, again.replayed, again.recorded_at) == (first.revision_id, True, first.recorded_at)
        error = refused(lambda: prices.publish(*site, pub(None, "k1", value="1.26"), SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (409, "IDEMPOTENCY_KEY_REUSED")
        assert counts(engine) == (1, 1)

    def test_stale_expected_prior_is_refused(self, site, prices, engine) -> None:  # noqa: F811
        v1 = prices.publish(*site, pub(None, "a", vt=_t(2026, 3)), SYSTEM_PUBLISHER)
        stale = refused(lambda: prices.publish(*site, pub(None, "b", vf=_t(2026, 3)), SYSTEM_PUBLISHER))
        assert (stale.status, stale.code) == (409, "PRIOR_REVISION_MISMATCH")
        assert prices.publish(*site, pub(v1.revision_id, "b", vf=_t(2026, 3)), SYSTEM_PUBLISHER).revision_no == 2

    def test_concurrent_publications_against_one_prior_admit_exactly_one(self, site, prices, engine) -> None:  # noqa: F811
        v1 = prices.publish(*site, pub(None, "a", vt=_t(2026, 2)), SYSTEM_PUBLISHER)
        barrier, results = threading.Barrier(4), []

        def attempt(i: int) -> None:
            own = PostgresAssumptionStore(URL)
            barrier.wait()
            try:
                results.append(own.publish(*site, pub(v1.revision_id, f"race-{i}", vf=_t(2026, 2 + i),
                                                      vt=_t(2026, 3 + i)), SYSTEM_PUBLISHER))
            except PublicationRefused as error:
                results.append(error)
            finally:
                own.dispose()

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        won = [r for r in results if not isinstance(r, PublicationRefused)]
        lost = [r for r in results if isinstance(r, PublicationRefused)]
        assert len(won) == 1 and won[0].revision_no == 2
        assert [e.code for e in lost] == ["PRIOR_REVISION_MISMATCH"] * 3
        assert counts(engine) == (2, 2)

    def test_concurrent_exact_retries_return_one_revision(self, site, prices, engine) -> None:  # noqa: F811
        barrier, results = threading.Barrier(3), []

        def attempt() -> None:
            own = PostgresAssumptionStore(URL)
            barrier.wait()
            try:
                results.append(own.publish(*site, pub(None, "same"), SYSTEM_PUBLISHER))
            finally:
                own.dispose()

        threads = [threading.Thread(target=attempt) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len({r.revision_id for r in results}) == 1
        assert sorted(r.replayed for r in results) == [False, True, True]
        assert counts(engine) == (1, 1)


class TestDatabaseGuards:
    def _revision(self, c, tenant_id, site_id, value="1.00", vf=_t(2026, 1), vt=None):
        rid = uuid4()
        c.execute(text(
            "INSERT INTO financial_assumption_revision (id, tenant_id, site_id, assumption_key, revision_no, "
            "currency, unit, value, basis, source_reference, valid_from, valid_to, recorded_at, change_kind, "
            "actor_kind, actor_id, channel, authorization_basis, provenance, idempotency_key, request_sha256) "
            "VALUES (:id, :t, :s, 'diesel_price_per_litre', 1, 'USD', 'currency/L', CAST(:v AS numeric), "
            "'AUTHORED_ESTIMATE', 'x', :vf, :vt, clock_timestamp(), 'INITIAL', 'SYSTEM', 'svc', 'SYSTEM_CLI', 'x', "
            "'{}', :k, repeat('0', 64))"),
            {"id": rid, "t": tenant_id, "s": site_id, "v": value, "vf": vf, "vt": vt, "k": str(rid)})
        return rid

    @pytest.mark.parametrize("value", ["-1", "NaN", "Infinity"])
    def test_value_must_be_finite_and_nonnegative(self, site, engine, value) -> None:  # noqa: F811
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                self._revision(c, *site, value=value)

    def test_assignment_outside_its_revision_range_is_refused(self, site, engine) -> None:  # noqa: F811
        with pytest.raises(DBAPIError, match="outside its revision"):
            with engine.begin() as c:
                rid = self._revision(c, *site, vt=_t(2026, 6))
                c.execute(text(
                    "INSERT INTO financial_assumption_assignment (id, tenant_id, site_id, assumption_key, revision_id, "
                    "publication_revision_id, valid_from, valid_to, recorded_from) VALUES (:id, :t, :s, "
                    "'diesel_price_per_litre', :r, :r, :vf, NULL, clock_timestamp())"),
                    {"id": uuid4(), "t": site[0], "s": site[1], "r": rid, "vf": _t(2026, 1)})

    def test_overlapping_assignments_at_one_recorded_instant_are_excluded(self, site, engine) -> None:  # noqa: F811
        with pytest.raises(DBAPIError, match="financial_assumption_assignment_no_overlap"):
            with engine.begin() as c:
                rid = self._revision(c, *site)
                for vf in (_t(2026, 1), _t(2026, 3)):
                    c.execute(text(
                        "INSERT INTO financial_assumption_assignment (id, tenant_id, site_id, assumption_key, "
                        "revision_id, publication_revision_id, valid_from, valid_to, recorded_from) VALUES (:id, :t, "
                        ":s, 'diesel_price_per_litre', :r, :r, :vf, NULL, clock_timestamp())"),
                        {"id": uuid4(), "t": site[0], "s": site[1], "r": rid, "vf": vf})

    def test_empty_ranges_are_refused(self, site, engine) -> None:  # noqa: F811
        with pytest.raises(DBAPIError, match="valid_range"):
            with engine.begin() as c:
                self._revision(c, *site, vf=_t(2026, 2), vt=_t(2026, 2))


class TestEqualStartSuccession:
    """S4-06 (`I-price-equal-start-succession`, Architect S4-02 Q1): a SUCCESSION exactly at the sole open-ended
    future assignment's `valid_from` replaces it from that instant; earlier recorded cutoffs keep the schedule."""

    @staticmethod
    def future() -> datetime:
        return (datetime.now(UTC) + timedelta(days=30)).replace(microsecond=0)

    @staticmethod
    def timeline(prices, site, cutoff):
        return prices.snapshot(*site, KEY, cutoff, 0, 50)["timeline"]

    def test_succession_at_the_scheduled_start_replaces_it_and_keeps_history(self, site, prices, engine) -> None:  # noqa: F811
        start = self.future()
        scheduled = prices.publish(*site, pub(None, "sched", vf=start, value="1.40"), SYSTEM_PUBLISHER)
        (old,) = self.timeline(prices, site, None)
        succ = prices.publish(*site, pub(scheduled.revision_id, "succ", kind="SUCCESSION", vf=start, value="1.55"),
                              SYSTEM_PUBLISHER)
        assert (succ.revision_no, succ.change_kind, succ.replayed) == (2, "SUCCESSION", False)
        assert counts(engine) == (2, 2)  # no zero-length left row was written

        (new,) = self.timeline(prices, site, None)
        assert (new["revision_id"], new["publication_revision_id"]) == (succ.revision_id, succ.revision_id)
        assert (new["valid_from"], new["valid_to"], new["recorded_from"], new["recorded_to"]) == \
            (start, None, succ.recorded_at, None)
        rows = prices.assignments(*site, KEY)
        assert all(r["valid_to"] is None or r["valid_from"] < r["valid_to"] for r in rows)
        closed = next(r for r in rows if r["id"] == old["id"])
        # Exact boundary continuity: same valid start, and the old tenure ends where the new one begins.
        assert (closed["valid_from"], closed["valid_to"]) == (start, None)
        assert (closed["recorded_from"], closed["recorded_to"]) == (scheduled.recorded_at, succ.recorded_at)

        # Before publication the schedule is what was known; from the publication instant, the replacement.
        before = succ.recorded_at - timedelta(microseconds=1)
        (was,) = self.timeline(prices, site, before)
        assert (was["id"], was["revision_id"]) == (old["id"], scheduled.revision_id)
        assert selected(rows, start, before) == scheduled.revision_id
        assert selected(rows, start + timedelta(days=400), before) == scheduled.revision_id
        for cutoff in (succ.recorded_at, succ.recorded_at + timedelta(days=1)):
            (now,) = self.timeline(prices, site, cutoff)
            assert (now["id"], now["revision_id"]) == (new["id"], succ.revision_id)
            assert selected(rows, start, cutoff) == succ.revision_id
        assert selected(rows, start - timedelta(microseconds=1)) is None
        cited = prices.snapshot(*site, KEY, before, 0, 50)["cited"]
        assert str(cited[scheduled.revision_id]["value"]) == "1.40"
        assert str(prices.snapshot(*site, KEY, None, 0, 50)["cited"][succ.revision_id]["value"]) == "1.55"

        # Exact retry replays; the same key with changed content and a stale prior are refused, writing nothing.
        again = prices.publish(*site, pub(scheduled.revision_id, "succ", kind="SUCCESSION", vf=start, value="1.55"),
                               SYSTEM_PUBLISHER)
        assert (again.revision_id, again.replayed, again.recorded_at) == (succ.revision_id, True, succ.recorded_at)
        reused = refused(lambda: prices.publish(*site, pub(scheduled.revision_id, "succ", kind="SUCCESSION",
                                                           vf=start, value="1.60"), SYSTEM_PUBLISHER))
        assert (reused.status, reused.code) == (409, "IDEMPOTENCY_KEY_REUSED")
        stale = refused(lambda: prices.publish(*site, pub(scheduled.revision_id, "late", kind="SUCCESSION",
                                                          vf=start, value="1.60"), SYSTEM_PUBLISHER))
        assert (stale.status, stale.code) == (409, "PRIOR_REVISION_MISMATCH")
        assert counts(engine) == (2, 2)

    def test_two_equal_start_publishers_on_one_prior_admit_exactly_one(self, site, prices, engine) -> None:  # noqa: F811
        start = self.future()
        scheduled = prices.publish(*site, pub(None, "sched", vf=start), SYSTEM_PUBLISHER)
        barrier, results = threading.Barrier(2), []

        def attempt(i: int) -> None:
            own = PostgresAssumptionStore(URL)
            barrier.wait()
            try:
                results.append(own.publish(*site, pub(scheduled.revision_id, f"race-{i}", kind="SUCCESSION",
                                                      vf=start, value=f"1.5{i}"), SYSTEM_PUBLISHER))
            except PublicationRefused as error:
                results.append(error)
            finally:
                own.dispose()

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        won = [r for r in results if not isinstance(r, PublicationRefused)]
        lost = [r for r in results if isinstance(r, PublicationRefused)]
        assert len(won) == 1 and won[0].revision_no == 2
        assert [(e.status, e.code) for e in lost] == [(409, "PRIOR_REVISION_MISMATCH")]
        assert counts(engine) == (2, 2)
        (current,) = self.timeline(prices, site, None)
        assert (current["revision_id"], current["valid_from"]) == (won[0].revision_id, start)

    def test_bounded_or_multiple_overlap_at_an_equal_start_is_refused(self, site, prices, engine) -> None:  # noqa: F811
        start = self.future()
        bounded = prices.publish(*site, pub(None, "b", vf=start, vt=start + timedelta(days=60)), SYSTEM_PUBLISHER)
        before = counts(engine)
        error = refused(lambda: prices.publish(*site, pub(bounded.revision_id, "s1", kind="SUCCESSION", vf=start),
                                               SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (409, "SUCCESSION_OVERLAP_NOT_PERMITTED")
        assert counts(engine) == before
        tail = prices.publish(*site, pub(bounded.revision_id, "t", vf=start + timedelta(days=60)), SYSTEM_PUBLISHER)
        before = counts(engine)
        error = refused(lambda: prices.publish(*site, pub(tail.revision_id, "s2", kind="SUCCESSION", vf=start),
                                               SYSTEM_PUBLISHER))
        assert (error.status, error.code) == (409, "SUCCESSION_OVERLAP_NOT_PERMITTED")
        assert counts(engine) == before

    def test_equal_start_replaces_a_correction_tail_on_an_older_revision(self, site, prices, engine) -> None:  # noqa: F811
        start = self.future()
        v1 = prices.publish(*site, pub(None, "v1", vf=start, value="1.40"), SYSTEM_PUBLISHER)
        mid, tail_start = start + timedelta(days=10), start + timedelta(days=20)
        v2 = prices.publish(*site, pub(v1.revision_id, "v2", kind="CORRECTION", vf=mid, vt=tail_start, value="1.45",
                                       reason="supplier quote"), SYSTEM_PUBLISHER)
        tail = next(a for a in self.timeline(prices, site, None) if a["valid_to"] is None)
        assert (tail["revision_id"], tail["publication_revision_id"], tail["valid_from"]) == \
            (v1.revision_id, v2.revision_id, tail_start)  # the tail cites v1, older than the head v2
        v3 = prices.publish(*site, pub(v2.revision_id, "v3", kind="SUCCESSION", vf=tail_start, value="1.50"),
                            SYSTEM_PUBLISHER)
        shape = [(a["revision_id"], a["valid_from"], a["valid_to"]) for a in self.timeline(prices, site, None)]
        assert shape == [(v1.revision_id, start, mid), (v2.revision_id, mid, tail_start),
                         (v3.revision_id, tail_start, None)]
        assert counts(engine) == (3, 5)  # v1, v2's three rows, v3's one: no zero-length row
        before = v3.recorded_at - timedelta(microseconds=1)
        assert [a["id"] for a in self.timeline(prices, site, before) if a["valid_to"] is None] == [tail["id"]]

    def test_an_earlier_price_keeps_selecting_windows_that_do_not_cross_the_new_start(self, site, prices,  # noqa: F811
                                                                                       engine) -> None:
        from assetops_backend.financials import fuel_cost as fc

        start = self.future()
        earlier = prices.publish(*site, pub(None, "early", vf=_t(2026, 1), vt=start, value="1.20"), SYSTEM_PUBLISHER)
        scheduled = prices.publish(*site, pub(earlier.revision_id, "sched", vf=start, value="1.40"), SYSTEM_PUBLISHER)

        def price(cutoff, w0, w1):
            snap = prices.snapshot(*site, fc.PRICE_KEY, cutoff, 0, 50)
            return fc.select_window_price(snap["timeline"], snap["cited"], w0, w1)

        inside = (start - timedelta(days=2), start - timedelta(days=1))
        touching = (start - timedelta(days=1), start)
        crossing = (start - timedelta(hours=1), start + timedelta(hours=1))
        known = {w: price(None, *w) for w in (inside, touching, crossing)}
        assert known[inside].state == known[touching].state == "PRICED"
        assert known[inside].revision_id == known[touching].revision_id == str(earlier.revision_id)
        assert known[crossing].reason == "PRICE_SPANS_WINDOW"

        succ = prices.publish(*site, pub(scheduled.revision_id, "succ", kind="SUCCESSION", vf=start, value="1.55"),
                              SYSTEM_PUBLISHER)
        for w in (inside, touching):
            after = price(None, *w)
            assert (after.state, after.revision_id, after.assignment_id, after.value) == \
                (known[w].state, known[w].revision_id, known[w].assignment_id, Decimal("1.20"))
        assert price(None, *crossing).reason == "PRICE_SPANS_WINDOW"
        later = (start, start + timedelta(days=1))
        assert price(None, *later).revision_id == str(succ.revision_id)
        assert price(succ.recorded_at - timedelta(microseconds=1), *later).revision_id == str(scheduled.revision_id)
