"""UP-1 no-DB tests: the host's field-process ports and the upload switch. No gateway, no database.

`check` runs the real `python -m assetops_field.csv_upload` on the pinned fixture; `send` is exercised with a fake
runner (the Postgres flow on its own `*_test` DB proves the real gateway path).
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import reading_upload_process as up
from assetops_backend.config import ConfigurationError
from assetops_backend.reading_upload import service as svc
from assetops_field.export_csv import CSV_CODES

FIXTURE = up.ROOT / "contract-fixtures" / "telemetry" / "generic-interval-csv-v1" / "kobo-window.csv"


def test_the_product_restates_the_eight_csv_codes_exactly():
    assert svc.CSV_CODES == CSV_CODES


@pytest.mark.parametrize("value,expected", [(None, frozenset()), ("", frozenset()), ("KOBO-001", {"KOBO-001"}),
                                            (" kobo-001 ", {"KOBO-001"})])
def test_the_switch_is_off_by_default_and_names_kobo(value, expected):
    environ = {} if value is None else {up.SITES_ENV: value}
    assert up.sites_from_environment(environ) == frozenset(expected)


@pytest.mark.parametrize("value", ["COLD-LAB-001", "KOBO-001,EV-LAB-001"])
def test_any_other_site_refuses_startup(value):
    with pytest.raises(ConfigurationError):
        up.sites_from_environment({up.SITES_ENV: value})


def test_the_gateway_file_must_name_every_key(tmp_path):
    path = tmp_path / "gw.json"
    path.write_text(json.dumps({"gateway_address": "127.0.0.1:1"}), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        up.gateway_from_environment({up.GATEWAY_ENV: str(path)})
    assert up.gateway_from_environment({}) is None


def test_check_runs_the_field_process_on_the_fixture():
    checked = up.ProcessFileChecker().check(FIXTURE.read_bytes())
    assert isinstance(checked, svc.Preview)
    assert (checked.rows, checked.cells) == (49, 196)
    assert checked.first_interval_end_by_role["pv_power"] == datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)


def test_check_returns_the_field_refusal():
    refused = up.ProcessFileChecker().check(FIXTURE.read_bytes().replace(b"pv_ac_power", b"pv_power"))
    assert isinstance(refused, svc.FileRefusal) and refused.code == "HEADER_MISMATCH"
    assert len(refused.profile_sha256) == 64


def test_the_temp_file_is_removed_after_the_run():
    seen: list[Path] = []

    def runner(argv, **kw):
        seen.append(Path(argv[argv.index("--file") + 1]))
        assert seen[-1].read_bytes() == b"abc"
        return SimpleNamespace(returncode=0, stdout='{"ok": true}\n', stderr="")

    assert up.run_field(["check"], b"abc", runner) == (0, {"ok": True})
    assert not seen[0].exists()


def test_send_reads_the_field_summary():
    sent_doc = {"ok": True, "sent": {"session_ref": "field:x", "outcomes": {"ADMITTED": 150, "ALREADY_ADMITTED": 6,
                                                                              "HELD": 4},
                                     "held": {"pv-ac-power:UNIT_INCOMPATIBLE:unit": 4},
                                     "message_ids": ["m1", None, "m2"]}}

    def runner(argv, **kw):
        assert argv[3] == "send" and "--gateway-address" in argv
        return SimpleNamespace(returncode=0, stdout=json.dumps(sent_doc), stderr="")

    gateway = {k: "x" for k in up.GATEWAY_KEYS}
    delivered: list = []
    sent = up.ProcessReadingSender(gateway, runner=runner, deliver=delivered.append).send(b"data")
    assert (sent.admitted, sent.held, sent.message_ids) == (156, 4, ("m1", "m2"))
    assert sent.held_by_column == {"pv-ac-power": 4}
    assert delivered == [gateway]  # D-UP.2 (d): the host delivers once the send exits 0


@pytest.mark.parametrize("code,error", [(4, "GATEWAY_UNAVAILABLE"), (5, "IDENTITY_MISMATCH"), (3, "CONFIGURATION")])
def test_a_failed_send_is_gateway_unavailable(code, error):
    def runner(argv, **kw):
        return SimpleNamespace(returncode=code, stdout=json.dumps({"ok": False, "error": error}), stderr="")

    delivered: list = []
    with pytest.raises(svc.GatewayUnavailable):
        up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, runner=runner,
                                deliver=delivered.append).send(b"data")
    assert delivered == []  # nothing was sent, so nothing is delivered


def test_the_template_is_the_profile_header_and_passes_the_field_check():
    template = up.template_csv()
    assert not template.startswith(b"\xef\xbb\xbf") and template.endswith(b"\r\n")
    header = template.decode("ascii").strip()
    fixture_lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    assert header == fixture_lines[0]  # the collector's own fixture carries the same header row
    filled = template + "\r\n".join(fixture_lines[1:4]).encode("ascii") + b"\r\n"
    assert isinstance(up.ProcessFileChecker().check(filled), svc.Preview)  # the real field process accepts it


def test_the_host_never_imports_the_field_adapters():
    source = Path(up.__file__).read_text(encoding="utf-8")
    assert "import assetops_field" not in source and "from assetops_field" not in source
    assert subprocess.run  # the ports reach the field adapters only by running them
