"""WALK1-4 D-W1-10: the mini-depth hour read judges each reading under its own as-accepted binding revision.

A reading bound under a superseded roles-4 set revision is selected when the pinned set binds the same role on the
same asset at the reading's time; a reading whose old binding names another asset is still skipped; the revision's
lineage lists the pinned set plus every as-accepted set used, sorted. The Postgres case pins `read_hour_rows`
returning the as-accepted binding of a row whose set is superseded (ASSETOPS_TEST_DATABASE_URL).
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.mini_depth import inputs as mini_inputs
from assetops_backend.mini_depth.projection import project
from assetops_backend.mini_depth.store import HourRows

TZ = "Africa/Nairobi"
WINDOW = mini_inputs.local_noon(date(2026, 10, 16), TZ)
SPLIT = WINDOW.start - timedelta(days=1)  # the pinned set's bindings start here; the old set's ended here
EARLY = WINDOW.start - timedelta(days=30)
CUTOFF = WINDOW.end + timedelta(hours=4)


def _sorted(*ids: UUID) -> list[UUID]:
    return sorted(ids, key=str)


def _row(binding_id: UUID, role: str, asset_id: UUID, at: datetime, value: str = "10") -> tuple:
    # (id, role, asset_id, source_time, interval_start, interval_end, quality, value_text, unit, record_kind,
    #  outcome, correlation_id, source_id, binding_revision_id, foundation_revision_id, decided_at)
    return (uuid4(), role, asset_id, at, at, at + timedelta(minutes=5), "GOOD", value, "kW", "MEASUREMENT", None,
            None, "src", binding_id, FOUNDATION, at + timedelta(minutes=10))


FOUNDATION = uuid4()


def _raw(*, old_asset: UUID, rows_asset: UUID, pinned_asset: UUID):
    pinned_set, old_set = uuid4(), uuid4()
    pinned_b, old_b = uuid4(), uuid4()
    pinned = (pinned_b, "pv_power", pinned_asset, SPLIT, None, pinned_set)
    # The old binding's own validity is open; its set (not passed: superseded at the split) is not known now.
    old = (old_b, "pv_power", old_asset, EARLY, None, old_set)
    at = WINDOW.start + timedelta(minutes=5)
    rows = [_row(old_b, "pv_power", rows_asset, at), _row(old_b, "pv_power", rows_asset, at + timedelta(minutes=5))]
    raw = HourRows(
        timezone=TZ, foundations=[(FOUNDATION, EARLY, None, {"components": []})],
        binding_sets=[(pinned_set, SPLIT, None)], bindings=[pinned[:5]], assets=[("pv-inverter", pinned_asset)],
        accepted=rows, prior_supply=[], row_foundations={FOUNDATION: (FOUNDATION, EARLY, None, {"components": []})},
        row_bindings={old_b: old},
    )
    return raw, pinned_set, old_set, rows


def _load(monkeypatch, raw):
    monkeypatch.setattr(mini_inputs, "read_hour_rows", lambda *a, **k: raw)
    return mini_inputs.load_hour_inputs(object(), uuid4(), uuid4(), WINDOW, CUTOFF)


def test_split_set_readings_selected_and_lineage_lists_both_sets(monkeypatch) -> None:
    asset = uuid4()
    raw, pinned_set, old_set, rows = _raw(old_asset=asset, rows_asset=asset, pinned_asset=asset)
    hi = _load(monkeypatch, raw)
    assert set(hi.evidence_ids) == {r[0] for r in rows}  # non-empty: both pre-split readings are selected
    assert hi.binding_set_revision_id == pinned_set
    assert list(hi.binding_set_revision_ids) == _sorted(pinned_set, old_set)
    assert hi.digest_basis()["binding_set_revision_ids"] == [str(i) for i in _sorted(pinned_set, old_set)]
    revision = project("renewable", hi)
    assert list(revision.binding_set_revision_ids) == _sorted(pinned_set, old_set)
    assert revision.result["basis"]["binding_set_revision_ids"] == [str(i) for i in _sorted(pinned_set, old_set)]


def test_old_revision_on_another_asset_is_still_skipped(monkeypatch) -> None:
    pinned_asset, other = uuid4(), uuid4()
    raw, pinned_set, _old_set, _rows = _raw(old_asset=other, rows_asset=other, pinned_asset=pinned_asset)
    hi = _load(monkeypatch, raw)
    assert hi.evidence_ids == ()
    assert list(hi.binding_set_revision_ids) == [pinned_set]  # an unused old set is not in the lineage


def test_old_revision_not_in_force_at_the_reading_is_skipped(monkeypatch) -> None:
    asset = uuid4()
    raw, pinned_set, _old_set, _rows = _raw(old_asset=asset, rows_asset=asset, pinned_asset=asset)
    (old_b, old), = raw.row_bindings.items()
    ended = (old_b, old[1], old[2], old[3], WINDOW.start, old[5])  # ended before the rows' source time
    hi = _load(monkeypatch, HourRows(**{**raw.__dict__, "row_bindings": {old_b: ended}}))
    assert hi.evidence_ids == () and list(hi.binding_set_revision_ids) == [pinned_set]


def test_pinned_binding_starting_after_the_reading_is_skipped(monkeypatch) -> None:
    """The pinned set must bind the role on the asset *at the reading*: a pinned binding that starts later does not."""
    asset = uuid4()
    raw, pinned_set, _old_set, _rows = _raw(old_asset=asset, rows_asset=asset, pinned_asset=asset)
    b = raw.bindings[0]
    later = (b[0], b[1], b[2], WINDOW.start + timedelta(minutes=30), b[4])  # valid_from after both rows
    hi = _load(monkeypatch, HourRows(**{**raw.__dict__, "bindings": [later]}))
    assert hi.evidence_ids == () and list(hi.binding_set_revision_ids) == [pinned_set]


URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_read_hour_rows_returns_as_accepted_binding_of_a_superseded_set(store, engine) -> None:  # noqa: F811
    from sqlalchemy import text
    from test_s2_evidence_ledger_postgres import enable
    from test_w203_cold_migration_postgres import _replica
    from test_w402_authored_v4_postgres import RECEIVED, cases, ingestion, install, principal, snapshot

    from assetops_backend.mini_depth.store import read_hour_rows

    installed = install(store)
    site_id, tenant_id = installed.result.site.id, installed.result.site.tenant_id
    enable(engine, site_id)
    doc, sha = snapshot(engine, installed.binding_set.id)
    service = ingestion()
    for b in cases.build_batches(cases.load_spec(), doc, sha, "positive"):
        service.submit(principal(doc), b.body.encode("utf-8"))
    window = mini_inputs.local_noon(date(2026, 10, 6), TZ)
    superseded = (RECEIVED - timedelta(seconds=1)).astimezone(timezone.utc)
    _replica(engine, f"UPDATE signal_binding_set_revision SET superseded_at = '{superseded.isoformat()}' "
                     f"WHERE id = '{installed.binding_set.id}'")
    with engine.connect() as c:
        raw = read_hour_rows(c, tenant_id, site_id, window.start, window.end, RECEIVED,
                             role_set="minigrid-roles-4", roles=mini_inputs.QUERY_ROLES, supply_role="site_supply_state")
    assert raw.binding_sets == [] and raw.bindings == []  # the set is no longer known at the cutoff
    used = {r[13] for r in raw.accepted}
    assert used and set(raw.row_bindings) == used  # non-empty: every row's own binding is read by id
    assert {b[5] for b in raw.row_bindings.values()} == {installed.binding_set.id}


if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: E402,F401
