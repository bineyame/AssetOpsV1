"""S4-05a phase 2: the exact-revision source provenance resolver.

`D-2026-10-15-s405-stored-demo-provenance`, `tasks/S4-05-stored-demo-provenance.md` shared contract item 3,
`.agent/architect-S4-05-answers.md` Q2 and Follow-up M1. One tenant/Site-scoped resolver states where a set of
accepted evidence IDs came from, from the immutable pre-admission bindings only
(`accepted_evidence.batch_id -> batch_publication_link -> evidence_publication`). Nothing here reads a date, a
spec file, a `SIMULATED`/`LIVE` mode or a Site/day match: an accepted ID without a binding is unknown
authorship, never a real measurement and never authored.

Sets resolved:

- a selected FindingRevision: its own immutable cited set (`finding_revision_evidence`), whatever the current
  head is;
- a consequence revision: the union of its FindingRevision's cited set and **its own** quantified power-interval
  IDs, reported beside both parts, so a later consequence can differ from its Finding.

Truth table (state, then typed reasons, each naming its exact accepted IDs):

| set | state |
| --- | --- |
| nonempty, every ID bound to authored publications with one fixture ID and version (any number of publications) | `AUTHORED_DEMONSTRATION` |
| nonempty, every ID bound to one registered run (one run ID and run identity digest) | `REGISTERED_SIMULATION` |
| differing fixture/version, several run IDs (N-L2: no compatible-run-basis record exists, so always), one run ID with differing identity digests, crossed classes, bound and unbound IDs mixed | `MIXED` |
| empty, no positive binding, or any missing, foreign-Site or broken accepted-ID/publication link | `UNKNOWN` |

A broken, missing or foreign-Site ID makes the whole set `UNKNOWN` even when the rest would be `MIXED`
(precedence); the reasons then name only the `UNKNOWN` causes, and `problematic_accepted_evidence_ids` names
every ID behind them.

This module is pure (no SQL, no designation command): an HTTP module may import it. S4-05a leaves the read DTOs
and the old date heuristic in place; S4-05b cuts the reads over.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol
from uuid import UUID

AUTHORED_DEMONSTRATION = "AUTHORED_DEMONSTRATION"
REGISTERED_SIMULATION = "REGISTERED_SIMULATION"
MIXED = "MIXED"
UNKNOWN = "UNKNOWN"
SOURCE_CLASSES = (AUTHORED_DEMONSTRATION, REGISTERED_SIMULATION)

# Per-ID link status.
BOUND = "BOUND"
UNBOUND = "UNBOUND"
NOT_FOUND = "NOT_FOUND"
FOREIGN_SITE = "FOREIGN_SITE"
BROKEN_LINK = "BROKEN_LINK"

# Set reasons. UNKNOWN causes first (they take precedence), then MIXED causes.
EMPTY_CITATION_SET = "EMPTY_CITATION_SET"
EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
FOREIGN_SITE_EVIDENCE = "FOREIGN_SITE_EVIDENCE"
BROKEN_PUBLICATION_LINK = "BROKEN_PUBLICATION_LINK"
NO_POSITIVE_BINDING = "NO_POSITIVE_BINDING"
BOUND_AND_UNBOUND = "BOUND_AND_UNBOUND"
CROSSED_SOURCE_CLASSES = "CROSSED_SOURCE_CLASSES"
AUTHORED_FIXTURE_VERSION_CONFLICT = "AUTHORED_FIXTURE_VERSION_CONFLICT"
MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS = "MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS"
RUN_IDENTITY_CONFLICT = "RUN_IDENTITY_CONFLICT"
CONSEQUENCE_POWER_INPUT_CONFLICT = "CONSEQUENCE_POWER_INPUT_CONFLICT"

# Broken-link details (per ID).
BATCH_NOT_FOUND = "BATCH_NOT_FOUND"
EVIDENCE_BATCH_SCOPE_MISMATCH = "EVIDENCE_BATCH_SCOPE_MISMATCH"
LINK_COMMITMENT_MISMATCH = "LINK_COMMITMENT_MISMATCH"
PUBLICATION_NOT_FOUND = "PUBLICATION_NOT_FOUND"
PUBLICATION_COMMITMENT_MISMATCH = "PUBLICATION_COMMITMENT_MISMATCH"
PUBLICATION_CLASS_INVALID = "PUBLICATION_CLASS_INVALID"


@dataclass(frozen=True)
class LinkRow:
    """The raw scoped join for one requested accepted ID, as the read adapter returns it. Commitments are
    `(tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256)` tuples, or None when the
    row was not found."""

    requested_id: str
    in_scope: bool  # an accepted_evidence row with this ID in the requested tenant/Site
    in_tenant_elsewhere: bool  # an accepted_evidence row with this ID in another Site of the same tenant
    batch_id: str | None = None
    evidence_gateway_source: tuple[str, str] | None = None
    batch: tuple[str, ...] | None = None  # the scoped ingestion_batch commitment
    link_publication_id: str | None = None
    link: tuple[str, ...] | None = None
    publication: tuple[str, ...] | None = None
    source_class: str | None = None
    fixture_id: str | None = None
    fixture_version: str | None = None
    run_id: str | None = None
    run_identity_sha256: str | None = None


@dataclass(frozen=True)
class EvidenceLink:
    accepted_evidence_id: str
    status: str
    batch_id: str | None = None
    publication_id: str | None = None
    source_class: str | None = None
    fixture_id: str | None = None
    fixture_version: str | None = None
    run_id: str | None = None
    run_identity_sha256: str | None = None
    broken_detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"accepted_evidence_id": self.accepted_evidence_id, "status": self.status,
                "batch_id": self.batch_id, "publication_id": self.publication_id,
                "source_class": self.source_class, "fixture_id": self.fixture_id,
                "fixture_version": self.fixture_version, "run_id": self.run_id,
                "run_identity_sha256": self.run_identity_sha256, "broken_detail": self.broken_detail}


def _class_coherent(row: LinkRow) -> bool:
    if row.source_class == AUTHORED_DEMONSTRATION:
        return bool(row.fixture_id and row.fixture_version) and row.run_id is None and row.run_identity_sha256 is None
    if row.source_class == REGISTERED_SIMULATION:
        return bool(row.run_id and row.run_identity_sha256) and row.fixture_id is None and row.fixture_version is None
    return False


def link_of(row: LinkRow) -> EvidenceLink:
    """One requested ID's exact provenance. Every link in the chain must agree with the scoped batch
    commitment; anything else is a broken link, never silently unbound or bound."""
    rid = row.requested_id
    if not row.in_scope:
        return EvidenceLink(rid, FOREIGN_SITE if row.in_tenant_elsewhere else NOT_FOUND)

    def broken(detail: str) -> EvidenceLink:
        return EvidenceLink(rid, BROKEN_LINK, batch_id=row.batch_id, publication_id=row.link_publication_id,
                            broken_detail=detail)

    if row.batch is None:
        return broken(BATCH_NOT_FOUND)
    if row.evidence_gateway_source != tuple(row.batch[2:4]):
        return broken(EVIDENCE_BATCH_SCOPE_MISMATCH)
    if row.link is None:
        return EvidenceLink(rid, UNBOUND, batch_id=row.batch_id)
    if row.link != row.batch:
        return broken(LINK_COMMITMENT_MISMATCH)
    if row.publication is None:
        return broken(PUBLICATION_NOT_FOUND)
    if row.publication != row.link:
        return broken(PUBLICATION_COMMITMENT_MISMATCH)
    if not _class_coherent(row):
        return broken(PUBLICATION_CLASS_INVALID)
    return EvidenceLink(rid, BOUND, batch_id=row.batch_id, publication_id=row.link_publication_id,
                        source_class=row.source_class, fixture_id=row.fixture_id,
                        fixture_version=row.fixture_version, run_id=row.run_id,
                        run_identity_sha256=row.run_identity_sha256)


def _reason(code: str, ids: Iterable[str], **detail: Any) -> dict[str, Any]:
    return {"code": code, "accepted_evidence_ids": sorted(set(ids)), **detail}


def classify(requested: Iterable[UUID | str], links: Mapping[str, EvidenceLink]) -> dict[str, Any]:
    """The set state for exactly `requested` (deduplicated), from each ID's `EvidenceLink`. An ID absent from
    `links` is not found."""
    ids = sorted({str(i) for i in requested})
    per = [links.get(i) or EvidenceLink(i, NOT_FOUND) for i in ids]
    by = {s: [e.accepted_evidence_id for e in per if e.status == s]
          for s in (BOUND, UNBOUND, NOT_FOUND, FOREIGN_SITE, BROKEN_LINK)}
    bound = [e for e in per if e.status == BOUND]
    reasons: list[dict[str, Any]] = []
    if not ids:
        state = UNKNOWN
        reasons.append(_reason(EMPTY_CITATION_SET, []))
    elif by[NOT_FOUND] or by[FOREIGN_SITE] or by[BROKEN_LINK]:
        state = UNKNOWN  # precedence over MIXED: the set cannot be read whole
        if by[NOT_FOUND]:
            reasons.append(_reason(EVIDENCE_NOT_FOUND, by[NOT_FOUND]))
        if by[FOREIGN_SITE]:
            reasons.append(_reason(FOREIGN_SITE_EVIDENCE, by[FOREIGN_SITE]))
        if by[BROKEN_LINK]:
            reasons.append(_reason(BROKEN_PUBLICATION_LINK, by[BROKEN_LINK], details=[
                {"accepted_evidence_id": e.accepted_evidence_id, "detail": e.broken_detail}
                for e in per if e.status == BROKEN_LINK]))
    elif not bound:
        state = UNKNOWN
        reasons.append(_reason(NO_POSITIVE_BINDING, by[UNBOUND]))
    else:
        if by[UNBOUND]:
            reasons.append(_reason(BOUND_AND_UNBOUND, by[UNBOUND]))
        classes = sorted({e.source_class for e in bound})
        if len(classes) > 1:
            reasons.append(_reason(CROSSED_SOURCE_CLASSES, [e.accepted_evidence_id for e in bound],
                                   source_classes=classes))
        authored = [e for e in bound if e.source_class == AUTHORED_DEMONSTRATION]
        fixtures = sorted({(e.fixture_id, e.fixture_version) for e in authored})
        if len(fixtures) > 1:
            reasons.append(_reason(AUTHORED_FIXTURE_VERSION_CONFLICT, [e.accepted_evidence_id for e in authored],
                                   fixtures=[{"fixture_id": f, "fixture_version": v} for f, v in fixtures]))
        simulated = [e for e in bound if e.source_class == REGISTERED_SIMULATION]
        runs = sorted({e.run_id for e in simulated})
        if len(runs) > 1:
            # N-L2: no compatible-run-basis record exists yet, so several runs are never coherent.
            reasons.append(_reason(MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS,
                                   [e.accepted_evidence_id for e in simulated], run_ids=runs))
        for run in runs:
            digests = sorted({e.run_identity_sha256 for e in simulated if e.run_id == run})
            if len(digests) > 1:
                reasons.append(_reason(RUN_IDENTITY_CONFLICT,
                                       [e.accepted_evidence_id for e in simulated if e.run_id == run],
                                       run_id=run, run_identity_sha256=digests))
        state = MIXED if reasons else classes[0]
    problematic = sorted({i for r in reasons for i in r["accepted_evidence_ids"]})
    return {
        "state": state,
        "reasons": reasons,
        "accepted_evidence_ids": ids,
        "problematic_accepted_evidence_ids": problematic,
        "publication_ids": sorted({e.publication_id for e in bound}),
        "source_classes": sorted({e.source_class for e in bound}),
        "fixtures": [{"fixture_id": f, "fixture_version": v} for f, v in
                     sorted({(e.fixture_id, e.fixture_version) for e in bound
                             if e.source_class == AUTHORED_DEMONSTRATION})],
        "runs": [{"run_id": r, "run_identity_sha256": d} for r, d in
                 sorted({(e.run_id, e.run_identity_sha256) for e in bound
                         if e.source_class == REGISTERED_SIMULATION})],
        "evidence": [e.as_dict() for e in per],
    }


class ProvenanceReads(Protocol):
    """Scoped, read-only rows (implemented by the ledger adapter, `PostgresEvidenceLedger`, the one evidence
    module that may use the driver). Each returns None when the named revision is not in the tenant/Site."""

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[LinkRow]: ...

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID,
                                  finding_revision_id: UUID) -> list[str] | None: ...

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID
                           ) -> tuple[str, list[str], list[str]] | None:
        """(finding_revision_id, that revision's cited IDs, this consequence revision's power-interval IDs)."""
        ...


class SourceProvenanceResolver:
    """`I-S4-05a` resolver. Read-only; the read DTOs adopt it in S4-05b."""

    def __init__(self, reads: ProvenanceReads) -> None:
        self._reads = reads

    def resolve(self, tenant_id: UUID, site_id: UUID, evidence_ids: Iterable[UUID | str]) -> dict[str, Any]:
        ids = sorted({str(i) for i in evidence_ids})
        rows = self._reads.link_rows(tenant_id, site_id, ids) if ids else []
        return classify(ids, {r.requested_id: link_of(r) for r in rows})

    def finding_revision(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID) -> dict[str, Any] | None:
        cited = self._reads.finding_revision_evidence(tenant_id, site_id, finding_revision_id)
        if cited is None:
            return None
        result = self.resolve(tenant_id, site_id, cited)
        return {"tenant_id": str(tenant_id), "site_id": str(site_id),
                "finding_revision_id": str(finding_revision_id), "consequence_revision_id": None,
                "cited_accepted_evidence_ids": result["accepted_evidence_ids"],
                "power_accepted_evidence_ids": None, **result}

    def consequence_revision(self, tenant_id: UUID, site_id: UUID,
                             consequence_revision_id: UUID) -> dict[str, Any] | None:
        inputs = self._reads.consequence_inputs(tenant_id, site_id, consequence_revision_id)
        if inputs is None:
            return None
        finding_revision_id, cited, power = inputs
        cited_ids, power_ids = sorted(set(cited)), sorted(set(power))
        ids = sorted(set(cited_ids) | set(power_ids))
        rows = self._reads.link_rows(tenant_id, site_id, ids) if ids else []
        links = {r.requested_id: link_of(r) for r in rows}
        finding_state = classify(cited_ids, links)["state"]
        result = classify(ids, links)
        if result["state"] == MIXED and finding_state != MIXED:
            power_only = sorted(set(power_ids) - set(cited_ids))
            result["reasons"].append(_reason(CONSEQUENCE_POWER_INPUT_CONFLICT, power_only,
                                             finding_revision_state=finding_state))
            result["problematic_accepted_evidence_ids"] = sorted(
                set(result["problematic_accepted_evidence_ids"]) | set(power_only))
        return {"tenant_id": str(tenant_id), "site_id": str(site_id),
                "finding_revision_id": finding_revision_id,
                "consequence_revision_id": str(consequence_revision_id),
                "cited_accepted_evidence_ids": cited_ids, "power_accepted_evidence_ids": power_ids,
                "finding_revision_state": finding_state, **result}
