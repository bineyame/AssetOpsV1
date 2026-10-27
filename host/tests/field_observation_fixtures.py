"""Generators for the pinned public-observation JSONL fixtures the field emulator replays (TEL-03, Q-T45).

The composition leaf may call `generate_observations` on a registered Kobo
draft; `field/tests` may not (ruling D4), so it reads only the JSONL written
here. Only public `DeviceObservation` fields cross: no run cause, no kernel
state. Run as a script to regenerate the checked-in fixture:

    python host/tests/field_observation_fixtures.py daytime
    python host/tests/field_observation_fixtures.py prolonged

`prolonged` (TEL-05b, amendment 2 item 2) is the registered
`kobo-mini-grid-prolonged` run over 2026-10-13T03:00Z-11:00Z at timestep 5
under `registered-kobo-publication` v4, after the S3 dispatch then the S6
verification demo configurations, built by the `configure()` and `draft()`
of `host/tests/test_s6_verification_publication.py`.
"""

from __future__ import annotations

import hashlib
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

from assetops_contracts.observation import exact_decimal_text  # noqa: E402
from assetops_contracts.source_envelope import canonical_json  # noqa: E402

PROLONGED_DIR = ROOT / "contract-fixtures" / "telemetry" / "kobo-prolonged-public-observations-v1"
DAYTIME_DIR = ROOT / "contract-fixtures" / "telemetry" / "kobo-public-observations-v1"
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


if __name__ == "__main__":
    generators = {"daytime": (generate_daytime_fixture, DAYTIME_DIR),
                  "prolonged": (generate_prolonged_fixture, PROLONGED_DIR)}
    if len(sys.argv) != 2 or sys.argv[1] not in generators:
        raise SystemExit("usage: field_observation_fixtures.py daytime|prolonged")
    generate, directory = generators[sys.argv[1]]
    print(json.dumps(generate(directory), indent=2))
