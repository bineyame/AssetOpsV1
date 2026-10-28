"""W4-02 q1 ruling 2: downgrade probes that cross 0029_w4_mini_depth without deleting mini history.

0029 refuses a downgrade while any mini-depth table row or any of its four exact `recompute_job` domains exists.
A MINIGRID fixture published or ingested at head creates that history, so an older migration's success or
round-trip probe seeds its predecessor rows *at the predecessor revision*, before 0029 is installed: the module's
fresh database is taken down to `PREDECESSOR` while it holds no mini history, the fixture is built there, and the
database is upgraded back to head. At the predecessor revision neither the 0029 accepted-row trigger nor the SQL
`mini_enqueue_configuration` exists, so the publication writer's 0029 enqueue call is the one head-only step not
run while seeding (`PostgresFoundationStore._enqueue_mini_configuration`, which would call a function that does
not exist yet). No row is deleted, no trigger is disabled and the 0029 guard is unchanged; every probe asserts the
three mini tables and the four mini domains are empty before crossing 0029. 0029 also refuses while any q12-6 `site_cutover_basis` row exists
(B-M1); that table exists only at head, so it is asserted empty at head on both sides of the crossing.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

from sqlalchemy import text

MINI_HEAD = "0037_cc_trial_cost_comparison"  # CC-M: current head above 0036 and 0035 (W5-03b above 0033, W5-02a above 0032, W5-01b above 0030)
COLD_WORK_PREDECESSOR = "0032_w5_cold_scenarios"  # 0033 is crossed empty first
COLD_WORK_TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action")
COLD_SCENARIO_PREDECESSOR = "0030_w4_mini_decisions"  # 0032 is crossed empty before 0029
COLD_SCENARIO_TABLES = ("cold_scenario_revision", "cold_scenario")
PREDECESSOR = "0027_w4_work_cases"
MINI_TABLES = ("mini_depth_revision", "mini_depth_revision_evidence", "mini_depth_selection")
MINI_JOB_DOMAINS = ("mini_renewable", "mini_service", "mini_fuel", "mini_backup")
MINI_REFUSED = "Downgrade of 0029_w4_mini_depth refused: mini-depth history exists"


def mini_history(engine) -> list[int]:
    """Row counts of the three mini tables then the four exact mini job domains, in that order."""
    with engine.connect() as connection:
        tables = [connection.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in MINI_TABLES]
        jobs = [connection.execute(text("SELECT count(*) FROM recompute_job WHERE domain = :d"), {"d": d}).scalar_one()
                for d in MINI_JOB_DOMAINS]
    return tables + jobs


def assert_no_mini_history(engine) -> None:
    assert mini_history(engine) == [0] * 7


def assert_no_cutover_basis(engine) -> None:
    """At head only: the q12-6 `site_cutover_basis` table, which also blocks the 0029 downgrade, is empty."""
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM site_cutover_basis")).scalar_one() == 0


def assert_no_cold_scenarios(engine) -> None:
    """At head only: the 0032 cold scenario tables, which block the 0032 downgrade, are empty."""
    with engine.connect() as connection:
        assert [connection.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()
                for t in COLD_SCENARIO_TABLES] == [0, 0]


def assert_no_cold_work(engine) -> None:
    """At head only: the 0033 domain Action tables, which block the 0033 downgrade, are empty."""
    with engine.connect() as connection:
        assert [connection.execute(text(f"SELECT count(*) FROM {t}")).scalar_one()
                for t in COLD_WORK_TABLES] == [0, 0, 0]


def has_mini_jobs(engine) -> bool:
    return sum(mini_history(engine)[len(MINI_TABLES):]) > 0


def _head(engine) -> str:
    with engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


@contextmanager
def seeded_before_0029(config, engine, *holders):
    """Build the fixture inside this block at `PREDECESSOR`; on exit the database is back at head with no mini
    history. `holders` (stores/engines) are disposed before each migration so no pooled connection waits on a
    migration lock."""
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from alembic import command

    def release() -> None:
        for holder in (*holders, engine):
            target = holder if hasattr(holder, "dispose") else getattr(holder, "_engine", None)
            if target is not None:
                target.dispose()

    assert _head(engine) == MINI_HEAD
    assert_no_mini_history(engine)
    assert_no_cutover_basis(engine)
    assert_no_cold_scenarios(engine)
    assert_no_cold_work(engine)
    release()
    command.downgrade(config, COLD_WORK_PREDECESSOR)  # traverse the empty 0033 first
    assert _head(engine) == COLD_WORK_PREDECESSOR
    command.downgrade(config, COLD_SCENARIO_PREDECESSOR)  # then the empty 0032
    assert _head(engine) == COLD_SCENARIO_PREDECESSOR
    command.downgrade(config, PREDECESSOR)
    assert _head(engine) == PREDECESSOR
    try:
        with patch.object(PostgresFoundationStore, "_enqueue_mini_configuration",
                          staticmethod(lambda *args, **kwargs: None)):
            yield
    finally:
        release()
        command.upgrade(config, "head")
    assert _head(engine) == MINI_HEAD
    assert_no_mini_history(engine)
    assert_no_cutover_basis(engine)
    assert_no_cold_scenarios(engine)
