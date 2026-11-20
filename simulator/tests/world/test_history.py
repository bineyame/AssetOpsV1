"""DS1a T2, T3, T4, T8, T9: golden digests, the private barrier, scope isolation,
refusals, October reproduced (spec §10)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction

import pytest

from assetops_simulator.world.canonical import canonical_bytes, file_bytes
from assetops_simulator.world.history import generate_history, generate_scope
from assetops_simulator.world.view import ManifestView, view_digest

from .conftest import CLI, GOLDEN, REPOSITORY_ROOT, scope_blocks, site_of, tenant_of

# The private block's name is assembled, so no source line names it (T3b).
PRIVATE = "ora" + "cle"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---- T2 golden -------------------------------------------------------------------


def test_t2_golden(view: dict, request: pytest.FixtureRequest) -> None:
    hist = generate_history(view)
    got = {
        "file_sha256": _sha(file_bytes(hist)),
        "view_digest": _sha(canonical_bytes(ManifestView.from_document(view))),
        "scopes": {k: _sha(canonical_bytes(b)) for k, b in scope_blocks(hist).items()},
    }
    if request.config.getoption("--update-golden", default=False):
        GOLDEN.write_bytes(file_bytes(got))
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    differing = sorted(k for k in set(want["scopes"]) | set(got["scopes"])
                       if want["scopes"].get(k) != got["scopes"].get(k))
    assert differing == [], f"scopes differ from golden: {differing}"
    assert got["view_digest"] == want["view_digest"] == hist["meta"]["view_digest"]
    assert got["file_sha256"] == want["file_sha256"]
    assert len(got["scopes"]) == 27


# ---- T3 private block ------------------------------------------------------------


def _planted(view: dict) -> dict:
    doc = json.loads(json.dumps(view))
    doc[PRIVATE] = {"lakeside-power/Kobo": {"candidate_l": 999}, "harvest-cold": {"kwh": 1}}
    doc["checks"] = ["spend == 0"]
    doc["findings"] = {"x": 1}
    for t in doc["tenants"]:
        t[PRIVATE] = {"anything": 5}
        t["portfolio"] = {"total": 1}
        for s in t["sites"]:
            s[PRIVATE] = {"actual": {"kwh": 1}}
            s["observations"] = {"october": {"major_assets": 99}}
            s["incident"] = {"liability": 77}
            p = s["period"]
            p["bridge"] = [{"driver": "x", "amount": "999.0"}]
            p["variance"] = "-999.0"
            p["fuel_balance"] = {"unexplained_l": 999}
            p["coverage_note"] = "changed"
            p["energy_per_crate_day"] = {"actual": "9.9"}
            p[PRIVATE] = {"kwh": 1}
    return doc


def test_t3a_private_block_changes_nothing(view: dict) -> None:
    planted = _planted(view)
    assert file_bytes(generate_history(planted)) == file_bytes(generate_history(view))
    assert view_digest(ManifestView.from_document(planted)) == view_digest(ManifestView.from_document(view))


def test_t3b_name_absent_from_generator() -> None:
    world = REPOSITORY_ROOT / "simulator" / "assetops_simulator" / "world"
    files = [f for f in sorted(world.rglob("*")) if f.is_file() and "__pycache__" not in f.parts] + [CLI]
    assert len(files) >= 8
    hits = [str(f) for f in files if re.search(PRIVATE.encode(), f.read_bytes(), re.IGNORECASE)]
    assert hits == []


ALLOW_TOP = {"manifest_version", "as_of", "accounting_period", "currency", "timezone_default", "history", "tenants"}
ALLOW_TENANT = {"tenant", "vertical", "prices", "energy_model", "capacity_crates_per_room", "sites"}
ALLOW_SITE = {"site", "code", "physical", "tariff", "period"}
ALLOW_PERIOD = {"plan", "actual", "coverage"}


def test_t3c_view_keys_are_allowlist_intersection(view: dict) -> None:
    source = _planted(view)
    del source["currency"]  # an absent key is omitted, never null
    del tenant_of(source, "metro-bus")["sites"][0]["tariff"]
    out = ManifestView.from_document(source)
    assert set(out) == ALLOW_TOP & set(source)
    assert "currency" not in out
    for st, ot in zip(source["tenants"], out["tenants"], strict=True):
        assert set(ot) == ALLOW_TENANT & set(st)
        for ss, os_ in zip(st["sites"], ot["sites"], strict=True):
            assert set(os_) == ALLOW_SITE & set(ss)
            assert set(os_["period"]) == ALLOW_PERIOD & set(ss["period"])
    assert ManifestView.from_document(out) == out  # idempotent on a view


# ---- T4 scope isolation ----------------------------------------------------------


def _changed_scopes(a: dict, b: dict) -> set[str]:
    sa, sb = scope_blocks(a), scope_blocks(b)
    assert set(sa) == set(sb)
    return {k for k in sa if sa[k] != sb[k]}


def test_t4_mwea_occupancy_changes_only_mwea(view: dict) -> None:
    base = generate_history(view)
    sites = view["history"]["sites"]
    key = "harvest-cold/Room A · Mwea"
    assert sites[key]["actual"]["crate_days"] == "occupancy 0.56 0.49 0.42"
    sites[key]["actual"]["crate_days"] = "occupancy 0.57 0.49 0.42"
    changed = _changed_scopes(base, generate_history(view))
    assert changed == {f"{key}/2026-0{m}" for m in (7, 8, 9)}


def test_t4_price_change_changes_no_scope(view: dict) -> None:
    base = generate_history(view)
    prices = tenant_of(view, "lakeside-power")["prices"]
    assert prices["diesel_usd_per_l"]["Kisiwa"] == "1.3"
    prices["diesel_usd_per_l"]["Kisiwa"] = "9.99"
    site_of(view, "metro-bus", "Embakasi")["tariff"]["prices"]["peak"] = "9.99"
    after = generate_history(view)
    assert _changed_scopes(base, after) == set()
    assert base["tenants"] == after["tenants"]


# ---- T8 refusals -----------------------------------------------------------------


def _rules(view: dict, vertical: str, side: str) -> dict:
    return view["history"]["rules"][vertical][side]


def _override(view: dict, key: str, side: str) -> dict:
    return view["history"]["sites"].setdefault(key, {}).setdefault(side, {})


def _p_unknown_word(v):
    _rules(v, "MINI_GRID", "actual")["om"] = "bogus"


def _p_unknown_vertical(v):
    del v["history"]["rules"]["EV_DEPOT"]


def _p_unknown_site(v):
    v["history"]["sites"]["harvest-cold/Room Z"] = {"actual": {"kwh": "fixed"}}


def _p_arity(v):
    _override(v, "lakeside-power/Kobo", "actual")["unexplained_l"] = "trend generator 0.10 0.10"


def _p_ref(v):
    _rules(v, "COLD_CHAIN", "actual")["outstanding"] = "ratio no_such_leaf"


def _p_cycle(v):
    _override(v, "metro-bus/Embakasi", "actual")["peak_kwh"] = "share offpeak_kwh 0.36 0.43 0.49"


def _p_family(v):
    _rules(v, "MINI_GRID", "actual")["delivered_kwh"] = "scale no_such_family"


def _p_bound_negative(v):
    site_of(v, "lakeside-power", "Kobo")["period"]["actual"]["staff"] = "-500.0"


def _p_bound_occupancy(v):
    _override(v, "harvest-cold/Room A · Mwea", "actual")["crate_days"] = "occupancy 1.2 0.49 0.42"


def _p_zero_occupancy(v):
    tenant_of(v, "harvest-cold")["capacity_crates_per_room"] = 0


def _p_zero_cold_kwh(v):
    tenant_of(v, "harvest-cold")["energy_model"].update({"base_kwh": 0, "k_kwh_per_crate_day": 0})


def _p_zero_ratio(v):
    site_of(v, "harvest-cold", "Room A · Mwea")["period"]["actual"]["crate_days"] = 0


def _p_zero_share(v):
    site_of(v, "metro-bus", "Embakasi")["period"]["plan"]["kwh"] = 0


def _p_zero_season(v):
    v["history"]["families"]["demand"]["season"]["short_rains"] = "0"


def _p_months_gap(v):
    v["history"]["months"] = {"2026-07": 31, "2026-09": 30, "2026-10": 31}


def _p_months_two(v):
    v["history"]["months"] = {"2026-08": 31, "2026-09": 30}


def _p_months_days(v):
    v["history"]["months"]["2026-09"] = 31


def _p_months_anchor(v):
    v["history"]["anchor_period"] = "2026-11"


def _p_money(v):
    v["history"]["money_leaves"] = [x for x in v["history"]["money_leaves"] if x != "staff"]


def _p_no_plan_value(v):
    del site_of(v, "harvest-cold", "Room A · Mwea")["period"]["plan"]["maint"]


def _p_missing_capacity(v):
    del tenant_of(v, "harvest-cold")["capacity_crates_per_room"]


def _p_missing_energy_model(v):
    del tenant_of(v, "harvest-cold")["energy_model"]


def _p_missing_october_leaf(v):
    del site_of(v, "harvest-cold", "Room A · Mwea")["period"]["actual"]["crate_days"]


def _p_nan_weight(v):
    v["history"]["families"]["demand"]["season"]["short_rains"] = "NaN"


def _p_infinite_jitter(v):
    v["history"]["families"]["demand"]["jitter"] = "Infinity"


def _p_text_weight(v):
    v["history"]["families"]["flat"]["day"]["SA"] = "heavy"


def _p_nan_token(v):
    _override(v, "lakeside-power/Kobo", "actual")["unexplained_l"] = "trend generator NaN 1 1"


def _p_text_token(v):
    _override(v, "lakeside-power/Kobo", "actual")["unexplained_l"] = "trend generator 1 1 anchor"


def _p_nan_leaf(v):
    site_of(v, "lakeside-power", "Kobo")["period"]["actual"]["staff"] = "NaN"


def _p_no_history(v):
    del v["history"]


def _p_huge_leaf(v):
    site_of(v, "lakeside-power", "Kobo")["period"]["actual"]["staff"] = "1e999999999"


def _p_tiny_weight(v):
    v["history"]["families"]["demand"]["season"]["short_rains"] = "1e-999999999"


def _p_long_text(v):
    site_of(v, "lakeside-power", "Kobo")["period"]["actual"]["staff"] = "1." + "0" * 40


def _p_nan_capacity(v):
    tenant_of(v, "harvest-cold")["capacity_crates_per_room"] = "Infinity"


def _p_missing_field(field):
    def plant(v):
        del v["history"][field]
    plant.__name__ = f"_p_missing_{field}"
    return plant


REQUIRED = ["version", "months", "anchor_period", "shape_source", "money_leaves", "label",
            "missing_cause", "seasons", "day_classes", "families", "rules"]

KOBO, MWEA, EMBAKASI = "lakeside-power/Kobo/2026-07", "harvest-cold/Room A · Mwea/2026-07", "metro-bus/Embakasi/2026-07"

REFUSALS = [
    ("HISTORY_RULE_UNKNOWN", _p_unknown_word, f"{KOBO} om"),
    ("HISTORY_RULE_UNKNOWN", _p_unknown_vertical, f"{EMBAKASI} EV_DEPOT"),
    ("HISTORY_RULE_UNKNOWN", _p_unknown_site, "harvest-cold/Room Z sites"),
    ("HISTORY_RULE_ARITY", _p_arity, f"{KOBO} unexplained_l"),
    ("HISTORY_RULE_REF", _p_ref, f"{MWEA} outstanding"),
    ("HISTORY_RULE_REF", _p_missing_capacity, f"{MWEA} crate_days"),
    ("HISTORY_RULE_REF", _p_missing_energy_model, f"{MWEA} kwh"),
    ("HISTORY_RULE_REF", _p_missing_october_leaf, f"{MWEA} kwh"),
    ("HISTORY_RULE_CYCLE", _p_cycle, f"{EMBAKASI} kwh_0000_0500"),
    ("HISTORY_FAMILY_UNKNOWN", _p_family, f"{KOBO} delivered_kwh"),
    ("HISTORY_BOUND", _p_bound_negative, f"{KOBO} staff"),
    ("HISTORY_BOUND", _p_bound_occupancy, f"{MWEA} crate_days"),
    ("HISTORY_ANCHOR_ZERO", _p_zero_occupancy, f"{MWEA} crate_days"),
    ("HISTORY_ANCHOR_ZERO", _p_zero_cold_kwh, f"{MWEA} kwh"),
    ("HISTORY_ANCHOR_ZERO", _p_zero_ratio, f"{MWEA} outstanding"),
    ("HISTORY_ANCHOR_ZERO", _p_zero_share, f"{EMBAKASI} peak_kwh"),
    ("HISTORY_ANCHOR_ZERO", _p_zero_season, f"{KOBO} adjustments_kwh"),
    ("HISTORY_MONTHS", _p_months_gap, "history 2026-09"),
    ("HISTORY_MONTHS", _p_months_two, "history months"),
    ("HISTORY_MONTHS", _p_months_days, "history 2026-09"),
    ("HISTORY_MONTHS", _p_months_anchor, "history anchor_period"),
    ("HISTORY_MONEY_LEAVES", _p_money, "history money_leaves"),
    ("HISTORY_NO_PLAN_VALUE", _p_no_plan_value, f"{MWEA} maint"),
    ("HISTORY_NUMBER", _p_nan_weight, "history demand"),
    ("HISTORY_NUMBER", _p_infinite_jitter, "history demand"),
    ("HISTORY_NUMBER", _p_text_weight, "history flat"),
    ("HISTORY_NUMBER", _p_nan_token, f"{KOBO} unexplained_l"),
    ("HISTORY_NUMBER", _p_text_token, f"{KOBO} unexplained_l"),
    ("HISTORY_NUMBER", _p_nan_leaf, f"{KOBO} staff"),
    ("HISTORY_NUMBER", _p_nan_capacity, f"{MWEA} crate_days"),
    ("HISTORY_NUMBER", _p_huge_leaf, f"{KOBO} staff"),
    ("HISTORY_NUMBER", _p_tiny_weight, "history demand"),
    ("HISTORY_NUMBER", _p_long_text, f"{KOBO} staff"),
    ("HISTORY_FIELD", _p_no_history, "history history"),
] + [("HISTORY_FIELD", _p_missing_field(f), f"history {f}") for f in REQUIRED]


@pytest.mark.parametrize("code, plant, text", REFUSALS, ids=[p.__name__[3:] for _, p, _ in REFUSALS])
def test_t8_refusals(view: dict, code: str, plant, text: str) -> None:
    generate_history(view)  # the unplanted view generates
    plant(view)
    with pytest.raises(ValueError) as caught:
        generate_history(view)
    assert str(caught.value) == f"{code} {text}"  # the full "<CODE> <scope> <leaf>" text


@pytest.mark.parametrize("plant", [_p_huge_leaf, _p_tiny_weight], ids=["1e999999999", "1e-999999999"])
def test_t8_extreme_exponent_refuses_fast(view: dict, plant) -> None:
    """DS1p L4: each planted call runs in a child process under a 1-second timeout, so an
    unbounded exponent fails the test instead of hanging the suite."""
    plant(view)
    child = (
        "import json, sys\n"
        "from assetops_simulator.world.history import generate_history\n"
        "try:\n"
        "    generate_history(json.load(sys.stdin))\n"
        "except ValueError as error:\n"
        "    print(error)\n"
    )
    try:
        done = subprocess.run(
            [sys.executable, "-c", child],
            input=json.dumps(view),
            capture_output=True,
            text=True,
            timeout=1,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        pytest.fail("the planted exponent did not refuse within 1 second")
    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("HISTORY_NUMBER "), done.stdout


def test_t8_missing_label_is_a_field_refusal(view: dict) -> None:
    del view["history"]["label"]
    with pytest.raises(ValueError, match=r"^HISTORY_FIELD history label$"):
        generate_history(view)


def test_t8_nan_float_refused_by_the_view() -> None:
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match=r"^VIEW_TYPE tenants\[0\]\.prices\.a$"):
            ManifestView.from_document({"tenants": [{"tenant": "t", "prices": {"a": bad}}]})


def test_t8_generate_scope_alone_validates(view: dict) -> None:
    del view["history"]["families"]["generator"]["jitter"]
    with pytest.raises(ValueError, match=r"^HISTORY_FAMILY_UNKNOWN history generator$"):
        generate_scope(view, "lakeside-power", "Kobo", "2026-10", jitter=False)
    del view["history"]["label"]
    with pytest.raises(ValueError, match=r"^HISTORY_FIELD history label$"):
        generate_scope(view, "lakeside-power", "Kobo", "2026-10", jitter=False)


def test_t8_generate_scope_does_not_check_month_membership(view: dict) -> None:
    assert generate_scope(view, "lakeside-power", "Kobo", "2026-10", jitter=False)["period_days"] == 31


def test_t8_unknown_leaf_skipped(view: dict) -> None:
    _rules(view, "MINI_GRID", "actual")["no_such_leaf"] = "fixed"
    hist = generate_history(view)
    assert all("no_such_leaf" not in b["actual"] for b in scope_blocks(hist).values())


# ---- T9 October reproduced -------------------------------------------------------

LISTED = {"trend", "level", "occupancy", "cold_kwh", "share"}


def _october_rule(rule: str) -> str:
    """Trends and levels at 1; occupancy, model and share lists at `anchor`."""
    tokens = rule.split()
    if tokens[0] in {"trend", "level"}:
        return " ".join(tokens[:-3] + ["1", "1", "1"])
    if tokens[0] in {"occupancy", "cold_kwh", "share"}:
        return " ".join(tokens[:-3] + ["anchor"] * 3)
    return rule


def test_t9_october_reproduces_itself(view: dict) -> None:
    hist = view["history"]
    for table in list(hist["rules"].values()) + list(hist["sites"].values()):
        for side in table.values():
            for leaf, rule in side.items():
                side[leaf] = _october_rule(rule)
    money = set(hist["money_leaves"])
    compared = 0
    for t in view["tenants"]:
        for s in t["sites"]:
            block = generate_scope(view, t["tenant"], s["site"], "2026-10", jitter=False)
            assert block["period_days"] == 31 and block["period_end"] == "2026-10-31"
            for side in ("plan", "actual"):
                rules = dict(hist["rules"][t["vertical"]][side])
                rules.update(hist["sites"].get(f"{t['tenant']}/{s['site']}", {}).get(side, {}))
                for leaf, value in block[side].items():
                    rule = rules[leaf].split()
                    if rule[0] in {"scale", "trend", "level"} or "anchor" in rule:
                        october = Fraction(Decimal(str(s["period"][side][leaf])))
                        expected = october * 100 if leaf in money else october
                        assert value == expected, (t["tenant"], s["site"], side, leaf, value, expected)
                        compared += 1
    assert compared >= 30
