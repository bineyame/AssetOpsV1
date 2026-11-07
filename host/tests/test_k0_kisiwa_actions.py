"""DIESEL-1 K0 (ruling DIESEL-1-R3f): the byte-equal pins, Kisiwa action setup and kernel parity with F0r.

Test 1 (byte-equal, §9c.3 (b)) rebuilds every fixture of `k0_byte_equal_pins` and asserts its three digests. It
lives here, not under `backend/tests`, because digest (c) needs the host's `frozen_world_inputs` and the Kobo
fixture is `host/tests/kobo.py`.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT / "backend" / "tests", ROOT / "tools", ROOT / "host", Path(__file__).resolve().parent):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from execution_adapter import frozen_world_inputs  # noqa: E402
from k0_byte_equal_pins import FIXED_CREATED_AT, FIXED_RUN_ID, PINS  # noqa: E402

import kobo  # noqa: E402
from assetops_backend.runs.parsing import render_run_document  # noqa: E402
from assetops_backend.runs.source_publication import run_identity_sha256  # noqa: E402
from assetops_contracts.trajectory import frozen_inputs_identity  # noqa: E402
from assetops_simulator.kernel.execute import KERNEL_VERSION, NUMERIC_POLICY  # noqa: E402


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dumps(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _ev_selection():
    """The EV fixture's registered selection, built fresh under F0's seeded uuid4 (see the pins docstring)."""
    import test_w205b_ev_scenarios as evs
    from probe_kisiwa_fuel import seeded_uuid4

    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.ev_lab import install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService

    with seeded_uuid4():
        store = evs.InMemoryFoundationStore()
        install_ev_lab(store, tenant_slug=evs.DEVELOPMENT_TENANT_SLUG, clock=lambda: evs.NOW - timedelta(hours=3))
        return RegisteredLabBasis(ImportedSiteRegistry(FoundationService(
            store, evs.DEVELOPMENT_TENANT_SLUG, lambda: evs.NOW))).select(
                evs.EV_SITE, start_time=evs.WINDOW["start"], end_time=evs.WINDOW["end"], knowledge_at=None)


def pinned_run(key: str):
    setup = PINS[key][0]
    if key == "cold":
        from test_w202_cold_run_identity import cold_request, cold_service

        service, _ = cold_service()
        return service.create_draft_run(cold_request())
    if key == "ev":
        from test_w205b_ev_scenarios import ev_request, ev_service

        service, _ = ev_service(selection=_ev_selection())
        return service.create_draft_run(ev_request())
    name, profile, version, start, end, step = setup
    return kobo.kobo_draft(name, model_profile=profile, model_profile_version=version, start_time=start,
                           end_time=end, timestep_minutes=step)


def pinned_digests(run) -> tuple:
    run = replace(run, run_id=FIXED_RUN_ID, created_at=FIXED_CREATED_AT)
    document = render_run_document(run)
    identity = document["deterministic_identity"]
    trajectory = None
    if not run.blocking_reasons:
        trajectory = frozen_inputs_identity(
            frozen_world_inputs(run), kernel_version=KERNEL_VERSION,
            model_profile_id=run.deterministic_identity.profiles.model_profile_id,
            model_profile_version=run.deterministic_identity.profiles.model_profile_version,
            numeric_policy=NUMERIC_POLICY)
    return (_sha(_dumps(document)), run_identity_sha256(run), _sha(_dumps(identity.get("causes"))), trajectory,
            len(identity.get("causes") or []), len(identity.get("reporting_path_conditions") or []))


def test_the_pins_cover_causes_conditions_and_trajectories() -> None:
    """Non-vacuity: the pinned set has scenario causes, reporting-path conditions and READY trajectories."""
    values = [row[1] for row in PINS.values()]
    assert sum(v[4] for v in values) >= 2
    assert sum(v[5] for v in values) >= 3
    assert sum(1 for v in values if v[3] is not None) >= 5
    assert {"kobo", "cold", "ev"} <= set(PINS)


@pytest.mark.parametrize("key", sorted(PINS))
def test_a_run_with_no_actions_is_byte_equal_to_its_pin(key: str) -> None:
    run = pinned_run(key)
    assert pinned_digests(run) == PINS[key][1]
    text = _dumps(render_run_document(run))
    assert '"origin"' not in text and '"action_ref"' not in text and '"operational_action_log"' not in text


# --- 9 and 10: registered setup, kernel parity with F0r, and the Lab API readback --------------------------------

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
REFERENCE = Path(__file__).resolve().parents[2] / ".agent" / "DIESEL-F0" / "probe-result.json"
IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
SETUP_AT = "2026-09-29T11:00:00Z"
KEY = {"log_id": "kisiwa-001-operational-actions", "log_version": 1}


@pytest.fixture(scope="module", params=["memory", "postgres"])
def registered_store(request):
    """KISIWA-001 registered by `register_in` on F0r's clock: in memory always; on Postgres when a *_test URL is set."""
    import demo_combined_kisiwa as kis

    if request.param == "memory":
        from foundation_fakes import InMemoryFoundationStore

        store = InMemoryFoundationStore()
        kis.register_in(store, IMPORT_AT, INSTALL_AT)
        yield store
        return
    if not URL:
        pytest.skip("ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
    import pg_harness
    from sqlalchemy.engine import make_url

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    owned = PostgresFoundationStore(URL)
    kis.register_in(owned, IMPORT_AT, INSTALL_AT)
    yield owned
    pg_harness.dispose(owned)


def _probe():
    import probe_kisiwa_fuel

    return probe_kisiwa_fuel


def test_the_kernel_moves_the_tank_exactly_as_f0r_did(registered_store) -> None:
    """§9c.3 (d), stop S3: runs 1-4 chained as F0r chains them, with the actions frozen through the real field path
    (origin and action_ref on the frozen records, no event-id carrier). Every non-generator tank step equals F0r's
    committed account, read from the evidence: run 2's delivery and run 4's removal at 40/3 L over steps 120-128.
    Every other step's non-generator change is 0, and each run starts from F0r's exact state."""
    from execution_adapter import run_to_end
    from kisiwa import KisiwaRegistered

    from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog

    p = _probe()
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    expected = [step for step in reference["gates"]["F2"]["non_generator_steps"] if step["run"] <= 4]
    reg = KisiwaRegistered(registered_store, SETUP_AT, YamlOperationalActionLog())
    soc, fuel, found = p.START_SOC, p.START_FUEL, []
    for k in range(1, 5):
        start = p._run_start(k)
        run = reg.draft(p.day_document(soc, fuel), p._iso(start), p._iso(start + timedelta(days=1)), "v7", KEY)
        assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
        identity = run.deterministic_identity
        assert list(identity.intervention_history) == reference["runs"][k - 1]["intervention_history"]
        assert all(c.origin == "OPERATIONAL_ACTION" and "/" in c.event_id
                   and not c.event_id.startswith("OPERATIONAL_ACTION/") for c in identity.causes)
        trajectory = run_to_end(run, reg.sim("v7")).trajectory
        begin = p._state(trajectory.boundaries[0])
        assert {key: str(value) for key, value in begin.items()} == reference["runs"][k - 1]["start"]
        found += [{"run": k, "step": i, "offset_minutes": i * p.STEP, "litres": str(other)}
                  for i, _, _, other, _ in p.tank_account(trajectory) if other != 0]
        end = p._state(trajectory.boundaries[-1])
        soc, fuel = float(end["soc"]), float(end["fuel"])
    assert found == expected
    assert [s["step"] for s in found if s["run"] == 4] == list(range(120, 129))
    assert {s["litres"] for s in found if s["run"] == 4} == {str(Fraction(40, 3))}
    assert [s for s in found if s["run"] == 2] == [s for s in expected if s["run"] == 2] and len(expected) == 10


class _NoTemplates:
    def list_templates(self):
        return ()

    def get_template(self, template_id):  # pragma: no cover
        raise AssertionError("no run route reads a template")


def test_the_lab_api_freezes_and_reads_back_the_operational_action(registered_store) -> None:
    """Test 10: the Lab router composed with the file adapter; POST a Kisiwa run with the key, then GET it."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from fixtures import FakeRuns, FakeScenarios, FakeSites
    from kisiwa import KisiwaRegistered

    from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog
    from assetops_backend.runs.profiles import MINI_GRID_V7_MODEL, REGISTERED_KOBO_PUBLICATION_PROFILE_V5
    from assetops_backend.scenarios.parsing import parse_scenario_document
    from assetops_backend.simulator_lab_api import build_simulator_lab_router

    p = _probe()
    reg = KisiwaRegistered(registered_store, SETUP_AT)
    definition = parse_scenario_document(p.day_document(p.START_SOC, p.START_FUEL), source="a Kisiwa scenario",
                                         origin="SHIPPED")
    profile = REGISTERED_KOBO_PUBLICATION_PROFILE_V5
    app = FastAPI()
    app.include_router(build_simulator_lab_router(
        _NoTemplates(), FakeSites(()), FakeScenarios((definition,)), FakeRuns(), (MINI_GRID_V7_MODEL,), (profile,),
        registered_bases=reg.basis, operational_actions=YamlOperationalActionLog()))
    client = TestClient(app)
    start = p._run_start(4)
    response = client.post("/api/simulator-lab/runs", json={
        "site_id": "KISIWA-001", "foundation_version": reg.foundation_version,
        "scenario_id": definition.scenario_id, "scenario_version": definition.version.scenario_version,
        "interval": {"start_time": p._iso(start), "end_time": p._iso(start + timedelta(days=1))},
        "timestep_minutes": 5, "seed": 20260929,
        "model_profile": {"profile_id": "mini-grid", "profile_version": 7},
        "publication_profile": {"profile_id": profile.publication_profile_id,
                                "profile_version": profile.publication_profile_version},
        "run_inputs": [], "operational_actions": KEY})
    assert response.status_code == 201, response.text
    run_id = response.json()["run"]["run_id"] if "run" in response.json() else response.json()["run_id"]
    body = client.get(f"/api/simulator-lab/runs/{run_id}").json()
    text = json.dumps(body)
    rows = [row for row in _find_rows(body) if row["answered_by"] == "OPERATIONAL_ACTION"]
    assert {row["field"] for row in rows} == {"Cause kis-removal-1/tank-decrease",
                                              "Reporting path kis-removal-1/sensor-disconnected",
                                              "Operational action log"}, text[:2000]
    assert any("by Unidentified" in row["answered_by_detail"] for row in rows)


def _find_rows(value) -> list[dict]:
    """Every frozen-input row in a response, wherever the payload nests them."""
    found, pending = [], [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if "frozen_inputs" in item and isinstance(item["frozen_inputs"], list):
                found += item["frozen_inputs"]
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return found
