"""D-DD.119 (the cold writer's books, built in process and byte-checked against the exported ledger) and D-DD.120
(Thika's events, a module table with an `M` parity test)."""

from __future__ import annotations

import importlib.util
import json
import re
from fractions import Fraction

import pytest

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.exports import file_name
from assetops_simulator.world.profile_csv import load_profile, render_profile
from assetops_simulator.world.telemetry_cold import STORY_EVENTS, cold_books_for

from .books_support import built, manifest
from .conftest import CLI, REPOSITORY_ROOT

LEDGER = "profile.cold-storage-ledger"
COLD = ("COLD-MWEA", "COLD-THIKA", "COLD-KIRI")


@pytest.fixture(scope="module")
def cold():
    view, history, records, books = built()
    return view, books, cold_books_for(view, history, records)


def _ledger_file(books):
    return next(f for f in books.files if f.key == LEDGER)


def test_every_cold_site_and_no_other_has_books(cold) -> None:
    _view, _books, out = cold
    assert sorted(out) == sorted(COLD)


def test_the_ledger_is_the_exported_ledger(cold) -> None:
    _view, books, out = cold
    exported = _ledger_file(books)
    rows = [r for code in COLD for r in out[code]["ledger"]]
    assert sorted(map(json.dumps, rows)) == sorted(json.dumps(r) for r in exported.records)
    assert all(r["site_code"] == code for code in COLD for r in out[code]["ledger"])
    layout = load_profile(exported.layout_id)[1]
    assert render_profile(layout, list(exported.records)) == exported.data


def test_cooling_seasons_and_day_classes_are_the_views(cold) -> None:
    view, _books, out = cold
    for code in COLD:
        assert out[code]["cooling"] == view["history"]["families"]["cooling"]
        assert out[code]["seasons"] == view["history"]["seasons"]
        assert out[code]["day_classes"] == view["history"]["day_classes"]


def test_efficiency_from_the_kwh_rule_and_the_period(cold) -> None:
    _view, _books, out = cold
    kiri = {m: Fraction(v) for m, v in out["COLD-KIRI"]["efficiency"].items()}
    assert kiri == {"2026-07": Fraction(21, 20), "2026-08": Fraction(11, 10), "2026-09": Fraction(117, 100),
                    "2026-10": Fraction(500, 403), "2026-11": Fraction(500, 403)}
    assert out["COLD-MWEA"]["efficiency"] == {} and out["COLD-THIKA"]["efficiency"] == {}


def test_events_are_the_module_table(cold) -> None:
    _view, _books, out = cold
    assert out["COLD-THIKA"]["events"] == list(STORY_EVENTS["COLD-THIKA"])
    assert out["COLD-MWEA"]["events"] == [] and out["COLD-KIRI"]["events"] == []
    assert sorted(STORY_EVENTS) == ["COLD-THIKA"]
    assert [e["kind"] for e in STORY_EVENTS["COLD-THIKA"]] == [
        "GRID_LOSS", "GENERATOR_FAILURE", "GENERATOR_HAND_START", "GRID_RESTORE"]


def test_story_events_match_m() -> None:
    """D-DD.120: the three `M` instants (after D-DD.89's commit)."""
    incident = next(s for t in manifest()["tenants"] for s in t["sites"] if s["code"] == "COLD-THIKA")["incident"]
    at = {e["kind"]: e["at"][11:16] for e in STORY_EVENTS["COLD-THIKA"]}
    assert incident["grid_outage"] == f"from {at['GRID_LOSS']}"
    failed = re.search(r"failed to start (\d\d:\d\d):\d\d", incident["backup"]).group(1)
    hand = re.search(r"started by hand (\d\d:\d\d)", incident["backup"]).group(1)
    assert failed == at["GENERATOR_FAILURE"] == at["GRID_LOSS"]
    assert hand == at["GENERATOR_HAND_START"] == "20:22"
    assert all(e["at"].startswith("2026-10-06T") and e["at"].endswith(":00+03:00") for e in STORY_EVENTS["COLD-THIKA"])


def _cli():
    spec = importlib.util.spec_from_file_location("world_history_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(tmp_path, cold, tamper: bool):
    _view, books, _out = cold
    booksdir = tmp_path / "books"
    booksdir.mkdir()
    for f in books.files:
        if f.tenant == "harvest-cold":
            data = f.data.replace(b"\n", b"\r\n", 1) if tamper and f.key == LEDGER else f.data
            (booksdir / file_name(f)).write_bytes(data)
    onboarding = json.loads((REPOSITORY_ROOT / "backend/tests/fixtures/on1/harvest-cold.onboarding.json").read_text())
    bindings = {c: json.loads((REPOSITORY_ROOT / f"backend/conversions/world/{c}-bindings.json").read_text())
                for c in COLD}
    sites = tmp_path / "sites.json"
    sites.write_text(json.dumps(tel.site_inputs(onboarding, bindings)))
    return booksdir, sites


@pytest.mark.parametrize("tamper", [False, True])
def test_the_cli_byte_checks_the_exported_ledger(tmp_path, cold, capsys, tamper) -> None:
    booksdir, sites = _inputs(tmp_path, cold, tamper)
    fixture = REPOSITORY_ROOT / "simulator/tests/world/fixtures/view_v1.json"
    code = _cli().main(["telemetry", "--manifest", str(fixture), "--sites", str(sites), "--books", str(booksdir),
                        "--out", str(tmp_path / "out"), "--start", "2026-07-01", "--end", "2026-07-01",
                        "--site", "COLD-MWEA"])
    if tamper:
        assert code == 3
        assert capsys.readouterr().err.startswith("TEL_BOOKS harvest-cold.profile.cold-storage-ledger.csv")
    else:
        assert code == 0
        assert (tmp_path / "out/harvest-cold/telemetry/COLD-MWEA.2026-07-01.readings.json").exists()
