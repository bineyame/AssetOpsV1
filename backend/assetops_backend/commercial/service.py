"""3A1 (spec §3; D-3A1.1 to D-3A1.12, R1, R8, R9, R10, R12, R13, R15, P2, P3): one canonical batch in, one call.

`CommercialRecords.ingest(tenant_id, data)` runs spec §3's rules in order and reports per record what happened:

1. `batch_sha256` is the SHA-256 of the bytes as received; the bytes are never stored. An envelope refusal (a
   `json` or `batch.` path) is a REFUSED intake with all counts 0, keeping only the envelope values that parsed
   before the refused one and pass their column check (R1).
2. An unknown tenant is a programming error (`LookupError`). A batch naming another tenant is REFUSED with
   `INTAKE_TENANT_MISMATCH batch.tenant_code`.
3. Records are decided in input order against a running state that includes the batch's earlier records (R9). A
   refused record is one rejection row and never stops the others.
4. A record's identity is (tenant, source system, source record ID); its kind and Site never change.
5. A new `source_version` is a revision that supersedes the last received one (R10: "latest" is arrival order; the
   source's version order is not interpreted). A known version with the same digest and provenance is UNCHANGED;
   with another digest it is `INTAKE_VERSION_CONFLICT`; with the same digest and another provenance it is
   `INTAKE_PROVENANCE_CHANGED` (R12).

The decision is made by `decide`, which the store calls under the tenant's lock with the records it re-read there
(P2), so the reported outcome is the one applied. Nothing here logs a ref, a value or `canonical` (R13); a refusal
carries 2a's bounded, ASCII-escaped path only.

3A2 (spec §3.5; D-3A2.8, D-3A2.13): `ingest` takes two keywords whose defaults keep 3A1's behaviour. `site_scope`
refuses a record not of that Site (`INTAKE_SITE_NOT_THIS_SITE`, portfolio-level records included). Every decision
records `basis_sha256`, the digest of the store state it decided against (each named record's latest revision ID and
each resolved Site); with `acceptance`, a differing basis raises `UploadStale` before planning, and an envelope or
tenant refusal raises `UploadStale` instead of writing a REFUSED intake. The decision row is written in the intake's
transaction.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Mapping
from uuid import UUID, uuid4

from assetops_backend.commercial.model import (Acceptance, ExistingRecord, IntakeResult, IntakeRow, Plan,
                                               RecordOutcome, RecordRow, RejectionRow, RevisionRow, UploadDecisionRow,
                                               UploadStale)
from assetops_backend.commercial.store import CommercialStore
from assetops_contracts.canonical.records_v1 import PROVENANCES
from assetops_contracts.canonical import (KIND_SPECS, BatchResult, CanonicalRecordV1, CanonicalRefused,
                                          loads_canonical, parse_batch, record_digest, to_canonical_json)

COMMERCIAL = "COMMERCIAL_RECORD"

#: The envelope fields in 2a's check order (`parse_batch`), each with its refusal path. A refusal at one of these
#: paths means every field before it parsed; any other envelope path means none did.
_STAGES = ("batch.tenant_code", "batch.source_type", "batch.source_system", "batch.provenance", "batch.produced_at",
           "batch.records")
_ENVELOPE_FIELDS = ("source_type", "source_system", "provenance", "produced_at")
_SOURCE_TYPE = re.compile(r"[a-z][a-z_]{0,39}", re.ASCII)


def _instant(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text)


def _day(text: str | None) -> date | None:
    return None if text is None else date.fromisoformat(text)


def _column_value(name: str, value: object) -> object | None:
    """A raw envelope value as its `commercial_intake` column holds it, or None when it fails the column's check."""
    if not isinstance(value, str):
        return None
    if name == "source_type":
        return value if _SOURCE_TYPE.fullmatch(value) else None
    if name == "source_system":
        return value if 1 <= len(value) <= 200 else None
    if name == "provenance":
        return value if value in PROVENANCES else None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else None


def _envelope_of_refusal(obj: object, path: str) -> dict[str, object | None]:
    """R1: the envelope values that parsed before the refused one, from the raw object, each only if it passes its
    column check."""
    passed = _STAGES.index(path) - 1 if path in _STAGES else 0
    out: dict[str, object | None] = dict.fromkeys(_ENVELOPE_FIELDS)
    if isinstance(obj, dict):
        for name in _ENVELOPE_FIELDS[:max(passed, 0)]:
            out[name] = _column_value(name, obj.get(name))
    return out


@dataclass
class _Known:
    """The running state of one record identity within an intake (R9)."""
    record_id: UUID
    kind: str
    site_id: UUID | None
    versions: dict[str, tuple[str, str]]  # source_version -> (digest, provenance)
    latest_id: UUID
    latest_no: int


@dataclass
class _Decision:
    tenant_id: UUID
    intake_id: UUID
    parsed: BatchResult
    sites: Mapping[str, UUID]
    envelope: Mapping[str, object]
    batch_sha256: str
    entered_by: str
    now: datetime
    site_scope: UUID | None = None
    acceptance: Acceptance | None = None
    records: list[RecordRow] = field(default_factory=list)
    revisions: list[RevisionRow] = field(default_factory=list)
    rejections: list[RejectionRow] = field(default_factory=list)
    outcomes: list[RecordOutcome] = field(default_factory=list)

    def refuse(self, index: int, source_record_id: str | None, code: str, path: str) -> None:
        self.rejections.append(RejectionRow(uuid4(), self.tenant_id, self.intake_id, index, source_record_id, code,
                                            path, self.now))
        self.outcomes.append(RecordOutcome(index, "REFUSED", source_record_id, None, None, code, path))

    def revision(self, record: CanonicalRecordV1, known: _Known, digest: str, number: int,
                 supersedes: UUID | None) -> RevisionRow:
        clocks = record.clocks
        amount, currency = record.amount if record.amount is not None else (None, None)
        quantity, unit = record.quantity if record.quantity is not None else (None, None)
        return RevisionRow(
            id=uuid4(), tenant_id=self.tenant_id, record_id=known.record_id, site_id=known.site_id, kind=known.kind,
            revision_no=number, source_version=record.source_version, intake_id=self.intake_id,
            record_sha256=digest, canonical=to_canonical_json(record).decode("utf-8"),
            provenance=self.parsed.batch.provenance, recognition_period=clocks.get("recognition_period"),
            occurred_at=_instant(clocks.get("occurred_at")), settled_at=_instant(clocks.get("settled_at")),
            effective_from=_day(clocks.get("effective_from")), effective_to=_day(clocks.get("effective_to")),
            amount=amount, currency=currency, quantity=quantity, unit=unit, status=record.status,
            supersedes_revision_id=supersedes, recorded_at=self.now,
            source_system=self.parsed.batch.source_system, source_record_id=record.source_record_id)

    def basis(self, existing: Mapping[str, ExistingRecord]) -> str:
        """D-3A2.13: the store state this decision reads: each named record's latest revision and each resolved Site."""
        lines = sorted([f"r\x1f{key}\x1f{e.latest_revision_id}" for key, e in existing.items()]
                       + [f"s\x1f{code}\x1f{site_id}" for code, site_id in self.sites.items()])
        return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

    def __call__(self, existing: Mapping[str, ExistingRecord]) -> Plan:
        basis_sha256 = self.basis(existing)
        if self.acceptance is not None and self.acceptance.basis_sha256 != basis_sha256:
            raise UploadStale()
        self.records, self.revisions, self.rejections, self.outcomes = [], [], [], []
        state = {key: _Known(e.record_id, e.kind, e.site_id,
                             {v: (d, e.provenances[v]) for v, d in e.versions.items()},
                             e.latest_revision_id, e.latest_revision_no) for key, e in existing.items()}
        provenance = self.parsed.batch.provenance
        for index, outcome in enumerate(self.parsed.outcomes):
            if isinstance(outcome, CanonicalRefused):
                self.refuse(index, None, outcome.code, outcome.path)
                continue
            record: CanonicalRecordV1 = outcome
            key = record.source_record_id
            if KIND_SPECS[record.kind].store_family != COMMERCIAL:
                self.refuse(index, key, "INTAKE_NOT_COMMERCIAL", "record.kind")
                continue
            site_id = None
            if record.site_code is not None:
                site_id = self.sites.get(record.site_code)
                if site_id is None:
                    self.refuse(index, key, "INTAKE_SITE_UNKNOWN", "record.site_code")
                    continue
            if self.site_scope is not None and site_id != self.site_scope:
                self.refuse(index, key, "INTAKE_SITE_NOT_THIS_SITE", "record.site_code")
                continue
            known = state.get(key)
            if known is not None and known.kind != record.kind:
                self.refuse(index, key, "INTAKE_KIND_CHANGED", "record.kind")
                continue
            if known is not None and known.site_id != site_id:
                self.refuse(index, key, "INTAKE_SITE_CHANGED", "record.site_code")
                continue
            digest = record_digest(record)
            if known is not None and record.source_version in known.versions:
                seen_digest, seen_provenance = known.versions[record.source_version]
                if seen_digest != digest:
                    self.refuse(index, key, "INTAKE_VERSION_CONFLICT", "record.source_version")
                elif seen_provenance != provenance:
                    self.refuse(index, key, "INTAKE_PROVENANCE_CHANGED", "record.source_version")
                else:
                    self.outcomes.append(RecordOutcome(index, "UNCHANGED", key, known.record_id, None, None, None))
                continue
            if known is None:
                known = _Known(uuid4(), record.kind, site_id, {}, uuid4(), 0)
                self.records.append(RecordRow(known.record_id, self.tenant_id, site_id, record.kind,
                                              self.parsed.batch.source_system, key, self.now))
                state[key] = known
                row = self.revision(record, known, digest, 1, None)
                label = "NEW"
            else:
                row = self.revision(record, known, digest, known.latest_no + 1, known.latest_id)
                label = "REVISED"
            self.revisions.append(row)
            known.versions[record.source_version] = (digest, provenance)
            known.latest_id, known.latest_no = row.id, row.revision_no
            self.outcomes.append(RecordOutcome(index, label, key, known.record_id, row.revision_no, None, None))
        count = {name: sum(o.outcome == name for o in self.outcomes) for name in ("NEW", "REVISED", "UNCHANGED",
                                                                                 "REFUSED")}
        intake = IntakeRow(
            id=self.intake_id, tenant_id=self.tenant_id, batch_sha256=self.batch_sha256, state="STORED",
            refusal_code=None, refusal_path=None, record_count=len(self.outcomes), new_count=count["NEW"],
            revised_count=count["REVISED"], unchanged_count=count["UNCHANGED"], refused_count=count["REFUSED"],
            entered_by=self.entered_by, entered_at=self.now, **self.envelope)
        return Plan(intake, tuple(self.records), tuple(self.revisions), tuple(self.rejections), tuple(self.outcomes),
                    basis_sha256)


class CommercialRecords:
    def __init__(self, store: CommercialStore, *, clock: Callable[[], datetime]) -> None:
        self._store = store
        self._clock = clock

    def ingest(self, tenant_id: UUID, data: bytes, *, entered_by: str, dry_run: bool = False,
               site_scope: UUID | None = None, acceptance: Acceptance | None = None) -> IntakeResult:
        slug = self._store.tenant_slug(tenant_id)
        if slug is None:
            raise LookupError("unknown tenant")  # R15: a programming error, not a stored intake
        data = bytes(data)
        batch_sha256 = hashlib.sha256(data).hexdigest()
        now = self._clock()
        intake_id = uuid4()
        obj: object = None
        try:
            obj = loads_canonical(data)
            parsed = parse_batch(obj)
        except CanonicalRefused as refused:
            if acceptance is not None:  # R6: an accepted upload never writes a REFUSED intake
                raise UploadStale() from None
            return self._refuse(tenant_id, intake_id, _envelope_of_refusal(obj, refused.path), batch_sha256,
                                refused.code, refused.path, entered_by, now, dry_run)
        batch = parsed.batch
        envelope = {"source_type": batch.source_type, "source_system": batch.source_system,
                    "provenance": batch.provenance, "produced_at": _instant(batch.produced_at)}
        if batch.tenant_code != slug:
            if acceptance is not None:
                raise UploadStale()
            return self._refuse(tenant_id, intake_id, envelope, batch_sha256, "INTAKE_TENANT_MISMATCH",
                                "batch.tenant_code", entered_by, now, dry_run)
        records = [o for o in parsed.outcomes
                   if isinstance(o, CanonicalRecordV1) and KIND_SPECS[o.kind].store_family == COMMERCIAL]
        codes = {r.site_code for r in records if r.site_code is not None}
        sites = self._store.site_ids(tenant_id, codes) if codes else {}
        decide = _Decision(tenant_id, intake_id, parsed, sites, envelope, batch_sha256, entered_by, now,
                           site_scope=site_scope, acceptance=acceptance)
        ids = {r.source_record_id for r in records}
        if acceptance is None:
            plan = self._store.write_intake(tenant_id, batch.source_system, ids, decide, dry_run=dry_run)
        else:
            decision = UploadDecisionRow(acceptance.decision_id, tenant_id, acceptance.upload_id, "ACCEPTED", None,
                                         intake_id, acceptance.person_id, acceptance.role, now)
            plan = self._store.write_intake(tenant_id, batch.source_system, ids, decide, dry_run=dry_run,
                                            decision=decision)
        return _result(plan, dry_run)

    def _refuse(self, tenant_id: UUID, intake_id: UUID, envelope: Mapping[str, object], batch_sha256: str, code: str,
                path: str, entered_by: str, now: datetime, dry_run: bool) -> IntakeResult:
        intake = IntakeRow(
            id=intake_id, tenant_id=tenant_id, batch_sha256=batch_sha256, state="REFUSED", refusal_code=code,
            refusal_path=path, record_count=0, new_count=0, revised_count=0, unchanged_count=0, refused_count=0,
            entered_by=entered_by, entered_at=now, **envelope)
        plan = Plan(intake, (), (), (), ())
        applied = self._store.write_intake(tenant_id, intake.source_system, set(), lambda _existing: plan,
                                           dry_run=dry_run)
        return _result(applied, dry_run)


def _result(plan: Plan, dry_run: bool) -> IntakeResult:
    intake = plan.intake
    return IntakeResult(None if dry_run else intake.id, intake.state, intake.refusal_code, intake.refusal_path,
                        plan.outcomes, dry_run, plan.basis_sha256)
