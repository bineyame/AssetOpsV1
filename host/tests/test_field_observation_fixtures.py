"""Freshness of the pinned field-observation JSONL (TEL-03). Light: no gateway, no database (Q-T45, Q-T68)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_observation_fixtures import DAYTIME_DIR, ROOT, daytime_run, write_fixture  # noqa: E402

from assetops_field.profile import load_profile  # noqa: E402

PROFILE_1 = ROOT / "field" / "profiles" / "gx-system-illustrative-1.json"


def test_daytime_fixture_is_fresh_and_its_profile_matches_the_run(tmp_path):
    observations, reporting, request = daytime_run()
    manifest = write_fixture(tmp_path, observations, generator="generate_daytime_fixture", request=request)

    checked_in = (DAYTIME_DIR / "observations.jsonl").read_bytes()
    assert (tmp_path / "observations.jsonl").read_bytes() == checked_in
    assert (tmp_path / "manifest.json").read_bytes() == (DAYTIME_DIR / "manifest.json").read_bytes()
    assert manifest["sha256"] == hashlib.sha256(checked_in).hexdigest()
    assert b"\r" not in checked_in and checked_in.endswith(b"\n") and not checked_in.endswith(b"\n\n")

    lines = checked_in.decode("utf-8").splitlines()
    assert len(lines) == manifest["observation_count"]
    assert {frozenset(json.loads(line)) for line in lines} == {frozenset(
        {"device_id", "signal_id", "reading_class", "source_sample_time", "outcome", "reported_value",
         "canonical_unit"})}

    declared = {(spec.device_id, spec.signal_id): spec for spec in reporting.signals}
    profile = load_profile(PROFILE_1)
    for row in profile.rows:
        spec = declared[(row.device_id, row.signal_id)]
        assert row.reading_class == spec.reading_class, row.row_id
        assert row.cadence_seconds == spec.cadence_minutes * 60, row.row_id
        assert row.source_unit == spec.canonical_unit, row.row_id
        if row.reading_class == "INTERVAL_SIGNAL":
            assert row.span_seconds == spec.cadence_minutes * 60, row.row_id
