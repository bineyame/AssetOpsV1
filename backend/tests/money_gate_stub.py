"""Test-only money eligibility stubs for consequence reads built without the Postgres S3/S4 lineage.

The production composition always wires `financials.money_eligibility.MoneyEligibility`; a service built without
a gate fails closed. Tests that exercise basis currentness alone pass one of these explicitly.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID


class FixedEligibility:
    def __init__(self, state: str = "ELIGIBLE") -> None:
        self.state = state

    def for_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any]:
        return {"version": "money-eligibility-1", "state": self.state, "finding_id": str(finding_id),
                "latest_finding_revision_id": None, "pending_reasons": [], "series_limits": [], "windows": [],
                "note": "test stub"}


ELIGIBLE = FixedEligibility()


class FixedProvenance:
    """S4-05b phase 2: a stored-provenance resolver stub with one fixed state. Production composes the S4-05a
    resolver; a consequence read without one reads UNKNOWN and withholds the current amount
    (`MIXED_OR_UNKNOWN_SOURCE`). Tests that exercise basis currentness alone pass `AUTHORED` explicitly."""

    def __init__(self, state: str = "AUTHORED_DEMONSTRATION") -> None:
        self.state = state

    def _block(self, tenant_id: UUID, site_id: UUID, finding_revision_id: Any, consequence_revision_id: Any = None
               ) -> dict[str, Any]:
        return {"tenant_id": str(tenant_id), "site_id": str(site_id),
                "finding_revision_id": str(finding_revision_id),
                "consequence_revision_id": None if consequence_revision_id is None else str(consequence_revision_id),
                "cited_accepted_evidence_ids": [], "power_accepted_evidence_ids": None, "state": self.state,
                "reasons": [], "accepted_evidence_ids": [], "problematic_accepted_evidence_ids": [],
                "publication_ids": [], "source_classes": [], "fixtures": [], "runs": [], "evidence": []}

    def finding_revision(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID) -> dict[str, Any]:
        return self._block(tenant_id, site_id, finding_revision_id)

    def consequence_revision(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID) -> dict[str, Any]:
        return self._block(tenant_id, site_id, "stub", consequence_revision_id)


AUTHORED = FixedProvenance()
