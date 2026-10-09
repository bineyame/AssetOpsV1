"""A real `python -m assetops_gateway serve` process for host tests (S2-01b).

The gateway is provisioned the way an operator would: once, from its own config
file, with the tenant, Site, gateway and permitted source UUIDs of the Site it
serves - never from a request or a run.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

from assetops_gateway.ipc import GatewayLink


def address(state_dir: Path) -> str:
    if sys.platform == "win32":
        return rf"\\.\pipe\assetops-gateway-hosttest-{uuid.uuid4().hex}"
    return str(state_dir / "gw.sock")


def provisioning_from_snapshot(snapshot_text: str, *, epoch: str = "epoch-1", site_id: str | None = None) -> dict:
    """Operator provisioning for the Site a registered snapshot describes."""
    document = json.loads(snapshot_text)
    return {
        "tenant_id": document["tenant_id"],
        "site_id": site_id or document["site"]["site_id"],
        "gateway_id": document["gateway"]["gateway_id"],
        "source_mode": "SIMULATED",
        "permitted_source_ids": sorted(s["source_id"] for s in document["sources"]),
        "sequence_epoch": epoch,
    }


def write_config(state_dir: Path, provisioning: dict) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    config = state_dir / "gateway.json"
    config.write_text(
        json.dumps(
            {
                "database": "gateway.sqlite3",
                "credential_file": "gateway.credential",
                "address": address(state_dir),
                "provisioning": provisioning,
            }
        ),
        encoding="utf-8",
    )
    return config


class GatewayProcess:
    def __init__(self, config: Path) -> None:
        self.config = config
        self.process = subprocess.Popen(
            [sys.executable, "-m", "assetops_gateway", "serve", "--config", str(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.first_line = self.process.stdout.readline().strip()
        document = json.loads(config.read_text(encoding="utf-8"))
        self.link = GatewayLink(document["address"], config.parent / document["credential_file"])
        self.database = config.parent / document["database"]

    @property
    def ready(self) -> bool:
        return self.first_line.startswith("READY")

    def kill(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=30)
        self.process.stdout.close()
