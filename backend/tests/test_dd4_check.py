"""DD4.4 (spec `specs/DD-demo-data/spec.md` §8.1 C-DD5, C-DD6, C-DD7, C-DD20; D-DD.55, D-DD.99, D-DD.124): the judges on
hand rows, no database. The judges on the emulator's rows are `simulator/tests/world/test_dd4_checker_on_emulated_rows.py`
(a product test may not import the simulator).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import dd_check  # noqa: E402

T0 = datetime.fromisoformat("2026-10-01T00:00:00+03:00")
DAY = timedelta(days=1)
FIVE = timedelta(minutes=5)


def mean(source: str, signal: str, at: datetime, value: str, unit: str = "kW", minutes: int = 5) -> dict:
    return {"source_id": source, "signal_id": signal, "start": at.isoformat(),
            "end": (at + timedelta(minutes=minutes)).isoformat(), "value": value, "unit": unit}


def instant(source: str, signal: str, at: str, value=None, event: dict | None = None) -> dict:
    row = {"source_id": source, "signal_id": signal, "start": at, "end": at, "value": value,
           "unit": "event" if event else "state"}
    if event:
        row["event"] = event
    return row


def day_of(source: str, signal: str, value_at, start: datetime = T0, days: int = 1) -> list[dict]:
    return [mean(source, signal, start + FIVE * i, value_at(start + FIVE * i)) for i in range(288 * days)]


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


# --- C-DD5: cadence, source mode, gaps ---------------------------------------------------------------------------------

def _cadence(readings, modes=None, outages=None):
    modes = {"COLD-MWEA": "SIMULATED"} if modes is None else modes
    return dd_check.judge_cadence(readings, modes, ("COLD-MWEA",), T0, T0 + DAY, outages or {})


def test_c5_the_checkers_cadence_table_and_span() -> None:
    assert dd_check.CADENCE == {"state": "ON_CHANGE", "event": "ON_CHANGE"}
    assert dd_check.MEAN_SLOT == FIVE


def test_c5_span_is_ms_history_start_to_as_of_at_06_00(inputs) -> None:
    start, end = dd_check.span_of(inputs.manifest)
    assert (start.isoformat(), end.isoformat()) == ("2026-07-01T00:00:00+03:00", "2026-11-06T06:00:00+03:00")


def test_c5_a_whole_day_of_means_and_states_passes() -> None:
    rows = day_of("compressor-meter", "power", lambda t: "2.400")
    rows.append(instant("compressor-controller", "state", "2026-10-01T03:07:00+03:00", "RUNNING"))
    result = _cadence({"COLD-MWEA": rows})
    assert result.check == "C-DD5" and result.passed, result.detail


def test_c5_a_missing_slot_is_a_gap_unless_declared() -> None:
    rows = day_of("compressor-meter", "power", lambda t: "2.400")
    del rows[100]
    result = _cadence({"COLD-MWEA": rows})
    assert not result.passed and any("gap" in d and "08:20" in d for d in result.detail), result.detail
    outage = {"COLD-MWEA": [(T0 + FIVE * 100, T0 + FIVE * 101)]}
    assert _cadence({"COLD-MWEA": rows}, outages=outage).passed


@pytest.mark.parametrize("change, words", [
    (lambda rows, modes: modes.update({"COLD-MWEA": "MEASURED"}), "source_mode"),
    (lambda rows, modes: modes.clear(), "source_mode"),
    (lambda rows, modes: rows.append(mean("compressor-meter", "power", T0 + FIVE * 3, "1.0", minutes=10)), "cadence"),
    (lambda rows, modes: rows.append(mean("compressor-meter", "power", T0 + timedelta(minutes=2), "1.0")), "cadence"),
    (lambda rows, modes: rows.append(mean("compressor-meter", "power", T0 + DAY, "1.0")), "outside the span"),
])
def test_c5_fails_on_mode_cadence_and_span(change, words) -> None:
    rows, modes = day_of("compressor-meter", "power", lambda t: "2.400"), {"COLD-MWEA": "SIMULATED"}
    change(rows, modes)
    result = _cadence({"COLD-MWEA": rows}, modes)
    assert not result.passed and any(words in d for d in result.detail), result.detail


def test_c5_a_site_without_readings_fails_and_the_store_holds_none_until_dd5(inputs) -> None:
    result = _cadence({})
    assert not result.passed and result.detail == ["COLD-MWEA: no readings"]
    on_clone = dd_check.LIVE["C-DD5"](inputs)
    assert not on_clone.passed and len([d for d in on_clone.detail if d.endswith("no readings")]) == 9


# --- C-DD6: the EV clauses --------------------------------------------------------------------------------------------

def _fault(source: str, at: str) -> dict:
    return instant(source, "fault-event", at, event={"record_kind": "EV_CONNECTOR_FAULT", "outcome": "FAULTED"})


def _ev_faults() -> dict:
    return {"EV-KAS": [_fault("ch-k2-c1-connector-controller", "2026-11-01T23:40:00+03:00"),
                       _fault("ch-k2-c2-connector-controller", "2026-11-01T23:40:00+03:00")],
            "EV-RUI": [_fault("ch-r7-c2-connector-controller", "2026-10-06T00:00:00+03:00")]}


def test_c6_ev_clauses_are_live_and_kisiwa_mto_stay_pending() -> None:
    result = dd_check.judge_failures_at_instant(_ev_faults(), sites=("EV-KAS", "EV-RUI"))
    assert result.passed, result.detail
    assert not any(p.startswith("EV-") for p in result.pending)
    assert [p.split()[0] for p in result.pending] == ["KISIWA-001", "MTO-001"]


@pytest.mark.parametrize("edit", [
    lambda r: r["EV-KAS"].pop(),  # one connector of CH-K2 only
    lambda r: r["EV-KAS"][0].update(start="2026-11-01T23:41:00+03:00"),  # a minute late
    lambda r: r["EV-RUI"].append(_fault("ch-r8-c1-connector-controller", "2026-10-06T03:00:00+03:00")),  # wrong unit too
    lambda r: r["EV-RUI"].clear(),
])
def test_c6_ev_clauses_fail_on_a_moved_or_misplaced_fault(edit) -> None:
    readings = _ev_faults()
    edit(readings)
    assert not dd_check.judge_failures_at_instant(readings, sites=("EV-KAS", "EV-RUI")).passed


def test_c6_all_sites_by_default() -> None:
    assert not dd_check.judge_failures_at_instant(_ev_faults()).passed  # Thika's clauses have no rows


# --- C-DD7: readings and books agree exactly --------------------------------------------------------------------------

def _charge(code: str, month: str, quantity: str, unit: str, band: str | None = None) -> dict:
    body = {"line_type": "DEMAND" if unit == "kW" else "USAGE"}
    if band:
        body["band"] = band
    return {"kind": "CHARGE", "site_code": code, "clocks": {"recognition_period": month},
            "quantity": {"value": quantity, "unit": unit}, "amount": {"value": "1.00", "currency": "USD"}, "body": body}


SCHEDULE = {"kind": "TARIFF_SCHEDULE", "site_code": "EV-EMB", "clocks": {"effective_from": "2026-07-01"},
            "body": {"bands": [{"band": "OFFPEAK-AM", "from": "00:00", "to": "18:00"},
                               {"band": "PEAK", "from": "18:00", "to": "22:00"},
                               {"band": "OFFPEAK-PM", "from": "22:00", "to": "24:00"}]}}


def _import_kw(t: datetime) -> str:
    if t.hour == 19 and t.minute < 30:
        return "200"
    return "100" if 18 <= t.hour < 22 else "50"


def _ev_import() -> list[dict]:
    rows = day_of("site-meter", "import", _import_kw)
    split = next(i for i, r in enumerate(rows) if r["start"].startswith("2026-10-01T19:00"))
    rows[split:split + 1] = [mean("site-meter", "import", T0 + timedelta(hours=19), "200", minutes=1),
                             mean("site-meter", "import", T0 + timedelta(hours=19, minutes=1), "200", minutes=4)]
    return rows


def _roster(bus: str, required: str) -> dict:
    return {"kind": "FLEET_ROSTER", "site_code": "EV-KAS", "clocks": {"effective_from": "2026-11-01"},
            "body": {"vehicle_ref": bus, "required_kwh": required}}


def _departure(bus: str, met: bool, kwh: str) -> dict:
    return {"kind": "DEPARTURE", "site_code": "EV-KAS",
            "body": {"vehicle_ref": bus, "service_day": "2026-11-01", "block_met": met, "kwh_at_departure": kwh}}


def _books() -> list[dict]:
    return [_charge("COLD-MWEA", "2026-10", "57.600", "kWh"),
            _charge("EV-EMB", "2026-10", "450.000", "kWh", "PEAK"), _charge("EV-EMB", "2026-10", "1000.000", "kWh", "OFFPEAK"),
            _charge("EV-EMB", "2026-10", "200.000", "kW", "DEMAND"), SCHEDULE,
            _roster("EV-KAS-B01", "150.000"), _roster("EV-KAS-B03", "150.000"),
            _departure("EV-KAS-B01", True, "150.000"), _departure("EV-KAS-B03", False, "63.333")]


def _readings() -> dict:
    return {"COLD-MWEA": day_of("compressor-meter", "power", lambda t: "2.400"), "EV-EMB": _ev_import()}


def _meter(rows, readings=None, sites=("COLD-MWEA", "EV-EMB", "EV-KAS"), manifest=None):
    return dd_check.judge_meter_books(manifest or {}, _readings() if readings is None else readings, rows, sites)


def test_c7_readings_and_books_agree_exactly() -> None:
    result = _meter(_books())
    assert result.check == "C-DD7" and result.passed, result.detail
    assert any(p.startswith("mini-grid") for p in result.pending)


@pytest.mark.parametrize("index, edit, words", [
    (0, lambda r: r["quantity"].update(value="57.601"), "COLD-MWEA 2026-10 bill"),
    (1, lambda r: r["quantity"].update(value="449.999"), "EV-EMB 2026-10 PEAK"),
    (3, lambda r: r["quantity"].update(value="199.000"), "EV-EMB 2026-10 DEMAND"),
    (7, lambda r: r["body"].update(block_met=False), "EV-KAS-B01"),
    (8, lambda r: r["body"].update(block_met=True), "EV-KAS-B03"),
    (8, lambda r: r["body"].update(kwh_at_departure="150.001"), "above"),
])
def test_c7_fails_on_one_disagreement(index, edit, words) -> None:
    rows = _books()
    edit(rows[index])
    result = _meter(rows)
    assert not result.passed and any(words in d for d in result.detail), result.detail


def test_c7_a_roster_night_without_its_departure_and_a_book_without_readings_fail() -> None:
    rows = _books()[:-1]
    assert any("EV-KAS-B03" in d and "no departure" in d for d in _meter(rows).detail)
    readings = _readings()
    del readings["EV-EMB"]
    assert not _meter(_books(), readings).passed


def test_c7_prints_the_manifests_figure_beside_the_metered_one(inputs) -> None:
    result = _meter(_books(), manifest=inputs.manifest)
    assert any(line.startswith("info: COLD-MWEA 2026-10 bill 57.600 kWh; M 2650") for line in result.info), result.info


# --- C-DD20: the story directions -------------------------------------------------------------------------------------

def _bill(code, values):
    return [_charge(code, f"2026-{m:02d}", v, "kWh") for m, v in zip((7, 8, 9, 10), values)]


def _story_rows(emb_peak=("100", "110", "120", "130")) -> list[dict]:
    rows = _bill("COLD-MWEA", ("1659.750", "1613.000", "1589.950", "1576.300"))
    rows += _bill("COLD-KIRI", ("1842.405", "1908.075", "2016.711", "2113.603"))
    for m, peak in zip((7, 8, 9, 10), emb_peak):
        rows += [_charge("EV-EMB", f"2026-{m:02d}", peak, "kWh", "PEAK"),
                 _charge("EV-EMB", f"2026-{m:02d}", "200", "kWh", "OFFPEAK")]
    return rows


CRATE_DAYS = {"COLD-MWEA": {"2026-07": 6944, "2026-08": 6076, "2026-09": 5040, "2026-10": 4340},
              "COLD-KIRI": {"2026-07": 9796, "2026-08": 10044, "2026-09": 9600, "2026-10": 9920}}


def test_c20_crate_days_are_the_checkers_own_read_of_history_and_m(inputs) -> None:
    assert {k: v for k, v in dd_check.crate_days_of(inputs).items() if k in CRATE_DAYS} == CRATE_DAYS


def test_c20_directions_hold_and_the_mini_grid_clauses_stay_pending() -> None:
    result = dd_check.judge_story_directions(_story_rows(), CRATE_DAYS)
    assert result.check == "C-DD20" and result.passed, result.detail
    assert [p.split()[0] for p in result.pending] == ["KISIWA-001", "MTO-001"]


@pytest.mark.parametrize("rows, crates, words", [
    (_story_rows(("100", "110", "110", "130")), CRATE_DAYS, "EV-EMB peak share"),
    ([r for r in _story_rows() if not (r["site_code"] == "COLD-KIRI" and r["clocks"]["recognition_period"] == "2026-09")],
     CRATE_DAYS, "COLD-KIRI"),
    (_story_rows(), {**CRATE_DAYS, "COLD-MWEA": {**CRATE_DAYS["COLD-MWEA"], "2026-10": 9000}}, "COLD-MWEA"),
])
def test_c20_a_direction_that_does_not_hold_fails(rows, crates, words) -> None:
    result = dd_check.judge_story_directions(rows, crates)
    assert not result.passed and any(words in d for d in result.detail), result.detail


def test_c5_c7_c20_are_live() -> None:
    assert {"C-DD5", "C-DD7", "C-DD20"} <= set(dd_check.LIVE) and not {"C-DD5", "C-DD7", "C-DD20"} & set(dd_check.STUBS)
