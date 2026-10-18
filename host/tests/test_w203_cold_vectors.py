"""W2-03 pure-rule replay vectors stay exactly the W2-02 producer's public series.

`backend/tests/fixtures/w2/cold-w203-vectors.json` pins, per W2-02 case, the public v2 reports the registered
cold producer publishes (device, signal, timing, payload, report SHA). The backend pure-rule tests read only
that file; this test re-runs the producer and refuses any drift. Regenerate with
`ASSETOPS_W203_WRITE_VECTORS=1`.
"""

from __future__ import annotations

import hashlib
import json
import os

from test_cold_publication import ROOT, _series

CASES = ("normal", "excursion", "backup-failed", "missing-probe", "late-reading", "contradictory")
VECTORS = ROOT / "backend" / "tests" / "fixtures" / "w2" / "cold-w203-vectors.json"


def _record(report, parsed) -> dict:
    return {
        "report_key": report.report_key,
        "report_sha256": hashlib.sha256(report.report_text.encode("utf-8")).hexdigest(),
        "device_id": parsed.device_id,
        "signal_id": parsed.signal_id,
        "family": parsed.family,
        "record_kind": parsed.record_kind,
        "source_time": parsed.source_time,
        "published_at": report.published_at,
        "quality": parsed.quality,
        "value": parsed.value,
        "unit": parsed.unit,
        "event_id": parsed.event_id,
        "correlation_id": parsed.correlation_id,
        "outcome": parsed.outcome,
    }


def build() -> dict:
    return {"schema": "cold-w203-vectors/1",
            "cases": {case: [_record(r, p) for r, p in _series(case)] for case in CASES}}


def test_vectors_match_the_registered_producer() -> None:
    built = build()
    text = json.dumps(built, indent=1, sort_keys=True) + "\n"
    if os.environ.get("ASSETOPS_W203_WRITE_VECTORS") == "1":
        VECTORS.write_text(text, encoding="utf-8", newline="\n")
    assert VECTORS.read_text(encoding="utf-8") == text
