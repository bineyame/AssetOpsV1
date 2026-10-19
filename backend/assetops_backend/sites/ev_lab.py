"""W2-05a registered EV charging lab: EV-LAB-001 and its first complete `ev-roles-1` binding revision.

`D-2026-10-18-w2-05-buildspec` Q1/Q6/Q8: the fixture imports as the Site's first Foundation revision, and the
fifteen exact `simulator-lab-gateway-ev/1` channel requests of `ev-lab-001-bindings.json` publish at the
Foundation's `valid_from` through `BindingService.publish`, so every row carries the closed v4 entry's five
metadata keys. EV-LAB-001 has no historical v3 conversion, so nothing is replayed through
`binding_conversion.convert` (whose CONVERSION origin carries no v4 metadata). Gap examples are later
revisions of this same Site, made by tests in isolated stores; nothing here creates them.

    python -m assetops_backend.sites.ev_lab --tenant demo
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable

from assetops_backend.sites.binding_conversion import plan_requests
from assetops_backend.sites.binding_service import BindingPublishResult, BindingService
from assetops_backend.sites.composition import read_binding_conversion_fixture, read_site_import_source

EV_LAB_SITE_CODE = "EV-LAB-001"
BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_PATH = os.path.join(BACKEND, "tests", "fixtures", "w2", "ev-lab-001.yaml")
CONVERSION_PATH = os.path.join(BACKEND, "conversions", "ev-lab-001-bindings.json")


def binding_fixture() -> dict[str, Any]:
    return read_binding_conversion_fixture(CONVERSION_PATH)[0]


def publish_complete_bindings(store, service: BindingService, tenant, site) -> BindingPublishResult:
    """Publish EV-LAB-001's complete binding revision at its original Foundation's `valid_from`."""
    fixture = binding_fixture()
    original = next(r for r in store.revisions(tenant.id, site.id) if r.origin == "IMPORT")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, _declared, _rows = plan_requests(
        fixture, site, original.content.get("signal_mappings") or (), asset_ids
    )
    return service.publish(
        tenant, site, requests=requests, effective_from=original.valid_from, note=fixture["note"],
        role_set=fixture["role_set"],
    )


def install_ev_lab(store, *, tenant_slug: str, clock: Callable[[], datetime], source_path: str | None = None):
    """Import EV-LAB-001 and publish its complete binding revision (idempotent per step)."""
    from assetops_backend.sites.foundation_service import ImportSource, import_site

    source = read_site_import_source(FIXTURE_PATH)
    result = import_site(
        store, tenant_slug=tenant_slug, configured_tenant_slug=tenant_slug,
        source=ImportSource(path=source_path or "var/sites/ev-lab-001.yaml", sha256=source.sha256,
                            record=source.record),
        legacy_documents=(), clock=clock,
    )
    if not store.binding_sets(result.tenant.id, result.site.id):
        # Run 8 M4: no activation delay; the binding service records at the install clock and effective_from is
        # still the original Foundation's valid_from.
        publish_complete_bindings(store, BindingService(store, clock), result.tenant, result.site)
    return result


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - operator entry point
    from assetops_backend.config import database_url
    from assetops_backend.sites.composition import build_foundation_store

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    store = build_foundation_store(database_url())
    result = install_ev_lab(store, tenant_slug=args.tenant, clock=lambda: datetime.now(timezone.utc))
    sets = store.binding_sets(result.tenant.id, result.site.id)
    print(json.dumps([{"version": s.version, "valid_from": s.valid_from.isoformat(), "origin": s.origin,
                       "snapshot_sha256": s.snapshot_sha256} for s in sets], indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
