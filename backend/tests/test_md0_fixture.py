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
    ("assetops_mechanism_tpl_0a1b2c3d_test", True),
    ("assetops_mechanism_tplb_0a1b2c3d_test", True),
    ("assetops_mechanism_tpl_0a1b2c3_test", False),
    ("assetops_mechanism_tpl_0A1B2C3D_test", False),
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


def test_template_name_is_per_fingerprint() -> None:
    """CH5a1-R3 M4: one template per input fingerprint, named for its first 8 hex digits."""
    assert md.template_name("ab12cd34" + "0" * 56) == "assetops_mechanism_tpl_ab12cd34_test"
    assert md.TEMPLATE_RE.fullmatch(md.template_name("f" * 64))
    assert not md.TEMPLATE_RE.fullmatch(md.LEGACY_TEMPLATE_DB)
    with pytest.raises(md.MechanismRefused, match="MECHANISM_DB_ONLY"):
        md.template_name("not-a-fingerprint")


def test_prune_keeps_the_two_newest_and_never_the_legacy_template() -> None:
    """M4: after a publish, the new template and the newest other one stay; older ones and nothing else go."""
    a, b, c, d = (f"assetops_mechanism_tpl_{x * 8}_test" for x in "abcd")
    assert md.prune_list([a, b, c, d], a) == [c, d]
    assert md.prune_list([b, a, c], a) == [c]  # the kept one need not be first (an older fingerprint rebuilt)
    assert md.prune_list([a], a) == [] and md.prune_list([a, b], a) == []
    assert md.prune_list([a, md.LEGACY_TEMPLATE_DB, b, c], a) == [c]
    assert md.prune_list([a, b, c], a, keep=1) == [b, c]


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


def test_build_work_writes_kobo_days_as_site_local_days(tmp_path) -> None:
    """CH-5a1 D-2d-1 (closes MD0-R R10): a Kobo `days.json` entry is its Addis local day in UTC, the window
    `chain_coherence.day_windows` reads; a gap day is still listed (no delivery needed)."""
    import json

    manifest = {"day_set": "test", "days": [1, 13], "findings": {}}
    md.build_work("postgresql://unused", tmp_path, manifest)
    days = json.loads((tmp_path / "days.json").read_text(encoding="utf-8"))["days"]
    by_day = {d["day"]: d for d in days}
    assert (by_day["2026-10-19"]["start"], by_day["2026-10-19"]["end"]) == ("2026-10-18T21:00:00Z", "2026-10-19T21:00:00Z")
    assert (by_day["2026-10-31"]["start"], by_day["2026-10-31"]["end"]) == ("2026-10-30T21:00:00Z", "2026-10-31T21:00:00Z")
    assert {d["kind"] for d in days if d["day"] == md.day(SPEC, 7).isoformat()} == {"gap"}


# --- MD-0b: verification, the close variant, the drained mini queue ---------------------------------------------------


def test_generator_power_is_the_declared_running_value_while_running_and_zero_otherwise() -> None:
    """The bound generator_power role every verification slot needs (`verification_rules._SINGLE_POWER_ROLES`),
    derived by the fixture's rule from the generator status of the same step."""
    rows = md.kobo_rows(SPEC, 4, "overrun")
    status = {r[2]: r[3] for r in rows if isinstance(r, tuple) and r[1] == "status"}
    power = [r for r in rows if not isinstance(r, tuple) and (r.device, r.signal) == ("generator-controller", "ac-power")]
    assert len(power) == 288
    running = SPEC["sites"]["kobo"]["derived_channels"]["generator_power"]["running_kw"]
    assert {r.value for r in power} == {"0", running}
    assert all(r.value == (running if status[r.interval_start] == "RUNNING" else "0") for r in power)


def test_action_hooks_cut_each_day_in_story_order() -> None:
    assert md.action_hooks(SPEC) == {11: [("13:00", "accept")], 13: [("00:30", "freeze"), ("10:00", "evaluate")]}
    close = md.variant_spec(SPEC, "close")
    assert md.action_hooks(close) == {2: [("13:00", "accept")], 4: [("00:30", "freeze"), ("10:00", "evaluate")]}


@pytest.mark.parametrize("variant_set", ["states", "close"])
def test_the_verify_windows_fit_the_product_rules(variant_set) -> None:
    """B/actions/verification.py freeze: 60-minute windows on the same UTC clock hour, the baseline ending before the
    change's effect and the later window after it; the freeze precedes the later window and follows the 06:00Z
    read edge of the baseline's next UTC day (BASELINE_SELECTION_CHANGED otherwise); the evaluation follows the
    later window's own 06:00Z edge."""
    spec = md.variant_spec(SPEC, variant_set)
    a = spec["sites"]["kobo"]["actions"][0]
    at = lambda node: md.local_instant(spec, "kobo", node["day"], node["local"])  # noqa: E731
    v = a["verify"]
    b0, l0, effective = at(v["baseline"]), at(v["later"]), at(a["effective"])
    assert b0.minute % 5 == 0 and b0.second == 0 and (l0 - b0) % md.timedelta(days=1) == md.timedelta(0)
    assert b0 + md.timedelta(hours=1) <= effective <= l0
    edge = lambda t: datetime.combine(t.date() + md.timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)         + md.timedelta(hours=6)  # noqa: E731
    assert edge(b0) <= at(v["freeze"]) < l0
    assert at(v["evaluate"]) >= max(l0 + md.timedelta(hours=1), edge(l0) - md.timedelta(days=1))
    # the baseline starts inside the declared overrun of the Action's Finding, once its configured 30 min minimum
    # runtime has passed (those minutes are INDETERMINATE, so a window holding them is UNSUPPORTED)
    event = next(e for e in spec["sites"]["kobo"]["events"] if e["anchor"] == a["for_event"])
    run_start = md.local_instant(spec, "kobo", event["day"], event["from_local"])
    assert v["baseline"]["day"] == event["day"]
    assert run_start + md.timedelta(minutes=30) == b0 < md.local_instant(spec, "kobo", event["day"], event["to_local"])


def test_the_close_variant_is_its_own_story() -> None:
    close = md.variant_spec(SPEC, "close")
    k = close["sites"]["kobo"]
    assert close["gaps"] == [] and k["studies"] == []
    assert [(e["anchor"], e["day"]) for e in k["events"]] == [("K-OVR-D2", 2), ("K-OVR-D13", 13)]
    assert md.seed_steps(SPEC, "close") == ["begin", *[f"D{n}" for n in range(1, 15)], "drain_mini", "studies",
                                            "derive"]
    assert md.kobo_day_kind(close, 7) == "normal" and md.kobo_day_kind(close, 13) == "overrun"
    assert SPEC["sites"]["kobo"]["events"][0]["anchor"] == "K-OVR-D4"  # the main fixture is untouched
    assert md.template_name("ab" * 32, "close") == "assetops_mechanism_tplc_abababab_test"
    assert md.CLOSE_TEMPLATE_RE.fullmatch(md.template_name("f" * 64, "close"))
    assert not md.TEMPLATE_RE.fullmatch(md.template_name("f" * 64, "close"))
    with pytest.raises(md.MechanismRefused, match="VARIANT_UNKNOWN"):
        md.variant_spec(SPEC, "other")


def test_the_drain_runs_before_the_studies_and_never_in_the_derive() -> None:
    steps = md.seed_steps(SPEC, "states")
    assert steps.index("drain_mini") == steps.index("studies") - 1 and steps[-1] == "derive"
    assert "drain_mini" in md.input_steps(SPEC, "states")
