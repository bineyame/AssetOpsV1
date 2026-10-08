"""Convert an imported Site's legacy `signal_mappings` into its first binding set (S1-02).

The conversion fixture states every role, unit and conversion explicitly; no
role is inferred from a mapping label. Each legacy mapping must be covered by
exactly one fixture binding with the same device, signal and asset, and the
fixture may add bindings for signals it declares jointly (the first atomic
Foundation-plus-binding publication). The legacy mappings stay in the
Foundation content as comparison evidence; nothing here edits them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from assetops_backend.sites.binding_service import (
    BindingPublishResult,
    BindingRefused,
    BindingRequest,
    BindingService,
    DeclaredSignal,
)
from assetops_backend.sites.foundation_content import parse_utc_text
from assetops_backend.sites.foundation_records import FoundationStore, StoredSite, TenantRef

CONVERSION_SCHEMA = {"id": "assetops.binding-conversion", "version": 1}
FIXTURE_KEYS = frozenset(
    {"schema", "status", "site_code", "role_set", "effective_from", "note", "declare_signals", "bindings"}
)
FIXTURE_BINDING_KEYS = frozenset(
    {"legacy_mapping_id", "device_id", "signal_id", "asset_code", "role", "source_unit",
     "canonical_unit", "conversion"}
)
ORIGINAL_VALID_FROM = "FOUNDATION_ORIGINAL_VALID_FROM"


class ConversionConflict(Exception):
    """The fixture does not match the imported Site; nothing was written."""


@dataclass(frozen=True)
class ComparisonRow:
    legacy_mapping_id: str | None
    device_id: str
    signal_id: str
    legacy_component: str | None
    asset_code: str
    role: str
    units: str
    conversion_kind: str


@dataclass(frozen=True)
class ConversionResult:
    created: bool
    rows: tuple[ComparisonRow, ...]
    effective_from: datetime
    published: BindingPublishResult | None


def _fail(message: str) -> ConversionConflict:
    return ConversionConflict(message)


def plan_requests(
    fixture: Mapping[str, Any],
    site: StoredSite,
    legacy_mappings: Sequence[Mapping[str, Any]],
    asset_ids: Mapping[str, str],
) -> tuple[list[BindingRequest], list[DeclaredSignal], list[ComparisonRow]]:
    if set(fixture) != FIXTURE_KEYS:
        raise _fail(f"Fixture fields must be exactly {sorted(FIXTURE_KEYS)}; got {sorted(fixture)}.")
    if fixture["schema"] != CONVERSION_SCHEMA:
        raise _fail(f"Unsupported fixture schema {fixture['schema']!r}.")
    if fixture["site_code"].lower() != site.site_code.lower():
        raise _fail(f"The fixture is for {fixture['site_code']}, not {site.site_code}.")
    legacy = {m["mapping_id"]: m for m in legacy_mappings}
    seen: set[str] = set()
    requests: list[BindingRequest] = []
    rows: list[ComparisonRow] = []
    for index, item in enumerate(fixture["bindings"]):
        if set(item) != FIXTURE_BINDING_KEYS:
            raise _fail(f"bindings[{index}] fields must be exactly {sorted(FIXTURE_BINDING_KEYS)}.")
        mapping_id = item["legacy_mapping_id"]
        component = None
        if mapping_id is not None:
            mapping = legacy.get(mapping_id)
            if mapping is None:
                raise _fail(f"bindings[{index}] names legacy mapping {mapping_id!r}, which the Foundation lacks.")
            if mapping_id in seen:
                raise _fail(f"Legacy mapping {mapping_id!r} is converted twice.")
            seen.add(mapping_id)
            component = mapping["component_id"]
            if (mapping["device_id"], mapping["signal_id"], component) != (
                item["device_id"], item["signal_id"], item["asset_code"]
            ):
                raise _fail(
                    f"bindings[{index}] does not match legacy mapping {mapping_id!r} "
                    f"({mapping['device_id']} / {mapping['signal_id']} -> {component})."
                )
        if item["asset_code"] not in asset_ids:
            raise _fail(f"bindings[{index}] names asset {item['asset_code']!r}, not registered to {site.site_code}.")
        requests.append(
            BindingRequest(
                device_id=item["device_id"],
                signal_id=item["signal_id"],
                asset_id=asset_ids[item["asset_code"]],
                role=item["role"],
                source_unit=item["source_unit"],
                canonical_unit=item["canonical_unit"],
                conversion=item["conversion"],
            )
        )
        rows.append(
            ComparisonRow(
                legacy_mapping_id=mapping_id,
                device_id=item["device_id"],
                signal_id=item["signal_id"],
                legacy_component=component,
                asset_code=item["asset_code"],
                role=item["role"],
                units=f"{item['source_unit']} -> {item['canonical_unit']}",
                conversion_kind=item["conversion"]["kind"] if isinstance(item["conversion"], dict) else "?",
            )
        )
    unconverted = sorted(set(legacy) - seen)
    if unconverted:
        raise _fail(f"Legacy mappings {unconverted} have no explicit conversion in the fixture.")
    declared = [
        DeclaredSignal(d["device_id"], d["signal_id"], d["display_name"], d["unit"])
        for d in fixture["declare_signals"]
    ]
    return requests, declared, rows


def convert(
    store: FoundationStore,
    service: BindingService,
    tenant: TenantRef,
    site: StoredSite,
    fixture: Mapping[str, Any],
) -> ConversionResult:
    """Publish the first binding set once; a rerun reports the existing one."""
    revisions = store.revisions(tenant.id, site.id)
    original = next((r for r in revisions if r.origin == "IMPORT"), None)
    if original is None:
        raise _fail(f"{site.site_code} has no imported Foundation revision to convert from.")
    asset_ids = {a.asset_code: str(a.id) for a in store.registrations(tenant.id, site.id).assets}
    requests, declared, rows = plan_requests(
        fixture, site, original.content.get("signal_mappings") or (), asset_ids
    )
    effective = fixture["effective_from"]
    effective_from = original.valid_from if effective == ORIGINAL_VALID_FROM else parse_utc_text(effective)
    existing = [s for s in store.binding_sets(tenant.id, site.id) if s.origin == "CONVERSION"]
    if existing:
        return ConversionResult(False, tuple(rows), effective_from, None)
    try:
        published = service.publish(
            tenant, site, requests=requests, effective_from=effective_from,
            note=fixture["note"], declare=declared, origin="CONVERSION",
        )
    except BindingRefused as error:
        raise ConversionConflict(f"{error.code}: {error.message}") from error
    return ConversionResult(True, tuple(rows), effective_from, published)
