"""Freshness of the pinned field-observation JSONL (TEL-03, TEL-05b). Light: no gateway, no database (Q-T45, Q-T68)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_observation_fixtures import (  # noqa: E402
    DAYTIME_DIR, PROLONGED_DIR, ROOT, daytime_run, prolonged_run, write_fixture,
)

from assetops_field.profile import load_profile  # noqa: E402

PROFILE_1 = ROOT / "field" / "profiles" / "gx-system-illustrative-1.json"
PROFILE_2 = ROOT / "field" / "profiles" / "gx-system-illustrative-2.json"
PUBLIC_KEYS = frozenset({"device_id", "signal_id", "reading_class", "source_sample_time", "outcome", "reported_value",
                         "canonical_unit"})


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


def _assert_fresh(tmp_path, directory, observations, generator, request):
    manifest = write_fixture(tmp_path, observations, generator=generator, request=request)
    checked_in = (directory / "observations.jsonl").read_bytes()
    assert (tmp_path / "observations.jsonl").read_bytes() == checked_in
    assert (tmp_path / "manifest.json").read_bytes() == (directory / "manifest.json").read_bytes()
    assert manifest["sha256"] == hashlib.sha256(checked_in).hexdigest()
    assert b"\r" not in checked_in and checked_in.endswith(b"\n") and not checked_in.endswith(b"\n\n")
    lines = checked_in.decode("utf-8").splitlines()
    assert len(lines) == manifest["observation_count"]
    assert {frozenset(json.loads(line)) for line in lines} == {PUBLIC_KEYS}
    return manifest


def test_prolonged_fixture_is_fresh_and_profile_2_matches_the_run_and_its_snapshot(tmp_path):
    observations, reporting, request, draft = prolonged_run()
    manifest = _assert_fresh(tmp_path, PROLONGED_DIR, observations, "generate_prolonged_fixture", request)
    assert manifest["publication_profile"] == "registered-kobo-publication:4"
    assert manifest["window"] == {"start": "2026-10-13T03:00:00Z", "end": "2026-10-13T11:00:00Z"}

    # Spans, cadences and reading classes equal the V4 publication profile's declaration (TEL-05b).
    declared = {(spec.device_id, spec.signal_id): spec for spec in reporting.signals}
    profile = load_profile(PROFILE_2)
    assert profile.status == "ILLUSTRATIVE"
    for row in profile.rows:
        spec = declared[(row.device_id, row.signal_id)]
        assert row.reading_class == spec.reading_class, row.row_id
        assert row.cadence_seconds == spec.cadence_minutes * 60, row.row_id
        assert row.source_unit == spec.canonical_unit, row.row_id
        if row.reading_class == "INTERVAL_SIGNAL":
            assert row.span_seconds == spec.cadence_minutes * 60, row.row_id

    # Every row binds its role in the snapshot; the enum texts are labels of the status binding's ENUM map
    # (the gateway holds any other value INVALID_ENUM).
    snapshot = json.loads(draft.registered_basis.snapshot_canonical)
    bindings = {(b["device_id"], b["signal_id"]): b for b in snapshot["bindings"]}
    for row in profile.rows:
        assert bindings[(row.device_id, row.signal_id)]["role"] == row.role, row.row_id
    status = next(row for row in profile.rows if row.decode == "ENUM")
    binding = bindings[(status.device_id, status.signal_id)]
    assert binding["conversion"]["kind"] == "ENUM"
    assert set(status.enum_map.values()) <= set(binding["conversion"]["parameters"]["map"])
