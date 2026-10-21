"""W2-05a EV-LAB-001: Foundation import, the complete `ev-roles-1` v4 binding revision, the EV Draft gate and
same-Site gap revisions, persisted and reloaded.

`D-2026-10-18-w2-05-buildspec` Q1/Q2/Q6/Q8. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database;
skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from assetops_contracts.source_envelope_v4 import V4_EV_CHANNEL_MAPPINGS

    from assetops_backend.sites.binding_service import (
        BindingRefused,
        BindingRequest,
        BindingService,
        Snapshot,
        SnapshotUnavailable,
        acquisition_snapshot,
    )
    from assetops_backend.sites.ev_lab import binding_fixture, install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService
    from test_s1_bindings_postgres import Clock, _alembic, engine, store  # noqa: F401

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
ORIGINAL_FROM = datetime(2026, 10, 1, tzinfo=timezone.utc)
#: Q6: gap revisions start after the 6 October complete-run window.
MISSING_METER_FROM = datetime(2026, 10, 8, tzinfo=timezone.utc)
MISSING_LIMIT_FROM = datetime(2026, 10, 12, tzinfo=timezone.utc)


def install(store):
    return install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=3)))


def selected(store, result, at: datetime):
    sets = [s for s in store.binding_sets(result.tenant.id, result.site.id) if s.superseded_at is None
            and s.valid_from <= at and (s.valid_to is None or at < s.valid_to)]
    assert len(sets) == 1, sets
    return sets[0]


def snapshot_at(store, result, at: datetime):
    return acquisition_snapshot(
        result.tenant.id, result.site, store.revisions(result.tenant.id, result.site.id),
        store.registrations(result.tenant.id, result.site.id), selected(store, result, at),
    )


def complete_requests(store, result) -> list[BindingRequest]:
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(result.tenant.id, result.site.id).assets}
    return [BindingRequest(device_id=b["device_id"], signal_id=b["signal_id"], asset_id=asset_ids[b["asset_code"]],
                           role=b["role"], source_unit=b["source_unit"], canonical_unit=b["canonical_unit"],
                           conversion=b["conversion"]) for b in binding_fixture()["bindings"]]


def test_install_persists_the_complete_basis_and_reloads(store) -> None:
    result = install(store)
    [revision] = store.revisions(result.tenant.id, result.site.id)
    assert (revision.valid_from, revision.valid_to) == (ORIGINAL_FROM, None)
    assert revision.content["connector_enable_schedules"][0]["time_zone"] == "Etc/UTC"
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    assert (binding_set.role_set, binding_set.origin, binding_set.valid_from) == ("ev-roles-1", "PUBLISH",
                                                                                  ORIGINAL_FROM)
    assert binding_set.foundation_revision_id == revision.id
    assert len(binding_set.bindings) == 15
    codes = {a.id: a.asset_code for a in store.registrations(result.tenant.id, result.site.id).assets}
    for b in binding_set.bindings:
        entry = V4_EV_CHANNEL_MAPPINGS[(b.device_id, b.signal_id)]
        assert b.role == entry.role
        assert b.v4_mapping == entry.metadata()
        assert codes[b.asset_id] == ("site-meter-1" if b.device_id == "site-meter" else b.device_id[:2])
    snapshot = snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc))
    assert isinstance(snapshot, Snapshot), snapshot
    pinned = {(r["device_id"], r["signal_id"]): r for r in json.loads(snapshot.body)["bindings"]}
    assert set(pinned) == set(V4_EV_CHANNEL_MAPPINGS)
    # Idempotent: a second install neither re-imports nor republishes.
    install_ev_lab(store, tenant_slug="demo", clock=Clock(NOW - timedelta(hours=2)))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == 1


def test_missing_meter_revision_blocks_draft_and_keeps_the_original(store) -> None:
    result = install(store)
    requests = [r for r in complete_requests(store, result)
                if (r.device_id, r.signal_id) != ("c2-connector-meter", "energy")]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note="W2-05a test: connector 2 energy meter not bound.", role_set="ev-roles-1")
    gap = snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and "METER_NOT_BOUND" in gap.reason, gap
    assert isinstance(snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc)), Snapshot)


@pytest.mark.parametrize("drop,code", [(("c1-charger-controller", "session-event"), "SESSION_EVENTS_NOT_BOUND"),
                                       (("c1-connector-controller", "state"), "STATUS_NOT_BOUND")])
def test_missing_event_or_status_revision_blocks_draft(store, drop, code) -> None:
    result = install(store)
    requests = [r for r in complete_requests(store, result) if (r.device_id, r.signal_id) != drop]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note=f"W2-05a test: {code}.", role_set="ev-roles-1")
    gap = snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and code in gap.reason, gap


def test_optional_role_absence_does_not_block(store) -> None:
    result = install(store)
    optional = {("site-meter", "import"), ("c1-connector-controller", "fault-event"),
                ("c1-connector-meter", "power"), ("c1-connector-controller", "requested-power"),
                ("c1-connector-controller", "allocated-limit")}
    requests = [r for r in complete_requests(store, result) if (r.device_id, r.signal_id) not in optional]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM,
        note="W2-05a test: optional channels absent.", role_set="ev-roles-1")
    assert isinstance(snapshot_at(store, result, MISSING_METER_FROM + timedelta(hours=1)), Snapshot)


def test_missing_limit_foundation_revision_blocks_draft(store) -> None:
    result = install(store)

    def without_limit(content, _version):
        changed = json.loads(json.dumps(content))
        feed = next(c for c in changed["components"] if c["component_type"] == "AC_BUS")
        feed.pop("properties")
        return changed

    FoundationService(store, "demo", Clock(NOW - timedelta(hours=1)))._publish_content_change(
        result.tenant, result.site, effective_from=MISSING_LIMIT_FROM,
        note="W2-05a test: site import limit not declared.", unchanged=lambda _c: None, change=without_limit)
    revisions = store.revisions(result.tenant.id, result.site.id)
    assert any(r.valid_from == MISSING_LIMIT_FROM for r in revisions)
    gap = snapshot_at(store, result, MISSING_LIMIT_FROM + timedelta(hours=1))
    assert isinstance(gap, SnapshotUnavailable) and "FEED_OR_LIMIT_MISSING" in gap.reason, gap
    assert isinstance(snapshot_at(store, result, datetime(2026, 10, 6, 12, tzinfo=timezone.utc)), Snapshot)


@pytest.mark.parametrize("change,code", [
    (lambda r: BindingRequest(**{**r.__dict__, "role": "ev_connector_power"}), "BINDING_CHANNEL_ROLE_MISMATCH"),
    (lambda r: BindingRequest(**{**r.__dict__, "conversion": {"kind": "IDENTITY", "parameters": {}}}),
     "BINDING_CONVERSION_INVALID"),
])
def test_energy_channel_refusals(store, change, code) -> None:
    result = install(store)
    requests = [change(r) if (r.device_id, r.signal_id) == ("c1-connector-meter", "energy") else r
                for r in complete_requests(store, result)]
    with pytest.raises(BindingRefused) as caught:
        BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
            result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM, note="refused",
            role_set="ev-roles-1")
    assert code in {p["code"] for p in caught.value.problems}


def _refused_codes(store, result, requests) -> set[str]:
    with pytest.raises(BindingRefused) as caught:
        BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
            result.tenant, result.site, requests=requests, effective_from=MISSING_METER_FROM, note="refused",
            role_set="ev-roles-1")
    return {p["code"] for p in caught.value.problems}


@pytest.mark.parametrize("device,other", [("c1-connector-meter", "c2"), ("site-meter", "c1")])
def test_source_bound_to_another_asset_is_refused(store, device, other) -> None:
    """QG: a source binds only the asset it is registered to (registered UUIDs, not name prefixes)."""
    result = install(store)
    regs = store.registrations(result.tenant.id, result.site.id)
    other_id = str(next(a.id for a in regs.assets if a.asset_code == other))
    requests = [BindingRequest(**{**r.__dict__, "asset_id": other_id}) if r.device_id == device else r
                for r in complete_requests(store, result)]
    before = len(store.binding_sets(result.tenant.id, result.site.id))
    assert "BINDING_SOURCE_ASSET_MISMATCH" in _refused_codes(store, result, requests)
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == before


def test_legacy_w200_tuples_cannot_bind_under_the_ev_profile(store) -> None:
    """QF: the unsuffixed W2-00 tuples keep their role labels globally but are outside simulator-lab-gateway-ev/1."""
    from assetops_contracts.source_envelope_v4 import (
        V4_CHANNEL_MAPPINGS, V4_COLD_CHANNEL_MAPPINGS, V4_MINI_CHANNEL_MAPPINGS)

    # W4-02 B2: the authored mini tuples are their own profile, not legacy W2-00 tuples.
    legacy = {k: v for k, v in V4_CHANNEL_MAPPINGS.items()
              if k not in V4_EV_CHANNEL_MAPPINGS and k not in V4_COLD_CHANNEL_MAPPINGS
              and k not in V4_MINI_CHANNEL_MAPPINGS}
    assert {v.role for v in legacy.values()} == {"ev_session_event", "ev_connector_fault"}
    result = install(store)
    template = {(r.device_id, r.signal_id): r for r in complete_requests(store, result)}
    for (device, signal), entry in legacy.items():
        model = template[("c1-charger-controller", "session-event")] if entry.role == "ev_session_event" \
            else template[("c1-connector-controller", "fault-event")]
        requests = [r for r in template.values() if r is not model]
        requests.append(BindingRequest(**{**model.__dict__, "device_id": device, "signal_id": signal}))
        assert "BINDING_CHANNEL_V4_UNKNOWN" in _refused_codes(store, result, requests)


# --- Run 8 M2: connector-free binding refusal --------------------------------------------------------------


def _publish_connector_free_revision(store, result, effective_from: datetime) -> None:
    def without_connectors(content, _version):
        changed = json.loads(json.dumps(content))
        gone = {c["component_id"] for c in changed["components"] if c["component_type"] == "EV_CONNECTOR"}
        assert gone
        changed["components"] = [c for c in changed["components"] if c["component_id"] not in gone]
        changed.pop("connector_enable_schedules", None)
        topology = changed["topology"]
        nodes = {n["node_id"] for n in topology["nodes"] if n["component_id"] in gone}
        topology["nodes"] = [n for n in topology["nodes"] if n["node_id"] not in nodes]
        topology["connections"] = [e for e in topology["connections"] if e["from_node"] not in nodes and e["to_node"] not in nodes]
        changed["devices"] = [d for d in changed.get("devices") or () if d.get("component_id") not in gone]
        return changed

    FoundationService(store, "demo", Clock(NOW - timedelta(hours=1)))._publish_content_change(
        result.tenant, result.site, effective_from=effective_from,
        note="W2-05a test: no connector declared.", unchanged=lambda _c: None, change=without_connectors)


def test_binding_set_without_a_declared_connector_is_refused_and_writes_nothing(store) -> None:
    result = install(store)
    _publish_connector_free_revision(store, result, MISSING_LIMIT_FROM)
    complete = complete_requests(store, result)
    site_import = [r for r in complete if r.role == "ev_site_import"]
    assert len(site_import) == 1
    before = store.binding_sets(result.tenant.id, result.site.id)
    for requests, effective_from in [
        ([], MISSING_LIMIT_FROM + timedelta(days=1)),
        (site_import, MISSING_LIMIT_FROM + timedelta(days=1)),
        # A period that starts on the connector-bearing revision but overlaps the connector-free one.
        (complete, datetime(2026, 10, 5, tzinfo=timezone.utc)),
    ]:
        with pytest.raises(BindingRefused) as caught:
            BindingService(store, Clock(NOW - timedelta(minutes=30))).publish(
                result.tenant, result.site, requests=requests, effective_from=effective_from, note="refused",
                role_set="ev-roles-1")
        [problem] = [p for p in caught.value.problems if p["code"] == "BINDING_EV_CONNECTOR_NOT_DECLARED"]
        assert problem["binding"] == ""
        assert problem["message"] == ("An EV binding set needs at least one declared connector in every covering "
                                      "Foundation revision.")
        assert store.binding_sets(result.tenant.id, result.site.id) == before


def test_binding_set_with_declared_connectors_still_publishes(store) -> None:
    result = install(store)
    before = len(store.binding_sets(result.tenant.id, result.site.id))
    published = BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site,
        requests=[r for r in complete_requests(store, result) if r.role != "ev_connector_power"],
        effective_from=MISSING_METER_FROM, note="W2-05a test: connector-bearing set.", role_set="ev-roles-1")
    assert published is not None
    assert len(store.binding_sets(result.tenant.id, result.site.id)) > before


def test_ev_lab_install_publishes_without_an_activation_delay(store) -> None:
    """Run 8 M4: bindings are readable at the install clock; a later Foundation revision is allowed immediately;
    a reinstall writes no extra binding revision."""
    clock_at = NOW - timedelta(hours=3)
    result = install(store)
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    assert binding_set.valid_from == ORIGINAL_FROM
    assert binding_set.recorded_at == clock_at
    assert isinstance(snapshot_at(store, result, clock_at), Snapshot)
    def without_limit(content, _version):
        changed = json.loads(json.dumps(content))
        next(c for c in changed["components"] if c["component_type"] == "AC_BUS").pop("properties")
        return changed

    FoundationService(store, "demo", Clock(clock_at))._publish_content_change(
        result.tenant, result.site, effective_from=MISSING_LIMIT_FROM,
        note="W2-05a test: later revision at the install clock.", unchanged=lambda _c: None, change=without_limit)
    sets_before = len(store.binding_sets(result.tenant.id, result.site.id))
    install_ev_lab(store, tenant_slug="demo", clock=Clock(clock_at))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == sets_before


def test_out_of_range_clock_bound_is_refused_as_ev_configuration_invalid(store) -> None:
    """Run 8 L3: `ev-clock-error-bound: 1e300` refuses `EV_CONFIGURATION_INVALID` naming its property position."""
    from assetops_backend.sites.foundation_service import FoundationRefused

    result = install(store)

    def huge(content, _version):
        changed = json.loads(json.dumps(content))
        connector = next(c for c in changed["components"] if c["component_type"] == "EV_CONNECTOR")
        next(p for p in connector["properties"] if p["property_key"] == "ev-clock-error-bound")["value"] = 1e300
        return changed

    before = len(store.revisions(result.tenant.id, result.site.id))
    with pytest.raises(FoundationRefused) as caught:
        FoundationService(store, "demo", Clock(NOW - timedelta(hours=1)))._publish_content_change(
            result.tenant, result.site, effective_from=MISSING_LIMIT_FROM, note="refused",
            unchanged=lambda _c: None, change=huge)
    assert caught.value.code == "EV_CONFIGURATION_INVALID"
    assert "ev-clock-error-bound" in str(caught.value) or "properties[" in str(caught.value)
    assert len(store.revisions(result.tenant.id, result.site.id)) == before


#: W2-05b q3 Q15: the corrected map's normal publication, effective before the 6 October run window.
CORRECTED_FROM = datetime(2026, 10, 5, tzinfo=timezone.utc)
OLD_STATE_MAP = {v: v for v in ("AVAILABLE", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")}


def _state_maps(snapshot) -> list[dict]:
    return [r["conversion"]["parameters"]["map"] for r in json.loads(snapshot.body)["bindings"]
            if r["role"] == "ev_connector_state"]


def test_an_old_map_stays_immutable_and_the_corrected_revision_is_selected(store) -> None:
    """q3 Q15: an already published 05a map without `UNPLUGGED` is never patched; a new normal publication
    carries the seven-label map and is the revision selected for the 6 October window."""
    from dataclasses import replace

    from assetops_backend.sites.composition import read_site_import_source
    from assetops_backend.sites.ev_lab import FIXTURE_PATH
    from assetops_backend.sites.foundation_service import ImportSource, import_site

    source = read_site_import_source(FIXTURE_PATH)
    result = import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                         source=ImportSource(path="var/sites/ev-lab-001.yaml", sha256=source.sha256,
                                             record=source.record),
                         legacy_documents=(), clock=Clock(NOW - timedelta(hours=3)))
    corrected = complete_requests(store, result)
    old = [replace(r, conversion={"kind": "ENUM", "parameters": {"map": OLD_STATE_MAP}})
           if r.role == "ev_connector_state" else r for r in corrected]
    BindingService(store, Clock(NOW - timedelta(hours=2))).publish(
        result.tenant, result.site, requests=old, effective_from=ORIGINAL_FROM,
        note="W2-05b test: the first 05a map.", role_set="ev-roles-1")
    early = datetime(2026, 10, 2, tzinfo=timezone.utc)
    before = snapshot_at(store, result, early)
    assert isinstance(before, Snapshot) and _state_maps(before) == [OLD_STATE_MAP] * 2
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=corrected, effective_from=CORRECTED_FROM,
        note="W2-05b q3 Q15: state map labels UNPLUGGED.", role_set="ev-roles-1")
    # The first revision row keeps its id, map and pinned bytes; the later publication only adds rows.
    [first] = [s for s in store.binding_sets(result.tenant.id, result.site.id) if s.id == before.binding_set.id]
    assert (first.snapshot_sha256, first.snapshot_canonical) == (before.sha256, before.body)
    assert _state_maps(snapshot_at(store, result, early)) == [OLD_STATE_MAP] * 2
    window = snapshot_at(store, result, datetime(2026, 10, 6, 8, tzinfo=timezone.utc))
    assert isinstance(window, Snapshot) and window.sha256 != before.sha256
    assert _state_maps(window) == [{v: v for v in (
        "AVAILABLE", "UNPLUGGED", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")}] * 2
    assert selected(store, result, datetime(2026, 10, 6, 8, tzinfo=timezone.utc)).valid_from == CORRECTED_FROM


# --- q4 Q19: the corrected map's normal re-publication on an already installed EV-LAB-001 ---------------------

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _install_with_state_map(store, state_map=OLD_STATE_MAP):
    """An installation made with the first 05a file: the import plus one binding revision without UNPLUGGED."""
    from dataclasses import replace

    from assetops_backend.sites.composition import read_site_import_source
    from assetops_backend.sites.ev_lab import FIXTURE_PATH
    from assetops_backend.sites.foundation_service import ImportSource, import_site

    source = read_site_import_source(FIXTURE_PATH)
    result = import_site(store, tenant_slug="demo", configured_tenant_slug="demo",
                         source=ImportSource(path="var/sites/ev-lab-001.yaml", sha256=source.sha256,
                                             record=source.record),
                         legacy_documents=(), clock=Clock(NOW - timedelta(hours=3)))
    old = [replace(r, conversion={"kind": "ENUM", "parameters": {"map": state_map}})
           if r.role == "ev_connector_state" else r for r in complete_requests(store, result)]
    BindingService(store, Clock(NOW - timedelta(hours=3))).publish(
        result.tenant, result.site, requests=old, effective_from=ORIGINAL_FROM,
        note=binding_fixture()["note"], role_set="ev-roles-1")
    return result


def _ev_draft(store, *, knowledge_at=None):
    from run_fixtures import FakeRuns, FakeScenarios, FakeSites

    from assetops_backend.runs.profiles import EV_CHARGER_MODEL, EV_PUBLICATION_PROFILE
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import ReadOnlyYamlScenarioStore
    from assetops_backend.sites.cutover import ImportedSiteRegistry

    runs = FakeRuns()
    shipped = ReadOnlyYamlScenarioStore(Path(BACKEND_DIR).parent / "config" / "scenarios")
    setup = RunSetupService(
        runs, FakeSites(()), FakeScenarios(tuple(s for s in shipped.list_scenarios() if s.scenario_id == "ev-complete")),
        model_profiles=(EV_CHARGER_MODEL,), publication_profiles=(EV_PUBLICATION_PROFILE,),
        now=lambda: "2026-10-17T12:00:00Z",
        registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))))
    request = {
        "site_id": "EV-LAB-001", "foundation_version": 1, "scenario_id": "ev-complete", "scenario_version": 1,
        "interval": {"start_time": "2026-10-06T08:00:00Z", "end_time": "2026-10-06T09:00:00Z"},
        "timestep_minutes": 1, "seed": 20517, "model_profile": {"profile_id": "ev-charger", "profile_version": 1},
        "publication_profile": {"profile_id": "ev-publication", "profile_version": 1}, "run_inputs": [],
    }
    if knowledge_at is not None:
        request["knowledge_at"] = knowledge_at
    return setup.create_draft_run(request), runs


def test_republish_corrected_bindings_on_an_old_installation(store) -> None:
    from assetops_backend.runs.refusals import RunSetupRefused
    from assetops_backend.sites.ev_lab import CORRECTED_NOTE, republish_corrected_bindings

    result = _install_with_state_map(store)
    [old] = store.binding_sets(result.tenant.id, result.site.id)
    old_bytes = (old.id, old.snapshot_sha256, old.snapshot_canonical)
    window = datetime(2026, 10, 6, 8, tzinfo=timezone.utc)
    assert _state_maps(snapshot_at(store, result, window)) == [OLD_STATE_MAP] * 2
    # q4 Q18: a Draft against the old selected map refuses before any run exists.
    with pytest.raises(RunSetupRefused) as caught:
        _ev_draft(store)
    assert caught.value.kind == "VERSION_UNAVAILABLE"

    acted_at = NOW - timedelta(hours=1)
    outcome = republish_corrected_bindings(store, tenant_slug="demo", clock=Clock(acted_at))
    assert outcome.published
    sets = store.binding_sets(result.tenant.id, result.site.id)
    [kept] = [s for s in sets if s.id == old.id]
    assert (kept.id, kept.snapshot_sha256, kept.snapshot_canonical) == old_bytes
    current = sorted((s for s in sets if s.superseded_at is None), key=lambda s: s.valid_from)
    assert [(s.valid_from, s.valid_to) for s in current] == [(ORIGINAL_FROM, CORRECTED_FROM), (CORRECTED_FROM, None)]
    assert _state_maps(snapshot_at(store, result, datetime(2026, 10, 2, tzinfo=timezone.utc))) == [OLD_STATE_MAP] * 2
    corrected = current[1]
    assert (corrected.recorded_at, corrected.change_note) == (acted_at, CORRECTED_NOTE)
    assert (outcome.revision_id, outcome.snapshot_sha256) == (str(corrected.id), corrected.snapshot_sha256)
    assert outcome.snapshot_sha256 != old.snapshot_sha256
    assert all("UNPLUGGED" in m for m in _state_maps(snapshot_at(store, result, window)))

    # Idempotent: a second run publishes nothing and names the same corrected revision.
    again = republish_corrected_bindings(store, tenant_slug="demo", clock=Clock(NOW))
    assert (again.published, again.revision_id, again.snapshot_sha256) == (
        False, outcome.revision_id, outcome.snapshot_sha256)
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == len(sets)

    # A fresh 6 October Draft freezes the corrected revision; the old selected map (as known before the
    # correction) still refuses.
    run, _ = _ev_draft(store)
    assert (run.registered_basis.binding_set_revision_id, run.registered_basis.snapshot_sha256) == (
        outcome.revision_id, outcome.snapshot_sha256)
    with pytest.raises(RunSetupRefused) as caught:
        _ev_draft(store, knowledge_at=(acted_at - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert caught.value.kind == "VERSION_UNAVAILABLE"


def test_republish_on_a_fresh_corrected_install_is_a_no_change(store) -> None:
    from assetops_backend.sites.ev_lab import republish_corrected_bindings

    result = install(store)
    [only] = store.binding_sets(result.tenant.id, result.site.id)
    outcome = republish_corrected_bindings(store, tenant_slug="demo", clock=Clock(NOW))
    assert (outcome.published, outcome.revision_id, outcome.snapshot_sha256) == (
        False, str(only.id), only.snapshot_sha256)
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == 1


def test_republish_refuses_a_later_independent_publication(store) -> None:
    from assetops_backend.sites.ev_lab import EvLabRepublishRefused, republish_corrected_bindings

    result = _install_with_state_map(store)
    BindingService(store, Clock(NOW - timedelta(hours=2))).publish(
        result.tenant, result.site, requests=complete_requests(store, result),
        effective_from=datetime(2026, 10, 7, tzinfo=timezone.utc), note="independent", role_set="ev-roles-1")
    before = len(store.binding_sets(result.tenant.id, result.site.id))
    with pytest.raises(EvLabRepublishRefused, match="later binding publication"):
        republish_corrected_bindings(store, tenant_slug="demo", clock=Clock(NOW))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == before


def test_republish_refuses_a_map_that_is_not_the_known_first_one(store) -> None:
    from assetops_backend.sites.ev_lab import EvLabRepublishRefused, republish_corrected_bindings

    five = {v: v for v in ("PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")}
    result = _install_with_state_map(store, five)
    before = len(store.binding_sets(result.tenant.id, result.site.id))
    with pytest.raises(EvLabRepublishRefused, match="not the known first"):
        republish_corrected_bindings(store, tenant_slug="demo", clock=Clock(NOW))
    assert len(store.binding_sets(result.tenant.id, result.site.id)) == before
