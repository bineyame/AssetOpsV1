"""DIESEL-K5 L0 (`.agent/build-sheet-DIESEL-1.md` §9l.2 A1-A7): the Fuel page's night-mode wording, with no database.
Every "must fail" names the mutation it kills."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

import pytest

from assetops_backend.actions.verification_rules import fmt
from assetops_backend.fuel_balance import finding_text as ft
from assetops_backend.fuel_balance import night_text as nt
from assetops_backend.fuel_balance.model import REASONS, STATES, FuelBalanceWindow, FuelFinding

REPO = Path(__file__).resolve().parents[2]
PROBE = json.loads((REPO / ".agent" / "DIESEL-F0" / "probe-result.json").read_text(encoding="utf-8"))
TZ = "Africa/Dar_es_Salaam"
SFC = Fraction("0.355")
FORBIDDEN = ("theft", "stolen", "stole", "siphon", "pilfer")
GAP = ((datetime(2026, 10, 4, 21, 45, tzinfo=timezone.utc), datetime(2026, 10, 4, 23, 30, tzinfo=timezone.utc)),)


@dataclass(frozen=True)
class Rec:
    """The `work.fuel_records.FuelRecord` fields the night text reads."""
    root_id: str
    code: str
    kind: str
    occurred_at: datetime
    quantity_l: Decimal


def probe_window(index: int, *, records=(), spans=(), limitations=(), idle_seconds: int = 0,
                 state: str | None = None, reason: str | None = None, band=None) -> FuelBalanceWindow:
    """Night `index + 1` of F0's committed readings (exact), with a = 10 and SFC 0.355."""
    night = PROBE["nights"][index]
    r = night["readings"]
    use_low = Fraction(r["use_low"]["exact"])
    loaded = use_low / Fraction(9, 10)
    opening = Fraction(night["opening_reading_l"]["exact"])
    closing = Fraction(night["closing_reading_l"]["exact"])
    d = date.fromisoformat(night["window_local"][:10])
    start = datetime(d.year, d.month, d.day, 15, tzinfo=timezone.utc)
    low, high = band if band is not None else (Fraction(r["residual_low"]["exact"]), Fraction(r["residual_high"]["exact"]))
    terms = {"opening_l": fmt(opening), "opening_at": start.isoformat(), "closing_l": fmt(closing),
             "closing_at": (start + timedelta(hours=18)).isoformat(),
             "deliveries_l": r["deliveries"]["exact"], "generator_kwh": fmt(loaded / SFC),
             "loaded_litres": fmt(loaded), "idle_seconds": idle_seconds, "use_low": r["use_low"]["exact"],
             "use_high": r["use_high"]["exact"], "accuracy_l": "10", "sfc_l_per_kwh": "0.355",
             "no_load_l_per_h": "4.9"}
    gap = sum(int((b - a).total_seconds() // 60) for a, b in spans)
    return FuelBalanceWindow(
        id=uuid4(), tenant_id=uuid4(), site_id=uuid4(), tank_asset_id=uuid4(), generator_asset_id=uuid4(),
        night_date=d, window_start=start, window_end=start + timedelta(hours=18), revision=1,
        parameter_version="fuel-balance-1/v1", recorded_at=start + timedelta(hours=19),
        state=state or r["state"], reason=reason, residual_low=low, residual_high=high, gap_minutes=gap,
        gap_spans=tuple(spans), limitations=tuple(limitations), terms=terms, evidence_ids=("e1", "e2", "e3"),
        record_ids=tuple((x.root_id, x.root_id) for x in records), input_sha256="a" * 64)


def card(view, key):
    return next(c for c in view["cards"] if c["key"] == key)


def row(view, term):
    return next(b for b in view["bridge"] if b["term"] == term)


# --- A1 -------------------------------------------------------------------------------------------------------


def test_a1_night4_residual_status_and_use_note() -> None:
    view = nt.night_view(probe_window(3, spans=GAP, limitations=("REPORTING_GAP",)), [], TZ)
    assert card(view, "RESIDUAL")["value"] == "95.7–144.3 L"
    assert view["status"] == nt.STATUS["UNEXPLAINED"] and view["tone"] == "amber"
    assert card(view, "RESIDUAL")["note"] == nt.RESIDUAL_NOTE["UNEXPLAINED"]
    assert card(view, "USE")["note"] == "Modelled: 122.3 kWh × 0.355 L/kWh, 10 % either way"
    assert card(view, "USE")["note"] == nt.USE_NOTE.format(kwh="122.3", sfc="0.355")
    assert view["label"] == "Night of 4 Oct · 6 pm to noon"
    assert [c["label"] for c in view["cards"]] == ["Opening evidence", "Recorded deliveries",
                                                    "Modelled expected use", "Residual"]
    assert [b["label"] for b in view["bars"]] == ["Opening tank", "+ Deliveries", "− Modelled generator use",
                                                   "− Closing tank", "= Unexplained"]


def test_a1_litres_round_half_even_not_half_up() -> None:
    """Must fail if litres round half-up: [1.25, 2.35] gives "1.2–2.4" (half-up would give "1.3–2.4")."""
    view = nt.night_view(probe_window(3, band=(Fraction("1.25"), Fraction("2.35")), state="BELOW_MATERIALITY"), [],
                         TZ)
    assert card(view, "RESIDUAL")["value"] == "1.2–2.4 L"


# --- A2 -------------------------------------------------------------------------------------------------------


def test_a2_night2_delivery_and_night1_none() -> None:
    delivery = Rec("r-1", "REC-000002", "FUEL_DELIVERY", datetime(2026, 10, 2, 17, tzinfo=timezone.utc),
                   Decimal("300"))
    view = nt.night_view(probe_window(1, records=[delivery]), [delivery], TZ)
    assert card(view, "DELIVERIES")["value"] == "300 L"
    assert card(view, "DELIVERIES")["note"] == nt.DELIVERIES_NOTE_ONE
    assert row(view, "DELIVERIES")["basis"] == "1 delivery record"
    assert row(view, "DELIVERIES")["value"] == "300 L" and row(view, "DELIVERIES")["evidence_count"] == 1
    assert view["records"] == [{"code": "REC-000002", "kind": "Fuel delivery", "when": "20:00, 2 Oct",
                                "volume": "300 L", "occurred_at": delivery.occurred_at.isoformat()}]
    none = nt.night_view(probe_window(0), [], TZ)
    assert card(none, "DELIVERIES")["value"] == nt.DELIVERIES_NONE
    assert card(none, "DELIVERIES")["note"] == "Absence of record does not prove none occurred"
    assert row(none, "DELIVERIES")["basis"] == nt.DELIVERIES_BASIS_NONE


# --- A3 -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("state", [s for s in STATES if s != "NOT_ASSESSED"])
def test_a3_each_assessed_state(state: str) -> None:
    view = nt.night_view(probe_window(0, state=state), [], TZ)
    assert (view["status"], view["tone"]) == (nt.STATUS[state], nt.STATUS_TONE[state])
    assert card(view, "RESIDUAL")["note"] == nt.RESIDUAL_NOTE[state]
    assert nt.NOT_CHECKED.split(":")[0] not in " ".join(view["notes"])


@pytest.mark.parametrize("reason", REASONS)
def test_a3_not_assessed_each_reason(reason: str) -> None:
    view = nt.night_view(probe_window(0, state="NOT_ASSESSED", reason=reason, band=(None, None)), [], TZ)
    assert view["status"] == nt.STATUS["NOT_ASSESSED"] and view["tone"] == "neutral"
    assert card(view, "RESIDUAL")["value"] == nt.CANNOT_COMPUTE and card(view, "RESIDUAL")["word"] is True
    expected = nt.NOT_CHECKED.format(why=nt.FUEL_REASON_WORDS[reason])
    assert card(view, "RESIDUAL")["note"] == expected and view["notes"][-1] == expected
    assert row(view, "RESIDUAL")["value"] == nt.CANNOT_COMPUTE


def test_a3_notes_fixed_order() -> None:
    w = probe_window(3, spans=GAP, state="NOT_ASSESSED", reason="MISSING_CLOSING", band=(None, None),
                     limitations=("REPORTING_GAP", "DIP_SENSOR_CONFLICT", "DELIVERY_RECORDED_LATE"))
    assert nt.night_view(w, [], TZ)["notes"] == [ft.gap_line(GAP, TZ), nt.DIP_CONFLICT, nt.DELIVERY_LATE,
                                                 nt.NOT_CHECKED.format(why="no tank reading at noon")]


# --- A4 -------------------------------------------------------------------------------------------------------


def test_a4_idle_note_only_with_idle_seconds() -> None:
    assert card(nt.night_view(probe_window(0, idle_seconds=0), [], TZ), "USE")["note"].startswith("Modelled: ")
    assert "idle" not in card(nt.night_view(probe_window(0, idle_seconds=0), [], TZ), "USE")["note"]
    idle = card(nt.night_view(probe_window(0, idle_seconds=1500), [], TZ), "USE")["note"]
    assert idle == "Modelled: 122.3 kWh × 0.355 L/kWh plus 25 min idle at 4.9 L/h, 10 % either way"


def test_a4_every_visible_value_is_a_string() -> None:
    view = nt.night_view(probe_window(3, spans=GAP), [], TZ)
    for item in view["cards"] + view["bridge"]:
        assert isinstance(item["value"], str)
    assert all(isinstance(b["text"], str) for b in view["bars"])


def test_a4_records_volume_whole_litres_and_dip_kind() -> None:
    dip = Rec("r-9", "REC-000009", "TANK_DIP", datetime(2026, 10, 5, 4, tzinfo=timezone.utc), Decimal("706"))
    half = Rec("r-8", "REC-000008", "TANK_DIP", datetime(2026, 10, 5, 3, tzinfo=timezone.utc), Decimal("705.25"))
    rows = nt.night_view(probe_window(3), [dip, half], TZ)["records"]
    assert [(r["code"], r["kind"], r["when"], r["volume"]) for r in rows] == [
        ("REC-000008", "Tank dip", "06:00, 5 Oct", "705.2 L"), ("REC-000009", "Tank dip", "07:00, 5 Oct", "706 L")]


# --- A5 -------------------------------------------------------------------------------------------------------


def _samples() -> list[str]:
    return [*nt.LITERALS, nt.night_label(date(2026, 10, 4)), nt.not_checked("MISSING_OPENING"),
            nt.USE_NOTE.format(kwh="122.3", sfc="0.355"),
            nt.USE_NOTE_IDLE.format(kwh="122.3", sfc="0.355", m=25, r="4.9"),
            nt.DELIVERIES_NOTE_MANY.format(n=2), nt.OPENING_NOTE.format(hh_mm="18:00"),
            nt.RECORD_WHEN.format(hh_mm="07:00", date="5 Oct"),
            nt.VERSION_ROW.format(n=1, lifecycle=nt.LIFECYCLE["SUPPORTED"], hh_mm="16:00", date="5 Oct"),
            nt.FUEL_CHECKS_ROW.format(title=ft.TITLE, date="4 Oct", lo="95.7", hi="144.3")]


def test_a5_no_forbidden_word() -> None:
    for text in _samples():
        assert not any(word in text.lower() for word in FORBIDDEN), text


def test_a5_guard_v_patterns_pass() -> None:
    from test_out_b2_vocabulary import _patterns

    patterns = _patterns()
    hits = sorted({(text, name) for text in _samples() for name, pattern in patterns if pattern.search(text)})
    assert hits == []


def test_a5_literals_join_the_vocabulary_scan() -> None:
    from test_out_b2_vocabulary import _constants

    scanned = set(_constants())
    assert nt.FINDING_NOT_RAISED.strip(" ·") in scanned and nt.DIP_CONFLICT in scanned


# --- A6 / A7 (phase B) ----------------------------------------------------------------------------------------


def test_a6_margin_and_gap_lines_are_k4a_output() -> None:
    view = nt.night_view(probe_window(3, spans=GAP, limitations=("REPORTING_GAP",)), [], TZ)
    assert view["notes"][0] == ft.gap_line(GAP, TZ) == "The tank sensor sent no readings from 00:45 to 02:30."
    assert view["margin"] == ft.margin_line("10")
    assert nt.litres1 is ft.litres1 and nt.short_day is ft.short_day


def test_a7_fuel_checks_row_for_night4() -> None:
    w = probe_window(3, spans=GAP)
    ff = FuelFinding(uuid4(), uuid4(), 1, "SUPPORTED", w.night_date, w, None, w.recorded_at)
    assert nt.fuel_checks_row(ff) == "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L"
