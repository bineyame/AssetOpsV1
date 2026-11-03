"""CH-3 L2 (build sheet §8): the thread lifecycle on Postgres, through the CH-2 thread store, plus 0045 (CH3-R D-b).

Seeded with the CH-2 L2 fixture (F01/F02 on one generator thread, a real ACCEPTED mini Action and a raised domain
Action). The APPLIED action event and the VERIFIED outcome are added to the reader's lifecycle inputs (not to the
Action ledger), so this file proves the store, the triggers, idempotency and the bitemporal read; the Action and
verification ledgers keep their own L2 suites (`test_s6_*`).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import head

    import pg_harness
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.lifecycle_run import run_lifecycle


class _Reader:
    """The real reader, with extra mini action events / outcomes appended to its lifecycle inputs."""

    def __init__(self, real, events=(), outcomes=(), mini=True, lost=False) -> None:
        self.real, self.events, self.outcomes, self.mini, self.lost = real, list(events), list(outcomes), mini, lost

    def __getattr__(self, name):
        return getattr(self.real, name)

    def lifecycle_inputs(self, tenant_id, site_id):
        out = self.real.lifecycle_inputs(tenant_id, site_id)
        out["action_events"] = [*(out["action_events"] if self.mini else []), *self.events]
        out["outcomes"] = [*out["outcomes"], *self.outcomes]
        if self.lost:  # every occurrence's latest revision is NO_LONGER_SUPPORTED (the SUPPORT_LOST trigger)
            out["finding_lifecycle"] = {k: {**v, "lifecycle": "NO_LONGER_SUPPORTED"}
                                        for k, v in out["finding_lifecycle"].items()}
        return out


def _generator(engine, f01):
    with engine.connect() as c:
        tid = c.execute(text("SELECT thread_id FROM finding_thread_occurrence WHERE finding_id = :f"),
                        {"f": f01}).scalar_one()
        events = c.execute(text("SELECT seq, state, cause_kind, cause_known_at, recorded_at FROM finding_thread_event "
                                "WHERE thread_id = :t ORDER BY seq"), {"t": tid}).all()
        action = c.execute(text("SELECT action_id FROM chain_action_thread WHERE thread_id = :t AND action_kind = "
                                "'MINI_TRIAL'"), {"t": tid}).scalar_one()
        accepted = c.execute(text("SELECT recorded_at FROM action_event WHERE action_id = :a AND kind = 'ACCEPTED'"),
                             {"a": action}).scalar_one()
    return tid, events, action, accepted


def test_0045_head_and_columns(engine) -> None:  # noqa: F811
    assert head(engine) == pg_harness.alembic_head()
    with engine.connect() as c:
        cols = set(c.execute(text(
            "SELECT table_name || '.' || column_name FROM information_schema.columns WHERE column_name IN "
            "('cause_known_at', 'source_known_at') AND is_nullable = 'YES'")).scalars())
    assert cols == {"finding_thread_event.cause_known_at", "finding_thread_occurrence.source_known_at"}


def test_accept_apply_verify_rerun_and_bitemporal_read(seeded, engine) -> None:  # noqa: F811
    runner, reader, writer, f01, domain_id = seeded
    t, s = runner.tenant, runner.site
    run_threads(reader, writer, t, s, steps=("b", "c"))
    tid, events, action, accepted = _generator(engine, f01)
    assert [e[1] for e in events] == ["OPEN"] and events[0][3] is not None  # source revision's created_at

    # Accept (the real ACCEPTED event): ACTION_IN_HAND, carrying the action event's own recorded time.
    first = run_lifecycle(reader, writer, t, s)
    _, events, _, _ = _generator(engine, f01)
    assert [e[1] for e in events] == ["OPEN", "ACTION_IN_HAND"], first
    assert events[1][3] == accepted

    # Apply, then verify: CHANGE_APPLIED -> RESOLVED_MONITORING, each with its cause time.
    applied_at, verified_at = accepted + timedelta(hours=1), accepted + timedelta(days=1)
    more = _Reader(reader,
                   events=[{"id": uuid4(), "action_id": action, "kind": "APPLIED", "recorded_at": applied_at,
                            "effective_from": applied_at}],
                   outcomes=[{"id": uuid4(), "action_id": action, "outcome": "VERIFIED", "superseded": False,
                              "recorded_at": verified_at, "effective_from": verified_at, "later_end": None}])
    run_lifecycle(more, writer, t, s)
    _, events, _, _ = _generator(engine, f01)
    assert [e[1] for e in events] == ["OPEN", "ACTION_IN_HAND", "CHANGE_APPLIED", "RESOLVED_MONITORING"]
    assert [e[3] for e in events[2:]] == [applied_at, verified_at]

    # A rerun writes nothing.
    assert run_lifecycle(more, writer, t, s)["written"] == 0

    # Bitemporal read: at the ACCEPTED time the thread is in hand, although every row was recorded later.
    found = reader.lookup(t, [f01], [], known_at=accepted)["findings"][str(f01).lower()]
    assert found["state"] == "ACTION_IN_HAND"
    assert all(e[4] >= accepted for e in events)
    assert reader.lookup(t, [f01], [], known_at=None)["findings"][str(f01).lower()]["state"] == "RESOLVED_MONITORING"

    # Append-only holds for the new columns.
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            c.execute(text("UPDATE finding_thread_event SET cause_known_at = NULL WHERE thread_id = :t"), {"t": tid})

    # Downgrade of 0045 refuses while recorded cause times exist.
    from alembic import command

    engine.dispose()
    with pytest.raises(DBAPIError, match="Downgrade of 0045_thread_known_at refused"):
        command.downgrade(_alembic(), "0042_chain_threads")
    assert head(engine) == pg_harness.alembic_head()


def test_domain_raise_is_in_hand_and_support_lost_waits_for_the_action(seeded, engine) -> None:  # noqa: F811
    runner, reader, writer, f01, domain_id = seeded
    t, s = runner.tenant, runner.site
    run_threads(reader, writer, t, s, steps=("b", "c"))
    # Without the mini Action's events, the domain raise alone puts the thread in hand.
    report = run_lifecycle(_Reader(reader, mini=False), writer, t, s)
    with engine.connect() as c:
        dom = c.execute(text("SELECT e.state, e.cause_known_at = d.recorded_at FROM chain_action_thread l "
                             "JOIN finding_thread_event e ON e.thread_id = l.thread_id AND e.cause_id = "
                             "CAST(l.action_id AS text) JOIN domain_action d ON d.id = l.action_id "
                             "WHERE l.action_id = :a"), {"a": domain_id}).all()
    assert dom == [("ACTION_IN_HAND", True)], report
    # D-f, direction 1: every occurrence is NO_LONGER_SUPPORTED but the thread has a linked Action, so the
    # SUPPORT_LOST cause is skipped (the thread is ACTION_IN_HAND) and no WITHDRAWN is written.
    lost = run_lifecycle(_Reader(reader, mini=False, lost=True), writer, t, s)
    assert any(x["cause"] == "SUPPORT_LOST" and x["from_state"] == "ACTION_IN_HAND"
               for x in lost["skipped_causes"]), lost["skipped_causes"]
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM finding_thread_event WHERE state = 'WITHDRAWN'")).scalar_one() == 0


@pytest.fixture()
def bare(store, engine):  # noqa: F811
    """The CH-2 L2 seed without any Action: F01 and F02 on one thread, nothing accepted or raised."""
    from test_s6_action_store_postgres import CASES, CaseRunner, run_case

    runner = CaseRunner(store, engine)
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store

    yield runner, build_thread_sources(URL), build_thread_store(URL)


def test_support_lost_withdraws_a_thread_with_no_action(bare, engine) -> None:  # noqa: F811
    """D-f, direction 2: SUPPORT_LOST on a thread with NO linked Action writes WITHDRAWN (and without the
    cause, nothing is withdrawn)."""
    runner, reader, writer = bare
    t, s = runner.tenant, runner.site
    run_threads(reader, writer, t, s, steps=("b", "c"))
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM chain_action_thread")).scalar_one() == 0
    run_lifecycle(_Reader(reader, mini=False), writer, t, s)
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM finding_thread_event WHERE state = 'WITHDRAWN'")).scalar_one() == 0
    report = run_lifecycle(_Reader(reader, mini=False, lost=True), writer, t, s)
    with engine.connect() as c:
        rows = c.execute(text("SELECT state, cause_kind FROM finding_thread_event WHERE state = 'WITHDRAWN'")).all()
    assert rows == [("WITHDRAWN", "SUPPORT_LOST")], (rows, report)
