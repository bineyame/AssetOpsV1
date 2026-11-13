"""UP-1 D-UP.2: the demo's Kobo edge gateway and its TLS central, started by `demo_combined.py serve` only when
`ASSETOPS_READING_UPLOAD_SITES` is set.

    python tools/demo_upload_gateway.py prepare  --work <work>   # TLS, epoch, basis, credential, gateway.json
    python tools/demo_upload_gateway.py activate --work <work>   # after the gateway prints READY

- (a) Central: `python -m assetops_backend.serve_tls` on 127.0.0.1:8443 against the demo DB, with a self-signed
  certificate generated once into `<work>/tls/` (openssl, as `tools/s2_demo_walkthrough.py`); the gateway's `ca_file`
  is that certificate. The upload credential is issued once per state dir through
  `python -m assetops_backend.evidence.provision_gateway issue` (actor `service:demo-upload`, the CSV profile's
  sources enabled); it is reissued only when its file is missing (issuing revokes the earlier one).
- (b) State and epoch: one persistent state dir `<work>/gateways/kobo-edge/`, the Kobo edge gateway for UP-1 and,
  later, MB-1. Its sequence epoch is minted once with the state dir, kept in `sequence_epoch.txt`, and is never one of
  the per-Site-day epochs under `<work>/kobo-*/gw-*` (checked at every prepare).
- (c) Activation basis: the registered basis selected for the latest prepared Kobo day in `<work>/days.json` (the
  same `select_registered_basis` the day's draft run used). No draft run is written to the demo DB.
- (d) Delivery: the host delivers after each send (`host/reading_upload_process.deliver_now`); the gateway's own
  upload interval is 60 s as the backstop.
- After activation, `<work>/reading-upload-gateway.json` is written for the host (`ASSETOPS_READING_UPLOAD_GATEWAY`).

The file helpers are pure and tested without a database (`host/tests/test_up1_demo_upload_gateway.py`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
SITE, TENANT, ACTOR = "KOBO-001", "demo", "service:demo-upload"
STATE_REL = Path("gateways") / "kobo-edge"
TLS_REL = Path("tls")
GATEWAY_FILE = "reading-upload-gateway.json"
EPOCH_FILE, BASIS_FILE, EXPECT_FILE, CONFIG_FILE = ("sequence_epoch.txt", "basis.json", "expect-identity.json",
                                                    "gateway.json")
UPLOAD_CREDENTIAL = "upload.credential"
TLS_HOST, TLS_PORT = "127.0.0.1", 8443
UPLOAD_INTERVAL_SECONDS = 60
SITES_ENV = "ASSETOPS_READING_UPLOAD_SITES"


class GatewayPrepareRefused(Exception):
    pass


def state_dir(work: Path) -> Path:
    return work / STATE_REL


def tls_files(work: Path) -> tuple[Path, Path]:
    folder = work / TLS_REL
    return folder / "server.crt", folder / "server.key"


def upload_switched_on(environ: dict[str, str] | os._Environ = os.environ) -> bool:
    return bool((environ.get(SITES_ENV) or "").strip())


def _restrict(path: Path) -> None:
    from assetops_gateway.credential_protection import restrict_to_current_user

    restrict_to_current_user(path)


def ensure_tls(work: Path, run: Callable[..., Any] = subprocess.run,
               protect: Callable[[Path], None] = _restrict) -> tuple[Path, Path]:
    """A self-signed certificate for 127.0.0.1, generated once; an existing pair is kept (the gateway trusts it)."""
    cert, key = tls_files(work)
    if cert.is_file() and key.is_file():
        return cert, key
    cert.parent.mkdir(parents=True, exist_ok=True)
    run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "365", "-keyout", str(key),
         "-out", str(cert), "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost"],
        check=True, capture_output=True)
    protect(key)
    return cert, key


def per_day_epochs(work: Path) -> set[str]:
    """The sequence epochs of the per-Site-day Kobo gateway states the build left under `<work>`."""
    found: set[str] = set()
    for config in work.glob("kobo-*/gw-*/gateway.json"):
        found.add(config.parent.name[len("gw-"):])
        try:
            found.add(json.loads(config.read_text(encoding="utf-8"))["provisioning"]["sequence_epoch"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return found


def _mint() -> str:
    return f"kobo-edge-{secrets.token_hex(6)}"


def ensure_epoch(state: Path, existing: Iterable[str], mint: Callable[[], str] = _mint) -> str:
    """The edge gateway's one sequence epoch: minted with the state dir, then read back; never a per-day epoch."""
    path = state / EPOCH_FILE
    taken = set(existing)
    if path.is_file():
        epoch = path.read_text(encoding="utf-8").strip()
        if epoch in taken:
            raise GatewayPrepareRefused(f"the edge gateway's epoch {epoch!r} is also a per-day gateway's epoch")
        return epoch
    epoch = mint()
    if not epoch or epoch in taken:
        raise GatewayPrepareRefused(f"the minted epoch {epoch!r} is empty or already a per-day gateway's epoch")
    state.mkdir(parents=True, exist_ok=True)
    path.write_text(epoch, encoding="utf-8")
    return epoch


def latest_kobo_window(days_doc: dict) -> tuple[str, str]:
    """The [start, end] of the latest prepared Kobo day run in `<work>/days.json`."""
    runs = [d for d in days_doc.get("days", []) if d.get("site") == "kobo" and d.get("start") and d.get("end")]
    if not runs:
        raise GatewayPrepareRefused("days.json has no prepared Kobo day, so there is no basis to activate")
    last = max(runs, key=lambda d: (d["start"], d["end"]))
    return last["start"], last["end"]


def gateway_address(state: Path) -> str:
    if sys.platform == "win32":
        tag = hashlib.sha256(str(state.resolve()).encode("utf-8")).hexdigest()[:12]
        return rf"\\.\pipe\assetops-kobo-edge-{tag}"
    return str(state / "gw.sock")


def gateway_config(state: Path, provisioning: dict, *, ca_file: Path, upload_credential_file: Path) -> dict:
    return {
        "database": "gateway.sqlite3",
        "credential_file": "gateway.credential",
        "address": gateway_address(state),
        "provisioning": provisioning,
        "upload": {"server_url": f"https://{TLS_HOST}:{TLS_PORT}", "upload_credential_file": str(upload_credential_file),
                   "ca_file": str(ca_file), "timeout_seconds": 10, "batches_per_pass": 25,
                   "interval_seconds": UPLOAD_INTERVAL_SECONDS},
    }


def profile_sources(snapshot_text: str, row_sources: dict[str, str]) -> list[str]:
    """The source external IDs of the CSV profile's rows (to enable when the credential is issued)."""
    ids = set(row_sources.values())
    snapshot = json.loads(snapshot_text)
    return sorted(s["source_external_id"] for s in snapshot["sources"] if s["source_id"] in ids)


def existing_credential(state: Path) -> Path | None:
    """The upload credential file the state's gateway.json names, when it still exists (issue once per state dir)."""
    config = state / CONFIG_FILE
    if not config.is_file():
        return None
    try:
        named = Path(json.loads(config.read_text(encoding="utf-8"))["upload"]["upload_credential_file"])
    except (ValueError, KeyError, TypeError):
        return None
    return named if named.is_file() else None


def issue_credential(state: Path, gateway_external_id: str, sources: list[str],
                     run: Callable[..., Any] = subprocess.run) -> Path:
    argv = [sys.executable, "-m", "assetops_backend.evidence.provision_gateway", "issue", "--tenant", TENANT,
            "--site", SITE, "--gateway", gateway_external_id, "--credential-out", str(state / UPLOAD_CREDENTIAL),
            "--actor", ACTOR]
    for source in sources:
        argv += ["--enable-source", source]
    done = run(argv, capture_output=True, text=True)
    if done.returncode != 0:
        raise GatewayPrepareRefused(f"credential issue failed (exit {done.returncode}): {(done.stderr or '')[-600:]}")
    for line in (done.stdout or "").splitlines():
        if line.startswith("Credential file: "):
            return Path(line[len("Credential file: "):].strip())
    raise GatewayPrepareRefused("credential issue printed no 'Credential file:' line")


def host_gateway_doc(state: Path, config: dict, snapshot_sha256: str) -> dict[str, str]:
    """`ASSETOPS_READING_UPLOAD_GATEWAY` (read by `host/reading_upload_process.gateway_from_environment`)."""
    return {"gateway_address": config["address"], "ipc_credential": str(state / config["credential_file"]),
            "snapshot_sha256": snapshot_sha256, "expect_identity": str(state / EXPECT_FILE)}


def write_json(path: Path, document: Any) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(document, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(temp, path)


def wait_for_port(host: str, port: int, alive: Callable[[], bool], timeout: float = 90.0,
                  clock: Callable[[], float] = time.monotonic, pause: Callable[[float], None] = time.sleep) -> None:
    deadline = clock() + timeout
    while clock() < deadline:
        if not alive():
            raise GatewayPrepareRefused(f"the process serving {host}:{port} exited")
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            pause(0.5)
    raise GatewayPrepareRefused(f"nothing answered on {host}:{port} within {timeout:.0f} s")


def wait_for_line(log: Path, text: str, alive: Callable[[], bool], timeout: float = 90.0,
                  clock: Callable[[], float] = time.monotonic, pause: Callable[[float], None] = time.sleep) -> None:
    deadline = clock() + timeout
    while clock() < deadline:
        if log.is_file() and text in log.read_text(encoding="utf-8", errors="replace"):
            return
        if not alive():
            raise GatewayPrepareRefused(f"the process logging to {log} exited before printing {text!r}")
        pause(0.3)
    raise GatewayPrepareRefused(f"{log} did not show {text!r} within {timeout:.0f} s")


# ---- the database and gateway steps (run inside the demo tree's serve environment) ------------------------------
def _select_basis(start: str, end: str):
    from assetops_backend.config import database_url
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService

    store = PostgresFoundationStore(database_url())
    registry = ImportedSiteRegistry(FoundationService(store, TENANT))
    return RegisteredLabBasis(registry).select(SITE, start_time=start, end_time=end, knowledge_at=None).basis


def prepare(work: Path) -> dict:
    import field_bench
    from gateway_process import provisioning_from_snapshot
    from gateway_publication import claimed_references

    state = state_dir(work)
    cert, _ = ensure_tls(work)
    epoch = ensure_epoch(state, per_day_epochs(work))
    start, end = latest_kobo_window(json.loads((work / "days.json").read_text(encoding="utf-8")))
    basis = _select_basis(start, end)
    snapshot_text = basis.snapshot_canonical
    write_json(state / BASIS_FILE, {"window": [start, end], "snapshot_text": snapshot_text,
                                    "claimed": claimed_references(basis)})
    expect = field_bench.expect_identity_from_snapshot(snapshot_text, json.loads(PROFILE.read_text(encoding="utf-8")),
                                                       epoch)
    write_json(state / EXPECT_FILE, expect)
    provisioning = provisioning_from_snapshot(snapshot_text, epoch=epoch)
    config_path = state / CONFIG_FILE
    if config_path.is_file():
        before = json.loads(config_path.read_text(encoding="utf-8")).get("provisioning")
        if before != provisioning:
            raise GatewayPrepareRefused("the kobo-edge gateway was provisioned for a different basis or epoch; a "
                                        "provisioned gateway is never re-provisioned (remove its state dir to start "
                                        "a new epoch)")
    credential = existing_credential(state)
    issued = credential is None
    if issued:
        gateway_external_id = json.loads(snapshot_text)["gateway"]["gateway_external_id"]
        credential = issue_credential(state, gateway_external_id, profile_sources(snapshot_text,
                                                                                  expect["row_sources"]))
    write_json(config_path, gateway_config(state, provisioning, ca_file=cert, upload_credential_file=credential))
    return {"state": str(state), "epoch": epoch, "window": [start, end], "credential_issued": issued,
            "snapshot_sha256": basis.snapshot_sha256}


def activate(work: Path) -> dict:
    from assetops_gateway.ipc import GatewayLink

    state = state_dir(work)
    config = json.loads((state / CONFIG_FILE).read_text(encoding="utf-8"))
    basis = json.loads((state / BASIS_FILE).read_text(encoding="utf-8"))
    link = GatewayLink(config["address"], state / config["credential_file"])
    answer = link.call("activate", {"snapshot_text": basis["snapshot_text"], "claimed": basis["claimed"]})
    if answer.get("snapshot_sha256") != basis["claimed"]["snapshot_sha256"]:
        raise GatewayPrepareRefused(f"the gateway activated {answer} for basis {basis['claimed']['snapshot_sha256']}")
    doc = host_gateway_doc(state, config, answer["snapshot_sha256"])
    write_json(work / GATEWAY_FILE, doc)
    return doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="demo_upload_gateway")
    parser.add_argument("step", choices=["prepare", "activate"])
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        out = prepare(args.work) if args.step == "prepare" else activate(args.work)
    except GatewayPrepareRefused as refused:
        print(json.dumps({"ok": False, "error": str(refused)}))
        return 2
    print(json.dumps({"ok": True, args.step: out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
