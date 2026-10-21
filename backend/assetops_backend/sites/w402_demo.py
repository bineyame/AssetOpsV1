"""W4-02 MG-W402-001: the isolated authored mini-grid depth demonstration Site and its `minigrid-roles-4` bindings.

`D-2026-10-20-w4-02-buildspec` closure 4 S5 and closure 5 (with q1 ruling 1). The fixture imports as the Site's
first Foundation revision; on the first install the exact channel requests of `mg-w402-001-minigrid-roles-4.json`
publish at the Foundation's `valid_from` through `BindingService.publish(..., role_set="minigrid-roles-4")`, so the
three authored v4 rows carry their pinned `authored-mini-depth-cases/1` metadata and every other row stays a v3
binding. An identical rerun returns the persisted Site and binding revision and publishes nothing; a changed
import digest/path remains `ImportConflict`. KOBO-001 is never touched.

    python -m assetops_backend.sites.w402_demo --tenant demo
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from assetops_backend.sites.binding_conversion import plan_requests
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4
from assetops_backend.sites.binding_service import BindingService
from assetops_backend.sites.composition import (
    legacy_site_documents,
    read_binding_conversion_fixture,
    read_site_import_source,
)
from assetops_backend.sites.foundation_service import LegacyDocument
from assetops_backend.sites.identity import site_id_key

MG_W402_SITE_CODE = "MG-W402-001"
BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_PATH = os.path.join(BACKEND, "tests", "fixtures", "w4", "mg-w402-001.yaml")
CONVERSION_PATH = os.path.join(BACKEND, "conversions", "mg-w402-001-minigrid-roles-4.json")


def binding_fixture() -> dict[str, Any]:
    return read_binding_conversion_fixture(CONVERSION_PATH)[0]


@dataclass(frozen=True)
class MgW402Install:
    """The import result plus the Site's one `minigrid-roles-4` binding revision."""

    result: Any
    binding_set: Any
    published: bool


def install_mg_w402_site(store, *, tenant_slug: str, clock: Callable[[], datetime],
                         legacy_documents: Sequence[LegacyDocument] = ()) -> MgW402Install:
    """Import MG-W402-001 and publish its first binding revision (idempotent per step). `legacy_documents` are the
    legacy YAML Site documents the import is checked against (the operator entry passes the real stores')."""
    from assetops_backend.sites.foundation_service import import_site

    source = read_site_import_source(FIXTURE_PATH)
    result = import_site(store, tenant_slug=tenant_slug, configured_tenant_slug=tenant_slug, source=source,
                         legacy_documents=legacy_documents, clock=clock)
    tenant, site = result.tenant, result.site
    # q12-6 (final review B-L2): only when no legacy document declares this Site is there no legacy evidence set to
    # compare; then record that explicit basis with the import (idempotent). A Site a legacy document declares gets
    # no basis and keeps the S2 Evidence comparison. It is never inferred from a missing comparison.
    if not any(site_id_key(d.site_code) == site_id_key(site.site_code) for d in legacy_documents):
        store.record_no_legacy_evidence_basis(tenant.id, site.id, now=clock())
    existing = store.binding_sets(tenant.id, site.id)
    if existing:
        return MgW402Install(result, existing[0], False)
    fixture = binding_fixture()
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, declared, _rows = plan_requests(fixture, site, result.revision.content.get("signal_mappings") or (),
                                              asset_ids)
    published = BindingService(store, clock).publish(
        tenant, site, requests=requests, declare=declared, effective_from=result.revision.valid_from,
        note=fixture["note"], role_set=ROLE_SET_MINIGRID_4,
    )
    return MgW402Install(result, published.changed, True)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - operator entry point
    from assetops_backend.config import database_url
    from assetops_backend.sites.composition import build_foundation_store

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    store = build_foundation_store(database_url())
    installed = install_mg_w402_site(store, tenant_slug=args.tenant, clock=lambda: datetime.now(timezone.utc),
                                     legacy_documents=legacy_site_documents())
    site = installed.result.site
    regs = store.registrations(installed.result.tenant.id, site.id)
    print(json.dumps({
        "site_code": site.site_code, "site_id": str(site.id), "published": installed.published,
        "foundation_revision_id": str(installed.result.revision.id),
        "binding_set_revision_id": str(installed.binding_set.id),
        "role_set": installed.binding_set.role_set, "snapshot_sha256": installed.binding_set.snapshot_sha256,
        "gateways": {g.gateway_external_id: str(g.id) for g in regs.gateways},
        "sources": {s.source_external_id: str(s.id) for s in regs.sources},
        "assets": {a.asset_code: str(a.id) for a in regs.assets},
    }, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
