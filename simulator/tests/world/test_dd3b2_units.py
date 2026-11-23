"""DD3b2 (spec DD §4.2, §4.3; D-DD.128, D-DD.129, D-DD.126, D-DD.145, D-DD.146): the writer runs units.

This part's first tests: Kisiwa's and Mto's kit in Lakeside's `/2` file (D-DD.128)."""

from __future__ import annotations

import json

from .conftest import REPOSITORY_ROOT

ONBOARDING = REPOSITORY_ROOT / "backend" / "tests" / "fixtures" / "on1" / "lakeside-power.onboarding.json"


def _sites() -> dict[str, dict]:
    return {s["code"]: s for s in json.loads(ONBOARDING.read_text(encoding="utf-8"))["sites"]}


def _props(component: dict) -> dict[str, tuple]:
    return {p["property_key"]: (p["value"], p["unit"], p["source"], p["source_version"]) for p in component["properties"]}


def test_kisiwa_and_mto_units_carry_the_generic_kit_with_its_basis() -> None:
    """Per generator: no-load 0.08 L/h per kW of rating, minimum load 30 %; per Site taper 95 %; each GENERIC_DEFAULT,
    source SITE, version 1 (D-DD.128, spec §4.2, owner 7 Nov)."""
    for code, no_load in (("KISIWA-001", {"gen-ks-01": 4.8, "gen-ks-02": 4.8}), ("MTO-001", {"generator": 2.4})):
        components = _sites()[code]["components"]
        for unit, rate in no_load.items():
            props = _props(next(c for c in components if c["id"] == unit))
            assert props["generator-no-load-fuel-rate"] == (rate, "L/h", "SITE", 1)
            assert props["generator-minimum-load"] == (30, "%", "SITE", 1)
            for key in ("generator-no-load-fuel-rate-basis", "generator-minimum-load-basis"):
                assert props[key] == ("GENERIC_DEFAULT", "state", "SITE", 1)
        battery = _props(next(c for c in components if c["type"] == "BATTERY"))
        assert battery["battery-charge-taper-start"] == (95, "%", "SITE", 1)
        assert battery["battery-charge-taper-start-basis"] == ("GENERIC_DEFAULT", "state", "SITE", 1)


def test_each_inverter_declares_its_share_of_the_array_by_rating() -> None:
    """`pv-array-share` = the inverter's AC limit / the Site's summed limits: Mto 50 % each, Kisiwa's one 100 %."""
    for code, shares in (("KISIWA-001", {"pv-inverter": 100}), ("MTO-001", {"inv-mt-01": 50, "inv-mt-02": 50})):
        for unit, share in shares.items():
            props = _props(next(c for c in _sites()[code]["components"] if c["id"] == unit))
            assert props["pv-array-share"] == (share, "%", "SITE", 1)
            assert props["pv-array-share-basis"] == ("GENERIC_DEFAULT", "state", "SITE", 1)


def test_every_tank_rating_is_its_declared_capacity() -> None:
    """The 400 L template placeholder is gone: each FUEL_TANK's rating equals its `tank-capacity` (D-DD.128)."""
    expected = {"KOBO-001": 2500, "KISIWA-001": 5000, "MTO-001": 1000}
    for code, site in _sites().items():
        tank = next(c for c in site["components"] if c["type"] == "FUEL_TANK")
        assert tank["rating"] == {"value": expected[code], "unit": "L"}
        assert _props(tank)["tank-capacity"][0] == expected[code]


# --- the writer runs units (D-DD.129, D-DD.126, D-DD.145, D-DD.146, D-DD.97, D-DD.104) --------------------------------

import copy  # noqa: E402
from datetime import date  # noqa: E402
from fractions import Fraction  # noqa: E402

import pytest  # noqa: E402
import yaml  # noqa: E402

from assetops_simulator.world import telemetry as tel  # noqa: E402

from .conftest import load_fixture  # noqa: E402

BINDINGS = REPOSITORY_ROOT / "backend" / "conversions" / "world"
LAYER4 = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4"
MINI = ("KISIWA-001", "KOBO-001", "MTO-001")


def _f(codes: tuple[str, ...] = MINI) -> dict:
    onboarding = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    bindings = {c: json.loads((BINDINGS / f"{c}-bindings.json").read_text(encoding="utf-8")) for c in codes}
    return tel.site_inputs(onboarding, bindings)


def _site(code: str) -> dict:
    return next(s for s in _f()["sites"] if s["code"] == code)


@pytest.fixture(scope="module")
def books() -> dict:
    history = json.loads((LAYER4 / "history.json").read_text(encoding="utf-8"))
    return tel.books_for(load_fixture(), history, {"lakeside-power": ""})


def _values(frozen) -> dict[str, object]:
    return {v.address: v for v in frozen.initial_values}


def _run(books: dict, code: str, first: str, last: str) -> tuple[list[dict], dict]:
    result = tel.build_telemetry(load_fixture(), _f(), books, start=first, end=last, only=(code,))
    rows = [r for name, data in result.files if name.endswith(".readings.json")
            for r in json.loads(data)["readings"]]
    return rows, dict(result.manifests)[f"lakeside-power/telemetry/{code}.manifest.json"]


def test_kisiwa_runs_v9_with_every_generator_unit_answered(books: dict) -> None:
    frozen = tel.frozen_inputs(_site("KISIWA-001"), books["KISIWA-001"], "2026-10-30", "2026-10-30")
    values = _values(frozen)
    assert frozen.model_profile_version == 9
    for unit in ("gen-ks-01", "gen-ks-02"):
        for key in ("generator-rated-power", "generator-specific-fuel-consumption", "generator-no-load-fuel-rate",
                    "generator-minimum-load"):
            assert f"{key}@{unit}" in values
    for key in ("generator-start-soc-threshold", "generator-stop-soc-threshold", "generator-minimum-runtime",
                "generator-start-delay"):  # policy rows from the lead unit only (D-DD.43)
        assert [a for a in values if a.startswith(f"{key}@")] == [f"{key}@gen-ks-01"]
    share = values["pv-array-share@pv-inverter"]
    assert (share.value, share.canonical_unit, share.dimension) == (Fraction(1), "1", "FRACTION")
    attached = {(a.role, a.component_id, a.via_component_id) for a in frozen.bus_attachments}
    for unit in ("gen-ks-01", "gen-ks-02"):
        assert ("GENERATION", unit, None) in attached and ("FUEL_SUPPLY", "fuel-tank", unit) in attached
    states = {d.address: d.value for d in frozen.discrete_initial_values}
    assert states == {"generator-state@gen-ks-01": "STOPPED", "generator-state@gen-ks-02": "STOPPED",
                      "inverter-state@pv-inverter": "AVAILABLE"}


def test_mto_declares_half_the_array_on_each_inverter(books: dict) -> None:
    frozen = tel.frozen_inputs(_site("MTO-001"), books["MTO-001"], "2026-10-28", "2026-10-28")
    values = _values(frozen)
    assert frozen.model_profile_version == 9
    for inverter in ("inv-mt-01", "inv-mt-02"):
        assert values[f"pv-array-share@{inverter}"].value == Fraction(1, 2)
        assert values[f"inverter-ac-limit@{inverter}"].value == 25
        assert ("PV_SOURCE", "pv-array", inverter) in {(a.role, a.component_id, a.via_component_id)
                                                        for a in frozen.bus_attachments}


def test_kobo_one_of_each_stays_v8_with_no_v9_rows(books: dict) -> None:
    frozen = tel.frozen_inputs(_site("KOBO-001"), books["KOBO-001"], "2026-10-01", "2026-10-01")
    assert frozen.model_profile_version == 8
    assert not [a for a in _values(frozen) if a.startswith("pv-array-share@")]
    assert [d.address for d in frozen.discrete_initial_values] == ["generator-state@generator"]


def test_unit_events_equal_the_operations_record_of_m() -> None:
    """Parity (D-DD.51): every mini-grid generator or inverter incident of `M` `operations`, its failure at `at` and its
    restore at `restored`, is one `UNIT_EVENTS` row, and nothing else is."""
    manifest = yaml.safe_load((LAYER4 / "demo-site-scenario-manifest.yaml").read_text(encoding="utf-8"))
    codes = {"Kobo": "KOBO-001", "Kisiwa": "KISIWA-001", "Mto": "MTO-001"}
    expected = set()
    for site in manifest["operations"]["sites"]:
        if site["site"] not in codes:
            continue
        kinds = {a["code"]: a["type"] for a in site["assets"]}
        for incident in site.get("incidents") or []:
            if kinds[incident["asset"]] not in ("GENERATOR", "INVERTER"):
                continue
            unit = incident["asset"].lower()
            expected.add((codes[site["site"]], unit, "unit-fail", incident["at"], incident["key"]))
            if incident.get("restored"):
                expected.add((codes[site["site"]], unit, "unit-restore", incident["restored"], incident["key"]))
    assert {(e["site"], e["unit"], e["kind"], e["at"], e["source"]) for e in tel.UNIT_EVENTS} == expected
    assert len(tel.UNIT_EVENTS) == 4


def test_a_unit_event_is_a_one_minute_window_at_its_instant(books: dict) -> None:
    frozen = tel.frozen_inputs(_site("MTO-001"), books["MTO-001"], "2026-10-28", "2026-10-28")
    events = [f for f in frozen.forcings if f.state_key in ("unit-fail", "unit-restore")]
    assert [(f.address, f.shape, f.offset_minutes, f.duration_minutes) for f in events] == [
        ("unit-fail@inv-mt-02", "WINDOW", 11 * 60 + 2, 1)]


def test_kisiwa_gen_ks_01_state_row_is_failed_from_18_40_and_the_lag_is_stated(books: dict) -> None:
    rows, manifest = _run(books, "KISIWA-001", "2026-10-30", "2026-10-30")
    state = {r["start"][11:16]: r["value"] for r in rows
             if (r["source_id"], r["signal_id"]) == ("gen-ks-01-controller", "status")}
    assert state["18:40"] == "FAILED" and state["18:35"] != "FAILED"
    assert all(state[m] == "FAILED" for m in state if m >= "18:40")
    assert not [r for r in rows if r["source_id"] == "gen-ks-02-controller" and r["value"] == "FAILED"]
    conditions = manifest["conditions"]
    assert manifest["pack"] == {"model": "mini-grid", "version": 9}
    assert conditions["unit_events"] == [
        {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-fail", "at": "2026-08-14T19:20+03:00",
         "source": "kis-gen1-2026-08-14"},
        {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-restore", "at": "2026-08-17T11:00+03:00",
         "source": "kis-gen1-2026-08-14"},
        {"site": "KISIWA-001", "unit": "gen-ks-01", "kind": "unit-fail", "at": "2026-10-30T18:40+03:00",
         "source": "kis-gen1-2026-10-30"}]
    assert conditions["unit_event_timing"] == (
        "unit failures and restores apply at the 5-minute step holding their instant; the controller responds at the "
        "next step (Assumed)")


def test_kisiwa_august_outage_fails_at_19_20_and_restores_to_stopped_at_11_00(books: dict) -> None:
    rows, _ = _run(books, "KISIWA-001", "2026-08-14", "2026-08-17")
    state = {r["start"][:16]: r["value"] for r in rows
             if (r["source_id"], r["signal_id"]) == ("gen-ks-01-controller", "status")}
    assert state["2026-08-14T19:20"] == "FAILED" and state["2026-08-14T19:15"] != "FAILED"
    assert state["2026-08-17T10:55"] == "FAILED" and state["2026-08-17T11:00"] == "STOPPED"


def test_mto_inv_mt_02_power_is_zero_from_the_step_holding_11_02_and_no_inverter_state_is_written(books: dict) -> None:
    rows, _ = _run(books, "MTO-001", "2026-10-28", "2026-10-28")
    power = {(r["source_id"], r["start"][11:16]): Fraction(r["value"]) for r in rows if r["signal_id"] == "ac-power"
             and r["source_id"].startswith("inv-mt-")}
    assert power[("inv-mt-02-controller", "10:55")] > 0 and power[("inv-mt-01-controller", "11:00")] > 0
    assert all(v == 0 for (source, minute), v in power.items() if source == "inv-mt-02-controller" and minute >= "11:00")
    assert not [r for r in rows if r["source_id"].startswith("inv-mt-") and r["unit"] == "state"]


def test_the_season_v2_sun_calendar_applies_at_kobo_only(books: dict) -> None:
    weights = books["KISIWA-001"]["sun_weights"]
    day = date(2026, 9, 15)
    weight = Fraction(weights["season"][weights["seasons"]["2026-09"]]) * Fraction(weights["day"]["WD"])
    assert tel._sun(day, weights, "KISIWA-001") == tuple(Fraction(v) * weight for v in tel.SUN_W_PER_M2["clear"])
    assert tel._sun(day, weights, "KOBO-001") == tuple(Fraction(v) for v in tel.SUN_W_PER_M2["clear"])
    assert tel.SEASON_V2_SUN_SITES == ("KOBO-001",)


def test_the_residential_evening_block_starts_at_dark(books: dict) -> None:
    """D-DD.97 (owner-approved 22 Nov)."""
    assert tel.LOAD_SHAPE_KW["res"] == (5, 5, 3, 3, 3, 5, 8, 8, 6, 6, 5, 5, 6, 6, 8, 8, 8, 8, 14, 14, 14, 14, 9, 9)
    _, manifest = _run(books, "KOBO-001", "2026-10-01", "2026-10-01")
    assert manifest["conditions"]["load_shape_basis"] == (
        "residential evening use from dark (18:00 local); Assumed from measured East-African mini-grid profiles")


def test_the_starting_soc_is_the_midnight_state_after_one_warm_up_day(books: dict) -> None:
    """D-DD.104: no book carries a SOC; the value is exact and stated with its basis."""
    assert all("start_soc" not in b for b in books.values())
    frozen = tel.frozen_inputs(_site("KOBO-001"), books["KOBO-001"], "2026-07-01", "2026-07-01")
    soc = _values(frozen)["battery-state-of-charge@battery"]
    assert soc.answered_by == "SCENARIO" and soc.value != 40 and 30 < soc.value < 90
    _, manifest = _run(books, "KOBO-001", "2026-07-01", "2026-07-01")
    assert manifest["conditions"]["start_soc"] == {
        "value": tel._decimal(soc.value), "unit": "%",
        "basis": "Derived: the 00:00 state after one warm-up day of the span's first day from the declared stop "
                 "threshold (D-DD.104)"}


@pytest.mark.parametrize("key", ["sun_weights", "fuel_notes"])
def test_a_missing_book_key_is_refused_not_defaulted(books: dict, key: str) -> None:
    planted = copy.deepcopy(books["KOBO-001"])
    del planted[key]
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.frozen_inputs(_site("KOBO-001"), planted, "2026-10-01", "2026-10-01")
    assert refusal.value.code == "TEL_BOOKS"


def test_a_mini_grid_tenant_without_an_expenses_file_is_refused() -> None:
    history = json.loads((LAYER4 / "history.json").read_text(encoding="utf-8"))
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.books_for(load_fixture(), history, {})
    assert refusal.value.code == "TEL_BOOKS"


def test_a_site_with_no_binding_is_a_not_written_line(books: dict) -> None:
    sites = _f(("KOBO-001", "MTO-001"))
    result = tel.build_telemetry(load_fixture(), sites, books, start="2026-10-01", end="2026-10-01",
                                 only=("KISIWA-001",))
    line = dict(result.manifests)["lakeside-power/telemetry/KISIWA-001.manifest.json"]
    assert line["not_written"].startswith("TEL_BINDING")


def test_a_state_channel_with_an_empty_map_is_refused(books: dict) -> None:
    sites = _f()
    kobo = next(s for s in sites["sites"] if s["code"] == "KOBO-001")
    next(b for b in kobo["bindings"] if b["role"] == "generator_state")["conversion"]["parameters"]["map"] = {}
    with pytest.raises(tel.TelemetryRefused) as refusal:
        tel.build_telemetry(load_fixture(), sites, books, start="2026-10-01", end="2026-10-01", only=("KOBO-001",))
    assert refusal.value.code == "TEL_BINDING"
