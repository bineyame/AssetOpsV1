"""TEL-06 focused tests: the illustrative generic interval CSV collector (Q-T65).

The profile here is built in the test from the 0.6 `EXPORT_CSV` rules; it is
not the checked-in profile (its content is an open question, see
`.agent/TEL-06-questions.md` Q1). No gateway, no database.
"""

from __future__ import annotations

import hashlib
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import FakeLink, profile_document  # noqa: E402

from assetops_contracts.gateway_report import parse_device_report_text  # noqa: E402

from assetops_field.export_csv import CSV_CODES, CsvCollector, CsvRefused  # noqa: E402
from assetops_field.profile import parse_profile  # noqa: E402
from assetops_field.publish import GatewayPublisher  # noqa: E402

SOURCE = "assetops-generic-interval-csv/1, an illustrative format defined by AssetOps"
REF = "field:generic-interval-csv-test-1:1:20261028T120000Z:0a1b2c3d"
RELEASED = {"released_batch_ids": ["b1"], "released_now": 1, "delivery": {"pending": 0}}


def _row(row_id: str, device: str, signal: str, role: str, column: str, resolution: str) -> dict[str, Any]:
    return {
        "row_id": row_id, "status": "ILLUSTRATIVE", "source_document": SOURCE,
        "device_id": device, "signal_id": signal, "role": role, "source_unit": "kW",
        "quantity": {"kind": "AC_POWER", "point": "illustrative", "sign": "positive = delivered",
                     "phase_aggregation": "SINGLE_REGISTER"},
        "reading_class": "INTERVAL_SIGNAL", "span_seconds": 900, "cadence_seconds": 900,
        "output_resolution": resolution, "csv": {"column": column},
    }


DOCUMENT = {
    "schema": {"id": "assetops.field-profile", "version": 1},
    "profile_id": "generic-interval-csv-test-1",
    "profile_version": 1,
    "status": "ILLUSTRATIVE",
    "interface": "EXPORT_CSV",
    "source_timestamps": "UTC_Z_REQUIRED",
    "coverage": "ALL_EXPECTED_POLLS",
    "state_skew_max_seconds": 2,
    "rows": [
        _row("pv-ac-output", "pv-inverter-controller", "ac-power", "pv_power", "pv_power", "0.001"),
        _row("feeder-demand", "clinic-meter", "active-power", "feeder_demand", "feeder_demand", "0.01"),
    ],
}
PROFILE = parse_profile(DOCUMENT)
HEADER = "timestamp_utc,pv_power [kW],feeder_demand [kW]"
GOOD_FILE = HEADER + "\n2026-09-30T06:15:00Z,1.234,0.50\n2026-09-30T06:30:00Z,,-0.25\n"


def _collector(link: FakeLink | None = None) -> tuple[CsvCollector, FakeLink]:
    link = link or FakeLink({"admit": lambda body: {"admissions": [
        {"outcome": "ADMITTED", "message_id": f"m{i}"} for i, _ in enumerate(body["reports"])]},
        "seal": {"batch_ids": ["b1"]}, "release_run": RELEASED})
    return CsvCollector(PROFILE, GatewayPublisher(link, "0" * 64, REF, {})), link


def _file(tmp_path: Path, content: str | bytes, name: str = "window.csv") -> Path:
    path = tmp_path / name
    if isinstance(content, str):
        path.write_bytes(content.encode("utf-8"))
    else:
        path.write_bytes(content)
    return path


def _refused(tmp_path: Path, content: str | bytes) -> CsvRefused:
    collector, link = _collector()
    with pytest.raises(CsvRefused) as caught:
        collector.collect(_file(tmp_path, content))
    assert link.calls == [], "a refused file makes no IPC call"
    assert caught.value.profile_sha256 == PROFILE.sha256
    assert PROFILE.sha256 in str(caught.value)
    return caught.value


# --- reports ------------------------------------------------------------------------------------------------


def test_each_cell_is_one_interval_report_ending_at_its_timestamp(tmp_path):
    collector, link = _collector()
    reports = collector.reports(_file(tmp_path, GOOD_FILE))
    assert link.calls == []
    assert [(r.device_id, r.source_time, r.interval_start, r.value, r.quality, r.unavailable_reason)
            for r in reports] == [
        ("pv-inverter-controller", "2026-09-30T06:15:00Z", "2026-09-30T06:00:00Z", "1.234", "GOOD", None),
        ("clinic-meter", "2026-09-30T06:15:00Z", "2026-09-30T06:00:00Z", "0.5", "GOOD", None),
        ("pv-inverter-controller", "2026-09-30T06:30:00Z", "2026-09-30T06:15:00Z", None, "UNAVAILABLE",
         "NO_MEASUREMENT"),
        ("clinic-meter", "2026-09-30T06:30:00Z", "2026-09-30T06:15:00Z", "-0.25", "GOOD", None),
    ]
    assert {r.measurement for r in reports} == {"INTERVAL_MEAN"}
    assert reports[0].report_key.startswith("generic-interval-csv-test-1")
    assert Fraction(reports[1].value) == Fraction("0.50")


def test_a_blank_cell_becomes_unavailable_no_measurement(tmp_path):
    collector, _ = _collector()
    blank = [r for r in collector.reports(_file(tmp_path, GOOD_FILE)) if r.value is None]
    assert [(r.quality, r.unavailable_reason, r.interval_start) for r in blank] == [
        ("UNAVAILABLE", "NO_MEASUREMENT", "2026-09-30T06:15:00Z")]


def test_header_columns_in_any_order_and_crlf_give_the_same_reports(tmp_path):
    collector, _ = _collector()
    swapped = ("timestamp_utc,feeder_demand [kW],pv_power [kW]\r\n"
               "2026-09-30T06:15:00Z,0.50,1.234\r\n2026-09-30T06:30:00Z,-0.25,\r\n")
    assert collector.reports(_file(tmp_path, swapped, "b.csv")) == collector.reports(_file(tmp_path, GOOD_FILE))


def test_the_header_unit_is_passed_through_verbatim_not_compared(tmp_path):
    collector, _ = _collector()
    content = "timestamp_utc,pv_power [W],feeder_demand [kW]\n2026-09-30T06:15:00Z,1234,0.50\n"
    reports = collector.reports(_file(tmp_path, content))
    assert [(r.device_id, r.unit) for r in reports] == [("pv-inverter-controller", "W"), ("clinic-meter", "kW")]


def test_gaps_between_rows_are_allowed_and_publish_nothing_for_the_gap(tmp_path):
    collector, _ = _collector()
    content = HEADER + "\n2026-09-30T06:15:00Z,1,1\n2026-09-30T09:00:00Z,2,2\n"
    assert [r.source_time for r in collector.reports(_file(tmp_path, content))] == [
        "2026-09-30T06:15:00Z", "2026-09-30T06:15:00Z", "2026-09-30T09:00:00Z", "2026-09-30T09:00:00Z"]


# --- collect --------------------------------------------------------------------------------------------------


def test_collect_admits_every_report_in_file_order_then_seals_and_releases(tmp_path):
    collector, link = _collector()
    expected = [r for r in collector.reports(_file(tmp_path, GOOD_FILE))]
    result = collector.collect(_file(tmp_path, GOOD_FILE))
    assert link.ops == ["admit", "seal", "release_run"]
    body = link.calls[0][1]
    assert body["lab_run_ref"] == REF and body["snapshot_sha256"] == "0" * 64
    assert [parse_device_report_text(text) for text in body["reports"]] == expected
    assert link.calls[2][1] == {"lab_run_ref": REF}
    assert result["report_count"] == 4 and len(result["admissions"]) == 4
    assert result["profile_sha256"] == PROFILE.sha256
    assert result["file_sha256"] == hashlib.sha256(GOOD_FILE.encode("utf-8")).hexdigest()
    assert result["session_ref"] == REF
    assert set(result) == {"profile_sha256", "file_sha256", "session_ref", "report_count", "admissions", "sealed"}
    assert result["sealed"]["batch_ids"] == ["b1"]


def test_the_same_file_twice_sends_byte_identical_report_texts(tmp_path):
    collector, link = _collector()
    path = _file(tmp_path, GOOD_FILE)
    collector.collect(path)
    collector.collect(path)
    admits = [body for op, body in link.calls if op == "admit"]
    assert len(admits) == 2 and admits[0] == admits[1]


def test_a_non_csv_profile_is_refused_at_construction():
    modbus = parse_profile(profile_document())
    with pytest.raises(ValueError, match="EXPORT_CSV"):
        CsvCollector(modbus, GatewayPublisher(FakeLink(), "0" * 64, REF, {}))


# --- one focused test per CSV_CODES entry -------------------------------------------------------------------


def test_encoding_a_byte_order_mark_is_refused(tmp_path):
    refused = _refused(tmp_path, b"\xef\xbb\xbf" + GOOD_FILE.encode("utf-8"))
    assert (refused.code, refused.field) == ("ENCODING", "file")


def test_encoding_bytes_that_are_not_utf8_are_refused(tmp_path):
    refused = _refused(tmp_path, GOOD_FILE.encode("utf-8") + b"2026-09-30T06:45:00Z,\xff,1\n")
    assert refused.code == "ENCODING"


@pytest.mark.parametrize("content", ["", HEADER + "\n"])
def test_empty_file_no_data_rows_is_refused(tmp_path, content):
    assert _refused(tmp_path, content).code == "EMPTY_FILE"


@pytest.mark.parametrize("header,field", [
    ("timestamp_utc,pv_output [kW],feeder_demand [kW]", "header[1]"),     # renamed column
    ("timestamp_utc,pv_power [kW]", "header"),                             # missing column
    ("timestamp_utc,pv_power [kW],feeder_demand [kW],extra [kW]", "header[3]"),  # extra column
    ("timestamp_utc,pv_power [kW],pv_power [kW],feeder_demand [kW]", "header[2]"),  # repeated column
    ("timestamp_utc,pv_power kW,feeder_demand [kW]", "header[1]"),         # malformed unit
    ("timestamp_utc,pv_power  [kW],feeder_demand [kW]", "header[1]"),      # two spaces
    ("timestamp_utc,pv_power [],feeder_demand [kW]", "header[1]"),         # empty unit
    ("time,pv_power [kW],feeder_demand [kW]", "header[0]"),                # renamed timestamp column
])
def test_header_mismatch_refuses_the_whole_file_with_no_ipc(tmp_path, header, field):
    refused = _refused(tmp_path, header + "\n2026-09-30T06:15:00Z,1,1\n")
    assert (refused.code, refused.field) == ("HEADER_MISMATCH", field)


@pytest.mark.parametrize("stamp", ["2026-09-30T06:15:00", "2026-09-30T06:15:00+00:00", "2026-09-30 06:15:00Z",
                                   "2026-09-30T06:15:00.000Z", "2026-02-30T06:15:00Z"])
def test_invalid_timing_a_timestamp_without_z_or_off_grammar_is_refused(tmp_path, stamp):
    refused = _refused(tmp_path, HEADER + f"\n{stamp},1,1\n")
    assert (refused.code, refused.field) == ("INVALID_TIMING", "rows[0].timestamp_utc")


def test_span_mismatch_is_refused_not_resampled(tmp_path):
    refused = _refused(tmp_path, HEADER + "\n2026-09-30T06:15:00Z,1,1\n2026-09-30T06:20:00Z,1,1\n")
    assert (refused.code, refused.field) == ("SPAN_MISMATCH", "rows[1].timestamp_utc")


def test_duplicate_row_a_repeated_timestamp_is_refused(tmp_path):
    refused = _refused(tmp_path, HEADER + "\n2026-09-30T06:15:00Z,1,1\n2026-09-30T06:15:00Z,2,2\n")
    assert (refused.code, refused.field) == ("DUPLICATE_ROW", "rows[1].timestamp_utc")


def test_unsorted_rows_are_refused(tmp_path):
    refused = _refused(tmp_path, HEADER + "\n2026-09-30T06:30:00Z,1,1\n2026-09-30T06:15:00Z,2,2\n")
    assert (refused.code, refused.field) == ("UNSORTED_ROWS", "rows[1].timestamp_utc")


@pytest.mark.parametrize("cell", ["1,5", "1 000", "1e3", "+1", ".5", "1.", " 1", "NaN", "0.0005", "１"])
def test_invalid_value_cells_are_refused(tmp_path, cell):
    refused = _refused(tmp_path, HEADER + f'\n2026-09-30T06:15:00Z,"{cell}",1\n')
    assert (refused.code, refused.field) == ("INVALID_VALUE", "rows[0].pv_power")


@pytest.mark.parametrize("content", [
    HEADER + "\n2026-09-30T06:15:00Z,1\n",                                  # too few cells
    HEADER + "\n2026-09-30T06:15:00Z,1,1,1\n",                              # too many cells
    HEADER + "\n2026-09-30T06:15:00Z,1,1\n\n2026-09-30T06:30:00Z,1,1\n",    # blank line inside
    HEADER + "\n2026-09-30T06:15:00Z,1,1\n\n",                              # blank line after the last row
])
def test_invalid_value_a_row_whose_cell_count_differs_from_the_header(tmp_path, content):
    refused = _refused(tmp_path, content)
    assert refused.code == "INVALID_VALUE" and refused.field in ("rows[0]", "rows[1]")
    assert "cells where the header has 3" in refused.detail


def test_invalid_value_not_a_multiple_of_the_row_resolution(tmp_path):
    refused = _refused(tmp_path, HEADER + "\n2026-09-30T06:15:00Z,1,0.505\n")
    assert (refused.code, refused.field) == ("INVALID_VALUE", "rows[0].feeder_demand")


def test_a_late_refusal_still_refuses_the_whole_file(tmp_path):
    rows = "".join(f"2026-09-30T{6 + i // 4:02d}:{(i % 4) * 15:02d}:00Z,1,1\n" for i in range(1, 9))
    refused = _refused(tmp_path, HEADER + "\n" + rows + "2026-09-30T09:00:00Z,x,1\n")
    assert refused.code == "INVALID_VALUE" and refused.field == "rows[8].pv_power"


def test_every_csv_code_has_a_focused_test():
    source = Path(__file__).read_text(encoding="utf-8")
    for code in CSV_CODES:
        assert f"def test_{code.lower()}_" in source, code
    with pytest.raises(ValueError):
        CsvRefused("NOT_A_CODE", "file", "x", PROFILE.sha256)
