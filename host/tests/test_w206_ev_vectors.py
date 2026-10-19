"""W2-06 R12 (`.agent/W2-06-build-spec.md` "R12: exact vector artifact (Q1-Q9)"): the producer side rerun.

`backend/tests/fixtures/w2/ev-w206-vectors.json` is written by the W2-05b Postgres replay test from the persisted
publication -> batch -> disposition chain. This test reruns the public transform (`ev_reports`) for each of the six
shipped scenarios and checks every pinned record's report key and report SHA-256 (`sha256(report_text UTF-8)`)
against it, plus the report-side fields the record carries. Every accepted record pairs with exactly one report.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from assetops_backend.scenarios.ev_parsing import parse_ev_scenario_document
from assetops_contracts.gateway_report import parse_device_report_v2_text
from assetops_simulator.packs.ev_charger import DEFAULT_PARAMETERS
from ev_publication import ev_channels, ev_execution, ev_reports

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "backend" / "tests" / "fixtures" / "w2" / "ev-w206-vectors.json"
BINDINGS = json.loads((ROOT / "backend" / "conversions" / "ev-lab-001-bindings.json").read_text("utf-8"))["bindings"]
CASES = ("complete", "interrupted", "fault", "missing-meter", "late-record", "contradictory")
RECORD_KEYS = ("report_key", "report_sha256", "batch_external_id", "ordinal", "accepted_evidence_id",
               "envelope_sha256", "source_time", "interval_start", "interval_end", "connector_id", "session_id",
               "family", "record_kind", "measurement", "quality", "value", "unit", "event_id", "outcome", "asset_id",
               "binding_revision_id", "source_id", "sequence_epoch", "clock_attested", "source_class",
               "binding_set_revision_id", "role", "device_id", "signal_id")
#: Report fields a record carries verbatim (value/unit are the accepted normalized text, compared separately).
SAME = ("source_time", "interval_start", "interval_end", "connector_id", "session_id", "family", "record_kind",
        "measurement", "quality", "event_id", "outcome")


def _pinned() -> dict:
    text = VECTORS.read_text(encoding="utf-8")
    document = json.loads(text)
    assert text == json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert document["schema"] == "ev-w206-vectors/1" and set(document["cases"]) == set(CASES)
    return document


def _reports(case: str):
    path = ROOT / "config" / "scenarios" / f"ev-{case}.yaml"
    definition = parse_ev_scenario_document(yaml.safe_load(path.read_text("utf-8")), source=str(path))
    return ev_reports(definition, ev_channels(BINDINGS), ev_execution(definition, DEFAULT_PARAMETERS))


@pytest.mark.parametrize("case", CASES)
def test_pinned_records_pair_with_rerun_reports(case: str) -> None:
    pinned = _pinned()["cases"][case]
    assert pinned["manifest"] == f"contract-fixtures/w2/ev/{case}.json"
    assert tuple(sorted(pinned)) == ("binding_members", "expected", "first_cutoff", "manifest", "records",
                                     "selected_connector", "window")
    records = pinned["records"]
    by_key = {r.report_key: r for r in _reports(case)}
    keys = [r["report_key"] for r in records]
    assert len(set(keys)) == len(keys), "a report paired with two accepted records"
    assert set(keys) == set(by_key), "every rerun report is accepted exactly once"
    for record in records:
        assert tuple(sorted(record)) == tuple(sorted(RECORD_KEYS))
        report = by_key[record["report_key"]]
        assert record["report_sha256"] == hashlib.sha256(report.report_text.encode("utf-8")).hexdigest()
        parsed = parse_device_report_v2_text(report.report_text)
        assert {k: getattr(parsed, k) for k in SAME} == {k: record[k] for k in SAME}, record["report_key"]
        assert (record["device_id"], record["signal_id"]) == (parsed.device_id, parsed.signal_id)
        if parsed.value is None:
            assert record["value"] is None
        elif parsed.measurement in ("INTERVAL_DELTA", "INTERVAL_MEAN"):
            assert Decimal(record["value"]) == Decimal(parsed.value)
        else:
            assert record["value"] == parsed.value


def test_late_record_first_cutoff_excludes_held_end() -> None:
    held = [r for r in _reports("late-record") if r.held]
    assert len(held) == 1 and json.loads(held[0].report_text)["record_kind"] == "EV_SESSION_END"
    late = _pinned()["cases"]["late-record"]
    [end] = [r for r in late["records"] if r["report_key"] == held[0].report_key]
    assert end["accepted_evidence_id"] not in late["first_cutoff"]["accepted_evidence_ids"]
