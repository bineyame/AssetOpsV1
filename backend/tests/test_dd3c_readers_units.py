"""DD3c part 3 (D-DD.118, D-DD.110 Q3/Q10, D-DD.41, D-DD.111): the Site-figure readers `dispatch_v3`, verification
and `replay_series` build a multi-unit Site's figures through `sites/unit_roles`; minimum-runtime is the lead unit's
policy; the fuel night text and the fuel-balance run's Foundation ids read the per-unit terms (D-DD.117 risks).

Pure. One-unit and roles-4 behaviour is pinned beside each multi-unit case (a one-unit Site reads as today).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from types import SimpleNamespace
from uuid import UUID

import pytest
import test_k5_fuel_night_text as k5
from test_0k3_replay_series import (ASSETS, CODES, WINDOW, binding, mean, placed, r0, r0_bindings, reading,
                                     refused)
from test_s6_verification_rules import RESERVE, T0, full_window, point, power

from assetops_backend.actions import verification_rules as vr
from assetops_backend.analytics import dispatch_v3 as d3
from assetops_backend.analytics.adapters import postgres_assessment_store as pas
from assetops_backend.analytics.assessment_inputs import AcceptedReading, RoleBinding
from assetops_backend.fuel_balance import night_text as nt
from assetops_backend.runs.replay_series import bound_assets
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4, ROLE_SET_MINIGRID_5
from assetops_backend.sites.unit_roles import UnitRolesRefused

UTC = timezone.utc
PV = "pv_available_power"

# --------------------------------------------------------------------------- dispatch_v3


AT = datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
PV1, PV2, FEEDER = UUID(int=501), UUID(int=502), UUID(int=503)


def _reading(n: int, role: str, asset: UUID, end: datetime, value: str) -> AcceptedReading:
    return AcceptedReading(
        evidence_id=UUID(int=9000 + n), envelope_sha256="0" * 64, batch_id=UUID(int=7), gateway_id=UUID(int=8),
        source_id=UUID(int=9), sequence_epoch="e", sequence=n, role=role, asset_id=asset, source_time=end,
        interval_start=end - timedelta(minutes=5), interval_end=end, published_at=end, received_at=end,
        accepted_at=end, quality="GOOD", value=value, unit="kW", foundation_revision_id=UUID(int=10),
        binding_set_revision_id=UUID(int=11), binding_revision_id=UUID(int=12), source_mode="SIMULATED")


def _index(role_set: str, readings: list[AcceptedReading], pv_units=(PV1, PV2)) -> d3._Index:
    start = datetime(2026, 10, 1, tzinfo=UTC)
    bindings = [RoleBinding(PV, u, start, None, UUID(int=20), UUID(int=21 + i), role_set)
                for i, u in enumerate(pv_units)]
    bindings.append(RoleBinding("feeder_demand", FEEDER, start, None, UUID(int=20), UUID(int=30), role_set))
    inputs = SimpleNamespace(readings=readings, cohort=SimpleNamespace(limits=()), bindings=bindings, controls=())
    return d3._Index(inputs)


def _pv_night() -> list[AcceptedReading]:
    return [_reading(1, PV, PV1, AT, "3.5"), _reading(2, PV, PV2, AT, "4.25"),
            _reading(3, "feeder_demand", FEEDER, AT, "6")]


def test_dispatch_pv_sums_the_units_of_a_roles5_site() -> None:
    found, problems = _index(ROLE_SET_MINIGRID_5, _pv_night()).site_lookup(PV, AT)
    assert (found.value, found.problem, problems) == (Fraction(31, 4), None, [])
    assert found.ids == (str(UUID(int=9001)), str(UUID(int=9002)))


def test_dispatch_pv_unit_without_a_reading_makes_the_site_value_absent_named_by_unit() -> None:
    found, problems = _index(ROLE_SET_MINIGRID_5, _pv_night()[1:]).site_lookup(PV, AT)
    assert found.value is None and problems == [(str(PV1), "MISSING")]
    point_ = d3._evaluate(_index(ROLE_SET_MINIGRID_5, _pv_night()[1:]), AT, AT, AT, AT)
    assert f"{d3._missing(PV, 'MISSING')} (asset {PV1})" in point_.missing


def test_dispatch_two_pv_assets_under_roles4_stay_multiple_bindings() -> None:
    found, problems = _index(ROLE_SET_MINIGRID_4, _pv_night()).site_lookup(PV, AT)
    assert (found.value, found.problem, problems) == (None, "MULTIPLE_BINDINGS", [])


def test_dispatch_one_unit_reads_as_lookup() -> None:
    for role_set in (ROLE_SET_MINIGRID_4, ROLE_SET_MINIGRID_5):
        index = _index(role_set, _pv_night(), pv_units=(PV1,))
        assert index.site_lookup(PV, AT) == (index.lookup(PV, AT), [])


def test_dispatch_slot_sums_the_pv_units() -> None:
    assert _index(ROLE_SET_MINIGRID_5, _pv_night())._slot(AT) == (Fraction(6), Fraction(31, 4))
    gap = _index(ROLE_SET_MINIGRID_4, _pv_night())._slot(AT)
    assert (gap.input, gap.problem) == (PV, "MULTIPLE_BINDINGS")


def _gen(code: str, *props: tuple[str, int]) -> dict:
    return {"component_id": code, "component_type": "GENERATOR",
            "properties": [{"property_key": k, "value": v, "unit": "min"} for k, v in props]}


def test_minimum_runtime_is_the_lead_units_policy() -> None:
    lead = {"components": [_gen("gen-01", ("minimum-runtime", 30)), _gen("gen-02")]}
    assert pas._lead_policy_property(lead, "minimum-runtime")["value"] == 30
    stray = {"components": [_gen("gen-01"), _gen("gen-02", ("minimum-runtime", 45))]}
    with pytest.raises(UnitRolesRefused) as refusal:
        pas._lead_policy_property(stray, "minimum-runtime")
    assert refusal.value.unit == "gen-02"
    one = {"components": [_gen("gen-01", ("minimum-runtime", 30))]}
    assert pas._lead_policy_property(one, "minimum-runtime") == pas._property(one, "GENERATOR", "minimum-runtime")


# --------------------------------------------------------------------------- replay_series

PV_2 = UUID(int=777)
CODES_2 = {**CODES, PV_2: "pv-inverter-2"}


def _roles5(bindings: list[RoleBinding]) -> list[RoleBinding]:
    return [replace(b, role_set=ROLE_SET_MINIGRID_5) for b in bindings]


def _two_units() -> list[RoleBinding]:
    return _roles5(r0_bindings() + [replace(binding(PV, "pv-inverter"), asset_id=PV_2),
                                    binding("generator_power", "generator-2"),
                                    binding("generator_state", "generator-2")])


def test_replay_bound_assets_keeps_every_unit_under_roles5() -> None:
    bound = bound_assets(_two_units(), CODES_2, WINDOW)
    assert set(bound[PV]) == {ASSETS["pv-inverter"], PV_2}
    assert set(bound["generator_power"]) == {ASSETS["generator"], ASSETS["generator-2"]}
    roles4 = [replace(b, role_set=ROLE_SET_MINIGRID_4) for b in _two_units()]
    refused("READER_BINDING_CHANGED", PV, lambda: bound_assets(roles4, CODES_2, WINDOW))


def test_replay_series_sums_power_and_states_through_unit_roles() -> None:
    readings = r0()
    for k in range(288):
        readings.append(replace(mean(PV, "pv-inverter", k, "2.50"), asset_id=PV_2))
        readings.append(mean("generator_power", "generator-2", k, "12.000" if k < 72 else "0"))
        readings.append(reading("generator_state", "generator-2", at=WINDOW.start + k * timedelta(minutes=5),
                                value="RUNNING" if k < 72 else "STOPPED", unit="state"))
    series = placed(readings, bound_assets(_two_units(), CODES_2, WINDOW)).series
    assert series.pv_available_kw == (Fraction(15),) * 288
    assert series.generator_kwh == (Fraction(1),) * 72 + (Fraction(2),) * 24 + (Fraction(0),) * 192
    assert series.generator_state == ("RUNNING",) * 96 + ("STOPPED",) * 192


# --------------------------------------------------------------------------- verification window evidence


def _two_generators() -> list:
    out = [replace(r, value_text="RUNNING") if r.role == "generator_state" else r for r in full_window()]
    for i in range(12):
        t = T0 + vr.SLOT * i
        out.append(power("generator_power", "gen-2", t, t + vr.SLOT, "5"))
        out.append(point("generator_state", "gen-2", t, "STOPPED", unit="state"))
    return out


def _window(readings, **kw):
    return vr.window_evidence(T0, readings, load_asset_ids=["load-a", "load-b"], critical_load_asset_id="crit",
                              reserves=RESERVE, battery_asset_id="bat", **kw)


def test_verification_sums_generator_units_and_states_through_unit_roles() -> None:
    w = _window(_two_generators(), role_assets={"generator_power": ["gen", "gen-2"],
                                                "generator_state": ["gen", "gen-2"]},
                unit_roles=("generator_power", "generator_state"))
    assert w["complete"] is True and w["generator_kwh"] == "25"
    assert not [p for p in w["problems"] if p["code"] == "AMBIGUOUS_BINDING"]
    slot = w["slots"][0]
    assert (slot["generator_power"]["kwh"], slot["generator_state"]["value"]) == (vr.fmt(Fraction(25, 12)), "RUNNING")
    assert sorted(slot["generator_power"]["units"]) == ["gen", "gen-2"]


def test_verification_without_unit_roles_keeps_the_ambiguous_binding() -> None:
    w = _window(_two_generators(), role_assets={"generator_power": ["gen", "gen-2"],
                                                "generator_state": ["gen", "gen-2"]})
    assert w["complete"] is False
    assert {p["role"] for p in w["problems"] if p["code"] == "AMBIGUOUS_BINDING"} == {"generator_power",
                                                                                     "generator_state"}


def test_verification_one_unit_is_byte_identical_with_unit_roles_named() -> None:
    plain = _window(full_window())
    assert _window(full_window(), unit_roles=("generator_power", "generator_state", PV)) == plain


# --------------------------------------------------------------------------- D-DD.117 risks: night text, run ids


def _multi_unit_window(idle: int):
    w = k5.probe_window(0, idle_seconds=idle)
    terms = {**w.terms, "sfc_l_per_kwh": None, "no_load_l_per_h": None, "sfc_revision_id": None,
             "no_load_revision_id": None,
             "units": [{"asset_id": "u1", "generator_kwh": "10.5", "idle_seconds": idle, "loaded_litres": "3.7275",
                        "unknown_slots": 0, "sfc_l_per_kwh": "0.355", "sfc_revision_id": "rev-s1",
                        "no_load_l_per_h": "4.9", "no_load_basis": "DECLARED", "no_load_revision_id": "rev-n1"},
                       {"asset_id": "u2", "generator_kwh": "4", "idle_seconds": 0, "loaded_litres": "1.2",
                        "unknown_slots": 0, "sfc_l_per_kwh": "0.3", "sfc_revision_id": "rev-s2",
                        "no_load_l_per_h": "3.1", "no_load_basis": "DECLARED", "no_load_revision_id": "rev-n2"}]}
    return replace(w, terms=terms)


def test_night_text_use_note_at_a_multi_unit_site_states_every_unit_never_none() -> None:
    note = k5.card(nt.night_view(_multi_unit_window(0), [], k5.TZ), "USE")["note"]
    assert note == "Modelled: 10.5 kWh × 0.355 L/kWh + 4.0 kWh × 0.3 L/kWh, 10 % either way"
    idle = k5.card(nt.night_view(_multi_unit_window(1500), [], k5.TZ), "USE")["note"]
    assert idle == ("Modelled: 10.5 kWh × 0.355 L/kWh plus 25 min idle at 4.9 L/h + 4.0 kWh × 0.3 L/kWh, "
                    "10 % either way")
    assert "None" not in note + idle


def test_night_text_one_unit_note_unchanged() -> None:
    assert (k5.card(nt.night_view(k5.probe_window(0), [], k5.TZ), "USE")["note"]
            == nt.USE_NOTE.format(kwh=nt.kwh1(k5.probe_window(0).terms["generator_kwh"]), sfc="0.355"))


def test_fuel_balance_run_cites_every_units_foundation_revisions() -> None:
    terms = _multi_unit_window(0).terms | {"accuracy_revision_id": "rev-a"}
    assert pas._fuel_balance_foundation_ids(terms) == ["rev-a", "rev-n1", "rev-n2", "rev-s1", "rev-s2"]
    one = {"accuracy_revision_id": "rev-a", "sfc_revision_id": "rev-s", "no_load_revision_id": None}
    assert pas._fuel_balance_foundation_ids(one) == ["rev-a", "rev-s"]
