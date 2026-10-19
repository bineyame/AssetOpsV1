"""W2-05a registered EV charging lab: EV-LAB-001 and its first complete `ev-roles-1` binding revision.

`D-2026-10-18-w2-05-buildspec` Q1/Q6/Q8: the fixture imports as the Site's first Foundation revision, and the
fifteen exact `simulator-lab-gateway-ev/1` channel requests of `ev-lab-001-bindings.json` publish at the
Foundation's `valid_from` through `BindingService.publish`, so every row carries the closed v4 entry's five
metadata keys. EV-LAB-001 has no historical v3 conversion, so nothing is replayed through
`binding_conversion.convert` (whose CONVERSION origin carries no v4 metadata). Gap examples are later
revisions of this same Site, made by tests in isolated stores; nothing here creates them.

    python -m assetops_backend.sites.ev_lab --tenant demo
    python -m assetops_backend.sites.ev_lab --tenant demo --republish-corrected-bindings
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from assetops_backend.sites.binding_conversion import plan_requests
from assetops_backend.sites.binding_service import BindingPublishResult, BindingService
from assetops_backend.sites.composition import read_binding_conversion_fixture, read_site_import_source
from assetops_backend.sites.foundation_records import TenantNotFound

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


#: q4 Q19: the corrected map's normal re-publication on an already installed EV-LAB-001.
RUN_WINDOW_START = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
CORRECTED_EFFECTIVE_FROM = datetime(2026, 10, 5, tzinfo=timezone.utc)
CORRECTED_NOTE = "Correct EV-LAB-001 connector state maps to include UNPLUGGED for ev-publication/1."
CORRECTED_STATE_LABELS = ("AVAILABLE", "UNPLUGGED", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")
#: The first 05a map: the seven Q15 labels without `UNPLUGGED`.
OLD_STATE_LABELS = tuple(label for label in CORRECTED_STATE_LABELS if label != "UNPLUGGED")


class EvLabRepublishRefused(Exception):
    """The installed EV-LAB-001 binding timeline is not the known old 05a shape; nothing was published."""


@dataclass(frozen=True)
class RepublishResult:
    published: bool
    #: The binding revision selected for the 6 October run window after the action.
    revision_id: str
    snapshot_sha256: str


def _selected_at(store, tenant, site, at: datetime):
    current = [s for s in store.binding_sets(tenant.id, site.id) if s.superseded_at is None
               and s.valid_from <= at and (s.valid_to is None or at < s.valid_to)]
    if len(current) != 1:
        raise EvLabRepublishRefused(
            f"{EV_LAB_SITE_CODE} has {len(current)} current binding revisions at {at.isoformat()}; expected one. "
            "Nothing was published.")
    return current[0]


def _state_maps(binding_set) -> list[Any]:
    return [b.conversion.get("parameters", {}).get("map") for b in binding_set.bindings
            if b.role == "ev_connector_state"]


def _identity(labels) -> dict[str, str]:
    return {label: label for label in labels}


def _row_shape(device_id, signal_id, asset_id, role, source_unit, canonical_unit, conversion) -> tuple:
    return (device_id, signal_id, str(asset_id), role, source_unit, canonical_unit,
            json.dumps(conversion, sort_keys=True))


def republish_corrected_bindings(store, *, tenant_slug: str, clock: Callable[[], datetime]) -> RepublishResult:
    """q4 Q19: publish the corrected `ev-lab-001-bindings.json` once, effective 5 October, on an installed
    EV-LAB-001 whose selected 6 October revision is still the first 05a map. Idempotent: a selected map that
    already has all seven identity labels publishes nothing. The old row is never rewritten; an unexpected
    shape or a later independent publication refuses and writes nothing."""
    try:
        tenant = store.resolve_tenant(tenant_slug)
    except TenantNotFound as missing:
        raise EvLabRepublishRefused(f"{missing} Nothing was published.") from missing
    site = store.find_site(tenant.id, EV_LAB_SITE_CODE)
    if site is None:
        raise EvLabRepublishRefused(f"{EV_LAB_SITE_CODE} is not installed for tenant {tenant_slug!r}.")
    selected = _selected_at(store, tenant, site, RUN_WINDOW_START)
    maps = _state_maps(selected)
    if len(maps) == 2 and all(m == _identity(CORRECTED_STATE_LABELS) for m in maps):
        return RepublishResult(False, str(selected.id), selected.snapshot_sha256)

    fixture = binding_fixture()
    original = next(r for r in store.revisions(tenant.id, site.id) if r.origin == "IMPORT")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, _declared, _rows = plan_requests(
        fixture, site, original.content.get("signal_mappings") or (), asset_ids)

    def old(conversion):
        if conversion.get("kind") == "ENUM":
            return {"kind": "ENUM", "parameters": {"map": _identity(OLD_STATE_LABELS)}}
        return conversion

    expected = sorted(_row_shape(r.device_id, r.signal_id, r.asset_id, r.role, r.source_unit, r.canonical_unit,
                                 old(r.conversion) if r.role == "ev_connector_state" else r.conversion)
                      for r in requests)
    stored = sorted(_row_shape(b.device_id, b.signal_id, b.asset_id, b.role, b.source_unit, b.canonical_unit,
                               b.conversion) for b in selected.bindings)
    if selected.role_set != fixture["role_set"] or stored != expected:
        raise EvLabRepublishRefused(
            f"The {EV_LAB_SITE_CODE} binding revision {selected.id} selected for {RUN_WINDOW_START.isoformat()} "
            "is not the known first EV-LAB-001 map; nothing was published.")
    if selected.valid_from > CORRECTED_EFFECTIVE_FROM:
        raise EvLabRepublishRefused(
            f"The {EV_LAB_SITE_CODE} binding revision {selected.id} starts {selected.valid_from.isoformat()}, after "
            f"the correction's {CORRECTED_EFFECTIVE_FROM.isoformat()}; nothing was published.")
    # Later Foundation-aligned copies of the same rows are not independent publications (`BindingService` reaches
    # through them); any other later current revision would be overwritten.
    later = [s for s in store.binding_sets(tenant.id, site.id) if s.superseded_at is None and s.id != selected.id
             and s.valid_from > selected.valid_from
             and sorted(_row_shape(b.device_id, b.signal_id, b.asset_id, b.role, b.source_unit, b.canonical_unit,
                                   b.conversion) for b in s.bindings) != stored]
    if later:
        raise EvLabRepublishRefused(
            f"{EV_LAB_SITE_CODE} has a later binding publication from {later[0].valid_from.isoformat()} that the "
            "correction would overwrite; nothing was published.")
    BindingService(store, clock).publish(
        tenant, site, requests=requests, declare=(), effective_from=CORRECTED_EFFECTIVE_FROM, note=CORRECTED_NOTE,
        role_set=fixture["role_set"])
    after = _selected_at(store, tenant, site, RUN_WINDOW_START)
    return RepublishResult(True, str(after.id), after.snapshot_sha256)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - operator entry point
    from assetops_backend.config import database_url
    from assetops_backend.sites.composition import build_foundation_store

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--republish-corrected-bindings", action="store_true",
                        help="q4 Q19: publish the corrected connector state maps on an installed EV-LAB-001.")
    args = parser.parse_args(argv)
    store = build_foundation_store(database_url())
    if args.republish_corrected_bindings:
        try:
            outcome = republish_corrected_bindings(store, tenant_slug=args.tenant,
                                                   clock=lambda: datetime.now(timezone.utc))
        except EvLabRepublishRefused as refused:
            print(f"refused: {refused}")
            return 1
        print(json.dumps({"published": outcome.published, "binding_set_revision_id": outcome.revision_id,
                          "snapshot_sha256": outcome.snapshot_sha256}, indent=2))
        return 0
    result = install_ev_lab(store, tenant_slug=args.tenant, clock=lambda: datetime.now(timezone.utc))
    sets = store.binding_sets(result.tenant.id, result.site.id)
    print(json.dumps([{"version": s.version, "valid_from": s.valid_from.isoformat(), "origin": s.origin,
                       "snapshot_sha256": s.snapshot_sha256} for s in sets], indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
