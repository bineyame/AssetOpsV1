"""3A1 (spec §4.1; R4, R6, R7, P2, P7): the commercial record store port. 3A2 (spec §3.5): uploads and decisions."""
from __future__ import annotations

from typing import Callable, Mapping, Protocol
from uuid import UUID

from assetops_backend.commercial.model import (ExistingRecord, IntakeSummary, Plan, RevisionRow, UploadDecisionRow,
                                               UploadRecord, UploadRow)


class CommercialStore(Protocol):
    def tenant_slug(self, tenant_id: UUID) -> str | None:
        """The tenant's slug, or None for an unknown tenant."""

    def site_ids(self, tenant_id: UUID, codes: set[str]) -> dict[str, UUID]:
        """The tenant's Sites among `codes` (matched by `site_code_key`), keyed by the code as given."""

    def existing(self, tenant_id: UUID, source_system: str, ids: set[str]) -> dict[str, ExistingRecord]:
        """The stored records of (tenant, source system) among `ids`, keyed by source record ID."""

    def write_intake(self, tenant_id: UUID, source_system: str | None, ids: set[str],
                     decide: Callable[[Mapping[str, ExistingRecord]], Plan], *, dry_run: bool,
                     decision: UploadDecisionRow | None = None) -> Plan:
        """One READ COMMITTED transaction: take the tenant's commercial lock, re-read `existing` for `ids` under it,
        call `decide`, insert the plan's rows unless `dry_run`, and return the plan applied (P2).

        3A2: with `decision` and not a dry run, first (under the lock, before `decide`) refuse with
        `UploadAlreadyDecided` when the upload has a decision; after the plan's rows, insert the decision."""

    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None) -> tuple[RevisionRow, ...]:
        """Each record's latest revision (by revision_no, over all its revisions), then filtered (R7); None is no
        filter (P7). Sorted by (site_id NULLS FIRST, kind, recognition_period, source_system, source_record_id)."""

    def record_history(self, tenant_id: UUID, record_id: UUID) -> tuple[RevisionRow, ...]:
        """Every revision of one record, ascending by revision_no."""

    def intake(self, tenant_id: UUID, intake_id: UUID) -> IntakeSummary | None:
        """The stored account of one intake (R6)."""

    def add_upload(self, row: UploadRow) -> None:
        """Insert one submitted upload (3A2)."""

    def write_decline(self, row: UploadDecisionRow) -> None:
        """Under the tenant's commercial lock: `UploadAlreadyDecided` when the upload has a decision, else insert."""

    def upload(self, tenant_id: UUID, upload_id: UUID) -> UploadRecord | None:
        """One upload of the tenant, with names, decision and intake account."""

    def uploads_in_scope(self, tenant_id: UUID, site_id: UUID | None, limit: int) -> tuple[UploadRecord, ...]:
        """Exactly that Site's uploads, or the organisation's (`site_id IS NULL`); newest first by (submitted_at, id)."""
