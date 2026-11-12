"""UP-1 (rev 7 section 7.5): the host's reading-upload ports, each one run of `python -m assetops_field.csv_upload`.

The dependency-direction guard lets only `field/` and `host/tests` import `assetops_field` (TEL-01 ruling D4: field
adapters run as separate processes), so the API never imports the collector: it writes the bytes to a private temp
file and runs the field process, which validates the whole file (`check`) or validates and admits it through the
demo upload gateway's authenticated channel (`send`). Nothing is admitted inside the API process.

Configuration (`ASSETOPS_READING_UPLOAD_GATEWAY`): a JSON file naming `gateway_address`, `ipc_credential`,
`snapshot_sha256` and `expect_identity` (a path), written when the demo upload gateway is started (pre-flight Q2).
Without it the dry run still works and a confirm answers 503 READING_UPLOAD_GATEWAY_UNAVAILABLE.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from assetops_backend.config import ConfigurationError
from assetops_backend.reading_upload.service import (FileRefusal, GatewayUnavailable, Preview, Sent,
                                                     preview_from_document)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
SITES_ENV = "ASSETOPS_READING_UPLOAD_SITES"
GATEWAY_ENV = "ASSETOPS_READING_UPLOAD_GATEWAY"
#: D-17N.5: Kobo is the only Site with a CSV profile; any other code in the switch refuses startup.
SUPPORTED_SITES = frozenset({"KOBO-001"})
GATEWAY_KEYS = ("gateway_address", "ipc_credential", "snapshot_sha256", "expect_identity")
TIMEOUT_SECONDS = 120
EXIT_OK, EXIT_REFUSED = 0, 2


def sites_from_environment(environ: Mapping[str, str] = os.environ) -> frozenset[str]:
    """`ASSETOPS_READING_UPLOAD_SITES`: unset or empty is off; otherwise a comma list of supported Site codes."""
    value = (environ.get(SITES_ENV) or "").strip()
    if not value:
        return frozenset()
    codes = frozenset(part.strip().upper() for part in value.split(",") if part.strip())
    unsupported = sorted(codes - SUPPORTED_SITES)
    if unsupported:
        raise ConfigurationError(f"{SITES_ENV} may name only {sorted(SUPPORTED_SITES)}, not {unsupported}")
    return codes


def gateway_from_environment(environ: Mapping[str, str] = os.environ) -> dict[str, str] | None:
    path = environ.get(GATEWAY_ENV)
    if not path:
        return None
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in GATEWAY_KEYS if not isinstance(document.get(k), str) or not document[k]]
    if missing:
        raise ConfigurationError(f"{GATEWAY_ENV} file lacks {missing}")
    return {k: document[k] for k in GATEWAY_KEYS}


def _env() -> dict[str, str]:
    env = dict(os.environ)
    parts = [str(ROOT / "field"), str(ROOT / "gateway"), str(ROOT / "contracts")]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_field(argv: list[str], data: bytes, runner: Any = subprocess.run) -> tuple[int, dict]:
    """Write `data` to a private temp file, run the field process with `--file <it>`; its exit code and JSON line."""
    handle, name = tempfile.mkstemp(prefix="reading-upload-", suffix=".csv")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        done = runner([sys.executable, "-m", "assetops_field.csv_upload", *argv, "--file", name],
                      capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=_env(), cwd=str(ROOT))
    finally:
        Path(name).unlink(missing_ok=True)
    lines = [line for line in (done.stdout or "").splitlines() if line.strip()]
    try:
        return done.returncode, json.loads(lines[-1])
    except (IndexError, ValueError) as error:
        raise RuntimeError(f"the field process printed no JSON (exit {done.returncode}): "
                           f"{(done.stderr or '')[-400:]}") from error


def _refusal(document: Mapping[str, Any]) -> FileRefusal:
    r = document["refusal"]
    return FileRefusal(r["code"], r["field"], r["detail"], r.get("profile_sha256", ""))


class ProcessFileChecker:
    def __init__(self, profile: Path = PROFILE, runner: Any = subprocess.run) -> None:
        self._profile, self._runner = profile, runner

    def check(self, data: bytes) -> Preview | FileRefusal:
        code, document = run_field(["check", "--profile", str(self._profile)], data, self._runner)
        if code == EXIT_OK and document.get("ok"):
            return preview_from_document(document["preview"])
        if code == EXIT_REFUSED and "refusal" in document:
            return _refusal(document)
        raise RuntimeError(f"the field check failed (exit {code}): {document}")


class ProcessReadingSender:
    def __init__(self, gateway: Mapping[str, str], profile: Path = PROFILE, runner: Any = subprocess.run) -> None:
        self._gateway, self._profile, self._runner = dict(gateway), profile, runner

    def send(self, data: bytes) -> Sent | FileRefusal:
        g = self._gateway
        code, document = run_field(["send", "--profile", str(self._profile), "--gateway-address", g["gateway_address"],
                                    "--ipc-credential", g["ipc_credential"], "--snapshot-sha256", g["snapshot_sha256"],
                                    "--expect-identity", g["expect_identity"]], data, self._runner)
        if code == EXIT_REFUSED and "refusal" in document:
            return _refusal(document)
        if code != EXIT_OK or not document.get("ok"):
            raise GatewayUnavailable(f"the field send failed (exit {code}): {document.get('error')}")
        sent = document["sent"]
        outcomes = sent["outcomes"]
        held_by_column: dict[str, int] = {}
        for key, count in sent["held"].items():
            column = key.split(":", 1)[0]
            held_by_column[column] = held_by_column.get(column, 0) + int(count)
        return Sent(session_ref=sent["session_ref"],
                    admitted=int(outcomes.get("ADMITTED", 0)) + int(outcomes.get("ALREADY_ADMITTED", 0)),
                    held=int(outcomes.get("HELD", 0)), message_ids=tuple(m for m in sent["message_ids"] if m),
                    held_by_column=held_by_column)
