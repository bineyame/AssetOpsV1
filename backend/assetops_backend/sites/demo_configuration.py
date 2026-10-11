"""Publish S3-01's labelled simulated demo configuration for KOBO-001.

    python -m assetops_backend.sites.demo_configuration \
        --fixture backend/conversions/kobo-001-s3-dispatch-demo-config.json --tenant demo

Run from the repository root with `DATABASE_URL` set, the database migrated,
KOBO-001 imported and its S1-02 bindings converted. One labelled step at the
fixture's effective instant, in this order:

1. the template's generator control values as a later-effective Foundation
   revision (`FoundationService.publish_component_properties`, TEMPLATE
   provenance; decision `D-2026-10-08-s2-registered-kobo-demo-configuration`);
2. a `minigrid-roles-2` binding set carrying every current binding unchanged
   plus the two declared simulated capability channels.

Earlier periods are split, never rewritten, so roles-1 bases before the
instant stay selectable. Idempotent: a rerun publishes nothing and prints the
versions already in effect. Not an operator route.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url
from assetops_backend.sites.binding_service import BindingRefused, BindingRequest, BindingService, DeclaredSignal
from assetops_backend.sites.foundation_content import parse_utc_text, utc_text
from assetops_backend.sites.foundation_records import FoundationStore, FoundationStoreError, StoredSite, TenantRef
from assetops_backend.sites.foundation_service import (
    FoundationRefused,
    FoundationService,
    binding_set_at,
    revision_at,
    utc_now,
)
from assetops_backend.sites.ports import SiteRepositoryError

DEMO_CONFIGURATION_SCHEMA = {"id": "assetops.demo-configuration", "version": 1}
FIXTURE_KEYS = {"schema", "status", "label", "site_code", "effective_from", "component_properties", "bindings"}


class DemoConfigurationConflict(Exception):
    """The fixture does not fit the Site; nothing was written."""


@dataclass(frozen=True)
class DemoConfigurationResult:
    label: str
    effective_from: datetime
    properties_published: bool
    bindings_published: bool
    foundation_version: int
    foundation_revision_id: str
    binding_set_id: str
    binding_version: int
    role_set: str
    snapshot_sha256: str | None
    capability_channels: tuple[str, ...]

    def to_wire(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "effective_from": utc_text(self.effective_from),
            "properties_published": self.properties_published,
            "bindings_published": self.bindings_published,
            "foundation_version": self.foundation_version,
            "foundation_revision_id": self.foundation_revision_id,
            "binding_set_id": self.binding_set_id,
            "binding_version": self.binding_version,
            "role_set": self.role_set,
            "snapshot_sha256": self.snapshot_sha256,
            "capability_channels": list(self.capability_channels),
        }


def _check(fixture: Mapping[str, Any], site: StoredSite) -> None:
    if set(fixture) != FIXTURE_KEYS:
        raise DemoConfigurationConflict(f"Fixture fields must be exactly {sorted(FIXTURE_KEYS)}; got {sorted(fixture)}.")
    if fixture["schema"] != DEMO_CONFIGURATION_SCHEMA:
        raise DemoConfigurationConflict(f"Unsupported fixture schema {fixture['schema']!r}.")
    if "SIMULATED DEMO CONFIGURATION" not in str(fixture["status"]):
        raise DemoConfigurationConflict("The fixture status must label it SIMULATED DEMO CONFIGURATION.")
    if str(fixture["site_code"]).lower() != site.site_code.lower():
        raise DemoConfigurationConflict(f"The fixture is for {fixture['site_code']}, not {site.site_code}.")


def _requests(current: Sequence[Any], add: Sequence[Mapping[str, Any]], asset_ids: Mapping[str, str]
              ) -> list[BindingRequest]:
    requests = [
        BindingRequest(
            device_id=b.device_id, signal_id=b.signal_id,
            asset_id=None if b.asset_id is None else str(b.asset_id), role=b.role,
            source_unit=b.source_unit, canonical_unit=b.canonical_unit, conversion=dict(b.conversion),
        )
        for b in current
    ]
    for index, item in enumerate(add):
        if item["asset_code"] not in asset_ids:
            raise DemoConfigurationConflict(f"bindings.add[{index}] names an unregistered asset {item['asset_code']!r}.")
        requests.append(
            BindingRequest(
                device_id=item["device_id"], signal_id=item["signal_id"], asset_id=asset_ids[item["asset_code"]],
                role=item["role"], source_unit=item["source_unit"], canonical_unit=item["canonical_unit"],
                conversion=item["conversion"],
            )
        )
    return requests


def apply_demo_configuration(
    store: FoundationStore,
    foundation: FoundationService,
    bindings: BindingService,
    tenant: TenantRef,
    site: StoredSite,
    fixture: Mapping[str, Any],
) -> DemoConfigurationResult:
    """Publish the labelled demo configuration once; a rerun writes nothing."""
    _check(fixture, site)
    effective_from = parse_utc_text(fixture["effective_from"])
    props = fixture["component_properties"]
    properties_published = True
    try:
        foundation.publish_component_properties(
            tenant, site, asset_code=props["asset_code"], properties=props["properties"],
            effective_from=effective_from, note=props["note"],
        )
    except FoundationRefused as error:
        if error.code != "FOUNDATION_NO_CHANGE":
            raise DemoConfigurationConflict(f"{error.code}: {error.message}") from error
        properties_published = False

    spec = fixture["bindings"]
    wanted = {(a["device_id"], a["signal_id"], a["role"]) for a in spec["add"]}
    far = datetime(9999, 1, 1, tzinfo=effective_from.tzinfo)  # below the open-ended sentinel
    current = binding_set_at(store.binding_sets(tenant.id, site.id), effective_from, far)
    if current is None:
        raise DemoConfigurationConflict(
            f"{site.site_code} has no binding set at {utc_text(effective_from)}; convert its bindings first."
        )
    have = {(b.device_id, b.signal_id, b.role) for b in current.bindings}
    bindings_published = False
    if not (current.role_set == spec["role_set"] and wanted <= have):
        asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
        kept = [b for b in current.bindings if (b.device_id, b.signal_id) not in {(d, s) for d, s, _ in wanted}]
        try:
            bindings.publish(
                tenant, site, requests=_requests(kept, spec["add"], asset_ids), effective_from=effective_from,
                note=spec["note"],
                declare=[DeclaredSignal(d["device_id"], d["signal_id"], d["display_name"], d["unit"])
                         for d in spec["declare_signals"]],
                role_set=spec["role_set"],
            )
        except BindingRefused as error:
            raise DemoConfigurationConflict(f"{error.code}: {error.message}") from error
        bindings_published = True

    sets = store.binding_sets(tenant.id, site.id)
    revisions = store.revisions(tenant.id, site.id)
    now = far
    selected = binding_set_at(sets, effective_from, now)
    revision = revision_at(revisions, effective_from, now)
    if selected is None or revision is None:
        raise DemoConfigurationConflict("The published demo configuration is not readable at its effective instant.")
    channels = tuple(sorted(f"{b.device_id}/{b.signal_id}->{b.role}" for b in selected.bindings
                            if (b.device_id, b.signal_id, b.role) in wanted))
    return DemoConfigurationResult(
        label=str(fixture["label"]), effective_from=effective_from,
        properties_published=properties_published, bindings_published=bindings_published,
        foundation_version=revision.version, foundation_revision_id=str(revision.id),
        binding_set_id=str(selected.binding_set_id), binding_version=selected.version,
        role_set=selected.role_set, snapshot_sha256=selected.snapshot_sha256,
        capability_channels=channels,
    )


def main(argv: Sequence[str] | None = None) -> int:
    import json

    from assetops_backend.sites.composition import build_foundation_store, read_binding_conversion_fixture

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--tenant", required=True)
    args = parser.parse_args(argv)
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    try:
        fixture, fixture_path, fixture_sha = read_binding_conversion_fixture(args.fixture)
        store = build_foundation_store(database_url())
        foundation = FoundationService(store, DEVELOPMENT_TENANT_SLUG, utc_now)
        tenant = foundation.tenant()
        site = foundation.site(tenant, str(fixture.get("site_code", "")))
        if site is None:
            print(f"Site {fixture.get('site_code')!r} is not imported in tenant {args.tenant!r}.", file=sys.stderr)
            return 2
        result = apply_demo_configuration(store, foundation, BindingService(store, utc_now), tenant, site, fixture)
    except DemoConfigurationConflict as error:
        print(f"Demo configuration refused; nothing more was written. {error}", file=sys.stderr)
        return 2
    except (FoundationStoreError, SiteRepositoryError) as error:
        print(f"Demo configuration failed: {error}", file=sys.stderr)
        return 1
    print(f"SIMULATED DEMO CONFIGURATION {result.label} from `{fixture_path}` (sha256 {fixture_sha}).")
    print(json.dumps(result.to_wire(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
