"""6h (`specs/6h-named-option-levers/spec.md` §3.2, §5.3, §10.2 test 1): the named-option lever checks.

Branches 15 to 22 of `check_levers` refuse one planted fault each as `STRUCTURE_LEVER <structure>/<lever>`; the grid
branches 6 to 13 run for `SETTING_GRID` only (D-P6.63)."""
from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from assetops_backend.structure import pins as pins_module
from assetops_backend.structure.check import StructureError, check_levers
from assetops_backend.structure.levers import (LEVERS, RECORD, STUDY, ChangeSource, Lever, LeverOption, SettingAxis)
from assetops_backend.structure.registry import REGISTRIES

from decimal import Decimal

NAMED = Lever("t_named", "COLD_CHAIN", "excess_kwh", "STATED_OPTIONS", (), "", ("model_factor", "excess_kwh"),
              options=(LeverOption("repair", "REPAIR", ("excess_kwh",)),
                       LeverOption("replace", "CAPEX", ("model_factor", "excess_kwh"))),
              change_sources=MappingProxyType({"model_factor": RECORD, "excess_kwh": RECORD}))


def _registries(lever_id="t_named", factor_id="excess_kwh", key="COLD_CHAIN", **change):
    reg = REGISTRIES[key]
    rows = tuple(dataclasses.replace(r, levers=(*r.levers, lever_id), **change) if r.factor_id == factor_id else r
                 for r in reg.rows)
    return MappingProxyType({**REGISTRIES, key: dataclasses.replace(reg, rows=rows)})


def _named(**change) -> Lever:
    return dataclasses.replace(NAMED, **change)


def _opt(i=0, **change) -> tuple[LeverOption, ...]:
    opts = list(NAMED.options)
    opts[i] = dataclasses.replace(opts[i], **change)
    return tuple(opts)


def _check(lever: Lever, registries=None, pins=None) -> None:
    check_levers(MappingProxyType({**LEVERS, lever.lever_id: lever}), registries or _registries(lever.lever_id),
                 pins_module.PINS if pins is None else pins)


CASES = {
    "15-generator": dict(lever=_named(generator="CHOICE_LIST")),
    "16-sources-keys": dict(lever=_named(change_sources=MappingProxyType({"excess_kwh": RECORD}))),
    "16-source-kind": dict(lever=_named(change_sources=MappingProxyType({"model_factor": RECORD,
                                                                         "excess_kwh": ChangeSource("QUOTE")}))),
    "17-grid-with-options": dict(lever=dataclasses.replace(LEVERS["generator_stop_reserve"],
                                                           options=NAMED.options[:1])),
    "17-named-with-axes": dict(lever=_named(axes=(SettingAxis("stop_soc_pct", (Decimal(90),), "%"),))),
    "17-named-without-options": dict(lever=_named(options=())),
    "17-named-with-template": dict(lever=_named(key_template="repair-{x}")),
    "18-key-form": dict(lever=_named(options=_opt(0, key="Repair"))),
    "18-no-action": dict(lever=_named(options=_opt(0, key="no-action"))),
    "18-repeated": dict(lever=_named(options=_opt(1, key="repair"))),
    "19-kind": dict(lever=_named(options=_opt(0, kind="WISH"))),
    "20-empty": dict(lever=_named(options=_opt(0, changes=()))),
    "20-not-subset": dict(lever=_named(options=_opt(0, changes=("kwh_model",)))),
    "20-order": dict(lever=_named(options=_opt(1, changes=("excess_kwh", "model_factor")))),
    "21-no-action-words": dict(lever=_named(no_action_words="DO_NOTHING")),
    "22-bounds-on-optimize": dict(lever=_named(bounds_required=True)),
}


def test_1_a_planted_named_lever_passes() -> None:
    _check(NAMED)
    _check(_named(bounds_required=True, purpose_factor="nights_without_backup_cover", lever_id="t_cover",
                  changes=("uncovered_nights",), options=(LeverOption("stopgap", "SUPPLIER_REMEDY",
                                                                      ("uncovered_nights",)),),
                  change_sources=MappingProxyType({"uncovered_nights": RECORD}), no_action_words="WAIT_FOR_REMEDY"),
           registries=_registries("t_cover", "nights_without_backup_cover"))


@pytest.mark.parametrize("name", sorted(CASES))
def test_1_each_branch_15_to_22_refuses(name: str) -> None:
    lever = CASES[name]["lever"]
    with pytest.raises(StructureError) as caught:
        _check(lever, registries=_registries(lever.lever_id, lever.purpose_factor, lever.structure_key)
               if lever.lever_id != "generator_stop_reserve" else REGISTRIES)
    assert str(caught.value) == f"STRUCTURE_LEVER {lever.structure_key}/{lever.lever_id}"


def test_1_the_cases_cover_branches_15_to_22() -> None:
    assert sorted({int(n.split("-")[0]) for n in CASES}) == list(range(15, 23))


def test_1_grid_branches_run_for_setting_grid_only() -> None:
    # a named lever has no axes and an empty template: branches 6 to 13 would refuse it (10: template names)
    _check(NAMED)
    with pytest.raises(StructureError):
        _check(dataclasses.replace(LEVERS["generator_stop_reserve"], key_template="stop-{stop_soc_pct}"),
               registries=REGISTRIES)


def test_1_the_generator_lever_reads_its_study_sources_and_keep_settings() -> None:
    lever = LEVERS["generator_stop_reserve"]
    assert dict(lever.change_sources) == {"candidate_l": STUDY, "battery_throughput_kwh": STUDY}
    assert (lever.no_action_words, lever.bounds_required, lever.options) == ("KEEP_SETTINGS", False, ())


# --- 6h3: the real catalogue and the class rule (§5.1 to §5.3) ---------------------------------------------------------

from assetops_backend.structure.check import PENDING_LEVERS, check_all, check_lever_paths  # noqa: E402

NINE = {  # §5.1 as literals: structure, purpose, changes, options (key, kind, changes), bounds, no action
    "backup_cover": ("COLD_CHAIN", "nights_without_backup_cover", ("uncovered_nights",),
                     (("stopgap-and-claim", "SUPPLIER_REMEDY", ("uncovered_nights",)),
                      ("self-repair", "REPAIR", ("uncovered_nights",))), True, "WAIT_FOR_REMEDY"),
    "chamber_efficiency": ("COLD_CHAIN", "excess_kwh", ("model_factor", "excess_kwh"),
                           (("repair", "REPAIR", ("excess_kwh",)),
                            ("replace", "CAPEX", ("model_factor", "excess_kwh"))), False, "KEEP"),
    "storage_contract": ("COLD_CHAIN", "contract_crate_days", ("contract_crate_days", "contract_rate", "handling"),
                         (("storage-contract", "DEMAND_CONTRACT",
                           ("contract_crate_days", "contract_rate", "handling")),), False, "KEEP"),
    "charging_schedule": ("EV_DEPOT_CAPTIVE", "peak_kwh", ("peak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw",
                                                           "extra_missed_departures"),
                          (("deadline-aware", "SCHEDULE", ("peak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw",
                                                           "extra_missed_departures")),
                           ("cheapest-window", "SCHEDULE", ("peak_kwh", "kwh_2200_2400", "kwh_0000_0500", "max_kw",
                                                            "extra_missed_departures"))), False, "KEEP"),
    "charger_restore": ("EV_DEPOT_CAPTIVE", "departures_missed", ("covered_bus_nights", "extra_missed_departures"),
                        (("stopgap-and-claim", "SUPPLIER_REMEDY", ("covered_bus_nights",)),
                         ("local-repair", "REPAIR", ("extra_missed_departures",)),
                         ("reschedule", "SCHEDULE", ("extra_missed_departures",))), True, "WAIT_FOR_REMEDY"),
    "fleet_capacity_use": ("EV_DEPOT_CAPTIVE", "buses", ("buses",),
                           (("absorb-part", "CAPACITY_USE", ("buses",)), ("absorb-all", "CAPACITY_USE", ("buses",)),
                            ("add-chargers", "CAPEX", ("buses",))), False, "KEEP"),
    "generator_redundancy": ("MINI_GRID", "obligation_hours_without_redundancy", ("reduced_days",),
                             (("repair", "REPAIR", ("reduced_days",)), ("replace", "CAPEX", ("reduced_days",)),
                              ("add-storage", "CAPEX", ("reduced_days",))), True, "KEEP"),
    "productive_demand": ("MINI_GRID", "productive_kwh", ("productive_kwh",),
                          (("new-connection", "DEMAND_CONNECTION", ("productive_kwh",)),), False, "KEEP"),
    "fuel_reconciliation": ("MINI_GRID", "unexplained_l", ("unexplained_l",),
                            (("investigate", "INVESTIGATION", ("unexplained_l",)),), False, "KEEP"),
}
STUDY_SOURCED = {"charging_schedule"}


def test_1_the_nine_levers_are_the_catalogue_literals_after_the_generator() -> None:
    assert list(LEVERS) == ["generator_stop_reserve", *NINE]
    for lever_id, (key, purpose, changes, options, bounds, words) in NINE.items():
        lever = LEVERS[lever_id]
        assert (lever.structure_key, lever.purpose_factor, lever.generator, lever.axes, lever.key_template) == (
            key, purpose, "STATED_OPTIONS", (), ""), lever_id
        assert lever.changes == changes and tuple((o.key, o.kind, o.changes) for o in lever.options) == options
        kind = "STUDY" if lever_id in STUDY_SOURCED else "RECORD"
        assert {k: v.kind for k, v in lever.change_sources.items()} == {c: kind for c in changes}, lever_id
        assert (lever.bounds_required, lever.no_action_words) == (bounds, words), lever_id


def test_1_the_real_levers_pass_both_checks_and_check_all_runs_the_class_rule(monkeypatch) -> None:
    check_levers()
    check_lever_paths()
    assert PENDING_LEVERS == {}
    calls: list[str] = []
    import assetops_backend.structure.check as check_module
    monkeypatch.setattr(check_module, "check_lever_paths", lambda: calls.append("paths"))
    check_all()
    assert calls == ["paths"]


def test_1_every_site_type_has_a_lever() -> None:
    assert {lever.structure_key for lever in LEVERS.values()} == set(REGISTRIES)


def _without_lever(key: str, factor_id: str):
    reg = REGISTRIES[key]
    rows = tuple(dataclasses.replace(r, levers=()) if r.factor_id == factor_id else r for r in reg.rows)
    return MappingProxyType({**REGISTRIES, key: dataclasses.replace(reg, rows=rows)})


def test_1_a_pin_with_no_lever_and_not_pending_refuses() -> None:
    with pytest.raises(StructureError, match=r"^STRUCTURE_LEVER_PATH COLD_CHAIN/COLD_EXCURSION$"):
        check_lever_paths(registries=_without_lever("COLD_CHAIN", "excursion_crates"))
    check_lever_paths(registries=_without_lever("COLD_CHAIN", "excursion_crates"),
                      pending=MappingProxyType({"COLD_EXCURSION": "9c"}))


def test_1_a_pending_pin_whose_row_lists_a_lever_refuses() -> None:
    with pytest.raises(StructureError, match=r"^STRUCTURE_LEVER_PATH EV_DEPOT_CAPTIVE/EV_INTERRUPTION$"):
        check_lever_paths(pending=MappingProxyType({"EV_INTERRUPTION": "9c"}))


def test_1_a_pending_key_that_is_no_pin_refuses_with_an_empty_structure_key() -> None:
    with pytest.raises(StructureError) as caught:
        check_lever_paths(pending=MappingProxyType({"NOT_A_PIN": "9c"}))
    assert (caught.value.code, caught.value.structure_key, caught.value.factor_id) == (
        "STRUCTURE_LEVER_PATH", "", "NOT_A_PIN")
