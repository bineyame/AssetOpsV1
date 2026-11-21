"""3A1 (spec §4.1; R4, R6, R7, P2, P7): the commercial record store port. 3A2 (spec §3.5): uploads and decisions.
3A7 (spec §4): the management accounts' statements, the tolerance rows and the Site rows."""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping, Protocol
from uuid import UUID

from assetops_backend.commercial.model import (ExistingRecord, HeldUpload, IntakeSummary, Plan, ProfileRow,
                                               RevisionRow, SiteRow, StatementRow, ToleranceRow, UploadDecisionRow,
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
        `UploadAlreadyDecided` when the upload has a decision; after the plan's rows, insert the decision.

        3A6 (spec §2.6; D-3A6.15): with an ACCEPTED `decision` and not a dry run, after that check and before
        `decide`, refuse with `UploadSourceSwitched(system)` when another accepted upload of the tenant has the
        deciding upload's source type, another source system and a `month_site_code` value in common (NULL equal to
        NULL); `system` is the smallest such source system. Nothing is written."""

    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None,
                         known_at: datetime | None = None) -> tuple[RevisionRow, ...]:
        """Each record's latest revision (by revision_no, over all its revisions), then filtered (R7); None is no
        filter (P7). Sorted by (site_id NULLS FIRST, kind, recognition_period, source_system, source_record_id).
        3A4 (D-3A4.7): with `known_at`, only revisions with `recorded_at <= known_at` are candidates, latest is
        picked over those, and only then the filters apply; a record with no revision by then does not appear."""

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

    def held_uploads(self, tenant_id: UUID) -> tuple[HeldUpload, ...]:
        """3A3 (spec §2.8): every upload of the tenant with no decision or an ACCEPTED one, by upload id. 3A6: with
        its source system and its distinct `month_site_code` values (None first, then sorted)."""

    def intake_revisions(self, tenant_id: UUID,
                         intake_id: UUID) -> tuple[tuple[RevisionRow, RevisionRow | None], ...]:
        """3A4: each revision the intake wrote, with the revision it supersedes (None for revision 1), sorted by
        (source_system, source_record_id) byte-wise. At most two statements."""

    def site_zones(self, tenant_id: UUID) -> Mapping[UUID, str]:
        """3A4: the tenant's Sites and their time zones."""

    # --- 3A6 (spec §5; D-3A6.2, D-3A6.8): admitted source profiles ---------------------------------------------

    def source_profiles_all(self, tenant_id: UUID, profile_id: str) -> tuple[ProfileRow, ...]:
        """Every admitted version of one profile, by version."""

    def source_profile_latest(self, tenant_id: UUID, profile_id: str) -> ProfileRow | None:
        """The highest admitted version of one profile, or None."""

    def source_profiles_latest(self, tenant_id: UUID) -> tuple[ProfileRow, ...]:
        """The latest version of each of the tenant's profiles, by profile_id."""

    def add_source_profile(self, row: ProfileRow) -> None:
        """Insert one admitted version; a unique key refuses with `StoreRefused(<key name>)`."""

    # --- 3A7 (spec §4; D-3A7.5, D-3A7.11, D-3A7.12): the management accounts and the tolerance -------------------

    def add_accounts_statement(self, row: StatementRow) -> None:
        """Insert one statement (append-only)."""

    def accounts_statements(self, tenant_id: UUID) -> tuple[StatementRow, ...]:
        """Every statement of the tenant, by (recorded_at, id)."""

    def add_tolerance(self, row: ToleranceRow) -> None:
        """Insert one tolerance row (append-only)."""

    def tolerances(self, tenant_id: UUID) -> tuple[ToleranceRow, ...]:
        """Every tolerance row of the tenant, by (set_at, id)."""

    def site_rows(self, tenant_id: UUID) -> tuple[SiteRow, ...]:
        """Every Site of the tenant (ID, code, type), by site_code."""
