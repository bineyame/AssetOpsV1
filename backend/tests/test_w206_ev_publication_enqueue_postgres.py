"""W2-06 q3 P7: EV Foundation and binding publication enqueue `ev_charging` work on the publishing connection.

`PostgresFoundationStore.publish_configuration.work` calls SQL `ev_enqueue_configuration` for each inserted
Foundation or binding-set revision of an EV_CHARGING Site, after the joint inserts and before `then(plan)`, so the
publication and its enqueue commit or roll back together. Both publication services reach it: `BindingService.publish`
(through `install_ev_lab`) and `FoundationService.publish_component_properties`. Requires
ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.ev_lab import install_ev_lab
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.ev_lab import EV_LAB_SITE_CODE, OLD_STATE_LABELS, binding_fixture, plan_requests
    from assetops_backend.sites.foundation_service import FoundationRefused, FoundationService
    from test_w205b_ev_replay_postgres import chain  # noqa: F401 - the registered six-case replay fixture
    from test_w206_ev_store_postgres import run_worker

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
    # r5 R5-2: both inserted rows enqueue, the equal-SHA earlier segment at its own valid_from bracket too.
    [split] = [r for r in store.revisions(result.tenant.id, result.site.id)
               if r.origin == "SPLIT" and r.superseded_at is None]
    assert sorted(j[:3] for j in added) == [(*_bracket(split.valid_from), None), (*_bracket(CHANGE), None)]


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


# --- r5 R5-2: an equal-SHA split still requeues the selected EV window -------------------------------------------

#: Recorded before the replay's committed 09:00 disposition watermark, so the re-run at that cutoff selects the split;
#: effective after the selected window, whose only intersecting inserted row is the unchanged earlier segment.
SPLIT_RECORDED = datetime(2026, 10, 6, 8, 59, 30, tzinfo=timezone.utc)
SPLIT_FROM = datetime(2026, 10, 6, 10, 0, tzinfo=timezone.utc)
SESSION_START = datetime(2026, 10, 6, 8, 1, tzinfo=timezone.utc)  # the complete replay's accepted START
SPLIT_TABLE = {"foundation": ("foundation_revision", "content_sha256", "foundation_revision_ids"),
               "binding_set": ("signal_binding_set_revision", "bindings_sha256", "binding_set_revision_ids")}


def _selected_window(engine, site_id) -> tuple:  # noqa: F811
    with engine.connect() as c:
        [window] = c.execute(text(
            "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE site_id = :s "
            "AND analytic_id = 'ev-session/1' AND window_start <= :start AND window_end > :start"),
            {"s": site_id, "start": SESSION_START}).all()
    return tuple(window)


def _ev_jobs(engine, site_id) -> list[tuple]:  # noqa: F811
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(
            "SELECT id, window_start, window_end, status, xmin::text FROM recompute_job WHERE site_id = :s "
            "AND domain = 'ev_charging' ORDER BY created_at, id"), {"s": site_id})]


def _splits(engine, site_id, table: str, digest: str) -> list[tuple]:  # noqa: F811
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(
            f"SELECT n.id, n.derived_from_revision_id, n.{digest} = o.{digest}, n.valid_from, n.valid_to, "
            f"n.xmin::text FROM {table} n JOIN {table} o ON o.id = n.derived_from_revision_id "
            f"WHERE n.site_id = :s AND n.origin = 'SPLIT'"), {"s": site_id})]


def _scope(built):
    tenant = built.store.resolve_tenant("demo")
    return tenant, built.store.find_site(tenant.id, EV_LAB_SITE_CODE)


def _publish(built, kind: str, *, effective_from: datetime = SPLIT_FROM, value: float = 0.005) -> None:
    store = built.store
    tenant, site = _scope(built)
    if kind == "foundation":
        FoundationService(store, "demo", Clock(SPLIT_RECORDED)).publish_component_properties(
            tenant, site, asset_code="c1", effective_from=effective_from, note="W2-06 R5-2 split",
            properties=[{"property_key": "ev-meter-error-bound", "value": value, "unit": "kWh", "source": "SITE",
                         "source_version": 1}])
        return
    fixture = binding_fixture()
    original = next(r for r in store.revisions(tenant.id, site.id) if r.origin == "IMPORT")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, _declared, _rows = plan_requests(
        fixture, site, original.content.get("signal_mappings") or (), asset_ids)
    if effective_from == SPLIT_FROM:  # a real later change: the first 05a connector-state map, from SPLIT_FROM on
        requests = [replace(r, conversion={"kind": "ENUM", "parameters": {"map": {x: x for x in OLD_STATE_LABELS}}})
                    if r.role == "ev_connector_state" else r for r in requests]
    BindingService(store, Clock(SPLIT_RECORDED)).publish(
        tenant, site, requests=requests, effective_from=effective_from, note="W2-06 R5-2 split",
        role_set=fixture["role_set"])


def _c1_error_bound(built) -> float:
    tenant, site = _scope(built)
    [current] = [r for r in built.store.revisions(tenant.id, site.id)
                 if r.superseded_at is None and r.valid_from <= SPLIT_FROM
                 and (r.valid_to is None or SPLIT_FROM < r.valid_to)]
    [c1] = [x for x in current.content["components"] if x.get("component_id") == "c1"]
    [item] = [i for i in c1["properties"] if i["property_key"] == "ev-meter-error-bound"]
    return item["value"]


@pytest.mark.parametrize("kind", ["foundation", "binding_set"])
def test_equal_sha_split_requeues_selected_ev_window(chain, kind, monkeypatch) -> None:  # noqa: F811
    table, digest, basis_key = SPLIT_TABLE[kind]
    built = chain("complete")
    built.start_release_upload()
    run_worker(built)
    lo, hi = _selected_window(built.engine, built.site_id)
    assert hi <= SPLIT_FROM
    before = _ev_jobs(built.engine, built.site_id)
    assert before and all(j[3] == "DONE" for j in before), before

    # An unchanged request inserts no revision and enqueues nothing.
    if kind == "foundation":
        with pytest.raises(FoundationRefused, match="v"):
            _publish(built, kind, value=_c1_error_bound(built))
    else:
        tenant, site = _scope(built)
        [current] = [s for s in built.store.binding_sets(tenant.id, site.id) if s.superseded_at is None]
        try:
            _publish(built, kind, effective_from=current.valid_from)
        except Exception:  # noqa: BLE001 - a refused no-op is equally a request that inserts nothing
            pass
        assert [s.id for s in built.store.binding_sets(tenant.id, site.id) if s.superseded_at is None] == [current.id]
    assert _ev_jobs(built.engine, built.site_id) == before
    assert _splits(built.engine, built.site_id, table, digest) == []

    # A failure after the enqueue rolls back both the split and its job.
    original = PostgresFoundationStore._enqueue_ev_configuration

    def enqueue_then_fail(connection, tenant_id, site_id, plan):
        original(connection, tenant_id, site_id, plan)
        raise RuntimeError("injected failure after the enqueue")

    monkeypatch.setattr(PostgresFoundationStore, "_enqueue_ev_configuration", staticmethod(enqueue_then_fail))
    with pytest.raises(RuntimeError, match="injected failure"):
        _publish(built, kind)
    monkeypatch.setattr(PostgresFoundationStore, "_enqueue_ev_configuration", staticmethod(original))
    assert _splits(built.engine, built.site_id, table, digest) == []
    assert _ev_jobs(built.engine, built.site_id) == before

    _publish(built, kind)
    splits = [s for s in _splits(built.engine, built.site_id, table, digest) if s[4] == SPLIT_FROM]
    assert len(splits) == 1, splits
    split_id, derived_from, equal_sha, valid_from, _to, split_xmin = splits[0]
    assert equal_sha is True and split_id != derived_from and valid_from <= lo
    added = [j for j in _ev_jobs(built.engine, built.site_id) if j[0] not in {b[0] for b in before}]
    requeued = [j for j in added if j[1] < hi and j[2] > lo]
    assert requeued and all(j[3] == "PENDING" for j in requeued), added
    assert {j[4] for j in requeued} == {split_xmin}  # committed by the publication's own transaction

    run_worker(built)
    with built.engine.connect() as c:
        ids = c.execute(text(
            f"SELECT r.{basis_key} FROM analytic_run_selection s JOIN analytic_run r ON r.id = s.run_id "
            "WHERE s.site_id = :s AND s.analytic_id = 'ev-session/1' AND s.window_start = :lo "
            "AND s.window_end = :hi ORDER BY s.seq DESC LIMIT 1"), {"s": built.site_id, "lo": lo, "hi": hi}
        ).scalar_one()
    assert [str(x) for x in (ids if isinstance(ids, list) else json.loads(ids))] == [str(split_id)]
