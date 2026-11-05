"""CH-5c W6 (CH5c-R4 §8.1, R5-2): the listener guard is green on tracked reads and fails on every hole.

Non-vacuous by construction: a planted untracked table read fails it; a dropped change trigger (in a rolled-back
transaction) fails it; an unknown relation fails it; a view resolves through `pg_rewrite`/`pg_depend` to its base
tables. The R5-2 pin: the chain read's settled-flag statement reads `event_consumption`, so the table stays
triggered (Site-scoped through its outbox row) and is never excluded.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_s1_bindings_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine  # noqa: F401

import chain_watermark_guard as guard  # noqa: E402

TRACKED = "SELECT f.id FROM finding f JOIN finding_revision r ON r.finding_id = f.id WHERE f.site_id = :s"


def test_targets_skip_ctes_functions_columns_and_keywords() -> None:
    sql = ("WITH RECURSIVE w(x) AS (SELECT 1), v AS MATERIALIZED (SELECT id FROM site) "
           "SELECT extract(epoch FROM o.recorded_at), a IS DISTINCT FROM b FROM w "
           "JOIN LATERAL jsonb_array_elements(o.body) e ON true JOIN event_outbox o ON true "
           "LEFT JOIN v ON true, unnest(:ids) AS q(id)")
    assert guard.targets(sql) == {"site", "event_outbox"}


def test_guard_green_on_tracked_tables_and_views(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        assert guard.check(c, [TRACKED])["ok"]
    with engine.connect() as c:
        with c.begin():
            c.execute(text("CREATE VIEW ch5c_w6_view AS SELECT f.id FROM finding f JOIN site s ON s.id = f.site_id"))
            verdict = guard.check(c, ["SELECT id FROM ch5c_w6_view"])
            assert verdict["ok"] and {"finding", "site"} <= set(verdict["read"]), verdict
            c.rollback()


def test_guard_fails_on_a_planted_untracked_table(engine) -> None:  # noqa: F811
    with engine.connect() as c, c.begin():
        c.execute(text("CREATE TABLE ch5c_w6_planted (id int)"))
        verdict = guard.check(c, [TRACKED, "SELECT id FROM ch5c_w6_planted"])
        assert not verdict["ok"] and verdict["untracked"] == ["ch5c_w6_planted"], verdict
        c.execute(text("CREATE VIEW ch5c_w6_planted_view AS SELECT id FROM ch5c_w6_planted"))
        verdict = guard.check(c, ["SELECT id FROM ch5c_w6_planted_view"])
        assert verdict["untracked"] == ["ch5c_w6_planted"], verdict  # a view does not hide an untracked base
        c.rollback()


def test_guard_fails_on_a_dropped_trigger_and_an_unknown_relation(engine) -> None:  # noqa: F811
    with engine.connect() as c, c.begin():
        c.execute(text("DROP TRIGGER finding_revision_cic_del ON finding_revision"))
        verdict = guard.check(c, [TRACKED])
        assert verdict["untracked"] == ["finding_revision"], verdict
        c.rollback()
    with engine.connect() as c:
        verdict = guard.check(c, ["SELECT 1 FROM ch5c_no_such_relation"])
        assert not verdict["ok"] and verdict["unresolved"] == ["ch5c_no_such_relation"], verdict


def test_r5_2_pin_event_consumption_is_read_by_the_chain_read(engine) -> None:  # noqa: F811
    from assetops_backend.chain.adapters import postgres_chain_read as chain_read

    sql = [str(v) for v in vars(chain_read).values()
           if type(v).__name__ == "TextClause" and "event_consumption" in str(v)]
    assert sql, "the chain read no longer reads event_consumption: re-rule R5-2 before excluding it"
    with engine.connect() as c:
        verdict = guard.check(c, sql)
    assert verdict["ok"] and verdict["event_consumption_read"], verdict
