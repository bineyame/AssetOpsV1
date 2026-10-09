"""`python -m assetops_gateway serve --config <gateway.json>`: the gateway process.

The config is the gateway's own provisioning, read at startup and never taken
from a request or a run:

    {
      "database": "<path to the SQLite ledger>",
      "credential_file": "<path to the local host-to-gateway credential>",
      "address": "<named pipe or socket path>" (optional; default per gateway),
      "provisioning": {
        "tenant_id": "...", "site_id": "...", "gateway_id": "...",
        "source_mode": "SIMULATED", "permitted_source_ids": ["..."],
        "sequence_epoch": "..."
      },
      "diagnostics": {                     (optional; S2-01c defaults otherwise)
        "emission_cadence_seconds": 60,
        "disk_warn_free_bytes": ..., "disk_stop_free_bytes": ...
      },
      "upload": {                          (optional; S2-02. Absent: no network)
        "server_url": "https://...",       (https only; refused otherwise)
        "upload_credential_file": "...",   (owner-only `aog1.<selector>.<secret>`)
        "ca_file": "...",                  (optional; else the system store)
        "timeout_seconds": 10, "batches_per_pass": 50, "interval_seconds": 30
      }
    }

Relative paths resolve against the config file's directory. A ledger already
provisioned differently refuses to start (`IDENTITY_FIXED`); the epoch changes
only through `reprovision-epoch`, never by editing the config.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from assetops_contracts.gateway_diagnostics import DiagnosticConfig
from assetops_gateway.ipc import GatewayServer, default_address, ensure_credential
from assetops_gateway.service import GatewayRefused, GatewayService
from assetops_gateway.snapshot import Provisioning
from assetops_gateway.uploader import UploadConfig, UploadConfigInvalid, Uploader, parse_upload_config

CONFIG_KEYS = {"database", "credential_file", "address", "provisioning", "diagnostics", "upload"}
OPTIONAL_CONFIG_KEYS = {"address", "diagnostics", "upload"}
DIAGNOSTICS_KEYS = {"emission_cadence_seconds", "disk_warn_free_bytes", "disk_stop_free_bytes"}
PROVISIONING_KEYS = {"tenant_id", "site_id", "gateway_id", "source_mode", "permitted_source_ids", "sequence_epoch"}


@dataclass(frozen=True)
class GatewayConfig:
    database: Path
    credential_file: Path
    address: str
    provisioning: Provisioning
    sequence_epoch: str
    diagnostics: DiagnosticConfig = DiagnosticConfig()
    upload: UploadConfig | None = None


def load_config(path: Path) -> GatewayConfig:
    path = Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not set(document) <= CONFIG_KEYS or not (CONFIG_KEYS - OPTIONAL_CONFIG_KEYS) <= set(document):
        raise SystemExit(
            f"gateway config needs {sorted(CONFIG_KEYS - OPTIONAL_CONFIG_KEYS)} ({sorted(OPTIONAL_CONFIG_KEYS)} optional)"
        )
    raw_diagnostics = document.get("diagnostics", {})
    if not isinstance(raw_diagnostics, dict) or not set(raw_diagnostics) <= DIAGNOSTICS_KEYS:
        raise SystemExit(f"gateway diagnostics takes only {sorted(DIAGNOSTICS_KEYS)}")
    diagnostics = DiagnosticConfig(**raw_diagnostics)
    diagnostics.document()  # validates now, not at first emission
    raw = document["provisioning"]
    if not isinstance(raw, dict) or set(raw) != PROVISIONING_KEYS:
        raise SystemExit(f"gateway provisioning needs exactly {sorted(PROVISIONING_KEYS)}")
    base = path.parent
    try:
        upload = None if "upload" not in document else parse_upload_config(document["upload"], base)
    except UploadConfigInvalid as invalid:
        raise SystemExit(f"gateway {invalid}") from None
    database = (base / document["database"]).resolve()
    provisioning = Provisioning(
        tenant_id=raw["tenant_id"],
        site_id=raw["site_id"],
        gateway_id=raw["gateway_id"],
        source_mode=raw["source_mode"],
        permitted_source_ids=frozenset(raw["permitted_source_ids"]),
    )
    return GatewayConfig(
        database=database,
        credential_file=(base / document["credential_file"]).resolve(),
        address=document.get("address") or default_address(database.parent, provisioning.gateway_id),
        provisioning=provisioning,
        sequence_epoch=raw["sequence_epoch"],
        diagnostics=diagnostics,
        upload=upload,
    )


def serve(config: GatewayConfig) -> int:
    credential = ensure_credential(config.credential_file)
    service = GatewayService(config.database)
    try:
        service.provision(config.provisioning, sequence_epoch=config.sequence_epoch, diagnostics=config.diagnostics)
    except GatewayRefused as refused:
        print(f"REFUSED {refused.kind}: {refused.detail}", flush=True)
        service.close()
        return 2
    server = GatewayServer(service, config.database, config.address, credential)
    server.start_diagnostics(min(15.0, config.diagnostics.emission_cadence_seconds / 2))
    if config.upload is not None:
        server.attach_uploader(Uploader(service, config.upload, service_lock=server.lock))
    print(f"READY {config.address}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.close()
        service.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="assetops_gateway")
    commands = parser.add_subparsers(dest="command", required=True)
    serve_parser = commands.add_parser("serve")
    serve_parser.add_argument("--config", required=True, type=Path)
    epoch = commands.add_parser("reprovision-epoch")
    epoch.add_argument("--config", required=True, type=Path)
    epoch.add_argument("--epoch", required=True)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command == "serve":
        return serve(config)
    with GatewayService(config.database) as service:
        service.reprovision_epoch(args.epoch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
