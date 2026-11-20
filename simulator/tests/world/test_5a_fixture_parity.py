"""5a test 10 (spec `specs/5a-targets/spec.md` §6; ruling `rulings.md` "Mid-build answers", Q1).

The simulator's claim: DS1b writes what the product's fixture `backend/tests/fixtures/targets_lakeside.json` says it
writes. The fixture is read by path as a repository file; no product package is loaded.
"""

from __future__ import annotations

import json
from pathlib import Path

from assetops_contracts.canonical import to_canonical_json
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.records import build_records

from .conftest import REPOSITORY_ROOT, load_fixture

TARGETS_FIXTURE = REPOSITORY_ROOT / "backend" / "tests" / "fixtures" / "targets_lakeside.json"


def _step1_batch() -> dict:
    return json.loads(TARGETS_FIXTURE.read_text(encoding="utf-8"))["steps"][0]["batch"]


def _ds1b_batches() -> list[dict]:
    view = load_fixture()
    result = build_records(view, generate_history(view))
    return [json.loads(to_canonical_json(b)) for b in result.batches]


def _fixture_records() -> list[dict]:
    return _step1_batch()["records"]


def test_a_step1_holds_six_distinct_budget_lines() -> None:
    records = _fixture_records()
    assert len(records) == 6
    assert {r["kind"] for r in records} == {"BUDGET_LINE"}
    ids = [r["source_record_id"] for r in records]
    assert len(set(ids)) == len(ids)


def test_b_each_id_occurs_exactly_once_in_ds1b_output() -> None:
    written = [r["source_record_id"] for b in _ds1b_batches() for r in b["records"]]
    for rid in (r["source_record_id"] for r in _fixture_records()):
        assert written.count(rid) == 1, rid


def test_c_each_record_equals_ds1b_field_for_field() -> None:
    by_id = {r["source_record_id"]: r for b in _ds1b_batches() for r in b["records"]}
    for rec in _fixture_records():
        got = by_id[rec["source_record_id"]]
        for key in ("kind", "source_record_id", "source_version", "site_code", "clocks", "body"):
            assert rec[key] == got[key], (rec["source_record_id"], key)


def test_d_batch_envelope_matches_the_holding_ds1b_batch() -> None:
    step = _step1_batch()
    ids = {r["source_record_id"] for r in step["records"]}
    holders = [b for b in _ds1b_batches() if ids & {r["source_record_id"] for r in b["records"]}]
    assert len(holders) == 1
    for key in ("tenant_code", "source_type", "source_system", "provenance"):
        assert step[key] == holders[0][key], key


def test_e_ds1b_lakeside_october_plan_ids_equal_the_fixtures() -> None:  # review r1 F2: both directions
    ds1b = {r["source_record_id"] for b in _ds1b_batches() if b["tenant_code"] == "lakeside-power"
            for r in b["records"] if r["kind"] == "BUDGET_LINE" and r["clocks"]["recognition_period"] == "2026-10"
            and ":plan:" in r["source_record_id"]}
    assert ds1b == {r["source_record_id"] for r in _fixture_records()}
