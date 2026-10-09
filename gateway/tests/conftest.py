"""Shared fixtures: a provisioned gateway identity and registered snapshots.

The snapshot builder mirrors `assetops.acquisition-snapshot/1` as S1 writes it
(`backend/assetops_backend/sites/binding_alignment.py::snapshot_document_v1`):
the same keys, sorted rows and `bindings_sha256` rule. The gateway suite cannot
import the backend, so the shape is restated here and the phase-2 host suite
proves a real S2-01a snapshot activates.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from assetops_contracts.gateway_report import DeviceReport, device_report_text
from assetops_gateway.service import GatewayService
from assetops_gateway.snapshot import ClaimedReferences, Provisioning

TENANT = "00000000-0000-4000-8000-000000000001"
SITE = "11111111-1111-4111-8111-111111111111"
GATEWAY = "22222222-2222-4222-8222-222222222222"
SRC_BMS = "33333333-3333-4333-8333-333333333331"
SRC_PV = "33333333-3333-4333-8333-333333333332"
SRC_GEN = "33333333-3333-4333-8333-333333333333"
EPOCH = "epoch-1"

PROVISIONING = Provisioning(
    tenant_id=TENANT,
    site_id=SITE,
    gateway_id=GATEWAY,
    source_mode="SIMULATED",
    permitted_source_ids=frozenset({SRC_BMS, SRC_PV, SRC_GEN}),
)

NOW = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)


def _canonical(document: object) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _rows() -> list[dict]:
    def row(rev: str, device: str, signal: str, source: str, role: str, unit: str, conversion: dict) -> dict:
        return {
            "binding_revision_id": rev,
            "device_id": device,
            "signal_id": signal,
            "source_id": source,
            "gateway_id": GATEWAY,
            "asset_id": None,
            "role": role,
            "source_unit": unit,
            "canonical_unit": unit,
            "conversion": conversion,
        }

    identity = {"kind": "IDENTITY", "parameters": {}}
    return [
        row("b-1", "battery-bms", "soc", SRC_BMS, "battery_soc", "%", identity),
        row("b-2", "generator-controller", "status", SRC_GEN, "generator_state", "state",
            {"kind": "ENUM", "parameters": {"map": {"RUNNING": "RUNNING", "STOPPED": "STOPPED"}}}),
        row("b-3", "pv-inverter", "ac_power", SRC_PV, "pv_power", "kW", identity),
    ]


def snapshot(
    *,
    foundation_rev: str = "f-rev-1",
    foundation_version: int = 3,
    binding_rev: str = "bs-rev-1",
    binding_version: int = 2,
    valid_from: str = "2026-09-29T11:57:49Z",
    valid_to: str | None = None,
    rows: list[dict] | None = None,
    tenant: str = TENANT,
    site: str = SITE,
    mode: str = "SIMULATED",
) -> tuple[str, ClaimedReferences]:
    rows = sorted(rows if rows is not None else _rows(), key=lambda r: (r["device_id"], r["signal_id"]))
    content = [{k: v for k, v in r.items() if k != "binding_revision_id"} for r in rows]
    role_set = "kobo-hybrid"
    used = sorted({r["source_id"] for r in rows})
    document = {
        "schema": "assetops.acquisition-snapshot/1",
        "tenant_id": tenant,
        "site": {"site_id": site, "site_code": "KOBO"},
        "gateway": {"gateway_id": GATEWAY, "gateway_external_id": "kobo-gw", "mode": mode},
        "foundation": {
            "revision_id": foundation_rev,
            "version": foundation_version,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "content_sha256": "a" * 64,
        },
        "mapping": {
            "binding_set_id": "bs-kobo",
            "binding_set_revision_id": binding_rev,
            "version": binding_version,
            "role_set": role_set,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "bindings_sha256": hashlib.sha256(
                _canonical({"role_set": role_set, "bindings": content}).encode("utf-8")
            ).hexdigest(),
        },
        "sources": [{"source_id": s, "source_external_id": f"ext-{s[-1]}"} for s in used],
        "bindings": rows,
    }
    text = _canonical(document)
    claimed = ClaimedReferences(
        snapshot_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        foundation_revision_id=foundation_rev,
        foundation_version=foundation_version,
        binding_set_id="bs-kobo",
        binding_set_revision_id=binding_rev,
        binding_set_version=binding_version,
    )
    return text, claimed


def report(
    *,
    device: str = "battery-bms",
    signal: str = "soc",
    at: str = "2026-10-01T08:00:00Z",
    value: str | None = "61.5",
    unit: str = "%",
    key: str | None = None,
    quality: str = "GOOD",
    reason: str | None = None,
    measurement: str = "STATE_AT_INSTANT",
    interval_start: str | None = None,
) -> str:
    return device_report_text(
        DeviceReport(
            report_key=key,
            device_id=device,
            signal_id=signal,
            source_time=at,
            measurement=measurement,
            interval_start=interval_start,
            value=value,
            unit=unit,
            quality=quality,
            unavailable_reason=reason,
        )
    )


class Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "gateway.sqlite3"


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def gateway(db_path: Path, clock: Clock):
    service = GatewayService(db_path, clock=clock)
    service.provision(PROVISIONING, sequence_epoch=EPOCH)
    yield service
    service.close()


@pytest.fixture
def active(gateway: GatewayService) -> str:
    text, claimed = snapshot()
    gateway.activate(text, claimed)
    return claimed.snapshot_sha256
