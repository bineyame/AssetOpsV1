"""DD1b1-R L2. Q7: the objective recording seam set and unset. Q4: the DB-trigger enqueues carry the ledger's decision
instant, so a story clock needs no migration (R7's third item is withdrawn).
A fresh module database (pg_harness); requires ASSETOPS_TEST_DATABASE_URL naming `*_test`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w206_ev_enqueue_postgres import at, ev  # noqa: F401
    from test_w402_migration_postgres import mg, mg4  # noqa: F401

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.objectives.adapters.postgres_objective_store import PostgresObjectiveStore
    from assetops_backend.objectives.model import SYSTEM_DECLARER, Declaration

STORY = datetime(2026, 1, 15, 7, 0, tzinfo=timezone.utc)


def _declaration(site_code: str, key: str) -> Declaration:
    return Declaration(site_code, "MG-1", "productive_use_kwh", Decimal("300"), None, "DECLARED", "DD-1b1 L2", None, key)


def _head(store_, tenant_id, site_id, known_at):
    return {o["outcome_key"]: o["recorded_at"] for o in store_.current(tenant_id, site_id, known_at)}


def test_objective_recorded_at_set_and_unset(store) -> None:  # noqa: F811
    imported(store, "KOBO-001")
    imported(store, "COLD-LAB-001")
    story = PostgresObjectiveStore(URL, test_recorded_clock_override=lambda: STORY)
    live = PostgresObjectiveStore(URL)
    try:
        tenant = story.tenant_id("demo")
        row, inserted = story.declare(tenant, _declaration("KOBO-001", "dd1b1-set"), SYSTEM_DECLARER, "SYSTEM_CLI")
        assert inserted and row["recorded_at"] == STORY
        kobo = story.site_id(tenant, "KOBO-001")
        assert _head(story, tenant, kobo, STORY - timedelta(seconds=1)) == {}
        assert _head(story, tenant, kobo, STORY + timedelta(seconds=1)) == {"MG-1": STORY}
        assert _head(live, tenant, kobo, None) == {"MG-1": STORY}

        before = datetime.now(timezone.utc) - timedelta(minutes=5)
        row, inserted = live.declare(tenant, _declaration("COLD-LAB-001", "dd1b1-unset"), SYSTEM_DECLARER,
                                     "SYSTEM_CLI")
        assert inserted and row["recorded_at"] > before  # the server's clock, not a story instant
    finally:
        story.dispose()
        live.dispose()


def _decided(engine_, override) -> datetime:  # noqa: F811
    """The instant the ledger stamps on a disposition, with its decision override set or unset."""
    ledger = PostgresEvidenceLedger(URL, test_decision_clock_override=override)
    with engine_.connect() as c:
        return ledger._decision_instant(c)


def _job_clocks(engine_, site_id, domain_like: str) -> set[tuple[datetime, datetime]]:  # noqa: F811
    with engine_.connect() as c:
        return {tuple(r) for r in c.execute(text(
            "SELECT available_at, created_at FROM recompute_job WHERE site_id = :s AND domain LIKE :d"),
            {"s": site_id, "d": domain_like})}


@pytest.mark.parametrize("override", [lambda: STORY, None], ids=["set", "unset"])
def test_ev_trigger_job_carries_the_decision_instant(ev, engine, override) -> None:  # noqa: F811
    decided = _decided(engine, override)
    assert (decided == STORY) is (override is not None)
    ev.accept(role="ev_site_import", when=at(8, 2, 30), decided=decided)
    assert _job_clocks(engine, ev.ctx.s, "ev_charging") == {(decided, decided)}


@pytest.mark.parametrize("override", [lambda: STORY, None], ids=["set", "unset"])
def test_mini_trigger_job_carries_the_decision_instant(mg4, engine, override) -> None:  # noqa: F811
    decided = _decided(engine, override)
    noon = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo(mg4.tz)).astimezone(timezone.utc)
    mg4.accept(role="fuel_level", when=noon + timedelta(minutes=20), decided=decided)
    clocks = _job_clocks(engine, mg4.ctx.s, "mini\\_%")
    assert clocks == {(decided, decided)}
