"""W2-05a commit 5: migration `0024_w2_ev_config` against Postgres.

`.agent/W2-05a-build-spec.md` Q7 and the property paragraph: the only schema change is the partial
`(site_id, session_id, connector_id, source_time, id)` EV measurement index; the 0020 family CHECK and Foundation
history are untouched; no new configuration table; downgrade refuses while EV measurements exist (deleting nothing),
otherwise drops only the index. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import kit  # noqa: F401
    from test_w200_source_events_postgres import ASSET_CODE, raw_copy, remove_test_blockers, rows, v4  # noqa: F401
    from test_w203_cold_migration_postgres import constraint, head, scalar

HEAD = "0025_w2_ev_session"  # W2-06: 0025 sits above 0024
PREVIOUS = "0023_w2_cold_consequence"
INDEX = "accepted_evidence_ev_measurement"
REFUSED = "Downgrade of 0024_w2_ev_config refused"


def index_def(engine):  # noqa: F811
    return scalar(engine, "SELECT indexdef FROM pg_indexes WHERE indexname = :n", n=INDEX)


def ev_delta(engine, v4) -> object:  # noqa: F811
    v4.submit(v4.kit.pv(3, first=60))
    source = rows(engine, "SELECT id, source_time FROM accepted_evidence ORDER BY id")[0]
    return raw_copy(engine, source["id"], measurement="INTERVAL_DELTA", original_unit="kWh", normalized_unit="kWh",
                    original_value_text="1.5", normalized_value_text="1.5",
                    interval_start=source["source_time"] - timedelta(minutes=5), interval_end=source["source_time"],
                    session_id="sess-1", connector_id=ASSET_CODE)


class TestMigration0024:
    def test_upgrade_adds_only_the_partial_index_and_keeps_the_family_check(self, engine) -> None:  # noqa: F811
        assert head(engine) == HEAD
        definition = index_def(engine)
        assert definition is not None
        assert "(site_id, session_id, connector_id, source_time, id)" in definition
        assert "family = 'MEASUREMENT'" in definition and "measurement = 'INTERVAL_DELTA'" in definition
        assert constraint(engine, "accepted_evidence_family") is not None  # the 0020 family CHECK is retained
        # No configuration table: the migration creates no table at all.
        assert scalar(engine, "SELECT count(*) FROM pg_tables WHERE tablename LIKE '%ev_config%'") == 0

    def test_downgrade_drops_only_the_index_and_upgrade_restores_it(self, engine) -> None:  # noqa: F811
        from alembic import command

        config = _alembic()
        before = scalar(engine, "SELECT count(*) FROM pg_indexes WHERE tablename = 'accepted_evidence'")
        family = constraint(engine, "accepted_evidence_family")
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS and index_def(engine) is None
            assert scalar(engine, "SELECT count(*) FROM pg_indexes WHERE tablename = 'accepted_evidence'") == before - 1
            assert constraint(engine, "accepted_evidence_family") == family
        finally:
            command.upgrade(config, "head")
        assert head(engine) == HEAD and index_def(engine) is not None

    def test_downgrade_refuses_while_an_ev_measurement_exists(self, v4, engine) -> None:  # noqa: F811
        from alembic import command

        config = _alembic()
        ev_delta(engine, v4)
        count = scalar(engine, "SELECT count(*) FROM accepted_evidence")
        engine.dispose()
        try:
            with pytest.raises(DBAPIError, match=REFUSED):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and index_def(engine) is not None  # the whole downgrade rolled back
            assert scalar(engine, "SELECT count(*) FROM accepted_evidence") == count  # nothing deleted
        finally:
            remove_test_blockers(engine)
            if head(engine) != HEAD:
                command.upgrade(config, "head")
