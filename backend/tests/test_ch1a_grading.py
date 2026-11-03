"""CH-1a L0: pure grading, coverage, period bounds, fingerprint and config loaders."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from assetops_backend.chain import grading
from assetops_backend.chain.grading import (
    COMPLETE,
    LOW,
    NO_DATA,
    NOT_EXPECTED,
    PARTIAL,
    PENDING,
    classify_day,
    coverage_pct,
    covered_seconds,
    input_fp,
    period_bounds,
)
from assetops_backend.chain.composition import load_coverage_policy, load_operating_calendar
from assetops_backend.chain.policy import Bands, ChainConfigError

BANDS = Bands(complete=0.80, partial=0.25)
UTC = timezone.utc


def _t(h: int, m: int = 0, day: int = 31) -> datetime:
    return datetime(2026, 10, day, h, m, tzinfo=UTC)


@pytest.mark.parametrize(
    ("covered", "threshold", "expected"),
    [
        (0, None, NO_DATA),
        (1, None, LOW),
        (2499, None, LOW),
        (2500, None, PARTIAL),
        (7999, None, PARTIAL),
        (8000, None, COMPLETE),
        (10000, None, COMPLETE),
        (9999, 1.0, PARTIAL),
        (10000, 1.0, COMPLETE),
        (7000, 0.7, COMPLETE),
    ],
)
def test_classify_day_band_edges(covered: int, threshold: float | None, expected: str) -> None:
    assert classify_day(True, 10000, covered, False, BANDS, threshold) == expected


def test_classify_day_special_states() -> None:
    assert classify_day(False, 0, 0, False, BANDS, None) == NOT_EXPECTED
    assert classify_day(False, 100, 100, True, BANDS, None) == NOT_EXPECTED
    assert classify_day(True, 100, 100, True, BANDS, None) == PENDING
    assert classify_day(True, 0, 0, False, BANDS, None) == NO_DATA


def test_coverage_pct_rounds_and_caps() -> None:
    assert coverage_pct(86400, 28800) == "33.33"
    assert coverage_pct(3, 2) == "66.67"
    assert coverage_pct(100, 150) == "100.00"
    assert coverage_pct(0, 0) == "0.00"


def test_covered_seconds_overlap_clip_touch() -> None:
    lo, hi = _t(8), _t(10)
    assert covered_seconds([], lo, hi) == 0
    # overlapping intervals are not double counted
    assert covered_seconds([(_t(8), _t(9)), (_t(8, 30), _t(9, 30))], lo, hi) == 5400
    # clipped at both ends
    assert covered_seconds([(_t(7), _t(8, 30)), (_t(9, 45), _t(11))], lo, hi) == 1800 + 900
    # touching intervals join without gap or double count
    assert covered_seconds([(_t(8), _t(9)), (_t(9), _t(10))], lo, hi) == 7200
    # entirely outside
    assert covered_seconds([(_t(5), _t(6)), (_t(10), _t(11))], lo, hi) == 0


def _calendar(tmp_path, sites: dict, default: dict | None = None):
    payload = {
        "schema": "operating-calendar",
        "version": 1,
        "calendar_version": "operating-calendar/test",
        "sites": sites,
        "default": default
        or {"kind": "OPERATING", "label": "x", "days": "ALL", "hours": [{"from": "00:00", "to": "24:00"}]},
    }
    path = tmp_path / "cal.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return load_operating_calendar(path)


def test_period_bounds_addis_utc_tue_only_and_24h(tmp_path) -> None:
    cal = _calendar(
        tmp_path,
        {
            "ADDIS": {"kind": "OPERATING", "label": "x", "days": "ALL",
                      "hours": [{"from": "00:00", "to": "24:00"}], "reason": "r"},
            "EV": {"kind": "LAB_SESSION", "label": "x", "days": ["TUE"],
                   "hours": [{"from": "08:00", "to": "09:00"}], "reason": "r", "source": "s"},
            "COLD": {"kind": "LAB_SESSION", "label": "x", "days": "ALL",
                     "hours": [{"from": "19:00", "to": "20:05"}], "reason": "r", "source": "s"},
        },
    )
    # Addis (UTC+3, no DST): the full local day 31 Oct is 30 Oct 21:00 .. 31 Oct 21:00 UTC.
    lo, hi = period_bounds(cal.entry_for("ADDIS"), "Africa/Addis_Ababa", date(2026, 10, 31), "operating_hours")
    assert (lo, hi) == (_t(21, day=30), _t(21, day=31))
    assert (hi - lo) == timedelta(hours=24)
    lo, hi = period_bounds(cal.entry_for("ADDIS"), "Africa/Addis_Ababa", date(2026, 10, 31), "midday")
    assert (lo, hi) == (_t(9), _t(10))
    lo, hi = period_bounds(cal.entry_for("COLD"), "Africa/Addis_Ababa", date(2026, 10, 31), "operating_hours")
    assert (lo, hi) == (_t(16), _t(17, 5))
    # EV: Tuesday only, UTC. 27 Oct 2026 is a Tuesday, 26 Oct a Monday.
    assert date(2026, 10, 27).weekday() == 1
    lo, hi = period_bounds(cal.entry_for("EV"), "Etc/UTC", date(2026, 10, 27), "operating_hours")
    assert (lo, hi) == (_t(8, day=27), _t(9, day=27))
    assert period_bounds(cal.entry_for("EV"), "Etc/UTC", date(2026, 10, 26), "operating_hours") is None
    # Unknown site falls back to the default 24 h entry.
    lo, hi = period_bounds(cal.entry_for("OTHER"), "Etc/UTC", date(2026, 10, 26), "operating_hours")
    assert hi - lo == timedelta(hours=24)


def test_period_bounds_dst_free_zone_is_stable_all_year(tmp_path) -> None:
    cal = _calendar(tmp_path, {})
    for month in range(1, 13):
        lo, hi = period_bounds(cal.default, "Africa/Addis_Ababa", date(2026, month, 15), "operating_hours")
        assert hi - lo == timedelta(hours=24)
        assert lo.hour == 21


def test_input_fp_stable_under_order_and_sensitive_to_versions() -> None:
    base = input_fp(["b", "a"], "p/1", "c/1", 1, "k@1")
    assert base == input_fp(["a", "b"], "p/1", "c/1", 1, "k@1")
    assert len(base) == 64 and all(ch in "0123456789abcdef" for ch in base)
    variants = {
        input_fp(["a", "b", "c"], "p/1", "c/1", 1, "k@1"),
        input_fp(["a", "b"], "p/2", "c/1", 1, "k@1"),
        input_fp(["a", "b"], "p/1", "c/2", 1, "k@1"),
        input_fp(["a", "b"], "p/1", "c/1", 2, "k@1"),
        input_fp(["a", "b"], "p/1", "c/1", 1, "k@2"),
    }
    assert base not in variants and len(variants) == 5


def test_shipped_policy_and_calendar_load() -> None:
    policy = load_coverage_policy()
    assert policy.policy_version == "coverage-policy/1"
    assert (policy.bands.complete, policy.bands.partial) == (0.80, 0.25)
    assert policy.objective_min_complete_days == 3
    cal = load_operating_calendar()
    assert cal.calendar_version == "operating-calendar/1"
    kobo = cal.entry_for("KOBO-001")
    assert kobo.kind == "OPERATING" and kobo.hours == ((0, 1440),)
    for code in ("COLD-LAB-001", "EV-LAB-001"):
        entry = cal.entry_for(code)
        assert entry.kind == "LAB_SESSION" and entry.source and entry.reason


def _policy_file(tmp_path, **overrides):
    payload = {"schema": "coverage-policy", "version": 1, "policy_version": "p/1",
               "bands": {"complete": 0.8, "partial": 0.25},
               "objective_min_complete_days": 3, "share_of_expected_days": None}
    payload.update(overrides)
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_policy_loader_rejects_invalid(tmp_path) -> None:
    assert load_coverage_policy(_policy_file(tmp_path)).bands.complete == 0.8
    with pytest.raises(ChainConfigError):
        load_coverage_policy(_policy_file(tmp_path, bands={"complete": 0.2, "partial": 0.5}))
    with pytest.raises(ChainConfigError):
        load_coverage_policy(_policy_file(tmp_path, bands={"complete": 1.5, "partial": 0.5}))
    with pytest.raises(ChainConfigError):
        load_coverage_policy(_policy_file(tmp_path, objective_min_complete_days=0))


@pytest.mark.parametrize(
    "entry",
    [
        {"kind": "OPERATING", "label": "x", "days": "ALL", "hours": [{"from": "10:00", "to": "09:00"}], "reason": "r"},
        {"kind": "OPERATING", "label": "x", "days": "ALL", "hours": [{"from": "10:00", "to": "25:00"}], "reason": "r"},
        {"kind": "OPERATING", "label": "x", "days": ["MON", "FUNDAY"], "hours": [{"from": "00:00", "to": "24:00"}], "reason": "r"},
        {"kind": "OPERATING", "label": "x", "days": "ALL", "hours": [{"from": "00:00", "to": "24:00"}]},
        {"kind": "LAB_SESSION", "label": "x", "days": "ALL", "hours": [{"from": "08:00", "to": "09:00"}], "reason": "r"},
        {"kind": "SOMETIMES", "label": "x", "days": "ALL", "hours": [{"from": "08:00", "to": "09:00"}], "reason": "r"},
    ],
    ids=["from-after-to", "bad-hour", "unknown-day", "no-reason", "lab-without-source", "bad-kind"],
)
def test_calendar_loader_rejects_invalid(tmp_path, entry) -> None:
    with pytest.raises(ChainConfigError):
        _calendar(tmp_path, {"S": entry})


def test_grading_module_is_the_only_grade_vocabulary() -> None:
    assert grading.GRADES == (COMPLETE, PARTIAL, LOW, NO_DATA, NOT_EXPECTED, PENDING)
