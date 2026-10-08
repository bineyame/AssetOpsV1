"""The registered-basis adapter at the Lab setup boundary (S2-01a).

Read-only. It turns an imported Site code plus a run's source interval and
optional `knowledge_at` into the one registered Foundation + SignalBinding
basis the Draft will freeze, through the product Foundation service - never
the legacy YAML repository, which stays authoritative only for unimported
codes (D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary).

The selection rules live in `sites/registered_basis.py`; this module maps the
result onto the run's own records and its refusal vocabulary:

- the selected Foundation revision becomes the Site record the existing setup
  path freezes (topology, reserve control, devices);
- the registered binding set becomes the frozen signal mappings, one per
  binding that names an asset, keyed by the binding revision ID;
- the selection itself becomes a `RegisteredBasis` with the verified stored
  snapshot text and hash.

A store that cannot be read raises `SiteStoreUnavailable`; nothing falls back.
"""

from __future__ import annotations

from datetime import datetime, timezone

from assetops_backend.runs.models import FrozenSignalMapping, RegisteredBasis
from assetops_backend.runs.ports import RegisteredSiteSelection
from assetops_backend.runs.refusals import RunSetupRefused, refuse
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.ports import SiteStoreUnavailable
from assetops_backend.sites.registered_basis import (
    BasisRefused,
    RegisteredSelection,
    select_registered_basis,
)


def _instant(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class RegisteredLabBasis:
    """`RegisteredBasisPort` over the imported-Site registry."""

    def __init__(self, registry: ImportedSiteRegistry) -> None:
        self._registry = registry

    def registered(self, site_id: str) -> bool:
        return self._registry.imported(site_id) is not None

    def select(
        self,
        site_id: str,
        *,
        start_time: str,
        end_time: str,
        knowledge_at: str | None,
    ) -> RegisteredSiteSelection:
        service = self._registry.service
        if service is None:
            raise SiteStoreUnavailable(
                "The product Foundation store is not composed, so no registered basis can be read."
            )
        try:
            tenant = self._registry.tenant()
            site = self._registry.imported(site_id)
            if tenant is None or site is None:
                raise refuse(
                    "REGISTERED_BASIS_UNAVAILABLE",
                    f"Site {site_id} is not registered in the product Foundation store.",
                )
            selection = select_registered_basis(
                service,
                tenant,
                site,
                start=_instant(start_time),
                end=_instant(end_time),
                knowledge_at=None if knowledge_at is None else _instant(knowledge_at),
            )
        except BasisRefused as error:
            raise RunSetupRefused(
                "REGISTERED_BASIS_BOUNDARY" if error.boundary else "REGISTERED_BASIS_UNAVAILABLE",
                f"{error.message} No run was created.",
                reason_code=error.code,
            ) from error
        except FoundationStoreError as error:
            raise SiteStoreUnavailable(
                f"The product Foundation store could not be read for {site_id}: {error}"
            ) from error
        return RegisteredSiteSelection(
            site=selection.record,
            signal_mappings=_signal_mappings(selection),
            basis=_basis(selection, start_time),
            source_units=tuple(
                sorted(
                    (b.device_id, b.signal_id, b.source_unit)
                    for b in selection.binding_set.bindings
                )
            ),
        )


def _signal_mappings(selection: RegisteredSelection) -> tuple[FrozenSignalMapping, ...]:
    """The registered binding set as the run's device-signal-to-component links.

    A binding naming an asset maps to that asset's component code, which must
    be a component of the selected Foundation revision; anything else is a
    basis the Lab cannot honestly run from and is refused. A binding naming no
    asset (a Site-level role) describes no component, so it is not frozen as a
    component link; it remains in the frozen snapshot bytes.
    """
    codes = {asset.id: asset.asset_code for asset in selection.registrations.assets}
    components = {
        component.get("component_id")
        for component in selection.foundation.content.get("components") or ()
    }
    mappings: list[FrozenSignalMapping] = []
    for binding in sorted(
        selection.binding_set.bindings, key=lambda b: (b.device_id, b.signal_id)
    ):
        if binding.asset_id is None:
            continue
        code = codes.get(binding.asset_id)
        if code is None or code not in components:
            raise refuse(
                "REGISTERED_BASIS_UNAVAILABLE",
                f"Binding {binding.device_id}/{binding.signal_id} of binding "
                f"v{selection.binding_set.version} names asset {binding.asset_id}, which is "
                f"not a component of Foundation v{selection.foundation.version}. No run was created.",
            )
        mappings.append(
            FrozenSignalMapping(
                mapping_id=str(binding.id),
                device_id=binding.device_id,
                signal_id=binding.signal_id,
                component_id=code,
            )
        )
    return tuple(mappings)


def _basis(selection: RegisteredSelection, start_time: str) -> RegisteredBasis:
    foundation = selection.foundation
    binding_set = selection.binding_set
    snapshot = selection.snapshot
    return RegisteredBasis(
        tenant_id=str(selection.tenant.id),
        site_record_id=str(selection.site.id),
        foundation_revision_id=str(foundation.id),
        foundation_version=foundation.version,
        foundation_valid_from=_text(foundation.valid_from),
        foundation_valid_to=_text(foundation.valid_to),
        foundation_content_sha256=foundation.content_sha256,
        binding_set_id=str(binding_set.binding_set_id),
        binding_set_revision_id=str(binding_set.id),
        binding_set_version=binding_set.version,
        binding_valid_from=_text(binding_set.valid_from),
        binding_valid_to=_text(binding_set.valid_to),
        snapshot_schema=snapshot.schema,
        snapshot_sha256=snapshot.sha256,
        snapshot_canonical=snapshot.body.decode("utf-8"),
        source_start=start_time,
        knowledge_at=_text(selection.knowledge_at),
        site_display_name=selection.record.display_name,
        selection="CURRENT" if snapshot.current else "HISTORICAL",
        current_registration_gaps=tuple(gap.code for gap in snapshot.current_gaps),
    )
