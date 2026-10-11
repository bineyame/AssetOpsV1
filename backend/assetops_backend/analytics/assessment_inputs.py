"""Typed seam between the accepted-evidence ledger and a pure analytic (S3-01 phase 2).

`EvidenceQuery` names what is asked (tenant/Site/domain, UTC half-open window,
knowledge cutoff, optional explicit cohort). `EvidenceQueryResult` is what the
repository returns: accepted public readings only (never rejected, duplicate
or conflicting deliveries), each with its exact evidence ID, envelope digest,
gateway/source/epoch/sequence/batch provenance, as-accepted Foundation and
binding revision IDs, and the server times kept apart (source, publication,
receipt, acceptance). It also returns the public configuration selected at the
cutoff: time-valid Foundation controls and the role bindings of the selected
binding sets.

`AnalyticInputSet` is the frozen input of one analytic run: the selected public
cohort's readings, the configuration, role coverage, window and model version,
with a canonical SHA-256 over all of them. Nothing in this module reads a
database, an envelope's raw JSON, a Lab run or a file-backed assessment; the
pure analytic receives this object and nothing else (D-2026-10-11-s3-dispatch-
interval-assessment, "Input and cohort").
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

#: Bracketing evidence read on each side of a window, so an interval that
#: starts inside it can be bounded and continued (dispatch-3 table, "Windows").
BRACKET = timedelta(hours=6)


def utc(instant: datetime) -> datetime:
    if instant.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware UTC")
    return instant.astimezone(timezone.utc)


def iso(instant: datetime | None) -> str | None:
    return None if instant is None else utc(instant).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class Window:
    """UTC half-open `[start, end)`."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", utc(self.start))
        object.__setattr__(self, "end", utc(self.end))
        if not self.start < self.end:
            raise ValueError("a window needs start < end")

    def contains(self, instant: datetime) -> bool:
        return self.start <= instant < self.end

    def widened(self, by: timedelta) -> "Window":
        return Window(self.start - by, self.end + by)

    def payload(self) -> dict[str, str | None]:
        return {"start": iso(self.start), "end": iso(self.end)}


@dataclass(frozen=True, order=True)
class CohortMember:
    """One public report stream: a registered source on one sequence epoch, via one gateway."""

    gateway_id: UUID
    source_id: UUID
    sequence_epoch: str

    def payload(self) -> dict[str, str]:
        return {"gateway_id": str(self.gateway_id), "source_id": str(self.source_id),
                "sequence_epoch": self.sequence_epoch}


@dataclass(frozen=True)
class EvidenceQuery:
    tenant_id: UUID
    site_id: UUID
    domain: str
    window: Window
    knowledge_at: datetime
    #: None = default selection (a unique coherent cohort, else ambiguity).
    cohort: tuple[CohortMember, ...] | None = None
    bracket: timedelta = BRACKET

    def __post_init__(self) -> None:
        object.__setattr__(self, "knowledge_at", utc(self.knowledge_at))
        if self.cohort is not None:
            object.__setattr__(self, "cohort", tuple(sorted(set(self.cohort))))

    @property
    def read_range(self) -> Window:
        return self.window.widened(self.bracket)


@dataclass(frozen=True)
class AcceptedReading:
    """One centrally accepted public reading, normalized under its as-accepted binding."""

    evidence_id: UUID
    envelope_sha256: str
    batch_id: UUID
    gateway_id: UUID
    source_id: UUID
    sequence_epoch: str
    sequence: int
    role: str
    asset_id: UUID | None
    source_time: datetime
    interval_start: datetime | None
    interval_end: datetime | None
    published_at: datetime
    received_at: datetime
    accepted_at: datetime
    quality: str
    value: str | None
    unit: str | None
    foundation_revision_id: UUID
    binding_set_revision_id: UUID
    binding_revision_id: UUID
    source_mode: str

    @property
    def member(self) -> CohortMember:
        return CohortMember(self.gateway_id, self.source_id, self.sequence_epoch)

    @property
    def placed_at(self) -> datetime:
        """Where the reading lands on the source-time axis: interval end, else source time."""
        return self.interval_end or self.source_time

    @property
    def channel(self) -> tuple[str, str]:
        return (self.role, str(self.asset_id))


@dataclass(frozen=True)
class RoleBinding:
    """A role bound to an asset by a selected binding set over `[valid_from, valid_to)`."""

    role: str
    asset_id: UUID | None
    valid_from: datetime
    valid_to: datetime | None
    binding_set_revision_id: UUID
    binding_revision_id: UUID
    role_set: str

    def effective(self, at: datetime) -> bool:
        return self.valid_from <= at and (self.valid_to is None or at < self.valid_to)


@dataclass(frozen=True)
class ControlValue:
    """A time-valid public Foundation value (selected at the knowledge cutoff)."""

    key: str
    value: str
    unit: str
    valid_from: datetime
    valid_to: datetime | None
    foundation_revision_id: UUID
    source: str

    def effective(self, at: datetime) -> bool:
        return self.valid_from <= at and (self.valid_to is None or at < self.valid_to)

    def payload(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "unit": self.unit, "valid_from": iso(self.valid_from),
                "valid_to": iso(self.valid_to), "foundation_revision_id": str(self.foundation_revision_id),
                "source": self.source}


#: Control keys the repository resolves from Foundation content.
CONTROL_BATTERY_RESERVE = "battery_reserve_soc"
CONTROL_MINIMUM_RUNTIME = "generator_minimum_runtime"


@dataclass(frozen=True)
class EvidenceQueryResult:
    query: EvidenceQuery
    readings: tuple[AcceptedReading, ...]
    bindings: tuple[RoleBinding, ...]
    controls: tuple[ControlValue, ...]
    #: Role vocabulary each selected binding set used (role_set -> roles it defines).
    role_sets: tuple[str, ...]
    #: Configuration problems found while selecting (e.g. no unique Foundation revision at an instant).
    configuration_limits: tuple[str, ...] = ()

    def watermarks(self) -> dict[str, str | None]:
        """Source, publication and receipt/acceptance watermarks, kept separate."""
        r = self.readings
        return {
            "source_time": iso(max((x.placed_at for x in r), default=None)),
            "published_at": iso(max((x.published_at for x in r), default=None)),
            "received_at": iso(max((x.received_at for x in r), default=None)),
            "accepted_at": iso(max((x.accepted_at for x in r), default=None)),
        }


@dataclass(frozen=True)
class CohortLimit:
    """A span of a selected cohort whose readings cannot be used as one public series."""

    kind: str  # SEQUENCE_ORDER_INVERTED | REPORTS_OVERLAP
    role: str
    asset_id: str
    member: CohortMember
    start: datetime
    end: datetime
    evidence_ids: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {"kind": self.kind, "role": self.role, "asset_id": self.asset_id, "member": self.member.payload(),
                "start": iso(self.start), "end": iso(self.end), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class CohortSelection:
    """The persisted public cohort choice for a window, or why none could be made."""

    status: str  # SELECTED_UNIQUE | SELECTED_EXPLICIT | AMBIGUOUS | EMPTY
    members: tuple[CohortMember, ...]
    #: For AMBIGUOUS: each source's overlapping epochs (the choices a reader can make).
    alternatives: tuple[CohortMember, ...] = ()
    limits: tuple[CohortLimit, ...] = ()
    reason: str | None = None

    @property
    def usable(self) -> bool:
        return self.status in ("SELECTED_UNIQUE", "SELECTED_EXPLICIT")

    def payload(self) -> dict[str, Any]:
        return {"status": self.status, "members": [m.payload() for m in self.members],
                "alternatives": [m.payload() for m in self.alternatives],
                "limits": [x.payload() for x in self.limits], "reason": self.reason}

    def identity(self) -> str:
        """Stable cohort identity: status plus sorted members (and alternatives when ambiguous)."""
        return sha256_json({"status": self.status, "members": [m.payload() for m in self.members],
                            "alternatives": [m.payload() for m in self.alternatives]})


@dataclass(frozen=True)
class AnalyticInputSet:
    site_id: UUID
    analytic_id: str
    model_version: str
    window: Window
    knowledge_at: datetime
    cohort: CohortSelection
    readings: tuple[AcceptedReading, ...]
    bindings: tuple[RoleBinding, ...]
    controls: tuple[ControlValue, ...]
    role_sets: tuple[str, ...]
    role_coverage: dict[str, dict[str, Any]]
    configuration_limits: tuple[str, ...]
    read_range: Window
    input_sha256: str = field(default="")

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(sorted(str(r.evidence_id) for r in self.readings))

    @property
    def foundation_revision_ids(self) -> tuple[str, ...]:
        """As-accepted (readings) and selected (controls) Foundation revisions."""
        return tuple(sorted({str(r.foundation_revision_id) for r in self.readings}
                            | {str(c.foundation_revision_id) for c in self.controls}))

    @property
    def binding_set_revision_ids(self) -> tuple[str, ...]:
        return tuple(sorted({str(r.binding_set_revision_id) for r in self.readings}
                            | {str(b.binding_set_revision_id) for b in self.bindings}))

    def canonical(self) -> dict[str, Any]:
        """Everything the input hash covers. `knowledge_at` is deliberately excluded: the
        same accepted basis read at a later cutoff is the same input (idempotent run)."""
        return {
            "site_id": str(self.site_id), "analytic_id": self.analytic_id, "model_version": self.model_version,
            "window": self.window.payload(), "read_range": self.read_range.payload(),
            "cohort": self.cohort.payload(),
            "evidence": sorted([str(r.evidence_id), r.envelope_sha256] for r in self.readings),
            "as_accepted": sorted({(str(r.foundation_revision_id), str(r.binding_set_revision_id),
                                    str(r.binding_revision_id)) for r in self.readings}),
            "controls": sorted((c.payload() for c in self.controls), key=lambda p: json.dumps(p, sort_keys=True)),
            "bindings": sorted([b.role, str(b.asset_id), iso(b.valid_from), iso(b.valid_to),
                                str(b.binding_revision_id), b.role_set] for b in self.bindings),
            "role_coverage": self.role_coverage,
            "configuration_limits": sorted(self.configuration_limits),
        }


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
                          .encode("utf-8")).hexdigest()


def role_coverage(readings: tuple[AcceptedReading, ...], bindings: tuple[RoleBinding, ...],
                  role_sets: tuple[str, ...], roles_by_set: dict[str, tuple[str, ...]]) -> dict[str, dict[str, Any]]:
    """Per role of the selected role sets: bound assets, readings, non-GOOD count. A role defined by
    no selected set is not listed; a defined but unbound role is `UNBOUND` (a missing-role limit)."""
    defined = sorted({role for s in role_sets for role in roles_by_set.get(s, ())})
    out: dict[str, dict[str, Any]] = {}
    for role in defined:
        bound = sorted({str(b.asset_id) for b in bindings if b.role == role})
        mine = [r for r in readings if r.role == role]
        out[role] = {
            "status": "BOUND" if bound else "UNBOUND",
            "assets": bound,
            "readings": len(mine),
            "not_good": sum(1 for r in mine if r.quality != "GOOD"),
            "role_sets": sorted(s for s in role_sets if role in roles_by_set.get(s, ())),
        }
    return out


def build_input_set(result: EvidenceQueryResult, cohort: CohortSelection, *, analytic_id: str,
                    model_version: str, roles_by_set: dict[str, tuple[str, ...]]) -> AnalyticInputSet:
    """Freeze the selected cohort's readings and the selected configuration into one input set."""
    chosen = set(cohort.members) if cohort.usable else set()
    readings = tuple(sorted((r for r in result.readings if r.member in chosen),
                            key=lambda r: (r.placed_at, str(r.evidence_id))))
    coverage = role_coverage(readings, result.bindings, result.role_sets, roles_by_set)
    q = result.query
    draft = AnalyticInputSet(
        site_id=q.site_id, analytic_id=analytic_id, model_version=model_version, window=q.window,
        knowledge_at=q.knowledge_at, cohort=cohort, readings=readings, bindings=result.bindings,
        controls=result.controls, role_sets=result.role_sets, role_coverage=coverage,
        configuration_limits=result.configuration_limits, read_range=q.read_range,
    )
    return AnalyticInputSet(**{**draft.__dict__, "input_sha256": sha256_json(draft.canonical())})
