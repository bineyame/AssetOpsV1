"""S3-01 phase 1: `registered-kobo-publication` v3 publishes the two capability channels.

`D-2026-10-11-s3-dispatch-interval-assessment`. A registered KOBO-001 after the
labelled S3 demo configuration (`backend/conversions/kobo-001-s3-dispatch-demo-config.json`)
runs `mini-grid` v3 through a real gateway process. On a `minigrid-roles-2`
basis both capability readings are admitted as V3 envelopes; on the earlier
`minigrid-roles-1` basis (generator values present, capability channels not
bound) neither exists anywhere on the public path - the Lab publishes a
declared signal only where the frozen basis maps it, so the gateway never sees
one and nothing is substituted. The profile carries no record channel.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import RegisteredGatewayPublisher  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_backend.runs.profiles import (  # noqa: E402
    MINI_GRID_V3_MODEL,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V2,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V3,
)
from assetops_backend.sites.binding_service import BindingService  # noqa: E402
from assetops_backend.sites.demo_configuration import apply_demo_configuration  # noqa: E402
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402

V3 = REGISTERED_KOBO_PUBLICATION_PROFILE_V3
DEMO = json.loads((registered.REPOSITORY / "backend" / "conversions" / "kobo-001-s3-dispatch-demo-config.json")
                  .read_text(encoding="utf-8"))
CAPABILITY = {("pv-inverter-controller", "available-power"), ("battery-pcs-controller", "discharge-capability")}
GENERATOR_STATUS = ("generator-controller", "status")


def _scenario(name: str):
    return registered.parse_scenario_document(
        yaml.safe_load((registered.REPOSITORY / "config" / "scenarios" / f"{name}.yaml").read_text(encoding="utf-8")),
        source=name, origin="SHIPPED",
    )


PROLONGED = _scenario("kobo-mini-grid-prolonged")
DEGRADED = _scenario("kobo-s3-dispatch-degraded-reporting")
NECESSARY_RUN = _scenario("kobo-s3-dispatch-necessary-run")
NOW = registered.NOW


@pytest.fixture(scope="module")
def configured():
    store, result, _ = registered.converted()
    clock = registered.Clock(registered.CONVERTED_AT + timedelta(minutes=10))
    apply_demo_configuration(store, registered.FoundationService(store, "demo", clock), BindingService(store, clock),
                             result.tenant, result.site, DEMO)
    return store


def service(store):
    registry = registered.ImportedSiteRegistry(registered.FoundationService(store, "demo", registered.Clock(NOW)))
    return registered.RunSetupService(
        registered.FakeRuns(), registered.FakeSites(()), registered.FakeScenarios((PROLONGED, DEGRADED, NECESSARY_RUN)),
        model_profiles=(MINI_GRID_V3_MODEL,),
        publication_profiles=(REGISTERED_KOBO_PUBLICATION_PROFILE_V2, V3),
        now=lambda: registered.text(NOW),
        registered_bases=registered.RegisteredLabBasis(registry),
    )


def draft(store, day: str, foundation_version: int, scenario=PROLONGED):
    body = registered.request(
        foundation_version=foundation_version, scenario_id=scenario.scenario_id,
        scenario_version=scenario.version.scenario_version,
        interval={"start_time": f"2026-10-{day}T03:00:00Z", "end_time": f"2026-10-{day}T11:00:00Z"},
        timestep_minutes=5,
        model_profile={"profile_id": MINI_GRID_V3_MODEL.model_profile_id,
                       "profile_version": MINI_GRID_V3_MODEL.model_profile_version},
        publication_profile={"profile_id": V3.publication_profile_id,
                             "profile_version": V3.publication_profile_version},
    )
    run = service(store).create_draft_run(body)
    assert run.execution_status == "READY" and run.blocking_reasons == (), (run.execution_status, run.blocking_reasons)
    return run


def version_at(store, instant: str) -> tuple[int, str]:
    foundation = registered.FoundationService(store, "demo", registered.Clock(NOW))
    tenant = foundation.tenant()
    at = datetime.fromisoformat(instant.replace("Z", "+00:00"))
    view = foundation.read(foundation.site(tenant, "KOBO-001"), tenant, at, None)
    return view.revision.version, view.binding_set.role_set


def published(tmp_path: Path, run) -> list:
    process = GatewayProcess(write_config(tmp_path / "g", provisioning_from_snapshot(run.registered_basis.snapshot_canonical)))
    assert process.ready, process.first_line
    port = HostLabExecution(artifacts=YamlExecutionArtifacts(tmp_path / "h"), stages=JsonSourceStages(tmp_path / "s"),
                            gateway=RegisteredGatewayPublisher(process.link))
    try:
        port.start(run)
        assert port.run_to_end(run).status == "COMPLETED"
        view = port.registered_stage(run)
        return [parse_canonical_envelope_v3_text(e.envelope_text) for e in view.envelopes], view
    finally:
        process.kill()


def test_v3_is_measurement_only_and_v1_v2_are_unchanged() -> None:
    assert V3.record_channels == () and V3.publication_clock == "RUN_VIRTUAL"
    keys = {d.signal_key for d in V3.device_signals}
    assert CAPABILITY | {GENERATOR_STATUS} <= keys
    assert not (CAPABILITY | {GENERATOR_STATUS}) & {d.signal_key for d in REGISTERED_KOBO_PUBLICATION_PROFILE_V2.device_signals}
    assert V3.supported_reporting("battery-discharge-capability-reporting-availability") is not None
    assert V3.supported_reporting("override-record-reporting-availability") is None
    numeric = [d for d in V3.device_signals if d.canonical_unit != "state"]
    assert numeric and all(d.resolution == "0.000001" for d in numeric)


def test_roles_2_run_publishes_both_capability_readings(configured, tmp_path) -> None:
    version, role_set = version_at(configured, "2026-10-02T03:00:00Z")
    assert role_set == "minigrid-roles-2"
    run = draft(configured, "02", version)
    envelopes, _ = published(tmp_path, run)
    channels = {(e.device_id, e.signal_id) for e in envelopes}
    assert CAPABILITY | {GENERATOR_STATUS} <= channels
    capability = [e for e in envelopes if (e.device_id, e.signal_id) in CAPABILITY]
    assert len(capability) >= 2 * 32  # eight hours at fifteen minutes, both channels
    assert all(e.binding_version == run.registered_basis.binding_set_version for e in capability)


def test_roles_1_run_publishes_no_capability_reading(configured, tmp_path) -> None:
    version, role_set = version_at(configured, "2026-10-01T03:00:00Z")
    assert role_set == "minigrid-roles-1"
    run = draft(configured, "01", version)
    envelopes, view = published(tmp_path, run)
    channels = {(e.device_id, e.signal_id) for e in envelopes}
    assert GENERATOR_STATUS in channels and not CAPABILITY & channels
    assert envelopes, "the roles-1 run still publishes its bound measurements"


def test_degraded_scenario_gap_silences_discharge_capability_for_an_hour(configured, tmp_path) -> None:
    version, _ = version_at(configured, "2026-10-03T03:00:00Z")
    run = draft(configured, "03", version, scenario=DEGRADED)
    envelopes, _ = published(tmp_path, run)
    discharge = sorted(e.source_time for e in envelopes
                       if (e.device_id, e.signal_id) == ("battery-pcs-controller", "discharge-capability"))
    available = sorted(e.source_time for e in envelopes
                       if (e.device_id, e.signal_id) == ("pv-inverter-controller", "available-power"))
    assert len(available) - len(discharge) == 4  # one hour of 15-minute readings not carried


def test_necessary_run_scenario_is_short_of_capability_at_every_running_report(configured, tmp_path) -> None:
    """S3-01 phase 3 (review F5): the generator runs to the end of the interval, and at every
    report while it runs, published load exceeds PV available power plus PCS discharge capability
    (decision-table row 4), so a dispatch-3 interval there is all-Necessary on public values."""
    version, role_set = version_at(configured, "2026-10-09T03:00:00Z")
    assert role_set == "minigrid-roles-2"
    run = draft(configured, "09", version, scenario=NECESSARY_RUN)
    envelopes, _ = published(tmp_path, run)
    # no reporting fault: the only non-GOOD readings are the interval means not yet complete at run start
    assert {(e.source_time, e.unavailable_reason) for e in envelopes if e.quality != "GOOD"} == {
        ("2026-10-09T03:00:00Z", "NO_COMPLETED_INTERVAL")}
    grid: dict[str, dict[tuple[str, str], Decimal]] = {}
    for e in envelopes:
        if e.value is not None and (e.device_id, e.signal_id) != GENERATOR_STATUS:
            grid.setdefault(e.interval_end or e.source_time, {})[(e.device_id, e.signal_id)] = Decimal(e.value)
    status = {e.source_time: e.value for e in envelopes if (e.device_id, e.signal_id) == GENERATOR_STATUS}
    meters = [(m, "active-power") for m in ("residential-meter", "clinic-meter", "mill-meter")]
    running = sorted(t for t, v in status.items() if v == "RUNNING")
    assert running and running[-1] == "2026-10-09T11:00:00Z"  # runs to the end: no stop inside the interval
    assert "STOPPED" in {status[t] for t in status if t < running[0]}  # a STOPPED report before the first ON
    assert all(status[t] == "RUNNING" for t in status if t >= running[0])
    for t in running:
        slot = grid[t]
        load = sum(slot[m] for m in meters)
        pv, dis = slot[("pv-inverter-controller", "available-power")], slot[("battery-pcs-controller", "discharge-capability")]
        assert load > pv + dis, (t, load, pv, dis)
