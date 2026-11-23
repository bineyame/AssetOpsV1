"""DD3d-a (D-DD.154 as amended by D-DD.168): `fuel-records.json` from `exports --telemetry`.

The readings here are hand-written in `assetops.world-readings/1` (the Site manifest's `mappings` and the first-of-month
days only), so a dip is asserted on known text; the deliveries are asserted on the books `build_books` writes."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys

import pytest

from assetops_simulator.world import exports
from assetops_simulator.world import exports_fuel_records as fr

from .books_support import MANIFEST, built, manifest
from .conftest import CLI

LAKE = "lakeside-power"
CODES = ("KISIWA-001", "KOBO-001", "MTO-001")
DIPS = ("2026-07-01", "2026-08-01", "2026-09-01", "2026-10-01", "2026-11-01")
TICKET = re.compile(r"[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}")      # operational_entry.TICKET
VALUE = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,3})?")             # operational_entry.VALUE


def level(code: str, day: str) -> str:
    return f"{1000 + 100 * CODES.index(code) + DIPS.index(day)}.{DIPS.index(day)}50"


def readings(code: str, day: str) -> dict:
    def row(source, signal, minute, value):
        return {"source_id": source, "signal_id": signal, "unit": "L", "value": value,
                "start": f"{day}T00:{minute}:00+03:00", "end": f"{day}T00:{int(minute) + 5:02d}:00+03:00"}

    return {"schema": "assetops.world-readings/1", "site_code": code, "day": day, "timezone": "Africa/Nairobi",
            "role_set": "minigrid-roles-5", "readings": [
                row("generator-controller", "ac-power", "00", "7.000"), row("fuel-level-sensor", "fuel-level", "05", "1.000"),
                row("fuel-level-sensor", "fuel-level", "00", level(code, day))]}


def site_manifest(code: str) -> dict:
    return {"site_code": code, "mappings": [
        {"record": "generator-power@generator", "role": "generator_power", "source_id": "generator-controller",
         "signal_id": "ac-power"},
        {"record": "fuel-tank-volume@fuel-tank", "role": "fuel_level", "source_id": "fuel-level-sensor",
         "signal_id": "fuel-level"}]}


def documents() -> dict:
    return {code: {"manifest": site_manifest(code), "days": {d: readings(code, d) for d in DIPS}} for code in CODES}


def build(docs=None) -> dict:
    view, history, _, books = built()
    (tenant, data), = fr.build_fuel_records(view, history, books.files, {LAKE: documents() if docs is None else docs})
    assert tenant == LAKE
    return json.loads(data)


def by_site(document: dict, kind: str) -> dict[str, list[dict]]:
    return {s["site_code"]: [r for r in s["records"] if r["kind"] == kind] for s in document["sites"]}


def fuel_rows(code: str) -> list[dict]:
    _, _, _, books = built()
    [expenses] = [f for f in books.files if (f.tenant, f.key) == (LAKE, "expenses")]
    return [r for r in expenses.records if r["site_code"] == code and r["body"]["category"] == "FUEL"]


def test_the_file_is_one_document_per_mini_grid_tenant_with_every_site() -> None:
    document = build()
    assert set(document) == {"schema", "tenant", "sites"}
    assert (document["schema"], document["tenant"]) == ("assetops.world-fuel-records/1", LAKE)
    assert tuple(s["site_code"] for s in document["sites"]) == CODES
    for site in document["sites"]:
        assert set(site) == {"site_code", "records"}
        instants = [r["recorded_at"] for r in site["records"]]
        assert instants == sorted(instants)
        for r in site["records"]:
            assert set(r) == {"source_record_id", "kind", "taken_at_local", "litres", "ticket_reference", "recorded_at"}
            assert VALUE.fullmatch(r["litres"])
        ids = [r["source_record_id"] for r in site["records"]]
        assert len(ids) == len(set(ids))


def test_five_dips_per_site_are_the_readings_level_rows() -> None:
    for code, dips in by_site(build(), "TANK_DIP").items():
        assert [(d["source_record_id"], d["taken_at_local"], d["litres"], d["ticket_reference"], d["recorded_at"])
                for d in dips] == [(f"{code}:dip:{day}", f"{day}T00:00", level(code, day), None,
                                    f"{day}T00:00:00+03:00") for day in DIPS]


def test_deliveries_are_the_books_fuel_rows_by_id_and_litres() -> None:
    document = build()
    total = 0
    for code, deliveries in by_site(document, "FUEL_DELIVERY").items():
        rows = fuel_rows(code)
        total += len(rows)
        assert sorted((d["source_record_id"], d["litres"], d["taken_at_local"]) for d in deliveries) == sorted(
            (r["source_record_id"], r["quantity"]["value"], r["clocks"]["occurred_at"][:16]) for r in rows)
        for d in deliveries:
            assert TICKET.fullmatch(d["ticket_reference"])
    assert total == 11  # non-vacuous: Kobo 3, Kisiwa 8, Mto 0 (the notes file)


def test_tickets_number_the_notes_of_a_day_from_one() -> None:
    got = {(d["taken_at_local"], d["ticket_reference"]) for d in by_site(build(), "FUEL_DELIVERY")["KOBO-001"]}
    assert got == {("2026-09-25T10:00", "FN-KOBO-001-20260925-1"), ("2026-09-25T10:00", "FN-KOBO-001-20260925-2"),
                   ("2026-10-26T10:00", "FN-KOBO-001-20261026-1")}


def test_only_the_dated_note_is_recorded_late() -> None:
    late = []
    for code, deliveries in by_site(build(), "FUEL_DELIVERY").items():
        late += [(code, d["taken_at_local"], d["recorded_at"]) for d in deliveries
                 if d["recorded_at"][:16] != d["taken_at_local"]]
    assert late == [("KOBO-001", "2026-10-26T10:00", "2026-11-04T10:00:00+03:00")]


def test_the_recorded_date_is_the_manifests() -> None:
    (test,) = [t for t in manifest()["disorder_tests"] if t["id"] == "OOO-1"]
    recorded = re.search(r"\(recorded ([\d-]+) for", test["what"]).group(1)
    (row,) = exports.DATED_NOTES
    assert row[5] == recorded


def _no_day(docs):
    del docs["MTO-001"]["days"]["2026-11-01"]
    return "MTO-001 2026-11-01T00:00"


def _no_row(docs):
    rows = docs["KOBO-001"]["days"]["2026-09-01"]["readings"]
    rows[:] = [r for r in rows if r["signal_id"] != "fuel-level" or "T00:05" in r["start"]]
    return "KOBO-001 2026-09-01T00:00"


def _no_site(docs):
    del docs["KISIWA-001"]
    return "KISIWA-001 2026-07-01T00:00"


def _two_rows(docs):
    rows = docs["KOBO-001"]["days"]["2026-09-01"]["readings"]
    rows.append(copy.deepcopy(rows[-1]))
    return "KOBO-001 2026-09-01T00:00"


def _four_decimals(docs):
    docs["KOBO-001"]["days"]["2026-09-01"]["readings"][-1]["value"] = "1.2345"
    return "KOBO-001 2026-09-01T00:00"


@pytest.mark.parametrize("break_it", [_no_day, _no_row, _no_site, _two_rows, _four_decimals])
def test_a_dip_without_its_one_level_row_refuses(break_it) -> None:
    docs = documents()
    where = break_it(docs)
    with pytest.raises(ValueError) as raised:
        build(docs)
    assert str(raised.value) == f"EMU_FUEL_RECORDS {where}"


def write_telemetry(root, docs=None) -> None:
    folder = root / LAKE / "telemetry"
    folder.mkdir(parents=True)
    for code, doc in (documents() if docs is None else docs).items():
        (folder / f"{code}.manifest.json").write_text(json.dumps(doc["manifest"]), encoding="utf-8")
        for day, body in doc["days"].items():
            (folder / f"{code}.{day}.readings.json").write_text(json.dumps(body), encoding="utf-8")


def run(*args: str):
    return subprocess.run([sys.executable, str(CLI), "exports", "--manifest", str(MANIFEST), *args],
                          capture_output=True, text=True, timeout=600)


def test_the_cli_writes_the_file_beside_the_books_with_telemetry_only(tmp_path) -> None:
    write_telemetry(tmp_path / "tel")
    done = run("--out", str(tmp_path / "a"), "--tenant", LAKE, "--telemetry", str(tmp_path / "tel"))
    assert done.returncode == 0, done.stderr
    assert json.loads((tmp_path / "a" / LAKE / "fuel-records.json").read_bytes()) == build()
    again = run("--out", str(tmp_path / "b"), "--tenant", LAKE, "--telemetry", str(tmp_path / "tel"))
    assert again.returncode == 0
    name = f"{LAKE}/fuel-records.json"
    assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    assert run("--out", str(tmp_path / "c"), "--tenant", LAKE).returncode == 0
    assert not (tmp_path / "c" / LAKE).exists()


def test_the_cli_refuses_with_exit_3_and_writes_nothing(tmp_path) -> None:
    docs = documents()
    where = _no_day(docs)
    write_telemetry(tmp_path / "tel", docs)
    done = run("--out", str(tmp_path / "a"), "--tenant", LAKE, "--telemetry", str(tmp_path / "tel"))
    assert (done.returncode, done.stderr.strip()) == (3, f"EMU_FUEL_RECORDS {where}")
    assert not (tmp_path / "a").exists()
