"""Generators for the pinned public-observation JSONL fixtures the field emulator replays (TEL-03, Q-T45).

The composition leaf may call `generate_observations` on a registered Kobo
draft; `field/tests` may not (ruling D4), so it reads only the JSONL written
here. Only public `DeviceObservation` fields cross: no run cause, no kernel
state. Run as a script to regenerate the checked-in fixture:

    python host/tests/field_observation_fixtures.py daytime
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

DAYTIME_DIR = ROOT / "contract-fixtures" / "telemetry" / "kobo-public-observations-v1"
PUBLIC_FIELDS = ("device_id", "signal_id", "reading_class", "source_sample_time", "outcome", "reported_value",
                 "canonical_unit")


def daytime_run() -> tuple[tuple[Any, ...], Any, dict[str, Any]]:
    """The registered `kobo-daytime` draft executed with no gateway: (observations, reporting, request)."""
    store, _, _ = registered.converted()
    request = registered.request()
    draft = registered.setup_service(store).create_draft_run(request)
    with tempfile.TemporaryDirectory(prefix="assetops-field-fixture-") as work:
        root = Path(work)
        port = HostLabExecution(artifacts=YamlExecutionArtifacts(root), stages=JsonSourceStages(root / "stages"),
                                gateway=None)
        port.start(draft)
        assert port.run_to_end(draft).status == "COMPLETED"
        session = port._sessions[draft.run_id]
        observations = generate_observations(session.execution.boundaries, session.reporting)
        return observations, session.reporting, request


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


if __name__ == "__main__":
    if sys.argv[1:] != ["daytime"]:
        raise SystemExit("usage: field_observation_fixtures.py daytime")
    print(json.dumps(generate_daytime_fixture(DAYTIME_DIR), indent=2))
