"""S7-01b: the committed API contract the Site Health and battery screens are tested against.

Builds the S7-01a central cases (`s7_health_cases.HealthCases`) and three battery Sites on a fresh database, reads
both S7-01a contracts through their real routers, and compares every response with the committed
`backend/tests/fixtures/s7_health_api_contract.json` after replacing per-run UUIDs and digests with stable
placeholders (first appearance order). The frontend tests (`frontend/src/sites/__tests__/siteHealthBoundary.test.tsx`)
load that same file, so a drift in any field fails here first.

Regenerate (one run, then commit):   ASSETOPS_WRITE_S7_CONTRACT=1 pytest <this file>
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import NOW, Clock, engine, store  # noqa: F401
    from test_s7_asset_boundary_postgres import without_battery
    from test_s7_source_health_postgres import published, rig  # noqa: F401

    from assetops_backend.asset_boundary_api import build_asset_boundary_router
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "s7_health_api_contract.json"
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def normalise(document: dict) -> dict:
    """Stable placeholders for per-run UUIDs and digests, numbered by first appearance."""
    text = json.dumps(document, indent=1, sort_keys=True)
    ids: dict[str, str] = {}
    text = _UUID.sub(lambda m: ids.setdefault(m.group(0), f"00000000-0000-4000-8000-{len(ids) + 1:012d}"), text)
    digests: dict[str, str] = {}
    text = _HEX64.sub(lambda m: digests.setdefault(m.group(0), f"{len(digests) + 1:064x}"), text)
    return json.loads(text)


def answer(response) -> dict:
    return {"status": response.status_code, "body": response.json()}


def test_s7_health_api_contract(store, rig, published, tmp_path) -> None:  # noqa: F811
    without_battery(store, tmp_path, code="KOBO-NB")
    health = rig.client()
    app = FastAPI()
    app.include_router(build_asset_boundary_router(ImportedSiteRegistry(FoundationService(store, "demo", Clock(NOW)))))
    asset = TestClient(app)

    class Down:
        def source_health_snapshot(self, tenant_id, site_id):
            from assetops_backend.evidence.ledger import LedgerUnavailable
            raise LedgerUnavailable("store down")

    entry_001 = asset.get("/api/sites/KOBO-001/battery")
    entry_002 = asset.get("/api/sites/KOBO-002/battery")
    kobo_001_asset = entry_001.json()["batteries"][0]["asset_id"]
    contract = {
        "health_kobo001": answer(health.get("/api/sites/KOBO-001/source-health")),
        "health_kobo002": answer(health.get("/api/sites/KOBO-002/source-health")),
        "health_unknown_site": answer(health.get("/api/sites/NOT-A-SITE/source-health")),
        "health_unavailable": answer(rig.client(store=Down()).get("/api/sites/KOBO-001/source-health")),
        "battery_entry_kobo001": answer(entry_001),
        "battery_detail_kobo001": answer(asset.get(entry_001.json()["batteries"][0]["detail_path"])),
        "battery_entry_kobo002": answer(entry_002),
        "battery_detail_kobo002": answer(asset.get(entry_002.json()["batteries"][0]["detail_path"])),
        "battery_entry_kobonb": answer(asset.get("/api/sites/KOBO-NB/battery")),
        "battery_detail_foreign": answer(asset.get(f"/api/sites/KOBO-NB/assets/{kobo_001_asset}/battery")),
        "battery_detail_invalid": answer(asset.get("/api/sites/KOBO-001/assets/not-an-id/battery")),
    }
    c = contract
    assert c["health_kobo001"]["body"]["summary"]["status"] == "NOT_ALL_CURRENT"
    assert c["health_kobo002"]["body"]["summary"]["reason"] == "NO_ENABLED_GATEWAY"
    assert c["health_unknown_site"]["status"] == 404
    assert c["health_unavailable"]["status"] == 503
    assert c["battery_detail_kobo001"]["body"]["binding_status"] == "BOUND"
    assert c["battery_detail_kobo002"]["body"]["binding_status"] == "NO_BINDING_SET"
    assert c["battery_entry_kobonb"]["body"]["configuration"] == "NOT_CONFIGURED"
    assert c["battery_detail_foreign"]["status"] == 404
    assert c["battery_detail_invalid"]["status"] == 422
    if os.environ.get("ASSETOPS_WRITE_S7_CONTRACT"):
        FIXTURE.write_text(json.dumps(normalise(contract), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert normalise(contract) == committed
