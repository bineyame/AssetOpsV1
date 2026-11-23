"""DD2b (spec `specs/DD-demo-data/spec.md` §3, §5.2, §5.3; D-DD.24, D-DD.54): every tenant's books in one call,
every DS1b record in exactly one place, and the profiles' samples and expected files."""

from __future__ import annotations

import json

import pytest

from assetops_contracts.canonical import to_canonical_json
from assetops_contracts.native import read_layout
from assetops_simulator.world.books import STAGED_KINDS
from assetops_simulator.world.exports import build_exports, file_name
from assetops_simulator.world.profile_csv import PROFILES_DIR, load_profile

from .books_support import COLD, EV, HAND_SAMPLES, SAMPLE_EXTRAS, SAMPLES, built, emulated_files, expected_bytes, \
    sample_of, shipped

PROFILE_IDS = sorted(p.name.removesuffix(".profile.json") for p in PROFILES_DIR.glob("*.profile.json"))


def test_b1_every_ds1b_record_lands_in_exactly_one_place() -> None:
    """D-DD.54, D-DD.59, over all three tenants: an exported file (Thika's credit note is a row of the cold invoicing
    file), the staged DS1b JSON (none today) or `unwritten.json`. Mini-grid's
    history months are DD2.1's (DD2a); here its accounting period is asserted, as 3A3's E9 does."""
    view, _, records, books = built()
    in_files = {}
    for f in books.files:
        for r in f.records:
            in_files.setdefault((f.tenant, r["source_record_id"]), []).append(file_name(f))
    listed = {(row[0], row[4]) for row in books.unwritten if row[3] not in ("actual", "plan")}
    staged = {r["source_record_id"] for _, data in books.staged for r in json.loads(data)["records"]}
    ds1b_ids = set()
    for batch in records.batches:
        tenant = batch.batch.tenant_code
        for record in json.loads(to_canonical_json(batch))["records"]:
            rid = record["source_record_id"]
            ds1b_ids.add(rid)
            month = record.get("clocks", {}).get("recognition_period")
            if tenant not in (COLD, EV) and month != view["accounting_period"]:
                continue
            places = len(in_files.get((tenant, rid), [])) + (rid in staged) + ((tenant, rid) in listed)
            assert places == 1, (tenant, rid, in_files.get((tenant, rid)), rid in staged)
            if record["kind"] in STAGED_KINDS:  # D-DD.59: the credit note is a file row, not staged JSON
                assert in_files[(tenant, rid)] == [f"{COLD}.profile.cold-storage-invoicing.csv"], rid
    assert not staged & ds1b_ids  # what is staged today is `tariffs.py`'s (D-DD.61), not DS1b's


def test_b2_mini_grid_unchanged_and_no_vertical_left_unwritten() -> None:
    view, history, _, books = built()
    mini = build_exports(view, history)
    assert [(file_name(f), f.data) for f in books.files if f.tenant == "lakeside-power"] == [
        (file_name(f), f.data) for f in mini.files]
    assert not [r for r in books.unwritten if r[5] == "NOT_ON_PATH_VERTICAL"]
    assert {r[0] for r in books.unwritten} == {"lakeside-power", COLD, EV}


@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_b3_profile_ships_its_sample_and_expected(profile_id: str, request) -> None:
    sample_path, expected_path = shipped(profile_id)
    data, records = sample_of(profile_id)
    if request.config.getoption("--update-golden"):
        sample_path.write_bytes(data)
        expected_path.write_bytes(expected_bytes(records))
    assert sample_path.read_bytes() == data, "sample drifted from the emulator (or its hand-written records)"
    assert expected_path.read_bytes() == expected_bytes(records)
    read = read_layout(load_profile(profile_id)[1], data, tenant_code="acme", produced_at="2026-11-06T06:00:00+03:00",
                       provenance="source-emulated")
    assert dict(read.refused) == {} and read.obj["records"] == records
    assert 3 <= len(records) <= 200  # admission's sample size (3A6)


def test_b4_every_profile_sample_is_a_slice_of_emulated_rows() -> None:
    """D-DD.65a L1: `HAND_SAMPLES` is empty once `exports_measured` exists; every one of the nine profiles samples
    an emulated file (the measured books from the committed `measured.json` fixtures)."""
    assert HAND_SAMPLES == {}
    assert set(SAMPLES) == set(PROFILE_IDS)
    assert PROFILE_IDS == sorted([
        "cold-budget-illustrative", "cold-electricity-bill-illustrative", "cold-storage-invoicing-illustrative",
        "cold-storage-ledger-illustrative", "ev-budget-illustrative", "ev-departures-illustrative",
        "ev-fleet-roster-illustrative", "ev-service-tickets-illustrative", "ev-utility-invoice-illustrative"])


@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_b4b_sample_rows_are_rows_of_the_emulated_file(profile_id: str) -> None:
    """A sample cannot drift from the emulator: each sampled row is a row of the file (extras aside)."""
    name, _ = SAMPLES[profile_id]
    def strip(r):
        return {k: v for k, v in r.items() if k != "source_version"}

    rows = [strip(r) for r in emulated_files()[name].records]
    extras = [strip(r) for r in SAMPLE_EXTRAS.get(profile_id, [])]
    _, records = sample_of(profile_id)
    picked = [strip(r) for r in records if strip(r) not in extras]
    assert picked and all(r in rows for r in picked)


def test_b5_departures_block_met_is_a_json_boolean() -> None:
    """DD2.2's residual risk: the departure log's Y/N column reads as a JSON boolean through the profile."""
    data, _ = sample_of("ev-departures-illustrative")
    read = read_layout(load_profile("ev-departures-illustrative")[1], data, tenant_code="acme",
                       produced_at="2026-11-06T06:00:00+03:00", provenance="source-emulated")
    assert [r["body"]["block_met"] for r in read.obj["records"]] == [True, False, True]
    assert b",N," in data and b",Y," in data
