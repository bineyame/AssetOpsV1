"""DIESEL-1 F0: the Kisiwa fuel-events probe. In memory; no database, no product code.

The declared world, the `fuel-balance-1` parameters, the gates (F0a, F1-F10) and the stops are DIESEL-1-R2 §8.3
with §8.2a (`.agent/build-sheet-DIESEL-1.md`, dc72cb72a), fixed before any run and never tuned. Kisiwa's physics are
D0's (§2.2), imported from `tools/probe_kisiwa_nights.py` and never edited: start fuel 700 L, stop 90 % throughout.

OA-1: the scenario of every run is D0's `day_document` unchanged (weather and loads only). The fuel delivery, the
unrecorded removal (with the sensor unplugged), the dips, the seal and the sensor-power fix are operational actions
in `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`. `apply_actions` stands in for K0's run setup: it
adds each action's physical effect to the FROZEN run (a `FrozenCause`, and for the unplugged sensor a
`FrozenReportingPathCondition`) with `dataclasses.replace`, origin `OPERATIONAL_ACTION` and the action's content
hash carried in the event id and in `intervention_history`. No scenario entry is written.

Ten day-runs, each 15:00 to 15:00 local, from `2026-10-01T12:00:00Z`, chained at full precision; a reference chain of
the same ten runs without the actions checks that dispatch is unaffected (F3). Night k is 18:00 to 12:00 local,
steps [36, 252) of run k. Readings come from `registered-kobo-publication` v5 drafted for Kisiwa (F5) and are
turned into gateway report texts with `keyed_reports` against the run's frozen binding snapshot (F6).

DIESEL-1-R3/R3a (§9, §9a): every run is set up on the registered path (c): Kisiwa imported and converted into an
in-memory Foundation store, the real `RegisteredLabBasis` over it. Tank level from a probe-local mini-grid v7
identical in content to K1a's; product code has no v7 until K1a merges.

`python tools/probe_kisiwa_fuel.py` prints the result JSON; `--write` writes `.agent/DIESEL-F0/probe-result.json`
and prints the per-night line; `--check` exits 1 if the committed JSON differs from a fresh run (F8). `--handover`
is K7's and is not built.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import sys
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "host" / "tests"))
sys.path.insert(0, str(ROOT / "host"))

import yaml  # noqa: E402

from probe_kisiwa_nights import (  # noqa: E402  D0, imported, never edited
    FOUNDATION_VALID_FROM, FUEL, FUEL_LIMIT_NOTE, GEN, GENERATOR_FLOW, NIGHT, NO_LOAD_RATE, PROFILE, SFC, SITE_ID,
    SOC, STEPS_PER_RUN, STOP_BEFORE, day_document, dec, kisiwa_site, measure_night, stop_at)

ACTIONS = ROOT / ".agent" / "DIESEL-F0" / "kisiwa-001-operational-actions.draft.yaml"
RESULT = ROOT / ".agent" / "DIESEL-F0" / "probe-result.json"
D0_TEMPLATE = ROOT / ".agent" / "DIESEL-D0" / "kisiwa-diesel-hybrid-60kw.draft.yaml"

RUN1_START = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)  # 15:00 local (UTC+3)
RUNS = 10
START_SOC, START_FUEL = 100, 700  # §8.3: 700 L of 1000 at run 1
CHANGE_RUN = 6  # the change instant is the run 6 start (partitioning only)
INCIDENT_NIGHT = 4
STEP = 5
OPENING_ORIGIN = "OPERATIONAL_ACTION"
TANK_SIGNAL = ("fuel-level-sensor", "fuel-level")
REPORTING_STATE = "fuel-level-reporting-availability"
REGISTERED_PROFILE = ("registered-kobo-publication", 5)
TANK_CAPACITY_L = Fraction(1000)  # D0 §2.2 tank, the frozen fuel-tank-capacity (F11)
D0_NIGHT_LITRES = Fraction(26057, 600)  # D0's measured night litres at stop 90 (.agent/DIESEL-D0/probe-result.json)

# --- fuel-balance-1 parameters (§8.3), declared before any run; any change is a new parameter version ---------------
ACCURACY_L = Fraction(10)  # a = Foundation fuel-level-sensor-accuracy, GENERIC_DEFAULT (1 % of a 1000 L tank)
TANK_MARGIN_L = 2 * ACCURACY_L
DELIVERY_TOLERANCE = Fraction(1, 100)
USE_LOW_FACTOR, USE_HIGH_FACTOR = Fraction(9, 10), Fraction(11, 10)
MATERIALITY_L = Fraction(40)
EDGE_SEARCH_MIN = 30  # opening in [start - 30, start], closing in [end, end + 30]
GAP_LONGER_THAN_MIN = 60

PARAMETERS = {
    "id": "fuel-balance-1",
    "window": "night k, 18:00 local to 12:00 local next day",
    "opening": "last accepted fuel_level reading in [start - 30 min, start]; missing -> NOT_ASSESSED MISSING_OPENING",
    "closing": "first accepted fuel_level reading in [end, end + 30 min]; missing -> NOT_ASSESSED MISSING_CLOSING",
    "accuracy_a_l": "10 (GENERIC_DEFAULT)", "tank_margin_l": "2a = 20",
    "deliveries": "sum of FUEL_DELIVERY ticket volumes with instant in [start, end); tolerance 1/100 x ticket",
    "use": "loaded = sum kWh x 0.355; idle_h = RUNNING 5-min slots at 0 kWh; use_low = 9/10 loaded; "
           "use_high = 11/10 (loaded + idle_h x 4.9)",
    "residual_low": "(O - C) + D - D_tol - use_high - 2a", "residual_high": "(O - C) + D + D_tol - use_low + 2a",
    "states": "UNEXPLAINED iff residual_low >= 40; WITHIN_MARGIN iff residual_low <= 0 <= residual_high; "
              "BELOW_MATERIALITY iff 0 < residual_low < 40; EXCESS iff residual_high < 0",
    "gap": "sum of spans longer than 60 min between consecutive accepted fuel_level readings inside the window, "
           "edges included",
}


# --- the band, as pure functions --------------------------------------------------------------------------------------


def reporting_gap_minutes(reading_offsets, start: int, end: int) -> int:
    """Σ of spans longer than 60 min between consecutive accepted readings inside [start, end], edges included."""
    points = [start] + sorted(o for o in reading_offsets if start < o < end) + [end]
    return sum(b - a for a, b in zip(points, points[1:]) if b - a > GAP_LONGER_THAN_MIN)


def balance(terms: dict[str, Any]) -> dict[str, Any]:
    """`fuel-balance-1` over one window, exact Fractions.

    `terms`: `opening`, `closing` (litres or None), `deliveries` (ticket volumes in the window), `loaded_litres`,
    `idle_hours`, `gap_minutes`.
    """
    opening, closing = terms["opening"], terms["closing"]
    if opening is None or closing is None:
        return {"state": "NOT_ASSESSED", "limitation": "MISSING_OPENING" if opening is None else "MISSING_CLOSING",
                "residual_low": None, "residual_high": None, "gap_minutes": terms["gap_minutes"]}
    d = sum((Fraction(v) for v in terms["deliveries"]), Fraction(0))
    d_tol = DELIVERY_TOLERANCE * d
    loaded, idle_h = Fraction(terms["loaded_litres"]), Fraction(terms["idle_hours"])
    use_low = USE_LOW_FACTOR * loaded
    use_high = USE_HIGH_FACTOR * (loaded + idle_h * NO_LOAD_RATE)
    drop = Fraction(opening) - Fraction(closing)
    low = drop + d - d_tol - use_high - TANK_MARGIN_L
    high = drop + d + d_tol - use_low + TANK_MARGIN_L
    if low >= MATERIALITY_L:
        state = "UNEXPLAINED"
    elif high < 0:
        state = "EXCESS"
    elif low <= 0 <= high:
        state = "WITHIN_MARGIN"
    else:
        state = "BELOW_MATERIALITY"
    return {"state": state, "limitation": None, "residual_low": low, "residual_high": high,
            "opening_minus_closing": drop, "deliveries": d, "delivery_tolerance": d_tol, "use_low": use_low,
            "use_high": use_high, "gap_minutes": terms["gap_minutes"]}


# --- the operational-action log -----------------------------------------------------------------------------------


def _parse(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_actions(path: Path = ACTIONS) -> list[dict[str, Any]]:
    """The draft log, each action with its content hash (sha256 of its canonical JSON)."""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    actions = []
    for action in document["actions"]:
        canonical = json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        actions.append({**action, "content_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest()})
    return actions


def _offset(run_start: datetime, at: str) -> int:
    return int((_parse(at) - run_start).total_seconds() // 60)


def _in_run(run_start: datetime, at: str) -> bool:
    return 0 <= _offset(run_start, at) < 1440


def _event_id(action: dict[str, Any], effect: str) -> str:
    return f"{OPENING_ORIGIN}/{action['action_id']}/{effect}/{action['content_sha256'][:16]}"


def apply_actions(run, actions: list[dict[str, Any]], run_start: datetime):
    """The F0a hook, standing in for K0's run setup: add this run's physical effects to the FROZEN run.

    FUEL_DELIVERY -> INCREASE POINT; FUEL_REMOVAL_UNRECORDED -> DECREASE WINDOW plus, for `sensor_disconnected`, a
    reporting-path condition on `fuel-level-reporting-availability@fuel-tank`. Dips, the seal and the sensor fix
    move nothing. Origin and content hash ride in the event id and in `intervention_history` (the frozen records
    have no origin field)."""
    from assetops_backend.state_refs import component_state
    from assetops_backend.runs.models import FrozenCause, FrozenReportingPathCondition

    identity = run.deterministic_identity
    causes, conditions, history = list(identity.causes), list(identity.reporting_path_conditions), []
    tank = component_state("fuel-tank-volume", "fuel-tank")
    for action in actions:
        if not _in_run(run_start, action["at"]):
            continue
        kind, offset = action["kind"], _offset(run_start, action["at"])
        if kind == "FUEL_DELIVERY":
            causes.append(FrozenCause(
                event_id=_event_id(action, "tank-increase"), state_ref=tank, direction="INCREASE",
                parameter_id=f"{action['action_id']}-volume", canonical_value=float(action["volume_l"]),
                canonical_unit="L", dimension="VOLUME", timing_shape="POINT", offset_minutes=offset,
                duration_minutes=None))
        elif kind == "FUEL_REMOVAL_UNRECORDED":
            causes.append(FrozenCause(
                event_id=_event_id(action, "tank-decrease"), state_ref=tank, direction="DECREASE",
                parameter_id=f"{action['action_id']}-volume", canonical_value=float(action["volume_l"]),
                canonical_unit="L", dimension="VOLUME", timing_shape="WINDOW", offset_minutes=offset,
                duration_minutes=int(action["duration_minutes"])))
            span = action.get("sensor_disconnected")
            if span:
                conditions.append(FrozenReportingPathCondition(
                    event_id=_event_id(action, "sensor-disconnected"),
                    state_ref=component_state(REPORTING_STATE, "fuel-tank"), timing_shape="WINDOW",
                    offset_minutes=_offset(run_start, span["at"]), duration_minutes=int(span["duration_minutes"])))
        else:
            continue  # TANK_DIP, TANK_SEALED, SENSOR_POWER_PROTECTED: no physical effect in v1
        history.append(f"{OPENING_ORIGIN}:{action['action_id']}:{action['content_sha256']}")
    if not history:
        return run, ()
    frozen = replace(identity, causes=tuple(causes), reporting_path_conditions=tuple(conditions),
                     intervention_history=identity.intervention_history + tuple(history))
    return replace(run, deterministic_identity=frozen), tuple(history)


def _round_litre(value: Fraction) -> int:
    with localcontext() as ctx:
        ctx.prec = 60
        exact = Decimal(value.numerator) / Decimal(value.denominator)
        return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def dip_values(trajectories: dict[int, Any], actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each TANK_DIP's value: the run's tank stock at `at`, rounded half-even to 1 L. Read, never typed."""
    dips = []
    for action in actions:
        if action["kind"] != "TANK_DIP":
            continue
        k = next(k for k in trajectories if _in_run(_run_start(k), action["at"]))
        offset = _offset(_run_start(k), action["at"])
        assert offset % STEP == 0, action
        stock = dict(trajectories[k].boundaries[offset // STEP].stocks)[FUEL]
        dips.append({"action_id": action["action_id"], "at": action["at"], "run": k, "offset_minutes": offset,
                     "true_stock_l": dec(stock), "dip_l": _round_litre(stock)})
    return dips


# --- the Site, the Draft and the runs -----------------------------------------------------------------------------


def _run_start(k: int) -> datetime:
    return RUN1_START + timedelta(days=k - 1)


BINDINGS = ROOT / ".agent" / "DIESEL-F0" / "kisiwa-001-bindings.draft.json"
IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
CONVERT_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
IMPORT_PATH = "var/sites/kisiwa-001.yaml"


def register_kisiwa():
    """DIESEL-1-R3 §9.1 (c): import Kisiwa and convert its bindings in an in-memory Foundation store, with the
    product's own `import_site` and `convert`. Only the storage engine is substituted."""
    sys.path.insert(0, str(ROOT / "backend" / "tests"))
    from foundation_fakes import InMemoryFoundationStore
    from assetops_backend.sites.binding_conversion import convert
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.foundation_service import ImportSource, import_site
    from assetops_backend.sites.site_parsing import render_site_document

    record = kisiwa_site()
    payload = yaml.safe_dump(render_site_document(record), sort_keys=True).encode("utf-8")
    source = ImportSource(path=IMPORT_PATH, sha256=hashlib.sha256(payload).hexdigest(), record=record)
    store = InMemoryFoundationStore()
    imported = import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=source,
                           legacy_documents=(), clock=lambda: IMPORT_AT)
    fixture = json.loads(BINDINGS.read_text(encoding="utf-8"))
    outcome = convert(store, BindingService(store, lambda: CONVERT_AT), imported.tenant, imported.site, fixture)
    return store, imported, outcome


def _profile():
    from assetops_backend.runs.profiles import find_publication_profile  # noqa: F401
    from assetops_backend.runs.profiles import REGISTERED_KOBO_PUBLICATION_PROFILE_V5

    assert (REGISTERED_KOBO_PUBLICATION_PROFILE_V5.publication_profile_id,
            REGISTERED_KOBO_PUBLICATION_PROFILE_V5.publication_profile_version) == REGISTERED_PROFILE
    return REGISTERED_KOBO_PUBLICATION_PROFILE_V5


SETUP_AT = "2026-09-29T10:00:00Z"  # run setup clock (after conversion, before run 1); knowledge_at absent
PROBE_V7_LINE = ("Tank level from a probe-local mini-grid v7 identical in content to K1a's; product code has no v7 "
                 "until K1a merges.")
V7_SENTENCE = (" Version seven also samples the fuel in the tank at an instant, after that instant's events, so a "
               "tank level sensor can report it.")
V7_STOCK_STATEMENT = ("The fuel in the tank, initialized by the scenario, moved by accepted generator energy and by "
                      "any frozen declared cause, such as a recorded operational action.")


def probe_v7():
    """DIESEL-1-R3 §9.2 K1a's content, built here only (probe-local; no product file is edited):
    simulator `PROBE_V7_SIM` and product profile `PROBE_V7_PROFILE`."""
    from assetops_backend.runs.profiles import MINI_GRID_V6_MODEL as product_v6
    from assetops_simulator.packs import fuel
    from assetops_simulator.packs.mini_grid import MINI_GRID_V6_MODEL as sim_v6

    stock = [h for h in sim_v6.handlers if h.handler_id == "fuel-tank-volume-stock"]
    assert len(stock) == 1, stock
    handlers = tuple(replace(h, statement=V7_STOCK_STATEMENT) if h is stock[0] else h for h in sim_v6.handlers)
    sim = replace(sim_v6, model_profile_version=7, statement=sim_v6.statement + V7_SENTENCE,
                  handlers=handlers + (fuel.SAMPLE_HANDLER,))
    states = tuple(
        replace(s, supported_roles=frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}), statement=V7_STOCK_STATEMENT)
        if s.state_key == "fuel-tank-volume" else s for s in product_v6.supported_states)
    profile = replace(product_v6, model_profile_version=7, statement=product_v6.statement + V7_SENTENCE,
                      supported_states=states)
    return sim, profile


class Registered:
    """The (c) registered path: one in-memory store, the real `RegisteredLabBasis` over it."""

    def __init__(self) -> None:
        from assetops_backend.runs.registered_basis import RegisteredLabBasis
        from assetops_backend.sites.cutover import ImportedSiteRegistry
        from assetops_backend.sites.foundation_service import FoundationService

        self.store, self.imported, self.conversion = register_kisiwa()
        clock = lambda: datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)  # noqa: E731
        self.basis = RegisteredLabBasis(ImportedSiteRegistry(FoundationService(self.store, "demo", clock)))
        self.v7_sim, self.v7_profile = probe_v7()
        selection = self.basis.select(SITE_ID, start_time=_iso(RUN1_START),
                                      end_time=_iso(RUN1_START + timedelta(days=1)), knowledge_at=None)
        self.foundation_version = selection.basis.foundation_version

    def draft(self, document: dict[str, Any], start: str, end: str, model: str = "v7"):
        from assetops_backend.runs.profiles import MINI_GRID_V6_MODEL
        from assetops_backend.runs.service import RunSetupService
        from assetops_backend.scenarios.parsing import parse_scenario_document
        from fixtures import FakeRuns, FakeScenarios, FakeSites

        profile = _profile()
        chosen = self.v7_profile if model == "v7" else MINI_GRID_V6_MODEL
        definition = parse_scenario_document(copy.deepcopy(document), source="a Kisiwa probe scenario",
                                             origin="SHIPPED")
        setup = RunSetupService(
            FakeRuns(), FakeSites(()), FakeScenarios((definition,)), model_profiles=(chosen,),
            publication_profiles=(profile,), now=lambda: SETUP_AT, registered_bases=self.basis)
        return setup.create_draft_run({
            "site_id": SITE_ID, "foundation_version": self.foundation_version,
            "scenario_id": definition.scenario_id, "scenario_version": definition.version.scenario_version,
            "interval": {"start_time": start, "end_time": end}, "timestep_minutes": PROFILE["timestep_minutes"],
            "seed": 20260929,
            "model_profile": {"profile_id": chosen.model_profile_id,
                              "profile_version": chosen.model_profile_version},
            "publication_profile": {"profile_id": profile.publication_profile_id,
                                    "profile_version": profile.publication_profile_version},
            "run_inputs": []})

    def sim(self, model: str):
        from assetops_simulator.packs.mini_grid import MINI_GRID_V6_MODEL as sim_v6

        return self.v7_sim if model == "v7" else sim_v6


def node_count(document: Any) -> int:
    """The scenario parser's node count (`backend/assetops_backend/document_bounds.py` `reject_oversized`)."""
    nodes, pending = 0, [document]
    while pending:
        value = pending.pop()
        nodes += 1
        if isinstance(value, dict):
            for key, child in value.items():
                pending.extend((key, child))
        elif isinstance(value, (list, tuple)):
            pending.extend(value)
    return nodes


def scenario_is_weather_and_loads_only(document: dict[str, Any]) -> list[str]:
    """F0a: the scenario holds only weather and load entries. Returns the offending entries (empty when clean)."""
    bad = []
    for entry in document["timeline"]:
        text = json.dumps(entry)
        if (entry.get("entry_kind") != "EVENT" or entry.get("category") not in ("WEATHER", "LOAD")
                or entry.get("execution_role") != "FORCING_INPUT" or "fuel-tank" in text or "reporting" in text
                or "CAUSAL_INPUT" in text or "INTERVENTION" in text or "REPORTED_OBSERVATION" in text):
            bad.append(entry.get("event_id"))
    if document.get("observation_sources"):
        bad.append("observation_sources")
    return bad


TIMINGS: list[float] = []


def execute_day(reg: "Registered", k: int, soc, fuel, actions: list[dict[str, Any]] | None, model: str = "v7"):
    """One day-run on the registered path: the unchanged weather-and-loads scenario, then (optionally) the actions
    on the frozen run, executed on the probe-local v7 (or v6 for F3's physics comparison)."""
    from execution_adapter import run_to_end

    start = _run_start(k)
    document = day_document(soc, fuel)
    run = reg.draft(document, _iso(start), _iso(start + timedelta(days=1)), model)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]  # F1
    assert run.registered_basis is not None, "F1: the run did not freeze a registered basis"
    history: tuple = ()
    if actions is not None:
        run, history = apply_actions(run, actions, start)
    began = time.perf_counter()
    execution = run_to_end(run, reg.sim(model))
    TIMINGS.append(time.perf_counter() - began)
    trajectory = execution.trajectory
    assert len(trajectory.boundaries) == STEPS_PER_RUN + 1, (k, len(trajectory.boundaries),
                                                              getattr(trajectory, "failure", None))
    return document, run, execution, history


def _state(boundary) -> dict:
    stocks = dict(boundary.stocks)
    return {"soc": stocks[SOC], "fuel": stocks[FUEL], "generator": dict(boundary.discrete).get(GEN)}


def _energy(boundary) -> Fraction:
    return next(f.energy for f in boundary.control_step.accepted.flows if f.flow_id == GENERATOR_FLOW)


def tank_account(trajectory) -> list[tuple[int, Fraction, Fraction, Fraction, Fraction]]:
    """Per step: (index, tank_i, generator litres E_i x SFC, the residual moved by anything else, tank_{i+1})."""
    b, rows = trajectory.boundaries, []
    for i in range(len(b) - 1):
        before, after = dict(b[i].stocks)[FUEL], dict(b[i + 1].stocks)[FUEL]
        gen = _energy(b[i]) * SFC
        rows.append((i, before, gen, before - gen - after, after))
    return rows


def fuel_limited_steps(trajectory) -> int:
    count = 0
    for boundary in trajectory.boundaries[:-1]:
        accepted = boundary.control_step.accepted
        texts = list(accepted.notes) + [why for c in accepted.controls for why in c.limited_by]
        count += any(FUEL_LIMIT_NOTE in text for text in texts)
    return count


# --- readings and publication -------------------------------------------------------------------------------------


def readings(reg: "Registered", run, trajectory):
    from execution_adapter import reporting_inputs
    from assetops_simulator.observation.transform import generate_observations

    reporting = reporting_inputs(run, _profile(), reg.sim("v7"))
    observations = generate_observations(trajectory.boundaries, reporting)
    return reporting, observations


def fuel_level_binding(snapshot_canonical: str) -> dict[str, Any] | None:
    """The activated binding snapshot's `fuel_level` binding for fuel-level-sensor/fuel-level, or None."""
    pending = [json.loads(snapshot_canonical)]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if (value.get("device_id"), value.get("signal_id")) == TANK_SIGNAL and value.get("role") == "fuel_level":
                return value
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return None


def _tank_obs(observations):
    return [o for o in observations if (o.device_id, o.signal_id) == TANK_SIGNAL]


# --- build --------------------------------------------------------------------------------------------------------


def _litres(value: Fraction | None) -> dict[str, str] | None:
    return None if value is None else {"exact": str(value), "dec3": dec(value)}


def _band_json(result: dict[str, Any]) -> dict[str, Any]:
    out = {"state": result["state"], "limitation": result["limitation"], "gap_minutes": result["gap_minutes"]}
    for key in ("residual_low", "residual_high", "opening_minus_closing", "deliveries", "delivery_tolerance",
                "use_low", "use_high"):
        if key in result:
            out[key] = _litres(result[key])
    return out


def build() -> dict[str, Any]:
    from gateway_publication import keyed_reports

    TIMINGS.clear()
    reg = Registered()  # §9.1 (c); a refusal here is S1/S6 and stops the probe
    actions = load_actions()

    with_actions: dict[int, Any] = {}
    soc, fuel = START_SOC, START_FUEL
    ref_soc, ref_fuel = START_SOC, START_FUEL
    v6_soc, v6_fuel = START_SOC, START_FUEL
    runs, f0a_scenario_bad, nodes, added_causes, f3_diffs, f3_v6_diffs = [], [], {}, [], [], []
    f2_rows, f4_steps, residual_steps = [], 0, []
    reference_litres, f6 = {}, {"fuel_level_reported": 0, "fuel_level_report_texts": 0,
                                "texts_one_per_reported_observation": True}
    night_rows, f5, f11 = [], {}, []
    tank_obs_by_run: dict[int, list] = {}
    basis_record = None
    for k in range(1, RUNS + 1):
        initial_fuel = Fraction(fuel)
        document, run, execution, history = execute_day(reg, k, soc, fuel, actions)
        if basis_record is None:
            basis_record = run.registered_basis
        trajectory = execution.trajectory
        with_actions[k] = trajectory
        f0a_scenario_bad += [f"run {k}: {e}" for e in scenario_is_weather_and_loads_only(document)]
        nodes[k] = node_count(document)
        inputs = execution.inputs
        added = [c for c in inputs.causes if c.event_id.startswith(OPENING_ORIGIN + "/")]
        added_causes += [{"run": k, "event_id": c.event_id, "direction": c.direction, "quantity_l": str(c.quantity),
                          "shape": c.shape, "offset_minutes": c.offset_minutes,
                          "duration_minutes": c.duration_minutes} for c in added]
        assert len(added) == len([h for h in history]), (k, added, history)
        for cause in added:
            action_id, sha = cause.event_id.split("/")[1], cause.event_id.split("/")[3]
            assert any(h.startswith(f"{OPENING_ORIGIN}:{action_id}:{sha}") for h in inputs.intervention_history)

        # F2: the tank law per step.
        for i, before, gen, other, after in tank_account(trajectory):
            if other != 0:
                residual_steps.append({"run": k, "step": i, "offset_minutes": i * STEP, "litres": other})
        f4_steps += fuel_limited_steps(trajectory)

        # The reference step, the same run without the actions (F3).
        _, _, ref_exec, _ = execute_day(reg, k, ref_soc, ref_fuel, None)
        TIMINGS.pop()
        ref = ref_exec.trajectory
        for j, (a, r) in enumerate(zip(trajectory.boundaries, ref.boundaries)):
            sa, sr = _state(a), _state(r)
            if sa["soc"] != sr["soc"] or sa["generator"] != sr["generator"] or (
                    j < STEPS_PER_RUN and _energy(a) != _energy(r)):
                f3_diffs.append(f"run {k} boundary {j}")
        # F3 (R3): v6 without actions equals probe v7 without actions in physics at every boundary.
        _, _, v6_exec, _ = execute_day(reg, k, v6_soc, v6_fuel, None, model="v6")
        TIMINGS.pop()
        v6 = v6_exec.trajectory
        for j, (a, r) in enumerate(zip(ref.boundaries, v6.boundaries)):
            if _state(a) != _state(r) or (j < STEPS_PER_RUN and _energy(a) != _energy(r)):
                f3_v6_diffs.append(f"run {k} boundary {j}")
        v6_end = _state(v6.boundaries[-1])
        v6_soc, v6_fuel = float(v6_end["soc"]), float(v6_end["fuel"])
        reference_litres[k] = measure_night(ref)["night_litres"]
        ref_end = _state(ref.boundaries[-1])
        ref_soc, ref_fuel = float(ref_end["soc"]), float(ref_end["fuel"])
        del ref, ref_exec, v6, v6_exec

        # F11: K0's setup bounds for this run's actions (§9.3 item 2).
        run_deliveries = [a for a in actions if a["kind"] == "FUEL_DELIVERY" and _in_run(_run_start(k), a["at"])]
        run_removals = [a for a in actions if a["kind"] == "FUEL_REMOVAL_UNRECORDED"
                        and _in_run(_run_start(k), a["at"])]
        if run_deliveries or run_removals:
            delivered = sum((Fraction(a["volume_l"]) for a in run_deliveries), Fraction(0))
            earlier = sum((Fraction(a["volume_l"]) for a in run_deliveries
                           if run_removals and _parse(a["at"]) < _parse(run_removals[0]["at"])), Fraction(0))
            removed = sum((Fraction(a["volume_l"]) for a in run_removals), Fraction(0))
            f11.append({"run": k, "initial_stock_l": dec(initial_fuel), "deliveries_l": str(delivered),
                        "capacity_l": str(TANK_CAPACITY_L),
                        "initial_plus_deliveries_l": dec(initial_fuel + delivered),
                        "capacity_ok": initial_fuel + delivered <= TANK_CAPACITY_L,
                        "removal_l": str(removed), "stock_available_for_removal_l": dec(initial_fuel + earlier),
                        "removal_ok": removed <= initial_fuel + earlier})

        # Readings (F5) and the registered report path (F6).
        reporting, observations = readings(reg, run, trajectory)
        tank = _tank_obs(observations)
        tank_obs_by_run[k] = tank
        reported_tank = [o for o in tank if o.outcome == "REPORTED"]
        reports = keyed_reports(run.run_id, run.registered_basis.snapshot_sha256, observations,
                                PROFILE["timestep_minutes"])
        tank_texts = [(o, key, text) for o, key, text in reports if (o.device_id, o.signal_id) == TANK_SIGNAL]
        f6["fuel_level_reported"] += len(reported_tank)
        f6["fuel_level_report_texts"] += len(tank_texts)
        f6["texts_one_per_reported_observation"] = f6["texts_one_per_reported_observation"] and (
            [o for o, _, _ in tank_texts] == reported_tank)
        if k == 1:
            f6["example_fuel_level_report_text"] = tank_texts[0][2] if tank_texts else None
            f5["cadence_offsets_ok"] = sorted({o.at_offset_minutes for o in tank}) == list(range(0, 1441, 15))
            f5["outcomes_run1"] = {name: sum(o.outcome == name for o in tank) for name in sorted({o.outcome
                                                                                                 for o in tank})}
            f5["reporting_signals"] = [f"{s.device_id}/{s.signal_id} every {s.cadence_minutes} min bias {s.bias} "
                                       f"dropout {s.dropout_per_thousand}/1000" for s in reporting.signals
                                       if (s.device_id, s.signal_id) == TANK_SIGNAL]
        bias_ok = all(abs(o.reported_value - (dict(trajectory.boundaries[o.at_offset_minutes // STEP].stocks)[FUEL]
                                              - Fraction(1, 2))) <= Fraction(1, 2_000_000)
                      for o in tank if o.outcome == "REPORTED")
        f5.setdefault("bias_ok", True)
        f5["bias_ok"] = f5["bias_ok"] and bias_ok
        if k == INCIDENT_NIGHT:
            reported = [o.at_offset_minutes for o in tank if o.outcome == "REPORTED"]
            f5["night4_in_gap"] = [o for o in reported if 590 <= o < 680]
            f5["night4_before"] = [o for o in reported if 560 <= o < 590]
            f5["night4_after"] = [o for o in reported if 680 <= o <= 710]
            f5["night4_suppressed_offsets"] = [o.at_offset_minutes for o in tank if o.outcome == "SUPPRESSED_BY_GAP"]
            f2_rows = [(i, before, gen, other, after) for i, before, gen, other, after in tank_account(trajectory)
                       if NIGHT[0] <= i < NIGHT[1]]

        begin, end = _state(trajectory.boundaries[0]), _state(trajectory.boundaries[-1])
        runs.append({"run": k, "interval": [_iso(_run_start(k)), _iso(_run_start(k) + timedelta(days=1))],
                     "stop_soc_pct": STOP_BEFORE, "phase": "before" if k < CHANGE_RUN else "after",
                     "scenario_sha256": run.deterministic_identity.scenario.scenario_sha256,
                     "scenario_nodes": nodes[k], "intervention_history": list(history),
                     "start": {"soc": str(begin["soc"]), "fuel": str(begin["fuel"]), "generator": begin["generator"]},
                     "end": {"soc": str(end["soc"]), "fuel": str(end["fuel"]), "generator": end["generator"]}})
        soc, fuel = float(end["soc"]), float(end["fuel"])

    # Per-night band, both sources.
    deliveries = [a for a in actions if a["kind"] == "FUEL_DELIVERY"]
    nights = []
    for k in range(1, RUNS + 1):
        t = with_actions[k]
        m = measure_night(t)
        lo, hi = NIGHT[0] * STEP, NIGHT[1] * STEP
        start, end = _run_start(k) + timedelta(minutes=lo), _run_start(k) + timedelta(minutes=hi)
        d = [a["ticket"]["volume_l"] for a in deliveries if start <= _parse(a["at"]) < end]
        accepted = [(o.at_offset_minutes, o.reported_value) for o in tank_obs_by_run[k] if o.outcome == "REPORTED"]
        gap = reporting_gap_minutes([o for o, _ in accepted], lo, hi)
        opening = [v for o, v in accepted if lo - EDGE_SEARCH_MIN <= o <= lo]
        closing = [v for o, v in accepted if hi <= o <= hi + EDGE_SEARCH_MIN]
        common = {"deliveries": d, "loaded_litres": m["loaded_litres"],
                  "idle_hours": Fraction(m["idle_minutes"], 60), "gap_minutes": gap}
        true_band = balance({**common, "opening": dict(t.boundaries[NIGHT[0]].stocks)[FUEL],
                             "closing": dict(t.boundaries[NIGHT[1]].stocks)[FUEL]})
        read_band = balance({**common, "opening": opening[-1] if opening else None,
                             "closing": closing[0] if closing else None})
        local = _run_start(k) + timedelta(hours=3)
        nights.append({
            "night": k, "phase": "before" if k < CHANGE_RUN else "after",
            "window_local": f"{local.date()} 18:00 to {(local + timedelta(days=1)).date()} 12:00",
            "night_litres": _litres(m["night_litres"]), "loaded_litres": _litres(m["loaded_litres"]),
            "idle_minutes": m["idle_minutes"], "reference_night_litres": _litres(reference_litres[k]),
            "deliveries_l": d, "opening_reading_l": _litres(opening[-1]) if opening else None,
            "closing_reading_l": _litres(closing[0]) if closing else None,
            "true_tank": _band_json(true_band), "readings": _band_json(read_band)})
        night_rows.append((k, true_band, read_band))

    removal = [r for r in residual_steps if r["litres"] > 0]
    delivery = [r for r in residual_steps if r["litres"] < 0]
    removal_action = next(a for a in actions if a["kind"] == "FUEL_REMOVAL_UNRECORDED")
    delivery_action = deliveries[0]
    removal_steps_expected = [(INCIDENT_NIGHT, s) for s in range(_offset(_run_start(INCIDENT_NIGHT),
                                                                         removal_action["at"]) // STEP,
                                                                 (_offset(_run_start(INCIDENT_NIGHT),
                                                                          removal_action["at"])
                                                                  + removal_action["duration_minutes"]) // STEP)]
    f2_pass = (sum((r["litres"] for r in removal), Fraction(0)) == removal_action["volume_l"]
               and -sum((r["litres"] for r in delivery), Fraction(0)) == delivery_action["volume_l"]
               and [(r["run"], r["step"]) for r in removal] == removal_steps_expected
               and len(delivery) == 1 and delivery[0]["run"] == 2)
    f3_litres = {k: str(v) for k, v in reference_litres.items()}
    measured = {k: measure_night(with_actions[k])["night_litres"] for k in with_actions}
    f3_pass = not f3_diffs and not f3_v6_diffs and all(v == D0_NIGHT_LITRES for v in reference_litres.values()) and all(
        v == D0_NIGHT_LITRES for v in measured.values())
    f5_pass = (f5.get("cadence_offsets_ok") and not f5.get("night4_in_gap") and bool(f5.get("night4_before"))
               and bool(f5.get("night4_after")) and f5.get("bias_ok") and bool(f5.get("reporting_signals")))

    def expect(k, band):
        if band["state"] == "NOT_ASSESSED":
            return False
        if k == INCIDENT_NIGHT:
            return band["state"] == "UNEXPLAINED" and band["gap_minutes"] > 0
        return band["state"] == "WITHIN_MARGIN" and band["gap_minutes"] == 0
    f9 = {"true_tank": [k for k, tb, _ in night_rows if not expect(k, tb)],
          "readings": [k for k, _, rb in night_rows if not expect(k, rb)]}
    dips = dip_values(with_actions, actions)
    snapshot_binding = fuel_level_binding(basis_record.snapshot_canonical)
    f6_pass = (snapshot_binding is not None and f6["fuel_level_report_texts"] > 0
               and f6["fuel_level_report_texts"] == f6["fuel_level_reported"]
               and f6["texts_one_per_reported_observation"])
    gates = {
        "F0a": {"pass": not f0a_scenario_bad and len(added_causes) == 2,
                "scenario_entries_not_weather_or_load": f0a_scenario_bad,
                "causes_added_through_frozen_input_hook": added_causes,
                "detail": "scenario = D0 day_document unchanged; effects added to the frozen run with "
                          "dataclasses.replace (origin and content hash in event id and intervention_history); "
                          "the kernel applied them (see F2)"},
        "F1": {"pass": True, "detail": "every run READY at setup; run_to_end completed with the actions applied "
                                       "(asserted)"},
        "F2": {"pass": f2_pass, "detail": "tank[i+1] = tank[i] - E_i x 0.355 - removal_i + delivery_i at every step",
               "non_generator_steps": [{**r, "litres": str(r["litres"])} for r in residual_steps]},
        "F3": {"pass": f3_pass, "boundaries_differing_with_vs_without_actions": f3_diffs[:20],
               "boundaries_differing_v7_vs_v6_without_actions": f3_v6_diffs[:20],
               "reference_night_litres": f3_litres, "d0_night_litres": str(D0_NIGHT_LITRES)},
        "F4": {"pass": f4_steps == 0, "fuel_limited_steps": f4_steps},
        "F5": {"pass": bool(f5_pass), **f5},
        "F6": {"pass": bool(f6_pass), "snapshot_fuel_level_binding": snapshot_binding, **f6},
        "F7": {"pass": max(nodes.values()) < 4000, "largest_nodes": max(nodes.values())},
        "F8": {"pass": None, "detail": "checked by --check: a fresh run is byte-equal to the committed file"},
        "F9": {"pass": not f9["true_tank"] and not f9["readings"], "nights_differing": f9},
        "F10": {"pass": None, "detail": "checked by running tools/probe_kisiwa_nights.py --check (evidence file)"},
        "F11": {"pass": bool(f11) and all(r["capacity_ok"] and r["removal_ok"] for r in f11), "runs": f11},
    }
    return {
        "id": "assetops.kisiwa-fuel-probe", "version": 1,
        "assumptions": {
            "source": "DIESEL-1-R2 §8.3 (.agent/build-sheet-DIESEL-1.md, dc72cb72a); fixed before any run",
            "physics": "D0 §2.2 unchanged (tools/probe_kisiwa_nights.py imported), stop 90 % throughout",
            "d0_template_sha256": hashlib.sha256(D0_TEMPLATE.read_bytes()).hexdigest(),
            "actions_sha256": hashlib.sha256(ACTIONS.read_bytes()).hexdigest(),
            "start": {"soc_pct": START_SOC, "fuel_l": START_FUEL, "generator": "STOPPED"},
            "runs": RUNS, "run1_start": _iso(RUN1_START), "change_instant": _iso(_run_start(CHANGE_RUN)),
            "publication_profile": f"{REGISTERED_PROFILE[0]} v{REGISTERED_PROFILE[1]}",
            "model": f"probe-local mini-grid v7 (K1a content), {PROFILE['timestep_minutes']} min",
            "probe_local_v7": PROBE_V7_LINE,
            "registered_path": {
                "setup": "(c) DIESEL-1-R3 §9.1: import_site + convert into InMemoryFoundationStore, real "
                         "RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, 'demo', clock)))",
                "bindings_sha256": hashlib.sha256(BINDINGS.read_bytes()).hexdigest(),
                "import_at": _iso(IMPORT_AT), "convert_at": _iso(CONVERT_AT), "setup_at": SETUP_AT,
                "knowledge_at": None, "foundation_version": reg.foundation_version,
                "binding_set_version": basis_record.binding_set_version,
                "snapshot_sha256": basis_record.snapshot_sha256, "basis_selection": basis_record.selection},
            "foundation_valid_from": FOUNDATION_VALID_FROM, "fuel_balance_1": PARAMETERS},
        "runs": runs,
        "night4_tank_account": [[i, dec(before), dec(gen), dec(other), dec(after)] for i, before, gen, other, after
                                in f2_rows],
        "night4_tank_account_columns": ["step", "tank_i", "generator_litres", "other_litres", "tank_i+1"],
        "nights": nights,
        "dips": dips,
        "gates": gates,
    }


def _summary(result: dict[str, Any]) -> str:
    lines = []
    for n in result["nights"]:
        t, r = n["true_tank"], n["readings"]
        def band(b):
            if b["residual_low"] is None:
                return f"{b['state']} ({b['limitation']})"
            return f"[{b['residual_low']['dec3']}, {b['residual_high']['dec3']}] {b['state']} gap {b['gap_minutes']}"
        lines.append(f"night {n['night']:2d}: true {band(t)} | readings {band(r)}")
    lines.append("gates: " + ", ".join(f"{g}={v['pass']}" for g, v in result["gates"].items()))
    return "\n".join(lines)


SEED = 20260929


@contextlib.contextmanager
def seeded_uuid4():
    """DIESEL-1-R3b §9b F8: replace uuid4 with a seeded generator for the in-memory import and conversion, at
    `uuid.uuid4` and at every module-level `uuid4` binding (modules the run imports lazily are swept on exit too).
    Yields the list of patched names; restores everything on exit."""
    import random
    import uuid

    original = uuid.uuid4
    rng = random.Random(SEED)

    def fake_uuid4():
        return uuid.UUID(int=rng.getrandbits(128), version=4)

    patched: list[str] = []
    uuid.uuid4 = fake_uuid4
    patched.append("uuid.uuid4")
    for name, module in list(sys.modules.items()):
        if module is not uuid and getattr(module, "uuid4", None) is original:
            module.uuid4 = fake_uuid4
            patched.append(f"{name}.uuid4")
    try:
        yield patched
    finally:
        for name, module in list(sys.modules.items()):
            if module is not uuid and getattr(module, "uuid4", None) is fake_uuid4:
                module.uuid4 = original
                if f"{name}.uuid4" not in patched:
                    patched.append(f"{name}.uuid4")
        uuid.uuid4 = original


def main(argv: list[str]) -> int:
    if "--handover" in argv:
        print("--handover is K7's and is not built in F0.")
        return 2
    with seeded_uuid4() as patched:
        result = build()
    if "--patched" in argv:
        print("\n".join(patched))
        return 0
    text = json.dumps(result, indent=1, sort_keys=False, ensure_ascii=False) + "\n"
    if "--check" in argv:
        current = RESULT.read_text(encoding="utf-8") if RESULT.exists() else ""
        if current != text:
            print("probe result differs from the committed file")
            return 1
        print("probe result current")
        return 0
    if "--write" in argv:
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(text, encoding="utf-8", newline="\n")
        print(_summary(result))
        print("seconds per 24-hour run_to_end: " + ", ".join(f"{t:.2f}" for t in TIMINGS))
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
