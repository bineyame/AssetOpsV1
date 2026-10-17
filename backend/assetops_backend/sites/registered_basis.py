"""Select one registered Foundation + SignalBinding basis for a Lab run (S2-01a).

Read-only. The Lab setup boundary asks this module for the single immutable
basis a run will freeze: the Foundation revision and binding set revision that
are valid at the run's source-interval start AS RECORDED at `knowledge_at`,
with the canonical snapshot bytes stored at their publication, verified
against the stored SHA-256 and schema
(D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary).

- `knowledge_at` defaults to the store clock's now and is resolved, never left
  open, so the run can freeze the instant it was selected at.
- Every public source time the run can stamp lies in both selected revisions'
  ORIGINAL half-open valid periods. The current kernel can emit a reading at
  the run's `end_time`, so the end instant is checked too: a validity that ends
  at or before `end_time` refuses, with the boundary named.
- A superseded or ended (historical) basis is validated against its own stored
  identity; gaps in today's registration rows are reported, not used to deny
  it. A current basis still refuses on any configuration gap. Selected
  Foundation content gaps always refuse. Nothing falls back to the YAML Site,
  another revision or the current pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from assetops_backend.sites.binding_roles import serves
from assetops_backend.sites.binding_service import Snapshot, acquisition_snapshot
from assetops_backend.sites.foundation_content import record_at
from assetops_backend.sites.foundation_records import (
    BindingSetRevisionRow,
    Registrations,
    RevisionRow,
    StoredSite,
    TenantRef,
)
from assetops_backend.sites.foundation_service import (
    FoundationService,
    binding_set_at,
    revision_at,
)
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteConfigurationInvalid


class BasisRefused(Exception):
    """No registered basis can be selected. `code` is what a client switches on."""

    def __init__(self, code: str, message: str, *, boundary: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        #: True when the refusal is a validity boundary inside or at the end of
        #: the run interval, rather than an absent or invalid basis.
        self.boundary = boundary


@dataclass(frozen=True)
class RegisteredSelection:
    tenant: TenantRef
    site: StoredSite
    at: datetime
    knowledge_at: datetime
    foundation: RevisionRow
    binding_set: BindingSetRevisionRow
    snapshot: Snapshot
    registrations: Registrations
    #: The selected Foundation revision as a Site record, via the strict parser.
    record: SiteRecord


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def select_registered_basis(
    service: FoundationService,
    tenant: TenantRef,
    site: StoredSite,
    *,
    start: datetime,
    end: datetime,
    knowledge_at: datetime | None,
) -> RegisteredSelection:
    """The one registered basis covering `[start, end]`, or `BasisRefused`.

    Raises:
        BasisRefused: nothing valid can be selected; nothing was written.
        FoundationStoreError: the store could not be read (fail closed).
    """
    now = service.now()
    resolved_knowledge = now if knowledge_at is None else knowledge_at
    if resolved_knowledge > now:
        raise BasisRefused(
            "KNOWLEDGE_AT_IN_FUTURE",
            f"knowledge_at {_text(resolved_knowledge)} is after the server's now "
            f"({_text(now)}); what will have been recorded then is not known yet.",
        )
    store = service.store
    revisions = tuple(store.revisions(tenant.id, site.id))
    binding_sets = tuple(store.binding_sets(tenant.id, site.id))
    where = f"at {_text(start)} as recorded at {_text(resolved_knowledge)}"

    foundation = revision_at(revisions, start, resolved_knowledge)
    if foundation is None:
        raise BasisRefused(
            "FOUNDATION_NOT_REGISTERED",
            f"No Foundation revision of {site.site_code} was registered as effective {where}. "
            "The current configuration is not substituted.",
        )
    binding_set = binding_set_at(binding_sets, start, resolved_knowledge)
    if binding_set is None:
        raise BasisRefused(
            "BINDINGS_NOT_REGISTERED",
            f"No channel-link set of {site.site_code} was registered as effective {where}, "
            "so there is no configuration snapshot to run from.",
        )
    if binding_set.foundation_revision_id != foundation.id:
        raise BasisRefused(
            "BASIS_INCONSISTENT",
            f"Binding v{binding_set.version} selected {where} names Foundation revision "
            f"{binding_set.foundation_revision_id}, not the selected Foundation "
            f"v{foundation.version} ({foundation.id}).",
        )

    # Every public source time is in [start, end]: the end instant included,
    # because the current kernel can stamp a reading at `end_time`.
    for label, valid_to in (
        (f"Foundation v{foundation.version}", foundation.valid_to),
        (f"Binding v{binding_set.version}", binding_set.valid_to),
    ):
        if valid_to is not None and valid_to <= end:
            relation = "at the run's end_time" if valid_to == end else "inside the run interval"
            raise BasisRefused(
                "BASIS_BOUNDARY",
                f"{label} is valid until {_text(valid_to)}, {relation} "
                f"[{_text(start)}, {_text(end)}]. The Lab can stamp a public reading at "
                "end_time, so one run cannot cite one basis across that boundary; end the run "
                "before it, or start a separate run at it.",
                boundary=True,
            )

    registrations = store.registrations(tenant.id, site.id)
    snapshot = acquisition_snapshot(
        tenant.id, site, revisions, registrations, binding_set, now=now
    )
    if not isinstance(snapshot, Snapshot):
        raise BasisRefused(snapshot.code, snapshot.reason)
    # Architect amendment (S2-01a questions 1): a current Site type that the
    # selected binding role set does not serve refuses before any Draft, for a
    # historical basis too (where the current-row type gap is only reported).
    # S3-01: an older role-set version the Site type still serves remains a
    # valid basis; its bindings are read under that version's roles.
    if not serves(site.site_type, binding_set.role_set):
        raise BasisRefused(
            "SITE_TYPE_ROLE_SET_MISMATCH",
            f"Site {site.site_code} is currently of type {site.site_type!r}, which binding "
            f"v{binding_set.version}'s role set {binding_set.role_set!r} does not serve.",
        )
    try:
        # The Site row's name, type and time zone are not in the pinned
        # snapshot; the record is built from the CURRENT row plus the selected
        # revision's content. A row the strict parser refuses is a typed
        # refusal, never a substitute (open question S2-01a-questions-1).
        record = record_at(site, foundation)
    except SiteConfigurationInvalid as error:
        raise BasisRefused(
            "SITE_RECORD_INVALID",
            f"The Site row of {site.site_code} cannot be combined with Foundation "
            f"v{foundation.version}: {error}",
        ) from error
    return RegisteredSelection(
        tenant=tenant,
        site=site,
        at=start,
        knowledge_at=resolved_knowledge,
        foundation=foundation,
        binding_set=binding_set,
        snapshot=snapshot,
        registrations=registrations,
        record=record,
    )
