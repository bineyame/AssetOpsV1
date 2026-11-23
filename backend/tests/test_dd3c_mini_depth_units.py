"""DD3c fix round (review H1; D-DD.41, D-DD.110 Q3, D-DD.111-113, spec section 7 DD3.4): mini-depth takes a Site's
units through `sites/unit_roles`.

Under `minigrid-roles-5` a unit role bound to several assets (Kisiwa's two generators, Mto's two inverters) is the
Site figure: power summed per step (a unit with no value makes the Site value absent there), and fuel burnt per unit
on its own SFC, then summed. Under `minigrid-roles-4` two assets on one role keep today's refusal. One unit: every
hour's revision is byte-identical to main (`fixtures/dd3c/kobo-mini-depth-golden.json`, captured by `write()` below
running on main's code in a detached worktree BEFORE the fix).

Capture: `PYTHONPATH=<main>/backend:<main>/backend/tests python -c "import runpy;
runpy.run_path('<this file>')['write']('<golden path>', '<main sha>')"`.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from assetops_backend.mini_depth import inputs as mini_inputs
from assetops_backend.mini_depth.projection import assess, project
from assetops_backend.mini_depth.store import DOMAINS, HourRows

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "dd3c" / "kobo-mini-depth-golden.json"
ROLES_4, ROLES_5 = "minigrid-roles-4", "minigrid-roles-5"
TZ = "Africa/Nairobi"
WINDOW = mini_inputs.local_noon(date(2026, 10, 16), TZ)
EARLY = WINDOW.start - timedelta(days=30)
CUTOFF = WINDOW.end + timedelta(hours=4)
SLOT = timedelta(minutes=5)
FOUNDATION, SET = UUID(int=1), UUID(int=2)
TENANT, SITE = UUID(int=3), UUID(int=4)
KOBO_GEN = (("gen-01", "20", "0.3"),)
KOBO_PV = (("pv-01", "40", "30"),)


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (Decimal, datetime, date, UUID)):
        return f"{type(value).__name__}:{value}"
    return value


class _World:
    """One noon hour of a Kobo-shape mini-grid: every mini-depth domain has inputs, and one outage chain runs."""

    def __init__(self, role_set: str, gens, pvs, *, silent: dict[str, range] | None = None) -> None:
        self.n = 100
        self.silent = silent or {}
        self.asset: dict[str, UUID] = {}
        self.binding: dict[tuple[str, str], UUID] = {}
        self.rows: list[tuple] = []
        self.prior: list[tuple] = []
        self.role_set = role_set
        gen_codes = [g[0] for g in gens]
        pv_codes = [p[0] for p in pvs]
        bound = {
            "generator_power": gen_codes, "generator_state": gen_codes, "mini_backup_start_event": gen_codes[:1],
            "pv_power": pv_codes, "pv_available_power": pv_codes, "fuel_level": ["tank-01"],
            "feeder_demand": ["load-a", "load-b"], "feeder_requested_power": ["load-b"],
            "critical_load_requested_power": ["load-a"], "critical_load_delivered_power": ["load-a"],
            "storage_charge_requested_power": ["bat-01"], "site_supply_state": ["bus-01"],
            "mini_backup_bus_state": ["bus-01"],
        }
        for code in [*gen_codes, *pv_codes, "tank-01", "load-a", "load-b", "bat-01", "bus-01"]:
            self.asset[code] = self._id()
        for role, codes in bound.items():
            for code in codes:
                self.binding[(role, code)] = self._id()
        self.content = {
            "components": [
                *({"component_id": code, "component_type": "GENERATOR", "properties": [
                    {"property_key": "specific-fuel-consumption", "value": sfc, "unit": "L/kWh"}]}
                  for code, _kw, sfc in gens),
                *({"component_id": code, "component_type": "INVERTER", "properties": (
                    [{"property_key": "pv-available-uncertainty", "value": "1", "unit": "kW"}] if i == 0 else [])}
                  for i, code in enumerate(pv_codes)),
                {"component_id": "tank-01", "component_type": "FUEL_TANK", "properties": []},
                {"component_id": "load-a", "component_type": "LOAD", "display_name": "Clinic", "properties": []},
                {"component_id": "load-b", "component_type": "LOAD", "display_name": "Village", "properties": []},
                {"component_id": "bat-01", "component_type": "BATTERY", "properties": [
                    {"property_key": "renewable-retained-margin", "value": "3", "unit": "kW"},
                    {"property_key": "backup-recovery-target", "value": "15", "unit": "min"}]},
                {"component_id": "bus-01", "component_type": "BUS", "properties": []},
            ],
            "site_controls": [{"control_key": "critical-load-priority", "members": ["load-a"]}],
        }
        for i in range(12):
            t = WINDOW.start + SLOT * i
            for code, kw, _sfc in gens:
                self._power("generator_power", code, t, kw)
                self._row("generator_state", code, t, None, "RUNNING", "state", "STATE")
            for code, available, used in pvs:
                self._power("pv_available_power", code, t, available)
                self._power("pv_power", code, t, used)
            self._power("feeder_demand", "load-a", t, "8")
            self._power("feeder_demand", "load-b", t, "6")
            self._power("feeder_requested_power", "load-b", t, "6")
            self._power("critical_load_requested_power", "load-a", t, "8")
            self._power("critical_load_delivered_power", "load-a", t, "0" if i == 2 else "8")
            self._power("storage_charge_requested_power", "bat-01", t, "0")
        self._row("fuel_level", "tank-01", WINDOW.start, None, "500", "L", "MEASUREMENT")
        self._row("fuel_level", "tank-01", WINDOW.end - timedelta(minutes=1), None, "490", "L", "MEASUREMENT")
        minute = lambda m: WINDOW.start + timedelta(minutes=m)  # noqa: E731
        self._row("site_supply_state", "bus-01", WINDOW.start - SLOT, None, "ENERGIZED", "state", "STATE",
                  into=self.prior)
        self._row("site_supply_state", "bus-01", minute(10), None, "LOST", "state", "STATE")
        self._row("mini_backup_start_event", gen_codes[0], minute(10.5), None, None, "event", "START_REQUEST",
                  outcome="REQUESTED", correlation="c1")
        self._row("mini_backup_start_event", gen_codes[0], minute(11), None, None, "event", "START_RESULT",
                  outcome="SUCCEEDED", correlation="c1")
        self._row("mini_backup_bus_state", "bus-01", minute(12), None, "ENERGIZED", "state", "STATE")
        self._row("site_supply_state", "bus-01", minute(20), None, "ENERGIZED", "state", "STATE")

    def _id(self) -> UUID:
        self.n += 1
        return UUID(int=self.n)

    def _power(self, role: str, code: str, t: datetime, kw: str) -> None:
        slot = int((t - WINDOW.start) / SLOT)
        if slot in self.silent.get(code, ()):
            return
        self._row(role, code, t, t + SLOT, kw, "kW", "MEASUREMENT")

    def _row(self, role, code, start, end, value, unit, kind, *, outcome=None, correlation=None, into=None) -> None:
        # (id, role, asset_id, source_time, interval_start, interval_end, quality, value_text, unit, record_kind,
        #  outcome, correlation_id, source_id, binding_revision_id, foundation_revision_id, decided_at)
        source_time = end if end is not None else start
        (self.rows if into is None else into).append((
            self._id(), role, self.asset[code], source_time, start if end is not None else None, end, "GOOD", value,
            unit, kind, outcome, correlation, UUID(int=50 + sorted(self.asset).index(code)),
            self.binding[(role, code)], FOUNDATION, source_time + timedelta(minutes=2)))

    def raw(self) -> HourRows:
        bindings = [(b, role, self.asset[code], EARLY, None) for (role, code), b in self.binding.items()]
        foundation = (FOUNDATION, EARLY, None, self.content)
        return HourRows(
            timezone=TZ, foundations=[foundation], binding_sets=[(SET, EARLY, None, self.role_set)],
            bindings=sorted(bindings, key=lambda b: str(b[0])), assets=[(c, a) for c, a in self.asset.items()],
            accepted=sorted(self.rows, key=lambda r: (r[3], str(r[0]))), prior_supply=self.prior,
            row_foundations={FOUNDATION: foundation}, row_bindings={})


def hour(world: _World):
    raw = world.raw()
    saved = mini_inputs.read_hour_rows
    mini_inputs.read_hour_rows = lambda *a, **k: raw
    try:
        return mini_inputs.load_hour_inputs(object(), TENANT, SITE, WINDOW, CUTOFF)
    finally:
        mini_inputs.read_hour_rows = saved


def capture() -> dict:
    out = {}
    for name, world in (("kobo", _World(ROLES_5, KOBO_GEN, KOBO_PV)),
                        ("kobo_roles4", _World(ROLES_4, KOBO_GEN, KOBO_PV)),
                        ("kobo_gen_gap", _World(ROLES_5, KOBO_GEN, KOBO_PV, silent={"gen-01": range(6, 8)}))):
        hi = hour(world)
        out[name] = {"input_sha256": hi.input_sha256,
                     **{domain: _plain(project(domain, hi)) for domain in DOMAINS}}
    return out


def write(path: str, captured_on: str) -> None:
    Path(path).write_text(json.dumps({"captured_on": captured_on, "cases": capture()}, indent=1, sort_keys=True)
                          + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------------------- one unit: main's bytes


def test_one_unit_kobo_mini_depth_is_byte_identical_to_main() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    now = capture()
    assert set(now) == set(golden["cases"])
    for name in now:
        assert json.dumps(now[name], sort_keys=True) == json.dumps(golden["cases"][name], sort_keys=True), name


# ------------------------------------------------------------------------------------- two units: the Site figure

KISIWA_GENS = (("gen-ks-01", "10", "0.3"), ("gen-ks-02", "12", "0.35"))
MTO_PVS = (("inv-mt-01", "20", "15"), ("inv-mt-02", "20", "15"))


def test_mto_renewable_hour_sums_the_inverters() -> None:
    hi = hour(_World(ROLES_5, KOBO_GEN, MTO_PVS))
    h = assess("renewable", hi)
    assert "CONFLICT" not in h.constraints and "CAPABILITY_MISSING" not in h.constraints
    assert (h.capability_kw.low, h.capability_kw.high) == (Decimal("39"), Decimal("41"))  # 20 + 20 kW, +-1 kW
    assert h.coverage.observed_seconds == 3600
    rc = project("renewable", hi).result["basis"]["role_coverage"]
    assert rc["pv_available_power"]["observed_seconds"] == 3600 and rc["pv_power"]["observed_seconds"] == 3600


def test_kisiwa_fuel_hour_burns_each_unit_on_its_own_sfc() -> None:
    hi = hour(_World(ROLES_5, KISIWA_GENS, KOBO_PV))
    f = assess("fuel", hi)
    assert f.nominal_l == Decimal("7.2")  # 10 kWh x 0.3 + 12 kWh x 0.35
    assert f.expected_use_l.high == Decimal("7.92")
    assert len(f.sfc_property_revision_ids) == 1 and len(hi.fuel.sfc) == 1  # one Foundation revision, two units
    assert len(f.generator_power_evidence_ids) == 24  # both units' 12 intervals cited
    assert "CONFLICT" not in {l.code for l in f.limitations}
    rc = project("fuel", hi).result["basis"]["role_coverage"]
    assert rc["generator_power"]["observed_seconds"] == 3600


def test_kisiwa_unit_gap_makes_the_site_value_absent_there() -> None:
    f = assess("fuel", hour(_World(ROLES_5, KISIWA_GENS, KOBO_PV, silent={"gen-ks-02": range(6, 8)})))
    assert f.nominal_l is None and f.status == "LIMITED"
    assert [l.code for l in f.limitations if l.code in ("COVERAGE_GAP", "CONFLICT")] == ["COVERAGE_GAP"]
    assert f.coverage.observed_seconds == 3000  # 10 of 60 minutes have no Site value


def test_kisiwa_backup_chain_reads_the_units_generator_power() -> None:
    b = assess("backup", hour(_World(ROLES_5, KISIWA_GENS, KOBO_PV)))
    [chain] = b.chains
    assert [s.state for s in chain.steps] == ["OBSERVED"] * 6
    assert chain.result == "PASS" and b.status == "SUPPORTED"


def test_roles_4_with_two_generators_keeps_todays_refusal() -> None:
    hi = hour(_World(ROLES_4, KISIWA_GENS, KOBO_PV))
    assert hi.generator_asset_id is None
    f = assess("fuel", hi)
    assert f.nominal_l is None and f.generator_power_evidence_ids == ()
