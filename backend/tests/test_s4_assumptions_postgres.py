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


def run_fixture(prices, capsys, *steps: str, file: Path = FIXTURE) -> list[dict]:
    args = ["fixture", "--site", "KOBO-001", "--file", str(file)]
    for step in steps:
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

    def test_replay_from_a_modified_fixture_copy_returns_the_stored_ids(self, site, prices, engine, capsys,  # noqa: F811
                                                                         tmp_path) -> None:
        """Review M1: an appended step, a bumped version and CRLF line endings do not break replay."""
        out = run_fixture(prices, capsys)
        before = counts(engine)
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
        doc["version"] += 1
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
