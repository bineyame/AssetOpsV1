"""UP-1 focused tests: the reading-upload process (`assetops_field.csv_upload`). No gateway, no database.

The checked-in Kobo profile and the pinned TEL-06 fixture are used, so the preview is the one the API will show.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import FakeLink  # noqa: E402

from assetops_field import csv_upload  # noqa: E402
from assetops_field.export_csv import CSV_CODES, CsvRefused  # noqa: E402
from assetops_field.profile import load_profile  # noqa: E402
from assetops_field.publish import GatewayPublisher  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
FIXTURE = ROOT / "contract-fixtures" / "telemetry" / "generic-interval-csv-v1" / "kobo-window.csv"
PROFILE = load_profile(PROFILE_PATH)
HEADER = ("timestamp_utc,pv_ac_power [kW],clinic_feeder_power [kW],mill_feeder_power [kW],"
          "residential_feeder_power [kW]")
GOOD = HEADER + "\n2026-11-17T00:15:00Z,,1.5,0,2\n2026-11-17T00:30:00Z,0.25,1.25,0,2.125\n"
RELEASED = {"released_batch_ids": ["b1"], "released_now": 1, "delivery": {"pending": 0}}

#: One file per refusal code; each must be refused with that code by `check` (exit 2) and admit nothing.
REFUSED_FILES: dict[str, bytes] = {
    "ENCODING": b"\xef\xbb\xbf" + GOOD.encode("utf-8"),
    "EMPTY_FILE": (HEADER + "\n").encode("utf-8"),
    "HEADER_MISMATCH": GOOD.replace("pv_ac_power", "pv_power").encode("utf-8"),
    "INVALID_TIMING": GOOD.replace("2026-11-17T00:15:00Z", "2026-11-17T00:15:00").encode("utf-8"),
    "SPAN_MISMATCH": GOOD.replace("00:15:00Z", "00:10:00Z").encode("utf-8"),
    "DUPLICATE_ROW": GOOD.replace("00:30:00Z", "00:15:00Z").encode("utf-8"),
    "UNSORTED_ROWS": GOOD.replace("00:30:00Z", "00:00:00Z").encode("utf-8"),
    "INVALID_VALUE": GOOD.replace("1.25", "1,25").encode("utf-8"),
}


def _write(tmp_path: Path, data: bytes, name: str = "upload.csv") -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _run(capsys, *argv: str) -> tuple[int, dict]:
    code = csv_upload.main(list(argv))
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 1, lines
    return code, json.loads(lines[0])


def test_preview_of_the_pinned_fixture_counts_rows_columns_and_blanks():
    data = FIXTURE.read_bytes()
    p = csv_upload.preview(PROFILE, data)
    assert p["file_sha256"] == hashlib.sha256(data).hexdigest() and p["profile_sha256"] == PROFILE.sha256
    assert (p["rows"], p["cells"], p["span_seconds"]) == (49, 196, 900)
    assert p["period_start"] == "2026-09-30T02:45:00Z" and p["period_end"].startswith("2026-09-30T15:")
    assert [c["column"] for c in p["columns"]] == ["pv_ac_power", "clinic_feeder_power", "mill_feeder_power",
                                                   "residential_feeder_power"]
    assert all(c["blanks"] >= 1 and "2026-09-30T03:00:00Z" in c["blank_times"] for c in p["columns"])
    assert p["readings"] + p["blanks"] == p["cells"]
    assert p["first_interval_end_by_role"] == {"feeder_demand": "2026-09-30T03:00:00Z",
                                               "pv_power": "2026-09-30T03:00:00Z"}
    assert all(c["unit_matches"] for c in p["columns"])


def test_preview_flags_a_wrong_unit_without_refusing_it():
    p = csv_upload.preview(PROFILE, GOOD.replace("pv_ac_power [kW]", "pv_ac_power [W]").encode("utf-8"))
    pv = p["columns"][0]
    assert (pv["column"], pv["unit"], pv["profile_unit"], pv["unit_matches"]) == ("pv_ac_power", "W", "kW", False)


@pytest.mark.parametrize("code", CSV_CODES)
def test_check_refuses_each_csv_code_with_exit_2(tmp_path, capsys, code):
    exit_code, doc = _run(capsys, "check", "--profile", str(PROFILE_PATH), "--file",
                          str(_write(tmp_path, REFUSED_FILES[code])))
    assert exit_code == csv_upload.EXIT_REFUSED and doc["ok"] is False
    assert doc["refusal"]["code"] == code and doc["refusal"]["profile_sha256"] == PROFILE.sha256


def test_every_csv_code_has_a_refused_file():
    assert set(REFUSED_FILES) == set(CSV_CODES)


def test_check_prints_the_preview_and_touches_no_gateway(tmp_path, capsys):
    exit_code, doc = _run(capsys, "check", "--profile", str(PROFILE_PATH), "--file",
                          str(_write(tmp_path, GOOD.encode("utf-8"))))
    assert exit_code == 0 and doc["ok"] is True
    assert (doc["preview"]["rows"], doc["preview"]["readings"], doc["preview"]["blanks"]) == (2, 7, 1)
    assert "sent" not in doc


def test_the_dry_run_collector_has_no_channel():
    with pytest.raises(AssertionError):
        csv_upload._NoGateway().call("admit", {})


def test_a_missing_file_is_a_configuration_refusal(tmp_path, capsys):
    exit_code, doc = _run(capsys, "check", "--profile", str(PROFILE_PATH), "--file", str(tmp_path / "nope.csv"))
    assert exit_code == csv_upload.EXIT_CONFIG and doc["error"] == "CONFIGURATION"


def test_send_admits_in_file_order_and_names_each_held_column(tmp_path):
    def admit(body):
        answers = []
        for i, text in enumerate(body["reports"]):
            held = '"device_id":"pv-inverter-controller"' in text.replace(" ", "")
            answers.append({"outcome": "HELD", "kind": "UNIT_INCOMPATIBLE", "field": "unit"} if held
                           else {"outcome": "ADMITTED", "message_id": f"m{i}"})
        return {"admissions": answers}

    link = FakeLink({"admit": admit, "seal": {"batch_ids": ["b1"]}, "release_run": RELEASED})
    publisher = GatewayPublisher(link, "0" * 64, "field:generic-interval-csv-illustrative-1:1:20261117T000000Z:0a1b2c3d",
                                 {})
    sent = csv_upload.send(PROFILE, _write(tmp_path, GOOD.replace("[kW]", "[W]", 1).encode("utf-8")), publisher)
    assert link.ops == ["admit", "seal", "release_run"]
    assert sent["report_count"] == 8 and sent["outcomes"] == {"ADMITTED": 6, "HELD": 2}
    assert sent["held"] == {"pv-ac-power:UNIT_INCOMPATIBLE:unit": 2}
    assert sent["batch_ids"] == ["b1"] and sent["seal_refused"] is None


def test_send_never_admits_a_refused_file(tmp_path):
    link = FakeLink({})
    publisher = GatewayPublisher(link, "0" * 64, "ref", {})
    with pytest.raises(CsvRefused):
        csv_upload.send(PROFILE, _write(tmp_path, REFUSED_FILES["DUPLICATE_ROW"]), publisher)
    assert link.calls == []
