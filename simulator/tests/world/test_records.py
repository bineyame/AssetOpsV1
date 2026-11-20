"""DS1b T1-T9: the generator's canonical record writers (spec `specs/DS1b-canonical-writers/spec.md` §5).

Written before the module (W2). T3 and T9 read the pack manifest and `missing-records.json` independently of the
module's literal tables; the rest run on the fixture view and its generated history.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from assetops_contracts import canonical
from assetops_contracts.canonical import (
    LEAF_FACTORS,
    SOURCE_TYPES,
    CanonicalRecordV1,
    batch_digest,
    leaves_of,
    parse_batch,
    to_canonical_json,
)
from assetops_simulator.world import records
from assetops_simulator.world.canonical import file_bytes
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.leaves import MONEY_LEAVES
from assetops_simulator.world.records import (
    ACTUAL_WRITERS,
    PASS_THROUGH,
    READ_IN_EXPRESSION,
    STRUCTURE_KEY,
    batch_file_name,
    build_records,
)

from .conftest import CLI, HERE, REPOSITORY_ROOT, load_fixture

RECORDS_GOLDEN = HERE / "golden" / "records_v1.json"
LAYER4 = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4"
MANIFEST = LAYER4 / "demo-site-scenario-manifest.yaml"
MISSING = LAYER4 / "missing-records.json"
RECORDS_PY = REPOSITORY_ROOT / "simulator" / "assetops_simulator" / "world" / "records.py"

# R5: no output names a coverage word or a provenance stronger than source-emulated.
STRONGER = (b"RECORDED", b"Recorded", b"field-integrated", b"observed-financial", b"bench-tested")
REASONS = {"NOT_A_MONTH_RECORD", "ESTIMATED_NOT_RECEIVED", "ZERO_NO_ROW", "NOT_OWN_LINE",
           "READ_IN_AN_EXPRESSION", "NOT_READ_BY_A_LEAF"}

_CACHE: dict = {}


def _built() -> tuple[dict, dict, records.RecordsResult]:
    if "built" not in _CACHE:
        view = load_fixture()
        history = generate_history(view)
        _CACHE["built"] = (view, history, build_records(load_fixture(), history))
    return _CACHE["built"]


def _manifest() -> dict:
    if "manifest" not in _CACHE:
        _CACHE["manifest"] = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return _CACHE["manifest"]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unwritten_bytes(result) -> bytes:
    return file_bytes([list(row) for row in result.unwritten])


def _records(result):
    """(tenant, source type, parsed record) for every written record."""
    out = []
    for b in result.batches:
        for o in b.outcomes:
            assert isinstance(o, CanonicalRecordV1)
            out.append((b.batch.tenant_code, b.batch.source_type, o))
    return out


def _sites(view: dict) -> dict:
    """site code -> (tenant, site name, structure key)."""
    return {s["code"]: (t["tenant"], s["site"], STRUCTURE_KEY[t["vertical"]])
            for t in view["tenants"] for s in t["sites"]}


def _side(view: dict, history: dict, code: str, month: str, side: str) -> dict:
    tenant, site, _ = _sites(view)[code]
    if month == view["accounting_period"]:
        doc = next(s for t in view["tenants"] for s in t["sites"] if s["code"] == code)
        return doc["period"].get(side, {})
    return history["tenants"][tenant][site][month][side]


def _cents(view: dict, month: str, value) -> Fraction:
    """A money input in cents: history months hold cents, October holds the view's money."""
    if month == view["accounting_period"]:
        return Fraction(Decimal(str(value))) * 100
    return Fraction(value)


def _split_top(expression: str) -> list[str]:
    parts, depth, current = [], 0, ""
    for ch in expression:
        depth += ch in "([{"
        depth -= ch in ")]}"
        if ch == "|" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)
    return [p.strip() for p in parts]


# ---- T1 format, golden, labels -----------------------------------------------------


def test_t1_batches_parse_golden_and_labels(request: pytest.FixtureRequest) -> None:
    _, _, result = _built()
    assert result.batches, "no batch written; the checks would prove nothing"
    files = {}
    for b in result.batches:
        assert all(isinstance(o, CanonicalRecordV1) for o in b.outcomes)
        data = to_canonical_json(b)
        again = parse_batch(json.loads(data))
        refused = [str(o) for o in again.outcomes if not isinstance(o, CanonicalRecordV1)]
        assert refused == []
        assert len(again.outcomes) == len(b.outcomes) > 0
        assert batch_digest(again) == batch_digest(b) == _sha(data)
        assert b.batch.provenance == "source-emulated"
        assert b.batch.source_system == "assetops-world-generator"
        files[batch_file_name(b)] = batch_digest(b)
    unwritten = _unwritten_bytes(result)
    counts: dict[str, int] = {}
    for row in result.unwritten:
        counts[row[5]] = counts.get(row[5], 0) + 1
    got = {"files": files, "unwritten.json": _sha(unwritten), "unwritten_counts": counts}
    if request.config.getoption("--update-golden", default=False):
        RECORDS_GOLDEN.write_bytes(file_bytes(got))
    want = json.loads(RECORDS_GOLDEN.read_text(encoding="utf-8"))
    assert got == want
    for data in [to_canonical_json(b) for b in result.batches] + [unwritten]:
        assert [w for w in STRONGER if w in data] == []


# ---- T2 CLI determinism and refusals --------------------------------------------------


def _run(args: list[str], cwd: Path, seed: str = "0") -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env.pop("PYTHONPATH", None)  # the CLI puts the tree's simulator and contracts on its own path (P1)
    return subprocess.run([sys.executable, str(CLI), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, check=False)


def test_t2_cli_two_processes_identical(tmp_path: Path) -> None:
    from .conftest import FIXTURE

    outs = []
    for seed in ("1", "2"):
        cwd = tmp_path / f"cwd{seed}"
        cwd.mkdir()
        out = cwd / "out"
        done = _run(["records", "--manifest", str(FIXTURE), "--out", str(out)], cwd, seed)
        assert done.returncode == 0, done.stderr
        outs.append({p.name: p.read_bytes() for p in sorted(out.iterdir())})
    assert outs[0] == outs[1]
    _, _, result = _built()
    want = {batch_file_name(b): to_canonical_json(b) for b in result.batches}
    want["unwritten.json"] = _unwritten_bytes(result)
    assert outs[0] == want


def test_t2_cli_refuses_inside_repository(tmp_path: Path) -> None:
    from .conftest import FIXTURE

    target = REPOSITORY_ROOT / "simulator" / "tests" / "world" / "_ds1b_refused_out"
    done = _run(["records", "--manifest", str(FIXTURE), "--out", str(target)], tmp_path)
    assert (done.returncode, done.stderr.strip()) == (3, "DS1B_OUT inside-repository")
    assert not target.exists()


def test_t2_cli_refuses_not_empty(tmp_path: Path) -> None:
    from .conftest import FIXTURE

    target = tmp_path / "out"
    target.mkdir()
    (target / "keep.txt").write_text("x", encoding="utf-8")
    done = _run(["records", "--manifest", str(FIXTURE), "--out", str(target)], tmp_path)
    assert (done.returncode, done.stderr.strip()) == (3, "DS1B_OUT not-empty")
    assert sorted(p.name for p in target.iterdir()) == ["keep.txt"]


# ---- T3 independent derivations ---------------------------------------------------------


def test_t3_pass_through_derived_from_factor_map() -> None:
    manifest = _manifest()
    derived = {}
    for key, factor_map in manifest["factor_map"].items():
        rows = []
        for leaf, expression in factor_map.items():
            fields = [m.group(1) for m in (re.fullmatch(r"record\.([a-z0-9_]+)", a)
                                           for a in _split_top(str(expression))) if m]
            if fields:
                rows.append((leaf, fields))
        derived[key] = rows
    assert {k: [(leaf, list(fields)) for leaf, fields in v.items()] for k, v in PASS_THROUGH.items()} == derived
    sites = [s for t in manifest["tenants"] for s in t["sites"]]
    with_sources = [s for s in sites if s.get("factor_sources")]
    assert with_sources, "no Site declares factor_sources; the check would prove nothing"
    for site in with_sources:
        for leaf, expression in site["factor_sources"].items():
            hits = [a for a in _split_top(str(expression)) if re.fullmatch(r"record\.[a-z0-9_]+", a)]
            assert hits == [], (site["site"], leaf)


def test_t3_actual_writers_derived_from_leaf_sources() -> None:
    leaf_sources = _manifest()["empty_states"]["leaf_sources"]
    derived = {}
    for key, rows in leaf_sources.items():
        for leaf, row in rows.items():
            kind = str(row["kind"])
            if not kind.startswith(("EXPENSE", "ADJUSTMENT")) or row["absent"] == "OPTION_ONLY":
                continue
            if not LEAF_FACTORS[leaf].money:
                continue
            derived[(key, leaf)] = kind
    assert {(k, f) for k, v in ACTUAL_WRITERS.items() for f in v} == set(derived)
    by_parenthesis = {"(OM)": ("EXPENSE", "OM"), "(STAFF)": ("EXPENSE", "STAFF"),
                      "(credit note)": ("ADJUSTMENT", "CUSTOMER_COMPENSATION")}
    for (key, field), kind in derived.items():
        writer = ACTUAL_WRITERS[key][field]
        parenthesis = kind[kind.index("("):]
        assert (writer.kind, writer.code) == by_parenthesis[parenthesis], (key, field, kind)
        assert writer.kind in SOURCE_TYPES[writer.source_type].kinds


def test_t3_read_in_an_expression_derived() -> None:
    for key, factor_map in _manifest()["factor_map"].items():
        anywhere = {f for e in factor_map.values() for f in re.findall(r"record\.([a-z0-9_]+)", str(e))}
        passed = {f for fields in PASS_THROUGH[key].values() for f in fields}
        assert set(READ_IN_EXPRESSION[key]) == anywhere - passed, key
    assert "kwh" in READ_IN_EXPRESSION["COLD_CHAIN"]


def test_t3_structure_keys() -> None:
    assert set(STRUCTURE_KEY.values()) == set(canonical.STRUCTURE_KEYS)
    assert set(STRUCTURE_KEY) == set(_manifest()["history"]["rules"]) == set(load_fixture()["history"]["rules"])
    assert set(PASS_THROUGH) == set(ACTUAL_WRITERS) == set(READ_IN_EXPRESSION) == set(canonical.STRUCTURE_KEYS)


def test_t3_money_consistency_r11() -> None:
    for key in canonical.STRUCTURE_KEYS:
        pairs = [(leaf, f) for leaf, fields in PASS_THROUGH[key].items() for f in fields]
        pairs += [(f, f) for f in ACTUAL_WRITERS[key]]
        for leaf, field in pairs:
            assert leaf in leaves_of(key), (key, leaf)
            assert (field in MONEY_LEAVES) == LEAF_FACTORS[leaf].money, (key, leaf, field)


# ---- T4 sums --------------------------------------------------------------------------


def test_t4_every_line_equals_its_input() -> None:
    view, history, result = _built()
    sites = _sites(view)
    months = sorted(history["meta"]["months"]) + [view["accounting_period"]]
    seen_months, seen_codes, counts = set(), set(), {"EXPENSE": 0, "ADJUSTMENT": 0, "BUDGET_LINE": 0}
    for tenant, _, r in _records(result):
        code = r.site_code
        month = r.clocks["recognition_period"]
        assert sites[code][0] == tenant
        seen_months.add(month)
        seen_codes.add(code)
        counts[r.kind] += 1
        if r.kind in ("EXPENSE", "ADJUSTMENT"):
            field = r.source_record_id.split(":")[-1]
            assert r.source_record_id == f"gen:{code}:{month}:actual:{field}"
            want = _cents(view, month, _side(view, history, code, month, "actual")[field])
            got = Fraction(r.amount[0]) * 100
            assert got == (want if r.kind == "EXPENSE" else -want), r.source_record_id
            assert r.amount[1] == view["currency"]
        else:
            field = r.body["line_ref"]
            leaf = r.body["factor_id"]
            assert r.source_record_id == f"gen:{code}:{month}:plan:{leaf}"
            raw = _side(view, history, code, month, "plan")[field]
            if field in MONEY_LEAVES:
                assert Fraction(r.body["value"]) * 100 == _cents(view, month, raw), r.source_record_id
                assert r.body["currency"] == view["currency"]
            else:
                assert Fraction(r.body["value"]) == Fraction(Decimal(str(raw))), r.source_record_id
                assert "currency" not in r.body
    assert seen_months == set(months)
    assert seen_codes == set(sites) and len(sites) == 9
    assert all(counts.values()), counts


def test_t4_clocks_and_produced_at() -> None:
    _, _, result = _built()
    occurred = []
    for _, _, r in _records(result):
        month = r.clocks["recognition_period"]
        if r.kind == "EXPENSE":
            occurred.append(datetime.fromisoformat(r.clocks["occurred_at"]))
            assert r.clocks["occurred_at"].endswith("T17:00:00+03:00")
            assert r.status == "PAID" and r.subject == ("SITE", r.site_code)
            assert r.body["document_ref"] == r.source_record_id
        elif r.kind == "ADJUSTMENT":
            assert r.clocks["effective_from"] == f"{month}-01"
            assert r.body["reason_code"] == "CUSTOMER_COMPENSATION"
            assert r.body["authorised_by_ref"] == "finance-lead"
        else:
            assert r.body["version_ref"] == "budget-2026-v1"
    oct_expense = [r for _, _, r in _records(result) if r.kind == "EXPENSE"
                   and r.source_record_id == "gen:KOBO-001:2026-10:actual:om"]
    assert [r.clocks["occurred_at"] for r in oct_expense] == ["2026-10-31T17:00:00+03:00"]
    assert occurred
    for b in result.batches:
        assert b.batch.produced_at == "2026-11-06T06:00:00+03:00"
        produced = datetime.fromisoformat(b.batch.produced_at)
        assert all(produced > o for o in occurred)


def test_t4_batch_order_and_record_order() -> None:
    view, _, result = _built()
    tenants = [t["tenant"] for t in view["tenants"]]
    order = ("expense_ledger", "billing_export", "customer_invoicing", "budget_workbook")
    keys = [(tenants.index(b.batch.tenant_code), order.index(b.batch.source_type)) for b in result.batches]
    assert keys == sorted(keys) and len(set(keys)) == len(keys)
    for b in result.batches:
        ids = [o.source_record_id.split(":")[1:] for o in b.outcomes]
        assert ids == sorted(ids)
    # One canonical record per (Site, month, field) (D-DS1B.8).
    all_ids = [r.source_record_id for _, _, r in _records(result)]
    assert len(all_ids) == len(set(all_ids))


# ---- T5 the unwritten list ---------------------------------------------------------------


def test_t5_unwritten_list() -> None:
    view, history, result = _built()
    rows = list(result.unwritten)
    assert rows == sorted(rows) and len(rows) == len(set(rows))
    assert {r[5] for r in rows} <= REASONS
    estimated = sorted((r[1], r[2], r[3], r[4]) for r in rows if r[5] == "ESTIMATED_NOT_RECEIVED")
    assert estimated == [("COLD-THIKA", "2026-10", "actual", "maint"), ("EV-KAS", "2026-10", "actual", "maintenance"),
                         ("KISIWA-001", "2026-10", "actual", "om")]
    sites = _sites(view)
    for tenant, code, month, side, field, reason in rows:
        if reason == "ESTIMATED_NOT_RECEIVED" or side != "actual":
            continue
        if field in ACTUAL_WRITERS[sites[code][2]]:
            assert reason == "ZERO_NO_ROW" and field == "liability"
            assert _cents(view, month, _side(view, history, code, month, side)[field]) == 0
    assert all(r[3] == "actual" for r in rows if r[5] == "ZERO_NO_ROW")
    assert {r[4] for r in rows if r[5] == "NOT_OWN_LINE"} == {"billed_kwh", "diesel_l", "offpeak_kwh", "kwh"}
    assert {(r[1], r[4]) for r in rows if r[5] == "READ_IN_AN_EXPRESSION"} == {
        ("COLD-MWEA", "kwh"), ("COLD-THIKA", "kwh"), ("COLD-KIRI", "kwh")}


def test_t5_every_present_field_written_or_listed() -> None:
    view, history, result = _built()
    written: dict = {}
    for _, _, r in _records(result):
        side = r.source_record_id.split(":")[3]
        field = r.body["line_ref"] if r.kind == "BUDGET_LINE" else r.source_record_id.split(":")[-1]
        written.setdefault((r.site_code, r.clocks["recognition_period"], side), set()).add(field)
    listed: dict = {}
    for _, code, month, side, field, _ in result.unwritten:
        listed.setdefault((code, month, side), set()).add(field)
    months = sorted(history["meta"]["months"]) + [view["accounting_period"]]
    for code in _sites(view):
        for month in months:
            for side in ("actual", "plan"):
                w = written.get((code, month, side), set())
                u = listed.get((code, month, side), set())
                assert not w & u, (code, month, side, w & u)
                assert w | u == set(_side(view, history, code, month, side)), (code, month, side)


def test_t5_zero_handling_and_no_totals() -> None:
    _, _, result = _built()
    lines = {r.source_record_id: r for _, _, r in _records(result)}
    thika = lines["gen:COLD-THIKA:2026-10:plan:liability"]
    assert thika.kind == "BUDGET_LINE" and format(thika.body["value"], "f") == "0.00" and thika.body["currency"] == "USD"
    assert "gen:COLD-MWEA:2026-10:actual:liability" not in lines
    # D-DS1B.3: a zero liability writes no row (Thika's history months hold 0); a written one is never 0.
    adjustments = [r for r in lines.values() if r.kind == "ADJUSTMENT"]
    assert adjustments and all(r.amount[0] != 0 for r in adjustments)
    assert all(f"gen:COLD-THIKA:{m}:actual:liability" not in lines for m in ("2026-07", "2026-08", "2026-09"))
    for r in lines.values():
        if r.kind == "BUDGET_LINE":
            key = STRUCTURE_KEY[next(t["vertical"] for t in load_fixture()["tenants"]
                                     if any(s["code"] == r.site_code for s in t["sites"]))]
            assert r.body["factor_id"] in PASS_THROUGH[key]
            assert r.body["line_ref"] == PASS_THROUGH[key][r.body["factor_id"]][0]
            assert r.body["factor_id"] not in {"contribution", "revenue", "energy_cost", "total"}


# ---- T6 inputs untouched ------------------------------------------------------------------


def test_t6_inputs_not_mutated() -> None:
    view = load_fixture()
    history = generate_history(view)
    before = (file_bytes(view), file_bytes(history))
    build_records(view, history)
    assert (file_bytes(view), file_bytes(history)) == before


# ---- T7 refusals --------------------------------------------------------------------------


def _site_doc(view: dict, code: str) -> dict:
    return next(s for t in view["tenants"] for s in t["sites"] if s["code"] == code)


def _plant_vertical(v: dict) -> None:
    next(t for t in v["tenants"] if t["tenant"] == "metro-bus")["vertical"] = "EV_FLEET"


def _plant_money(v: dict) -> None:
    _site_doc(v, "KOBO-001")["period"]["actual"]["om"] = "10.005"


def _plant_format(v: dict) -> None:
    _site_doc(v, "COLD-MWEA")["period"]["plan"]["crate_days"] = "0.3333333333333333333333333333333"


def _plant_number(v: dict) -> None:
    _site_doc(v, "KOBO-001")["period"]["plan"]["om"] = "abc"


def _plant_as_of(v: dict) -> None:
    v["as_of"] = "soon"


@pytest.mark.parametrize("plant, text", [
    (_plant_vertical, "DS1B_VERTICAL metro-bus"),
    (_plant_money, "DS1B_MONEY lakeside-power/KOBO-001/2026-10 actual om"),
    (_plant_format, "DS1B_FORMAT CANONICAL_NUMBER record.body.value"),
    (_plant_number, "DS1B_NUMBER lakeside-power/KOBO-001/2026-10 plan om"),
    (_plant_as_of, "DS1B_AS_OF"),
])
def test_t7_refusals(plant, text: str) -> None:
    _, history, _ = _built()
    planted = load_fixture()
    plant(planted)
    with pytest.raises(ValueError) as caught:
        build_records(planted, history)
    assert str(caught.value) == text


def test_t7_money_mismatch_money_field_on_non_money_leaf(monkeypatch: pytest.MonkeyPatch) -> None:
    _, history, _ = _built()
    table = {k: dict(v) for k, v in PASS_THROUGH.items()}
    del table["MINI_GRID"]["in_transit"]
    table["MINI_GRID"]["adjustments_kwh"] = ("in_transit",)
    monkeypatch.setattr(records, "PASS_THROUGH", table)
    with pytest.raises(ValueError) as caught:
        build_records(load_fixture(), history)
    assert str(caught.value) == "DS1B_MONEY_MISMATCH MINI_GRID in_transit"


def test_t7_money_mismatch_plain_field_on_money_leaf(monkeypatch: pytest.MonkeyPatch) -> None:
    _, history, _ = _built()
    table = {k: dict(v) for k, v in PASS_THROUGH.items()}
    table["MINI_GRID"]["om"] = ("om_kwh",)
    monkeypatch.setattr(records, "PASS_THROUGH", table)
    with pytest.raises(ValueError) as caught:
        build_records(load_fixture(), history)
    assert str(caught.value) == "DS1B_MONEY_MISMATCH MINI_GRID om_kwh"


# ---- T8 neutrality ------------------------------------------------------------------------


def test_t8_records_imports_are_neutral() -> None:
    tree = ast.parse(RECORDS_PY.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            roots.add("." if node.level else node.module.split(".")[0])
    assert "assetops_backend" not in roots
    assert roots <= set(sys.stdlib_module_names) | {"assetops_contracts", "."}, roots
    assert "assetops_contracts" in roots


def test_t8_cli_has_no_literal_month_length() -> None:
    hits = [i for i, line in enumerate(CLI.read_text(encoding="utf-8").splitlines(), 1) if re.search(r"\b31\b", line)]
    assert hits == []


# ---- T9 no budget line for a labelled assumption -----------------------------------------------


def test_t9_no_budget_line_for_an_assumption() -> None:
    view, _, result = _built()
    october = view["accounting_period"]
    code_of = {f"{t['tenant']}/{s['site']}": s["code"] for t in view["tenants"] for s in t["sites"]}
    missing = json.loads(MISSING.read_text(encoding="utf-8"))["sites"]
    assumed = {}
    for site, entries in missing.items():
        for e in entries:
            if e.get("side") == "plan" and e.get("carried_as") == "ASSUMPTION":
                assumed.setdefault(code_of[site], set()).update(e.get("leaves", []))
    assert assumed.get("EV-EMB", set()) >= {"kwh_2200_2400"}, "the independent list lost its EV case"
    assert assumed.get("KOBO-001", set()) >= {"delivered_kwh", "necessary_l"}
    lines = [r for _, _, r in _records(result) if r.kind == "BUDGET_LINE"]
    for r in lines:
        if r.clocks["recognition_period"] == october:
            assert r.body["factor_id"] not in assumed.get(r.site_code, set()), r.source_record_id
        assert r.body["factor_id"] not in {"delivered_kwh", "necessary_l", "kwh_2200_2400"}, r.source_record_id
