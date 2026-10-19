"""W2-06 q3 P7: EV Foundation and binding publication enqueue `ev_charging` work on the publishing connection.

`PostgresFoundationStore.publish_configuration.work` calls SQL `ev_enqueue_configuration` for each inserted
Foundation or binding-set revision of an EV_CHARGING Site, after the joint inserts and before `then(plan)`, so the
publication and its enqueue commit or roll back together. Both publication services reach it: `BindingService.publish`
(through `install_ev_lab`) and `FoundationService.publish_component_properties`. Requires
ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.ev_lab import install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CHANGE = datetime(2026, 10, 6, 8, 7, 30, tzinfo=timezone.utc)


def jobs(engine, site_id) -> list[tuple]:  # noqa: F811
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(
            "SELECT window_start, window_end, cause_evidence_id, status, available_at FROM recompute_job "
            "WHERE site_id = :s AND domain = 'ev_charging' ORDER BY window_start, created_at"), {"s": site_id})]


def revisions(engine, site_id) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM foundation_revision WHERE site_id = :s"),
                         {"s": site_id}).scalar_one()


def _bracket(t: datetime) -> tuple[datetime, datetime]:
    lo = t.replace(minute=t.minute - t.minute % 5, second=0, microsecond=0)
    return lo, lo + timedelta(minutes=5)


def _publish_property(store, result):  # noqa: F811
    FoundationService(store, "demo", Clock(NOW)).publish_component_properties(
        result.tenant, result.site, asset_code="c1", effective_from=CHANGE, note="W2-06 P7 meter error",
        properties=[{"property_key": "ev-meter-error-bound", "value": 0.002, "unit": "kWh", "source": "SITE",
                     "source_version": 1}])


def test_binding_publication_seeds_its_change_bracket(store, engine) -> None:  # noqa: F811
    result = install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    [job] = jobs(engine, result.site.id)
    # No selected ev-session/1 window exists yet: the binding set's valid_from bracket, no cause evidence.
    assert job[:2] == _bracket(binding_set.valid_from) and job[2] is None and job[3] == "PENDING"


def test_foundation_property_publication_enqueues_on_its_connection(store, engine) -> None:  # noqa: F811
    result = install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    before = jobs(engine, result.site.id)
    _publish_property(store, result)
    added = [j for j in jobs(engine, result.site.id) if j not in before]
    assert [j[:3] for j in added] == [(*_bracket(CHANGE), None)]


def test_a_failed_publication_rolls_back_its_enqueue(store, engine, monkeypatch) -> None:  # noqa: F811
    result = install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))
    before, count = jobs(engine, result.site.id), revisions(engine, result.site.id)
    original = PostgresFoundationStore._enqueue_ev_configuration

    def enqueue_then_fail(connection, tenant_id, site_id, plan):
        original(connection, tenant_id, site_id, plan)
        assert len(connection.execute(text(
            "SELECT 1 FROM recompute_job WHERE site_id = :s AND domain = 'ev_charging'"),
            {"s": site_id}).all()) > len(before)
        raise RuntimeError("injected failure after the enqueue")

    monkeypatch.setattr(PostgresFoundationStore, "_enqueue_ev_configuration", staticmethod(enqueue_then_fail))
    with pytest.raises(RuntimeError, match="injected failure"):
        _publish_property(store, result)
    assert jobs(engine, result.site.id) == before and revisions(engine, result.site.id) == count
