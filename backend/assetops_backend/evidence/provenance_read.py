"""S4-05b phase 1: the exact-revision source provenance block every Finding and money read carries.

`tasks/S4-05-stored-demo-provenance.md` shared contract item 3. The block is the S4-05a resolver's answer for
one selected FindingRevision, or for one consequence revision (the union of its FindingRevision's cited set and
its own power-interval IDs). It replaces the retired date/spec heuristic (`demonstration_label.py`) in the
Finding detail, Finding Evidence, consequence and Finding Financials reads.

Fail closed: when the resolver is not composed or cannot be read, the block is `UNKNOWN` with a typed reason
and no IDs, never a positive class. Pure: no SQL and no designation command, so an HTTP module may import it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from assetops_backend.evidence.source_provenance import UNKNOWN

PROVENANCE_NOT_WIRED = "PROVENANCE_NOT_WIRED"
PROVENANCE_UNREADABLE = "PROVENANCE_UNREADABLE"
PROVENANCE_REVISION_NOT_FOUND = "PROVENANCE_REVISION_NOT_FOUND"


def unresolved(code: str, tenant_id: UUID, site_id: UUID, finding_revision_id: Any,
               consequence_revision_id: Any = None, detail: str | None = None) -> dict[str, Any]:
    """An `UNKNOWN` block that names why nothing could be resolved; no accepted ID is claimed either way."""
    reason: dict[str, Any] = {"code": code, "accepted_evidence_ids": []}
    if detail:
        reason["detail"] = detail
    return {
        "tenant_id": str(tenant_id), "site_id": str(site_id),
        "finding_revision_id": None if finding_revision_id is None else str(finding_revision_id),
        "consequence_revision_id": None if consequence_revision_id is None else str(consequence_revision_id),
        "cited_accepted_evidence_ids": [], "power_accepted_evidence_ids": None if consequence_revision_id is None
        else [], "state": UNKNOWN, "reasons": [reason], "accepted_evidence_ids": [],
        "problematic_accepted_evidence_ids": [], "publication_ids": [], "source_classes": [], "fixtures": [],
        "runs": [], "evidence": [],
        **({} if consequence_revision_id is None else {"finding_revision_state": UNKNOWN}),
    }


def finding_provenance(resolver: Any, tenant_id: UUID, site_id: UUID, finding_revision_id: Any) -> dict[str, Any]:
    """The selected FindingRevision's own cited-set provenance."""
    if resolver is None:
        return unresolved(PROVENANCE_NOT_WIRED, tenant_id, site_id, finding_revision_id)
    try:
        found = resolver.finding_revision(tenant_id, site_id, UUID(str(finding_revision_id)))
    except Exception as error:  # noqa: BLE001 - fail closed: an unreadable source is unknown, never positive
        return unresolved(PROVENANCE_UNREADABLE, tenant_id, site_id, finding_revision_id,
                          detail=type(error).__name__)
    if found is None:
        return unresolved(PROVENANCE_REVISION_NOT_FOUND, tenant_id, site_id, finding_revision_id)
    return found


def consequence_provenance(resolver: Any, tenant_id: UUID, site_id: UUID, finding_revision_id: Any,
                           consequence_revision_id: Any) -> dict[str, Any]:
    """One consequence revision's union provenance (its FindingRevision's cited set and its own power IDs)."""
    if resolver is None:
        return unresolved(PROVENANCE_NOT_WIRED, tenant_id, site_id, finding_revision_id, consequence_revision_id)
    try:
        found = resolver.consequence_revision(tenant_id, site_id, UUID(str(consequence_revision_id)))
    except Exception as error:  # noqa: BLE001 - fail closed
        return unresolved(PROVENANCE_UNREADABLE, tenant_id, site_id, finding_revision_id, consequence_revision_id,
                          detail=type(error).__name__)
    if found is None:
        return unresolved(PROVENANCE_REVISION_NOT_FOUND, tenant_id, site_id, finding_revision_id,
                          consequence_revision_id)
    return {**found, "finding_revision_id": str(found["finding_revision_id"])}
