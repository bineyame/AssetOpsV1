"""Generators for the pinned public-observation JSONL fixtures the field emulator replays (TEL-03, Q-T45).

The composition leaf may call `generate_observations` on a registered Kobo
draft; `field/tests` may not (ruling D4), so it reads only the JSONL written
here. Only public `DeviceObservation` fields cross: no run cause, no kernel
state. Run as a script to regenerate the checked-in fixture:

    python host/tests/field_observation_fixtures.py daytime
    python host/tests/field_observation_fixtures.py prolonged
    python host/tests/field_observation_fixtures.py interval-csv

`prolonged` (TEL-05b, amendment 2 item 2) is the registered
`kobo-mini-grid-prolonged` run over 2026-10-13T03:00Z-11:00Z at timestep 5
under `registered-kobo-publication` v4, after the S3 dispatch then the S6
verification demo configurations, built by the `configure()` and `draft()`
of `host/tests/test_s6_verification_publication.py`.

`interval-csv` (TEL-06, ruling M Q2) writes the illustrative
`assetops-generic-interval-csv/1` file from the checked-in daytime JSONL (no
new simulator run): one row per 15-minute interval end over the whole window,
one column per CSV profile row, each `REPORTED` value rounded half-even once
at the row's `output_resolution`, and a blank cell where nothing was reported.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import json
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts, generate_observations  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_contracts.observation import exact_decimal_text, quantize_half_even  # noqa: E402
from assetops_contracts.source_envelope import canonical_json  # noqa: E402

PROLONGED_DIR = ROOT / "contract-fixtures" / "telemetry" / "kobo-prolonged-public-observations-v1"
DAYTIME_DIR = ROOT / "contract-fixtures" / "telemetry" / "kobo-public-observations-v1"
INTERVAL_CSV_DIR = ROOT / "contract-fixtures" / "telemetry" / "generic-interval-csv-v1"
INTERVAL_CSV_PROFILE = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
INTERVAL_CSV_FORMAT = "assetops-generic-interval-csv/1"
_BLANK_OUTCOMES = ("NO_PRECEDING_INTERVAL", "NO_VALUE_AT_BOUNDARY")
_INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
PUBLIC_FIELDS = ("device_id", "signal_id", "reading_class", "source_sample_time", "outcome", "reported_value",
                 "canonical_unit")


def daytime_run() -> tuple[tuple[Any, ...], Any, dict[str, Any]]:
    """The registered `kobo-daytime` draft executed with no gateway: (observations, reporting, request)."""
    store, _, _ = registered.converted()
    request = registered.request()
    draft = registered.setup_service(store).create_draft_run(request)
    observations, reporting = _execute(draft)
    return observations, reporting, request


def prolonged_draft() -> Any:
    """The registered `kobo-mini-grid-prolonged` draft (in-memory store), as `test_s6_verification_publication`."""
    import test_s6_verification_publication as s6

    store, result, _ = registered.converted()
    s6.configure(store, result)
    run, _ = s6.draft(store)
    return run


def prolonged_run() -> tuple[tuple[Any, ...], Any, dict[str, Any], Any]:
    """The prolonged draft executed with no gateway: (observations, reporting, request, draft)."""
    import test_s6_verification_publication as s6

    draft = prolonged_draft()
    observations, reporting = _execute(draft)
    request = {  # the fields `s6.draft()` sets, for the manifest
        "scenario_id": s6.PROLONGED.scenario_id, "scenario_version": s6.PROLONGED.version.scenario_version,
        "interval": {"start_time": s6.START, "end_time": s6.END}, "timestep_minutes": 5,
        "publication_profile": {"profile_id": s6.V4.publication_profile_id,
                                "profile_version": s6.V4.publication_profile_version},
    }
    return observations, reporting, request, draft


def _execute(draft: Any) -> tuple[tuple[Any, ...], Any]:
    with tempfile.TemporaryDirectory(prefix="assetops-field-fixture-") as work:
        root = Path(work)
        port = HostLabExecution(artifacts=YamlExecutionArtifacts(root), stages=JsonSourceStages(root / "stages"),
                                gateway=None)
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        session = port._sessions[draft.run_id]
        observations = generate_observations(session.execution.boundaries, session.reporting)
        return observations, session.reporting


def public_document(observation: Any) -> dict[str, Any]:
    raw = observation.reported_value
    document = {field: getattr(observation, field) for field in PUBLIC_FIELDS}
    document["reported_value"] = exact_decimal_text(raw) if isinstance(raw, Fraction) else raw
    return document


def write_fixture(out_dir: Path, observations, *, generator: str, request: dict[str, Any]) -> dict[str, Any]:
    documents = sorted((public_document(o) for o in observations),
                       key=lambda d: (d["source_sample_time"], d["device_id"], d["signal_id"]))
    body = "".join(canonical_json(d) + "\n" for d in documents).encode("utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "observations.jsonl").write_bytes(body)
    profile = request["publication_profile"]
    manifest = {
        "generator": f"host/tests/field_observation_fixtures.py:{generator}",
        "scenario": f"{request['scenario_id']}:{request['scenario_version']}",
        "window": {"start": request["interval"]["start_time"], "end": request["interval"]["end_time"]},
        "publication_profile": f"{profile['profile_id']}:{profile['profile_version']}",
        "timestep_minutes": request["timestep_minutes"],
        "observation_count": len(documents),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    (out_dir / "manifest.json").write_bytes((canonical_json(manifest) + "\n").encode("utf-8"))
    return manifest


def generate_daytime_fixture(out_dir: Path) -> dict[str, Any]:
    observations, _, request = daytime_run()
    return write_fixture(out_dir, observations, generator="generate_daytime_fixture", request=request)


def generate_prolonged_fixture(out_dir: Path) -> dict[str, Any]:
    observations, _, request, _ = prolonged_run()
    return write_fixture(out_dir, observations, generator="generate_prolonged_fixture", request=request)


def generate_interval_csv_fixture(out_dir: Path) -> dict[str, Any]:
    """The TEL-06 CSV fixture and its manifest, from the checked-in daytime JSONL (ruling M Q2)."""
    from datetime import datetime, timezone

    from assetops_field.profile import load_profile

    source_path = DAYTIME_DIR / "observations.jsonl"
    source = source_path.read_bytes()
    source_manifest = json.loads((DAYTIME_DIR / "manifest.json").read_text(encoding="utf-8"))
    source_sha256 = hashlib.sha256(source).hexdigest()
    if source_sha256 != source_manifest["sha256"]:
        raise ValueError("the daytime JSONL does not match its manifest")
    profile = load_profile(INTERVAL_CSV_PROFILE)
    signals = [(row.device_id, row.signal_id) for row in profile.rows]
    cells: dict[str, dict[tuple[str, str], str]] = {}
    for line in source.decode("utf-8").splitlines():
        document = json.loads(line)
        signal = (document["device_id"], document["signal_id"])
        if signal not in signals:
            continue
        row = profile.rows[signals.index(signal)]
        instant = document["source_sample_time"]
        if _INSTANT.fullmatch(instant) is None:
            raise ValueError(f"{instant!r} is not a whole-second UTC instant")
        seconds = int((datetime.strptime(instant, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                       - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
        if seconds % row.span_seconds:
            raise ValueError(f"{instant} is not a multiple of {row.span_seconds} s")
        outcome = document["outcome"]
        if outcome == "REPORTED":
            text = exact_decimal_text(quantize_half_even(Fraction(document["reported_value"]), row.output_resolution))
        elif outcome in _BLANK_OUTCOMES:
            text = ""
        else:
            raise ValueError(f"{signal[0]}/{signal[1]} at {instant} is {outcome}; a CSV cannot omit one cell")
        by_signal = cells.setdefault(instant, {})
        if signal in by_signal:
            raise ValueError(f"{signal[0]}/{signal[1]} at {instant} appears twice")
        by_signal[signal] = text
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["timestamp_utc"] + [f"{row.csv.column} [{row.source_unit}]" for row in profile.rows])
    blank = 0
    for instant in sorted(cells):
        if set(cells[instant]) != set(signals):
            raise ValueError(f"{instant} does not carry every profile signal")
        values = [cells[instant][signal] for signal in signals]
        blank += values.count("")
        writer.writerow([instant] + values)
    body = buffer.getvalue().encode("utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "kobo-window.csv").write_bytes(body)
    manifest = {
        "generator": "host/tests/field_observation_fixtures.py:generate_interval_csv_fixture",
        "format": INTERVAL_CSV_FORMAT,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "profile_sha256": profile.sha256,
        "source_fixture": source_path.relative_to(ROOT).as_posix(),
        "source_sha256": source_sha256,
        "scenario": source_manifest["scenario"],
        "publication_profile": source_manifest["publication_profile"],
        "window": source_manifest["window"],
        "rounding": "quantize_half_even at each row's output_resolution",
        "row_count": len(cells),
        "cell_count": len(cells) * len(signals),
        "blank_cell_count": blank,
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    (out_dir / "manifest.json").write_bytes((canonical_json(manifest) + "\n").encode("utf-8"))
    return manifest


if __name__ == "__main__":
    generators = {"daytime": (generate_daytime_fixture, DAYTIME_DIR),
                  "prolonged": (generate_prolonged_fixture, PROLONGED_DIR),
                  "interval-csv": (generate_interval_csv_fixture, INTERVAL_CSV_DIR)}
    if len(sys.argv) != 2 or sys.argv[1] not in generators:
        raise SystemExit("usage: field_observation_fixtures.py daytime|prolonged|interval-csv")
    generate, directory = generators[sys.argv[1]]
    print(json.dumps(generate(directory), indent=2))
