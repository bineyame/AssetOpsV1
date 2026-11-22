"""D-DD.89 (the Thika incident resized: hand start at 20:22) measured from the writer's own readings, and C-DD6's
Thika clauses (D-DD.121) judged on the same rows.

Thika runs 1 Jul to 7 Oct through `build_telemetry` on the in-process cold books (D-DD.119, D-DD.120). The per-minute
chamber is the pack's own state, captured as the run steps; the 5-minute figures are the written readings. Nothing
here is tuned: a figure that differs from D-DD.89 is a stop for the Architect.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from assetops_simulator.packs import cold as cold_pack
from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.telemetry_cold import cold_books_for

from .books_support import built
from .conftest import REPOSITORY_ROOT

NAIROBI = ZoneInfo("Africa/Nairobi")
DAY = "2026-10-06"
READINGS = f"harvest-cold/telemetry/COLD-THIKA.{DAY}.readings.json"


def _local(hhmm: str) -> datetime:
    return datetime.fromisoformat(f"{DAY}T{hhmm}:00").replace(tzinfo=NAIROBI)


def _thika() -> dict:
    onboarding = json.loads((REPOSITORY_ROOT / "backend/tests/fixtures/on1/harvest-cold.onboarding.json").read_text())
    bindings = {"COLD-THIKA": json.loads(
        (REPOSITORY_ROOT / "backend/conversions/world/COLD-THIKA-bindings.json").read_text())}
    return tel.site_inputs(onboarding, bindings)["sites"][0]


@pytest.fixture(scope="module")
def incident():
    view, history, records, _books = built()
    books = cold_books_for(view, history, records)
    minutes: dict[datetime, tuple[Fraction, str]] = {}
    step = cold_pack.ColdPack.step
    lo, hi = _local("18:00"), _local("23:30")

    def capture(self, state, forcings=(), *, transition=True, start=None):
        tr = step(self, state, forcings, transition=transition, start=start)
        at = tr.after.minute.astimezone(NAIROBI)
        if transition and lo <= at <= hi:
            minutes[at] = (tr.after.temperature, tr.after.bus)
        return tr

    mp = pytest.MonkeyPatch()
    mp.setattr(cold_pack.ColdPack, "step", capture)
    try:
        result = tel.build_telemetry(view, {"sites": [_thika()]}, books, start="2026-07-01", end="2026-10-07")
    finally:
        mp.undo()
    rows = json.loads(dict(result.files)[READINGS])["readings"]
    return minutes, rows


def _excursion(points, limit):
    """The contiguous run of instants above `limit` that holds the peak (ordinary cycling elsewhere is not it)."""
    times = sorted(points)
    peak = max(times, key=lambda t: points[t])
    i = j = times.index(peak)
    while i > 0 and points[times[i - 1]] > limit:
        i -= 1
    while j + 1 < len(times) and points[times[j + 1]] > limit:
        j += 1
    return times[i:j + 1], times[j + 1] if j + 1 < len(times) else None


def _chamber(rows) -> list[tuple[datetime, Decimal]]:
    return [(datetime.fromisoformat(r["start"]), Decimal(r["value"])) for r in rows
            if r["source_id"] == "chamber-probe"]


def test_event_rows_at_their_minutes(incident) -> None:
    _minutes, rows = incident
    events = [(r["start"][11:16], r["source_id"], r["event"]["record_kind"], r["event"]["outcome"], r["event"]["actor"])
              for r in rows if r["unit"] == "event" and r["source_id"] in ("generator-controller", "transfer-controller")]
    starts = [e for e in events if e[2] == "START_RESULT"]
    assert [(e[0], e[3]) for e in starts] == [("19:11", "FAILED"), ("20:22", "SUCCEEDED")]
    assert starts[1][4] == "OPERATOR"
    assert [e[0] for e in events if e[1] == "transfer-controller" and e[0] > "20:22"][0] == "20:23"


def test_per_minute_excursion(incident) -> None:
    minutes, _rows = incident
    chamber = {t: c for t, (c, _b) in minutes.items()}
    above5, _ = _excursion(chamber, 5)
    above4, back = _excursion(chamber, 4)
    peak_at, peak = max(chamber.items(), key=lambda kv: kv[1])
    measured = {"peak": round(float(peak), 3), "peak_at": peak_at.strftime("%H:%M"), "above_5": len(above5),
                "above_5_from_to": (above5[0].strftime("%H:%M"), above5[-1].strftime("%H:%M")),
                "above_4": len(above4), "above_4_from": above4[0].strftime("%H:%M"),
                "above_4_in_window": sum(1 for c in chamber.values() if c > 4),
                "above_4_elsewhere": [t.strftime("%H:%M") for t, c in sorted(chamber.items()) if c > 4 and t not in above4],
                "back_at_or_below_4": back.strftime("%H:%M"),
                "unpowered": sum(1 for _c, b in minutes.values() if b == "UNPOWERED")}
    print("D-DD.89 measured per minute:", measured)
    assert measured == {"peak": 5.477, "peak_at": "20:24", "above_5": 25, "above_5_from_to": ("20:08", "20:32"),
                        "above_4": 79, "above_4_from": "19:33", "above_4_in_window": 82,
                        "above_4_elsewhere": measured["above_4_elsewhere"], "back_at_or_below_4": "20:52", "unpowered": 72}
    # D-DD.89's "above 4 degC 82 minutes" is the count over 18:00-23:30; the excursion itself is 79 (packet deviation)
    assert len(measured["above_4_elsewhere"]) == 3 and all(t > "20:52" for t in measured["above_4_elsewhere"])


def test_five_minute_readings_bound_the_excursion(incident) -> None:
    _minutes, rows = incident
    chamber = _chamber(rows)
    points = dict(chamber)
    above5 = [(t.strftime("%H:%M"), points[t]) for t in _excursion(points, 5)[0]]
    above4 = [t.strftime("%H:%M") for t in _excursion(points, 4)[0]]
    print("D-DD.89 measured 5-minute:", above5, above4[0], above4[-1])
    assert [t for t, _v in above5] == ["20:10", "20:15", "20:20", "20:25", "20:30"]
    assert max(above5, key=lambda tv: tv[1]) == ("20:25", Decimal("5.422"))
    assert ((len(above5) - 1) * 5, (len(above5) + 1) * 5) == (20, 30)  # M's above_limit_minutes "20-30"
    assert (above4[0], above4[-1], len(above4)) == ("19:35", "20:50", 16)  # bound 75-85
    after = next((t, v) for t, v in chamber if t > _local("20:50"))
    assert (after[0].strftime("%H:%M"), after[1]) == ("20:55", Decimal("3.793"))


def _dd_check():
    spec = importlib.util.spec_from_file_location("dd_check", REPOSITORY_ROOT / "tools/dd_check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["dd_check"] = module  # its dataclasses resolve their module
    spec.loader.exec_module(module)
    return module


def test_c_dd6_thika_clauses_live_on_the_writer_rows(incident) -> None:
    _minutes, rows = incident
    dd_check = _dd_check()
    result = dd_check.judge_failures_at_instant({"COLD-THIKA": rows})

    def thika_fails(judged) -> list[str]:  # Kisiwa's and Mto's clauses are judged on their own rows (D-DD.146)
        return [d for d in judged.detail if d.startswith("COLD-THIKA")]
    assert result.check == "C-DD6" and not thika_fails(result), result.detail
    assert [p.split()[0] for p in result.pending] == ["EV-KAS", "EV-RUI"]  # Kisiwa and Mto live (D-DD.146)
    moved = [dict(r) for r in rows]
    for r in moved:  # the failure planted a minute late: the clause fails
        if r["unit"] == "event" and r["event"]["outcome"] == "FAILED":
            r["start"] = r["start"].replace("T19:11", "T19:12")
    assert thika_fails(dd_check.judge_failures_at_instant({"COLD-THIKA": moved}))
    hot = [dict(r, value="12.5") if r["source_id"] == "chamber-probe" and r["start"][11:16] == "20:25" else r
           for r in rows]
    assert thika_fails(dd_check.judge_failures_at_instant({"COLD-THIKA": hot}))
    assert thika_fails(dd_check.judge_failures_at_instant({}))  # no Thika rows
