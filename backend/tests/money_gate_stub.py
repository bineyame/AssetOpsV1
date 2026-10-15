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
