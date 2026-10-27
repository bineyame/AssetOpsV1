"""TEL-01 report build: every text round-trips through parse_device_report_text."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import at, gx2_rows, profile_document  # noqa: E402

from assetops_contracts.gateway_report import parse_device_report_text  # noqa: E402

from assetops_field.aggregate import Result  # noqa: E402
from assetops_field.profile import parse_profile  # noqa: E402
from assetops_field.report import build_report, report_key, report_text  # noqa: E402

PROFILE = parse_profile(profile_document())
PV, SOC = PROFILE.rows
PROFILE2 = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE", profile_id="gx-system-illustrative-2"))
END = at("2026-09-30T06:15:00Z")
START = at("2026-09-30T06:00:00Z")


def test_report_key_shape():
    assert report_key(PROFILE, PV, END) == "gx-system-illustrative-1:1:pv-inverter-controller:ac-power:2026-09-30T06:15:00Z"


@pytest.mark.parametrize(
    "row, result, expected",
    [
        (PV, Result("GOOD", None, Fraction(1333, 1000), END, START),
         {"measurement": "INTERVAL_MEAN", "interval_start": "2026-09-30T06:00:00Z", "value": "1.333", "unit": "kW",
          "quality": "GOOD", "unavailable_reason": None}),
        (PV, Result("UNAVAILABLE", "NO_MEASUREMENT", None, END, START),
         {"measurement": "INTERVAL_MEAN", "interval_start": "2026-09-30T06:00:00Z", "value": None,
          "quality": "UNAVAILABLE", "unavailable_reason": "NO_MEASUREMENT"}),
        (PV, Result("UNAVAILABLE", "NO_COMPLETED_INTERVAL", None, END, START),
         {"interval_start": "2026-09-30T06:00:00Z", "unavailable_reason": "NO_COMPLETED_INTERVAL"}),
        (SOC, Result("GOOD", None, Fraction(87), END, None),
         {"measurement": "STATE_AT_INSTANT", "interval_start": None, "value": "87", "unit": "%"}),
        (SOC, Result("UNAVAILABLE", "NO_MEASUREMENT", None, END, None),
         {"measurement": "STATE_AT_INSTANT", "interval_start": None, "value": None}),
    ],
)
def test_build_report_fields_and_round_trip(row, result, expected):
    report = build_report(PROFILE, row, result)
    text = report_text(report)
    assert parse_device_report_text(text) == report
    assert report.source_time == "2026-09-30T06:15:00Z" and report.device_id == row.device_id
    assert report.report_key == report_key(PROFILE, row, END)
    for key, value in expected.items():
        assert getattr(report, key) == value, key


def test_enum_state_text_and_profile_2_rows_round_trip():
    status = PROFILE2.rows[1]
    report = build_report(PROFILE2, status, Result("GOOD", None, "RUNNING", END, None))
    assert report.value == "RUNNING" and report.unit == "state"
    assert parse_device_report_text(report_text(report)) == report
    block = PROFILE2.rows[2]
    report = build_report(PROFILE2, block, Result("GOOD", None, Fraction(-1234567, 1_000_000), END,
                                                  at("2026-09-30T06:10:00Z")))
    assert report.value == "-1.234567"
    assert parse_device_report_text(report_text(report)) == report


def test_an_interval_mean_without_its_span_is_refused():
    with pytest.raises(ValueError):
        build_report(PROFILE, PV, Result("UNAVAILABLE", "NO_MEASUREMENT", None, END, None))
