"""3A1 (spec §2, §4; R6, R12, P2): the rows of migration 0063 and the results of one intake.

- `IntakeRow`, `RecordRow`, `RevisionRow` and `RejectionRow` are the four tables' rows, every column. `RevisionRow`
  also carries its record's `source_system` and `source_record_id` (read through the join; not revision columns).
- `RevisionRow.provenance` is the batch's *declared* provenance (D-3A1.9); `3A2` caps what a path may declare.
- `Plan` is what one intake decides under the tenant lock: the intake row, the rows to insert and the per-record
  outcomes (P2). The service builds `IntakeResult` from the plan the store applied, never from a pre-lock guess.
- `IntakeSummary` is the stored account of one intake (R6): the intake row, its rejections in `record_index` order
  and the IDs of the revisions it wrote. UNCHANGED records are counted, not listed; only `ingest` returns the
  per-record `RecordOutcome`s.
- `STORED` means the intake was processed and its account kept. It never means "accepted" (R17; OD-15 is `3A2`'s).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Mapping
from uuid import UUID

OUTCOMES = ("NEW", "REVISED", "UNCHANGED", "REFUSED")
INTAKE_STATES = ("STORED", "REFUSED")


@dataclass(frozen=True)
class RecordOutcome:
    """One input record's outcome, in input order. `revision_no` is the revision this intake wrote (None when it
    wrote none); `record_id` is the stored record's ID when the record is known (None for a refusal or a format
    refusal). `code` and `path` are set only on REFUSED."""
    index: int
    outcome: str
    source_record_id: str | None
    record_id: UUID | None
    revision_no: int | None
    code: str | None
    path: str | None


@dataclass(frozen=True)
class IntakeResult:
    intake_id: UUID | None  # None on a dry run (R15)
    state: str
    refusal_code: str | None
    refusal_path: str | None
    outcomes: tuple[RecordOutcome, ...]
    dry_run: bool
    basis_sha256: str | None = None  # 3A2 (D-3A2.13): the store state the decision was made against


@dataclass(frozen=True)
class IntakeRow:
    id: UUID
    tenant_id: UUID
    source_type: str | None
    source_system: str | None
    provenance: str | None
    produced_at: datetime | None
    batch_sha256: str
    state: str
    refusal_code: str | None
    refusal_path: str | None
    record_count: int
    new_count: int
    revised_count: int
    unchanged_count: int
    refused_count: int
    entered_by: str
    entered_at: datetime


@dataclass(frozen=True)
class RecordRow:
    id: UUID
    tenant_id: UUID
    site_id: UUID | None
    kind: str
    source_system: str
    source_record_id: str
    first_recorded_at: datetime


@dataclass(frozen=True)
class RevisionRow:
    id: UUID
    tenant_id: UUID
    record_id: UUID
    site_id: UUID | None
    kind: str
    revision_no: int
    source_version: str
    intake_id: UUID
    record_sha256: str
    canonical: str
    provenance: str  # declared by the batch (D-3A1.9)
    recognition_period: str | None
    occurred_at: datetime | None
    settled_at: datetime | None
    effective_from: date | None
    effective_to: date | None
    amount: Decimal | None
    currency: str | None
    quantity: Decimal | None
    unit: str | None
    status: str | None
    supersedes_revision_id: UUID | None
    recorded_at: datetime
    source_system: str
    source_record_id: str


@dataclass(frozen=True)
class RejectionRow:
    id: UUID
    tenant_id: UUID
    intake_id: UUID
    record_index: int
    source_record_id: str | None  # NULL for a 2a format refusal, the parsed ID for an INTAKE_* refusal (P3)
    code: str
    path: str
    recorded_at: datetime


@dataclass(frozen=True)
class ExistingRecord:
    """A stored record as the intake decides against it (spec §4.1). `versions` maps each source version to its
    digest; `provenances` maps each source version to its declared provenance (R12)."""
    record_id: UUID
    kind: str
    site_id: UUID | None
    versions: Mapping[str, str]
    latest_revision_id: UUID
    latest_revision_no: int
    provenances: Mapping[str, str]


@dataclass(frozen=True)
class Plan:
    intake: IntakeRow
    records: tuple[RecordRow, ...]
    revisions: tuple[RevisionRow, ...]
    rejections: tuple[RejectionRow, ...]
    outcomes: tuple[RecordOutcome, ...]
    basis_sha256: str | None = None  # 3A2 (D-3A2.13)


@dataclass(frozen=True)
class IntakeSummary:
    intake: IntakeRow
    rejections: tuple[RejectionRow, ...]
    revision_ids: tuple[UUID, ...]


class StoreRefused(Exception):
    """A database constraint refused a planned row. It carries only the constraint's name, never a row value
    (D-2A.11's class, R13): the driver's message and DETAIL print the failing row and never survive."""

    def __init__(self, constraint: str | None) -> None:
        super().__init__(constraint or "unnamed constraint")
        self.constraint = constraint


# --- 3A2 (spec §2, §3.5, §4; D-3A2.4, D-3A2.13): uploads and their decisions -----------------------------------------

@dataclass(frozen=True)
class HeldUpload:
    """3A3 (spec §2.8; D-3A3.11): an upload the tenant holds (no decision yet, or accepted)."""
    upload_id: UUID
    source_type: str
    reader: str
    file_sha256: str
    waiting: bool
    submitted_by: UUID
    source_system: str = ""  # 3A6 (spec §2.6; D-3A6.5)
    site_codes: tuple[str | None, ...] = ()  # 3A6: distinct month_site_code values, None first then sorted


@dataclass(frozen=True)
class UploadRow:
    """Every column of `commercial_upload`; arrays as tuples. `site_id` None is the organisation path."""
    id: UUID
    tenant_id: UUID
    site_id: UUID | None
    file_name: str
    file_sha256: str
    file_bytes: int
    reader: str
    source_type: str
    source_system: str
    provenance: str
    batch: str
    batch_sha256: str
    kept_index: tuple[int, ...]
    basis_sha256: str
    row_map: tuple[int, ...] | None
    record_count: int
    new_count: int
    revised_count: int
    unchanged_count: int
    refused_count: int
    refusal_index: tuple[int, ...]
    refusal_code: tuple[str, ...]
    refusal_path: tuple[str, ...]
    month_site_code: tuple[str | None, ...]
    month_period: tuple[str, ...]
    submitted_by: UUID
    submitted_role: str
    submitted_at: datetime


@dataclass(frozen=True)
class UploadDecisionRow:
    """Every column of `commercial_upload_decision`."""
    id: UUID
    tenant_id: UUID
    upload_id: UUID
    decision: str  # ACCEPTED or DECLINED
    reason: str | None
    intake_id: UUID | None
    decided_by: UUID
    decided_role: str
    decided_at: datetime


@dataclass(frozen=True)
class UploadRecord:
    """One upload as read back: its row, the display names joined from `operator_account`, its decision and, when
    accepted, the stored account of its intake."""
    upload: UploadRow
    submitted_by_name: str
    decision: UploadDecisionRow | None
    decided_by_name: str | None
    intake: IntakeSummary | None


@dataclass(frozen=True)
class Acceptance:
    """An accept of one upload: the decision row's ID, the person and role, and the basis the check recorded."""
    decision_id: UUID
    upload_id: UUID
    person_id: UUID
    role: str
    basis_sha256: str


class UploadAlreadyDecided(Exception):
    """The upload already has a decision (checked under the tenant's commercial lock)."""


class UploadStale(Exception):
    """The store state differs from the one the check decided against (D-3A2.13); nothing was written."""


class UploadSourceSwitched(Exception):
    """3A6 (spec §2.6; D-3A6.15): at acceptance, under the tenant's lock, another accepted upload of the tenant has
    the deciding upload's source type, another source system and a Site in common. `system` is the smallest such
    source system. Nothing was written."""

    def __init__(self, system: str) -> None:
        super().__init__(system)
        self.system = system


# --- 3A6 (spec §2.5, §5; D-3A6.2, D-3A6.8): admitted source profiles ----------------------------------------------

@dataclass(frozen=True)
class ProfileRow:
    """Every column of `commercial_source_profile` (`profile_row_id` is its `id`). Nothing of the sample is kept
    but its SHA-256 and row count (RC4)."""
    profile_row_id: UUID
    tenant_id: UUID
    profile_id: str
    version: int
    reader: str
    status: str
    source_type: str
    source_system: str
    file_format: str
    profile_json: str
    profile_sha256: str
    sample_sha256: str
    expected_sha256: str
    sample_rows: int
    admitted_at: datetime
    admitted_by: UUID
    admitted_role: str


# --- 3A7 (spec §3, §4; D-3A7.5, D-3A7.11, D-3A7.12): the management accounts and the tolerance ---------------------

@dataclass(frozen=True)
class StatementRow:
    """Every column of `commercial_accounts_statement`. `site_id` None is the organisation's accounts. The money
    columns keep the text the finance lead gave (two decimals), never a float."""
    id: UUID
    tenant_id: UUID
    site_id: UUID | None
    period: str
    currency: str
    revenue: str
    fuel_cost: str
    source_ref: str
    recorded_at: datetime
    recorded_by: UUID
    recorded_role: str
    recorded_by_script: bool
    result_at_record: str
    tolerance_at_record: str


@dataclass(frozen=True)
class ToleranceRow:
    """Every column of `commercial_reconciliation_tolerance` (the owner's choice for one tenant, D-3A7.12)."""
    id: UUID
    tenant_id: UUID
    tolerance: str
    owner_ref: str
    owner_ref_sha256: str
    set_at: datetime


@dataclass(frozen=True)
class SiteRow:
    """One Site of the tenant: its ID, code and type (D-3A7.11)."""
    site_id: UUID
    site_code: str
    site_type: str
