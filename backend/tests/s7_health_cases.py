"""`D-edge-health-cases` (S7-01a): persisted central gateway-diagnostic cases for Site Health.

One registered gateway per case on one imported Site, so latest-per-gateway selection exposes every
case at once. Every diagnostic goes through the authenticated central path: a credential issued by
the provisioning CLI (`provision_gateway issue`), the bearer resolver (`StoreGatewayPrincipals`),
the TLS boundary and `DiagnosticIngestionService` behind `POST /api/gateways/{id}/diagnostics`.
The server receipt clock is the builder's `clock`; tests pass a settable clock, the S7-01b
walkthrough passes the real clock (then `advance` is a no-op and the stale case goes STALE after
two of its 30 s cadences).

Fixture SQL: the only direct writes are the case gateway and source registration rows (an import
registers exactly one gateway per Site, `foundation_service.py` import plan), inserted DISABLED as
an import leaves them; the provisioning CLI then enables them. No diagnostic, credential or
evidence row is written directly. Private Lab state supplies nothing.

Cases (gateway external id -> what the read must show):

* `s7-current`        received now, facts observed now: contact CURRENT, facts CURRENT.
* `s7-stale-cadence`  received once, then nothing past 2 x 30 s cadence: contact STALE, facts OLD.
* `s7-delayed-old`    an old diagnostic (observed 6 h earlier) received now: contact CURRENT, facts OLD.
* `s7-queue-growth`   queue 40 / 600 s, then 900 / 5400 s: last reported queue grew, old item.
* `s7-clock-offset`   clock offset 95 s reported: clock UNTRUSTED, facts UNKNOWN.
* `s7-disk-stop`      WARN then STOP (acquisition stop) with a growing queue.
* `s7-disk-recovery`  STOP then OK with the queue drained (recovery).
* `s7-never-received` enabled and credentialed, no diagnostic: contact UNKNOWN.

`deliver()` posts the next local sequence on `s7-current` and `s7-delayed-old` so both carry a
fresh server receipt immediately before viewing (the delayed case keeps its 6 h old facts).
`deliver(CURRENT_CONTACT_KEYS)` refreshes every case meant to read CURRENT contact (S7-01b walkthrough).
`register()` adds eight gateways to the Site, which breaks S1's one-gateway rule for later binding publishes
there: run it only after the Site's bindings exist, on a DB of its own (S7-01a review L1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
from assetops_backend.evidence.gateway_access import DiagnosticIngestionService, StoreGatewayPrincipals
from assetops_backend.evidence.provision_gateway import main as provision
from assetops_backend.gateway_api import build_gateway_router, install_gateway_tls_boundary
from assetops_contracts.gateway_diagnostics import seal_gateway_diagnostics_v1

EPOCH = "s7-epoch-1"
MANIFEST = "s7_health_cases.json"
DELAY = timedelta(hours=6)
DELIVER_DEFAULT = ("s7-current", "s7-delayed-old")
#: Cases whose contact is meant to read CURRENT; `s7-stale-cadence` and `s7-never-received` are not refreshed.
CURRENT_CONTACT_KEYS = ("s7-current", "s7-delayed-old", "s7-queue-growth", "s7-clock-offset", "s7-disk-stop",
                        "s7-disk-recovery")


@dataclass(frozen=True)
class Case:
    key: str
    cadence_seconds: int
    meaning: str


CASES = (
    Case("s7-current", 60, "received now, facts current"),
    Case("s7-stale-cadence", 30, "no receipt across two declared cadences"),
    Case("s7-delayed-old", 60, "old diagnostic received now"),
    Case("s7-queue-growth", 60, "growing queue and old queued item"),
    Case("s7-clock-offset", 60, "reported clock offset beyond tolerance"),
    Case("s7-disk-stop", 60, "disk pressure and acquisition stop"),
    Case("s7-disk-recovery", 60, "disk stop then recovery"),
    Case("s7-never-received", 60, "registered, never received"),
)


def _instant(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HealthCases:
    def __init__(self, url: str, site_code: str, work: Path, clock: Callable[[], datetime],
                 tenant_slug: str = "demo") -> None:
        self.url, self.site_code, self.work, self.clock, self.tenant_slug = url, site_code, Path(work), clock, tenant_slug
        self.engine = create_engine(url)
        self.access = PostgresGatewayAccess(url)
        self.manifest: dict = {}
        path = self.work / MANIFEST
        if path.exists():
            self.manifest = json.loads(path.read_text(encoding="utf-8"))

    def close(self) -> None:
        self.engine.dispose()
        if self.access._engine is not None:
            self.access._engine.dispose()

    # --- registration (fixture SQL + provisioning CLI) ------------------------------------------

    def register(self) -> dict:
        self.work.mkdir(parents=True, exist_ok=True)
        with self.engine.begin() as c:
            site = c.execute(text(
                "SELECT s.tenant_id, s.id FROM site s JOIN tenant t ON t.id = s.tenant_id "
                "WHERE t.slug = :slug AND s.site_code_key = lower(:code)"),
                {"slug": self.tenant_slug, "code": self.site_code}).one()
            asset = c.execute(text("SELECT id FROM asset WHERE tenant_id = :t AND site_id = :s "
                                   "ORDER BY asset_code LIMIT 1"), {"t": site.tenant_id, "s": site.id}).scalar_one()
            at = self.clock()
            gateways = {}
            for case in CASES:
                gateway_id, source_id = uuid4(), uuid4()
                c.execute(text(
                    "INSERT INTO gateway (id, tenant_id, site_id, gateway_external_id, mode, registered_at, "
                    "disabled_at) VALUES (:g, :t, :s, :ext, 'SIMULATED', :at, :at)"),
                    {"g": gateway_id, "t": site.tenant_id, "s": site.id, "ext": case.key, "at": at})
                c.execute(text(
                    "INSERT INTO source (id, tenant_id, site_id, gateway_id, source_external_id, device_kind, "
                    "asset_id, registered_at, disabled_at) VALUES (:id, :t, :s, :g, :ext, 'CONTROLLER', :a, :at, :at)"),
                    {"id": source_id, "t": site.tenant_id, "s": site.id, "g": gateway_id,
                     "ext": f"{case.key}-device", "a": asset, "at": at})
                gateways[case.key] = {"gateway_id": str(gateway_id), "source_id": str(source_id),
                                      "cadence_seconds": case.cadence_seconds, "meaning": case.meaning}
        for key, entry in gateways.items():
            out = self.work / f"cred-{key}"
            before = set(self.work.glob(f"cred-{key}.*"))
            code = provision(["--tenant", self.tenant_slug, "--site", self.site_code, "--gateway", key, "issue",
                              "--credential-out", str(out), "--enable-source", f"{key}-device",
                              "--cadence-seconds", str(entry["cadence_seconds"]), "--actor", "s7-health-cases"],
                             store=self.access, now=self.clock())
            assert code == 0, f"provisioning {key} failed"
            [issued] = set(self.work.glob(f"cred-{key}.*")) - before
            entry["credential_path"] = str(issued)
        self.manifest = {"site_code": self.site_code, "site_id": str(site.id), "tenant_id": str(site.tenant_id),
                         "epoch": EPOCH, "gateways": gateways}
        (self.work / MANIFEST).write_text(json.dumps(self.manifest, indent=2, sort_keys=True), encoding="utf-8")
        return self.manifest

    # --- authenticated central ingestion ----------------------------------------------------------

    def client(self) -> TestClient:
        app = FastAPI()
        install_gateway_tls_boundary(app)
        principals = StoreGatewayPrincipals(self.access)
        app.include_router(build_gateway_router(
            principals, DiagnosticIngestionService(self.access, self.clock), self.access,
            lambda code: None, self.clock))
        return TestClient(app, base_url="https://testserver")

    def post(self, key: str, sequence: int, *, observed: datetime, queue: int = 0, oldest: int | None = None,
             disk: str = "OK", offset: int | None = 150, contact: datetime | None = None) -> dict:
        entry = self.manifest["gateways"][key]
        token = Path(entry["credential_path"]).read_text(encoding="ascii").strip()
        contact = observed - timedelta(seconds=30) if contact is None else contact
        _, body = seal_gateway_diagnostics_v1(
            site_id=self.manifest["site_id"], gateway_id=entry["gateway_id"], sequence_epoch=EPOCH,
            diagnostic_sequence=sequence, observed_at=_instant(observed),
            last_device_contact_by_source={entry["source_id"]: _instant(contact)},
            queue_count=queue, oldest_queue_age_seconds=oldest, disk_pressure=disk, clock_offset_ms=offset,
            mapping_error_count=0)
        answer = self.client().post(f"/api/gateways/{entry['gateway_id']}/diagnostics", content=body,
                                    headers={"Authorization": f"Bearer {token}"})
        assert answer.status_code in (200, 201), (key, answer.status_code, answer.text)
        return answer.json()

    def publish(self, advance: Callable[[int], None] = lambda seconds: None) -> dict[str, list[dict]]:
        """Publish the six central cases. `advance(600)` moves a test clock past the stale threshold."""
        receipts: dict[str, list[dict]] = {}

        def put(key, *args, **kwargs):
            receipts.setdefault(key, []).append(self.post(key, *args, **kwargs))

        now = self.clock()
        put("s7-stale-cadence", 1, observed=now - timedelta(seconds=2))
        put("s7-queue-growth", 1, observed=now - timedelta(seconds=2), queue=40, oldest=600)
        put("s7-disk-stop", 1, observed=now - timedelta(seconds=2), disk="WARN", queue=10, oldest=120)
        put("s7-disk-recovery", 1, observed=now - timedelta(seconds=2), disk="STOP", queue=250, oldest=3000)
        advance(600)
        now = self.clock()
        put("s7-current", 1, observed=now - timedelta(seconds=2))
        put("s7-delayed-old", 1, observed=now - DELAY, queue=12, oldest=21600)
        put("s7-queue-growth", 2, observed=now - timedelta(seconds=2), queue=900, oldest=5400)
        put("s7-clock-offset", 1, observed=now + timedelta(seconds=90), offset=95_000,
            contact=now + timedelta(seconds=60))
        put("s7-disk-stop", 2, observed=now - timedelta(seconds=2), disk="STOP", queue=300, oldest=720)
        put("s7-disk-recovery", 2, observed=now - timedelta(seconds=2), disk="OK", queue=0, oldest=None)
        return receipts

    def next_sequence(self, key: str) -> int:
        with self.engine.connect() as c:
            return 1 + c.execute(text(
                "SELECT coalesce(max(diagnostic_sequence), 0) FROM gateway_diagnostic WHERE gateway_id = :g "
                "AND sequence_epoch = :e"), {"g": self.manifest["gateways"][key]["gateway_id"], "e": EPOCH}
            ).scalar_one()

    def last_facts(self, key: str, now: datetime) -> dict:
        """The facts a case last published, restated for a delivery at ``now`` (same meaning, new receipt)."""
        recent = now - timedelta(seconds=2)
        return {
            "s7-current": dict(observed=recent),
            "s7-delayed-old": dict(observed=now - DELAY, queue=12, oldest=21600),
            "s7-queue-growth": dict(observed=recent, queue=900, oldest=5400),
            "s7-clock-offset": dict(observed=now + timedelta(seconds=90), offset=95_000,
                                    contact=now + timedelta(seconds=60)),
            "s7-disk-stop": dict(observed=recent, disk="STOP", queue=300, oldest=720),
            "s7-disk-recovery": dict(observed=recent, disk="OK", queue=0, oldest=None),
        }[key]

    def deliver(self, keys: tuple[str, ...] = DELIVER_DEFAULT) -> dict[str, dict]:
        """Fresh receipts for ``keys`` (default: the current and old-facts cases). Each re-posts the case's
        last facts at its gateway's next local sequence. The walkthrough passes `CURRENT_CONTACT_KEYS` so every
        case meant to read CURRENT contact on the real clock is refreshed just before viewing (review L4)."""
        now = self.clock()
        return {key: self.post(key, self.next_sequence(key), **self.last_facts(key, now)) for key in keys}


__all__ = ["CASES", "CURRENT_CONTACT_KEYS", "DELAY", "DELIVER_DEFAULT", "EPOCH", "HealthCases", "MANIFEST"]
