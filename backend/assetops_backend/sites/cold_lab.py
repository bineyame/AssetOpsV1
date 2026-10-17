"""W2-02 registered cold replay lab: COLD-LAB-001 and its immutable v4 binding revision.

`D-2026-10-17-w2-02-buildspec`: the fixture and its first conversion import as the historical
v3-compatible binding revision; `publish_v4_revision` then publishes the same eleven channel
requests at `V4_EFFECTIVE_FROM` through `BindingService.publish`, whose `cold-roles-1` rows carry
the closed v4 tuple's five metadata keys. A fresh private database reproduces the revision with
`install_cold_lab` (the walkthrough's explicit binding-publication helper). No existing revision is
mutated, and COLD-001/002 are untouched.

    python -m assetops_backend.sites.cold_lab --tenant demo
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from assetops_backend.sites.binding_conversion import convert, plan_requests
from assetops_backend.sites.binding_service import BindingPublishResult, BindingService

COLD_LAB_SITE_CODE = "COLD-LAB-001"
BACKEND = Path(__file__).resolve().parents[2]
FIXTURE_PATH = BACKEND / "tests" / "fixtures" / "w2" / "cold-lab-001.yaml"
CONVERSION_PATH = BACKEND / "conversions" / "cold-lab-001-bindings.json"
V4_EFFECTIVE_FROM = datetime(2026, 10, 1, 0, 1, tzinfo=timezone.utc)
V4_NOTE = "W2-02 v4 cold-roles-1 revision: the same eleven channels with closed v4 tuple metadata."


def conversion_fixture() -> dict[str, Any]:
    return json.loads(CONVERSION_PATH.read_text(encoding="utf-8"))


def publish_v4_revision(store, service: BindingService, tenant, site) -> BindingPublishResult:
    """Publish the immutable v4 revision of COLD-LAB-001's eleven channels at `V4_EFFECTIVE_FROM`."""
    fixture = conversion_fixture()
    revisions = store.revisions(tenant.id, site.id)
    original = next(r for r in revisions if r.origin == "IMPORT")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, _declared, _rows = plan_requests(
        fixture, site, original.content.get("signal_mappings") or (), asset_ids
    )
    return service.publish(
        tenant, site, requests=requests, effective_from=V4_EFFECTIVE_FROM, note=V4_NOTE,
        role_set=fixture["role_set"],
    )


def install_cold_lab(store, *, tenant_slug: str, clock: Callable[[], datetime], source_path: str | None = None):
    """Import COLD-LAB-001, replay its first conversion and publish the v4 revision (idempotent per step)."""
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.foundation_service import ImportSource, import_site

    source = read_import_source(str(FIXTURE_PATH))
    result = import_site(
        store, tenant_slug=tenant_slug, configured_tenant_slug=tenant_slug,
        source=ImportSource(path=source_path or "var/sites/cold-lab-001.yaml", sha256=source.sha256,
                            record=source.record),
        legacy_documents=(), clock=clock,
    )
    later = clock() + timedelta(minutes=5)
    convert(store, BindingService(store, lambda: later), result.tenant, result.site, conversion_fixture())
    if not any(s.valid_from == V4_EFFECTIVE_FROM and s.superseded_at is None
               for s in store.binding_sets(result.tenant.id, result.site.id)):
        latest = later + timedelta(minutes=5)
        publish_v4_revision(store, BindingService(store, lambda: latest), result.tenant, result.site)
    return result


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - operator entry point
    from assetops_backend.config import database_url
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    store = PostgresFoundationStore(database_url())
    result = install_cold_lab(store, tenant_slug=args.tenant, clock=lambda: datetime.now(timezone.utc))
    sets = store.binding_sets(result.tenant.id, result.site.id)
    print(json.dumps([{"version": s.version, "valid_from": s.valid_from.isoformat(), "origin": s.origin,
                       "snapshot_sha256": s.snapshot_sha256} for s in sets], indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
