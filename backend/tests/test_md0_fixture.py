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


def test_input_fingerprint_moves_with_an_input_writer_only(tmp_path) -> None:
    """Every input-writer tree and file is hashed; a file outside them (a chain module: the derive step) is not."""
    writers = [*md.INPUT_WRITER_FILES, *(f"{t}/x.py" for t in md.INPUT_WRITER_TREES)]
    for rel in [*writers, "backend/assetops_backend/chain/y.py"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"v1\n")
    base = md.input_fingerprint(tmp_path)
    (tmp_path / "backend/assetops_backend/chain/y.py").write_bytes(b"v2\n")
    assert md.input_fingerprint(tmp_path) == base
    for rel in writers:
        (tmp_path / rel).write_bytes(b"changed\n")
        assert md.input_fingerprint(tmp_path) != base, rel
        (tmp_path / rel).write_bytes(b"v1\n")
    (tmp_path / "backend/migrations/x.py").write_bytes(b"v1\r\n")  # CRLF == LF
    assert md.input_fingerprint(tmp_path) == base


# --- MD0-S4 R1/R2: producer shapes and the template's writers ----------------------------------------------------


def test_fingerprint_covers_the_per_day_output_writers_but_not_the_derive_step() -> None:
    trees = set(md.INPUT_WRITER_TREES)
    for tree in ("analytics", "mini_depth", "mini_decisions"):
        assert f"backend/assetops_backend/{tree}" in trees, tree
    assert not any(t.startswith("backend/assetops_backend/chain") for t in trees)


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
