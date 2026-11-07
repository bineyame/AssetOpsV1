"""DD-1b2a L2 (DD1b2-R Q2) on the CH-9b1 `mill` fixture's Site: the store's `story_clock` dates an opportunity revision
and its selection, `opportunity_revision_selected` holds at a story `command_now` only with it, and unset stores DB time."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_ch4_opportunity_postgres import _hours
    from test_ch9b1_opportunity_actions_postgres import _now, mill  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.work.domain_action import DomainIntentRefused


RESULT = {"status": "SUPPORTED", "eligible_days": 1, "days": []}


def _revise(mill, clock, day_shift: int) -> tuple:
    """A new revision and selection of a new study root, through the store's real inserts."""
    writer = PostgresMiniDecisionStore.from_url(URL, story_clock=clock)
    oid, rid = uuid4(), uuid4()
    first = datetime(2024, 1, 1, tzinfo=timezone.utc).date() + timedelta(days=day_shift)
    try:
        with writer.transaction() as c:
            writer.insert_opportunity(c, {"id": oid, "tenant_id": mill.t, "site_id": mill.s, "first_day": first,
                                          "last_day": first + timedelta(days=4), "model_version": "mini-opportunity/1"})
            writer.insert_opportunity_revision(c, {
                "id": rid, "tenant_id": mill.t, "site_id": mill.s, "opportunity_id": oid, "revision_no": 1,
                "selected_hours": _hours([first + timedelta(days=n) for n in range(5)]), "result": RESULT,
                "input_sha256": "sha256:" + "a" * 64, "producer_id": "dd1b2a-l2",
                "model_version": "mini-opportunity/1"}, backfill=True)
            writer.insert_opportunity_selection(c, {"tenant_id": mill.t, "site_id": mill.s, "opportunity_id": oid,
                                                    "revision_id": rid}, backfill=True)
    finally:
        writer.dispose()
    return oid, rid


def _stored(engine, rid) -> tuple:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT r.created_at, s.selected_at FROM mini_opportunity_revision r JOIN "
                              "mini_opportunity_selection s ON s.revision_id = r.id WHERE r.id = :r"), {"r": rid}).one()


def test_set_stores_the_instant_and_the_action_is_accepted_at_a_story_command_now(mill) -> None:  # noqa: F811
    instant = _now(mill.engine) - timedelta(days=14)
    oid, rid = _revise(mill, lambda: instant, 0)
    created, selected = _stored(mill.engine, rid)
    assert created == instant and selected == instant
    command_now = instant + timedelta(days=4)
    mill.svc._store.test_db_clock_override = lambda: command_now
    status, action = mill.svc.create_action(mill.t, mill.s, "KOBO-001", {
        "domain": "MINI", "origin_opportunity_id": str(oid), "origin_opportunity_revision_id": str(rid),
        "title": "Run the mill at midday", "owner_label": "Plant lead", "due_at": None,
        "raised_at": command_now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "actor": {
            "kind": "SERVICE", "id": "service:w401-fixture", "attestation": "service=w401-fixture;job=l2;rule=dd1b2-r"},
        "idempotency_key": "dd1b2a-l2-story"}, "service:w401-fixture")
    assert status == 201, action
    with mill.engine.connect() as c:
        origin, recorded = c.execute(text("SELECT origin_opportunity_id, recorded_at FROM domain_action WHERE id = :a"),
                                     {"a": action["id"]}).one()
    assert str(origin) == str(oid) and recorded == command_now


def test_unset_stores_db_time_and_the_action_is_refused_at_a_story_command_now(mill) -> None:  # noqa: F811
    """The premise of Q2: without the seam the selection is later than a story `command_now`."""
    before = _now(mill.engine)
    oid, rid = _revise(mill, None, 10)
    created, selected = _stored(mill.engine, rid)
    assert created >= before and selected >= before
    command_now = before - timedelta(days=10)
    mill.svc._store.test_db_clock_override = lambda: command_now
    with pytest.raises(DomainIntentRefused, match="DOMAIN_INTENT_LINK_INVALID"):
        mill.svc.create_action(mill.t, mill.s, "KOBO-001", {
            "domain": "MINI", "origin_opportunity_id": str(oid), "origin_opportunity_revision_id": str(rid),
            "title": "Run the mill at midday", "owner_label": "Plant lead", "due_at": None,
            "raised_at": command_now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "actor": {
                "kind": "SERVICE", "id": "service:w401-fixture", "attestation": "service=w401-fixture;job=l2;rule=dd1b2-r"},
            "idempotency_key": "dd1b2a-l2-wall"}, "service:w401-fixture")
