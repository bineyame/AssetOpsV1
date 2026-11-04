"""MD-0 L0 (build sheet §10.1): the mechanism fixture's schema rules, the Dn map, the Kobo-only scope (MD0-S2), the
gap placement, the `late_fill` refusals and the `MECHANISM_DB_ONLY` name check. Pure: no database."""

from __future__ import annotations

import copy
from datetime import date, datetime, timezone

import pytest

import mechanism_dataset as md
from assetops_backend.evidence.adapters.authored_fixture_specs import AuthoredFixtureSpecs

SPEC = md.load()


def test_the_fixture_is_a_declared_authored_fixture() -> None:
    assert AuthoredFixtureSpecs().declared(md.FIXTURE_ID) == (md.FIXTURE_ID, md.FIXTURE_VERSION)


def test_dn_map() -> None:
    assert md.day(SPEC, 1) == date(2026, 10, 19) and md.day(SPEC, 1).weekday() == 0
    assert md.day(SPEC, 13) == date(2026, 10, 31) and md.day(SPEC, 14) == date(2026, 11, 1)
    assert md.day(SPEC, 13).isoformat() == SPEC["story"]["S"][:10]
    assert [n for n in range(1, 15) if md.day(SPEC, n).weekday() == 1] == [2, 9]
    assert md.local_instant(SPEC, "kobo", 1, "00:00") == datetime(2026, 10, 18, 21, tzinfo=timezone.utc)
    assert md.local_instant(SPEC, "kobo", 14, "24:00") == datetime(2026, 11, 1, 21, tzinfo=timezone.utc)


def test_kobo_only_with_one_recurrence_after_the_apply() -> None:
    # MD0-S2: Cold and EV are removed (their normal data is proved on DD-1's real baseline).
    assert set(SPEC["sites"]) == {"kobo"} and {g["id"] for g in SPEC["gaps"]} == {"GAP-K7"}
    assert all(set(SPEC["day_sets"][n]) == {"kobo", "source"} for n in md.DAY_SETS)
    effective = SPEC["sites"]["kobo"]["actions"][0]["effective"]["day"]
    after = [e["day"] for e in SPEC["sites"]["kobo"]["events"] if e["day"] >= effective]
    assert after == [14] and all(14 in SPEC["day_sets"][n]["kobo"] for n in md.DAY_SETS)
    bad = copy.deepcopy(SPEC)
    bad["sites"]["cold"] = {"site_code": "COLD-LAB-001", "time_zone": "Africa/Addis_Ababa"}
    with pytest.raises(ValueError, match="KOBO-001 only"):
        md.validate(bad)


def test_gaps_avoid_events_actions_and_studies() -> None:
    fixed = md._event_and_action_days(SPEC)
    assert all((g["site"], g["day"]) not in fixed for g in SPEC["gaps"])
    bad = copy.deepcopy(SPEC)
    bad["gaps"][0]["day"] = 4  # GAP-K7 onto the D4 overrun
    with pytest.raises(ValueError, match="gap falls"):
        md.validate(bad)
    for name in md.DAY_SETS:
        assert 7 not in SPEC["day_sets"][name]["kobo"]


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s["sites"]["kobo"]["events"][0].pop("source"), "no source"),
    (lambda s: s["sites"]["kobo"]["events"][1].__setitem__("grade", "COMPLETE"), "output key"),
    (lambda s: s["threads"][0].__setitem__("state", "OPEN"), "output key"),
    (lambda s: s.__setitem__("note", "objective MG-1"), "outcome id"),
    (lambda s: s.__setitem__("schema", "assetops.mechanism-dataset"), "schema"),
])
def test_schema_rules_refuse(mutate, message) -> None:
    bad = copy.deepcopy(SPEC)
    mutate(bad)
    with pytest.raises(ValueError, match=message):
        md.validate(bad)


def test_late_fill_refuses_all_but_the_declared_fillable_gap() -> None:
    assert md.fill_target(SPEC, "KOBO-001", 7)["id"] == "GAP-K7"
    assert md.fill_target(SPEC, "KOBO-001", 7, "overrun")["id"] == "GAP-K7"
    for code, args in (("DUPLICATE_DAY", ("KOBO-001", 6)), ("DUPLICATE_DAY", ("COLD-LAB-001", 3)),
                       ("PREPARE_ONLY_KIND", ("KOBO-001", 7, "action"))):
        with pytest.raises(md.MechanismRefused, match=code):
            md.fill_target(SPEC, *args)
    held = copy.deepcopy(SPEC)
    held["gaps"][0]["fill"] = False  # a declared gap that holds evidence (the removed GAP-C3/E2 shape)
    with pytest.raises(md.MechanismRefused, match="DAY_HAS_EVIDENCE"):
        md.fill_target(held, "KOBO-001", 7)


@pytest.mark.parametrize("name, allowed", [
    ("assetops_mechanism_test", True),
    ("assetops_mechanism_close_test", True),
    ("assetops_mechanism_tpl_test", True),
    ("assetops_mechanism_c0a1b2c3d4e_test", True),
    ("assetops_mechanism_cxyz_test", False),
    ("assetops_mechanism_other_test", False),
    ("assetops_pt1a2b_main_test", True),
    ("assetops_pt7_gw3_test", True),
    ("assetops_polish_full_test", False),
    ("assetops_demo3_full_test", False),
    ("assetops_polish_client_test", False),
    ("assetops_test", False),
    ("assetops_mechanism", False),
    ("assetops_polish_pt1_main_test", False),
])
def test_mechanism_db_only(name, allowed) -> None:
    assert md.mechanism_db_allowed(name) is allowed


# --- MD0-S3 Q1: the input template (pure parts) ------------------------------------------------------------------


def test_template_holds_inputs_only() -> None:
    spec = md.load()
    steps = md.input_steps(spec, "states")
    assert "derive" not in steps and steps == md.seed_steps(spec, "states")[:-1]
    assert steps[0] == "begin" and steps[-1] == "studies"


def test_check_tag_refuses_missing_and_stale() -> None:
    with pytest.raises(md.MechanismRefused, match="TEMPLATE_MISSING"):
        md.check_tag(None, "a" * 64)
    tag = md.make_tag({"site": {}}, "states", fingerprint="a" * 64)
    with pytest.raises(md.MechanismRefused, match="TEMPLATE_STALE"):
        md.check_tag(tag, "b" * 64)
    assert md.check_tag(tag, "a" * 64) is tag


def test_input_fingerprint_moves_with_a_traced_module_or_a_data_file_only(tmp_path) -> None:
    """MD0-S5 M1: the traced modules and every file under the data folders are hashed; a module outside the list
    (a read-only module the seed never loads) and the derive step's `chain` package are not."""
    modules = ["backend/tests/mechanism_dataset.py", "backend/tests/test_s1_bindings_postgres.py",
               "tools/demo_combined.py", "backend/assetops_backend/financials/x.py"]
    data = [f"{t}/x.json" for t in md.INPUT_DATA_TREES] + ["backend/tests/fixtures/s1/kobo-001.yaml"]
    for rel in [*modules, *data, "backend/assetops_backend/chain/y.py", "backend/assetops_backend/api_only.py"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"v1\n")
    base = md.input_fingerprint(modules, tmp_path)
    for rel in ("backend/assetops_backend/chain/y.py", "backend/assetops_backend/api_only.py"):
        (tmp_path / rel).write_bytes(b"v2\n")
        assert md.input_fingerprint(modules, tmp_path) == base, rel
    for rel in [*modules, *data]:
        (tmp_path / rel).write_bytes(b"changed\n")
        assert md.input_fingerprint(modules, tmp_path) != base, rel
        (tmp_path / rel).write_bytes(b"v1\n")
    (tmp_path / "backend/migrations/x.json").write_bytes(b"v1\r\n")  # CRLF == LF
    assert md.input_fingerprint(modules, tmp_path) == base
    (tmp_path / "config/site-templates/new.yaml").write_bytes(b"v1\n")  # an added data file moves it too
    assert md.input_fingerprint(modules, tmp_path) != base
    (tmp_path / "tools/demo_combined.py").unlink()  # a listed module that is gone is stale, not skipped
    assert md.file_hashes(["tools/demo_combined.py"], tmp_path) == {"tools/demo_combined.py": "missing"}


def test_the_real_kobo_import_source_moves_the_template_fingerprint() -> None:
    """M1's named miss: `backend/tests/fixtures/s1/kobo-001.yaml` (the reserve 30 the Findings pin) is an input."""
    assert "backend/tests/fixtures/s1/kobo-001.yaml" in md.data_files()
    hashes = md.input_hashes([])
    moved = {**hashes, "backend/tests/fixtures/s1/kobo-001.yaml": "0" * 64}
    assert md.fingerprint_of(moved) != md.fingerprint_of(hashes)


def test_traced_modules_come_from_sys_modules_without_the_derive_step(monkeypatch) -> None:
    import sys
    import types

    for name, rel in (("md0_probe_chain", "backend/assetops_backend/chain/probe.py"),
                      ("md0_probe_writer", "backend/assetops_backend/financials/probe.py")):
        module = types.ModuleType(name)
        module.__file__ = str(md.REPO / rel)
        monkeypatch.setitem(sys.modules, name, module)
    traced = md.loaded_repo_files()
    assert "backend/assetops_backend/financials/probe.py" in traced
    assert not any(t.startswith(md.DERIVE_TREE) for t in traced)
    assert "backend/tests/mechanism_dataset.py" in traced  # this module itself: non-vacuous


def test_a_resume_is_refused_when_an_input_changed_since_the_build_started(tmp_path) -> None:
    """MD0-S5 L2: the start fingerprint is kept per file; any change (or an added data file) is named."""
    for rel in ("backend/tests/mechanism_dataset.py", "backend/conversions/a.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"v1\n")
    saved = md.input_hashes(["backend/tests/mechanism_dataset.py"], tmp_path)
    assert md.inputs_changed(saved, tmp_path) == []
    (tmp_path / "backend/tests/mechanism_dataset.py").write_bytes(b"v2\n")
    assert md.inputs_changed(saved, tmp_path) == ["backend/tests/mechanism_dataset.py"]
    (tmp_path / "backend/tests/mechanism_dataset.py").write_bytes(b"v1\n")
    (tmp_path / "backend/conversions/b.json").write_bytes(b"v1\n")
    assert md.inputs_changed(saved, tmp_path) == ["backend/conversions/b.json"]


def test_the_tag_carries_its_module_list_and_check_rehashes_it() -> None:
    tag = md.make_tag({"site": {}}, "states", modules=["backend/tests/mechanism_dataset.py"])
    assert tag["modules"] == ["backend/tests/mechanism_dataset.py"]
    assert md.check_tag(tag) is tag
    with pytest.raises(md.MechanismRefused, match="TEMPLATE_STALE"):
        md.check_tag({**tag, "modules": ["backend/tests/test_md0_fixture.py"]})


# --- MD0-S4 R1/R2 and MD0-S5 M2: producer shapes ------------------------------------------------------------------


def test_power_rows_are_interval_means_ending_at_their_source_time_and_tile_the_day() -> None:
    step = md.timedelta(minutes=SPEC["sites"]["kobo"]["reading_rules"]["step_minutes"])
    rows = md.kobo_rows(SPEC, 1)
    means = [r for r in rows if not isinstance(r, tuple)]
    points = [r for r in rows if isinstance(r, tuple)]
    assert means and points
    assert {(r[0], r[1]) for r in points} == {("generator-controller", "status"),
                                               ("battery-pcs-controller", "state-of-charge")}
    lo, hi = md.local_instant(SPEC, "kobo", 1, "00:00"), md.local_instant(SPEC, "kobo", 1, "24:00")
    for channel in {tuple(x) for x in SPEC["sites"]["kobo"]["shapes"]["interval_mean"]}:
        mine = sorted((r for r in means if (r.device, r.signal) == channel), key=lambda r: r.interval_start)
        assert all(r.kind == "MEAN" and r.source_time - r.interval_start == step for r in mine), channel
        # contiguous [00:00, 24:00) local: the coverage basis every chain measure counts
        assert mine[0].interval_start == lo and mine[-1].source_time == hi, channel
        assert all(a.source_time == b.interval_start for a, b in zip(mine, mine[1:])), channel


def test_the_act_day_cut_puts_an_interval_ending_at_the_cut_before_it() -> None:
    rows = md.kobo_rows(SPEC, 11, "overrun")
    cut = md.local_instant(SPEC, "kobo", 11, "13:00")
    before = [r for r in rows if md._before(r, cut)]
    after = [r for r in rows if not md._before(r, cut)]
    assert len(before) + len(after) == len(rows)
    assert all(md._row_start(r) < cut for r in before) and all(md._row_start(r) >= cut for r in after)


# --- MD0-S5 M2 (A): the renewable-hour channels all day and the busy noon -----------------------------------------

RENEWABLE = {("pv-inverter-controller", "ac-power"), ("battery-pcs-controller", "charge-requested-power"),
             ("clinic-meter", "requested-power"), ("clinic-meter", "delivered-power")}


def _noon_values(n: int, kind: str) -> dict:
    lo, hi = (md.local_instant(SPEC, "kobo", n, x) for x in SPEC["sites"]["kobo"]["noon"]["window_local"])
    out: dict = {}
    for r in md.kobo_rows(SPEC, n, kind):
        if not isinstance(r, tuple) and (r.device, r.signal) in RENEWABLE:
            out.setdefault((r.device, r.signal, lo <= r.interval_start < hi), set()).add(r.value)
    return out


@pytest.mark.parametrize("n,kind", [(1, "normal"), (4, "overrun"), (7, "overrun"), (7, "normal"), (14, "overrun")])
def test_the_busy_noon_requests_the_blocks_dis_on_every_day_but_the_spare_solar_days(n, kind) -> None:
    v = _noon_values(n, kind)
    assert v[("battery-pcs-controller", "charge-requested-power", True)] == {"20"}  # the block's dis
    assert v[("battery-pcs-controller", "charge-requested-power", False)] == {"0"}
    assert v[("pv-inverter-controller", "ac-power", True)] == {"40"}  # min(40, 30 + 20)
    assert v[("pv-inverter-controller", "ac-power", False)] == {"0", "30"}  # night 0, day min(40, 30)
    for signal in ("requested-power", "delivered-power"):
        assert v[("clinic-meter", signal, True)] == v[("clinic-meter", signal, False)] == {"10"}


def test_the_spare_solar_days_keep_a_zero_charge_request_before_the_w4_remap() -> None:
    v = _noon_values(12, "normal")
    assert v[("battery-pcs-controller", "charge-requested-power", True)] == {"0"}


def test_a_derived_channel_rule_is_evaluated_as_declared_or_refused() -> None:
    spec = copy.deepcopy(SPEC)
    spec["sites"]["kobo"]["derived_channels"]["pv_power"]["rule"] = "40"
    with pytest.raises(md.MechanismRefused, match="UNKNOWN_DERIVED_RULE"):
        md.kobo_rows(spec, 1)
    spec = copy.deepcopy(SPEC)
    del spec["sites"]["kobo"]["derived_channels"]["charge_request"]["source"]
    with pytest.raises(ValueError, match="no source"):
        md.validate(spec)
