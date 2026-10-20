"""W3-01 commit 1: the shared public `source_provenance` DTO boundary.

`D-2026-10-20-shared-provenance-dto` with its review-closure and review-closure-2 amendments (`.ai/DECISIONS.md`)
and `.agent/W3-01-build-spec.md` "Shared provenance DTO resolution", "Review closure" B8/B10 and "Review closure 2"
D2/D6. One public wire shape across W1, cold and EV:

    {classification, state, source_ids, evidence_ids, basis_sha256, reasons[, detail]}

- `classification` is the exact-ID resolver state (`AUTHORED_DEMONSTRATION|REGISTERED_SIMULATION|MIXED|UNKNOWN`);
  `state` is the compatibility alias, always equal to it, for the existing W1 readers.
- The class basis is only `SourceProvenanceResolver` over the full, deduplicated cited accepted-ID set of one
  Site, never a page subset, run mode or earlier head. Resolution is per Site; no cross-Site union is classified.
- `evidence_ids` keeps every cited accepted UUID, including missing and foreign ones; `source_ids` holds only the
  `source_id` of accepted rows found in the requested tenant/Site.
- `basis_sha256` is a provenance *selection digest* (`sha256:` + SHA-256 of sorted-key compact JSON
  `{version:"source-provenance-basis/1",tenant_id,site_id,selected_revision_ids,accepted_evidence_ids}`), never a
  Finding or consequence economic basis hash. Any selected revision gives a digest, even for an empty cited set;
  only no selection gives null. Which IDs a domain row selects is the caller's input, never guessed here.
- `reasons` and the optional `detail` (the resolver's nine keys) are canonically sorted; `detail.reasons` equals
  the top-level `reasons`. Typed resolver extras are preserved.
- A consequence keeps `SourceProvenanceResolver.consequence_revision`'s fail-closed Finding conflict.
- Run 1 rulings (q1), `.agent/W3-01-build-spec.md`: ruling 2 fixes each represented row's selected-ID set (the
  `*_selection` helpers name them; the W1 Finding/consequence sets are derived here by default); ruling 4 is the
  selected-EV persisted-class adapter (`PublicProvenance.ev_selected`); ruling 5 the pending dual blocks
  (`dual_blocks`); ruling 6 the estate six-key projection (`estate_projection`, or `detail=False`).

Pure apart from the `ProvenanceReads` port it is handed (no SQL, no driver import): the caller passes reads bound
to its own connection when it needs one transaction. Nothing persisted is read for change or mutated.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

from assetops_backend.evidence.source_provenance import (
    UNKNOWN,
    LinkRow,
    ProvenanceReads,
    SourceProvenanceResolver,
)

BASIS_VERSION = "source-provenance-basis/1"

#: The resolver's nine result keys that `detail` mirrors (`source_provenance.py:classify`).
DETAIL_KEYS = ("state", "reasons", "accepted_evidence_ids", "problematic_accepted_evidence_ids", "publication_ids",
               "source_classes", "fixtures", "runs", "evidence")

_PUBLIC_KEYS = ("classification", "state", "source_ids", "evidence_ids", "basis_sha256", "reasons")


def _ids(values: Iterable[UUID | str]) -> list[str]:
    """Sorted, deduplicated, lowercase UUID text."""
    return sorted({str(v).lower() for v in values})


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def basis_sha256(tenant_id: UUID | str, site_id: UUID | str, selected_revision_ids: Iterable[UUID | str],
                 accepted_evidence_ids: Iterable[UUID | str]) -> str | None:
    """The provenance selection digest; None only when nothing is selected."""
    selected = _ids(selected_revision_ids)
    if not selected:
        return None
    doc = {"version": BASIS_VERSION, "tenant_id": str(tenant_id).lower(), "site_id": str(site_id).lower(),
           "selected_revision_ids": selected, "accepted_evidence_ids": _ids(accepted_evidence_ids)}
    return "sha256:" + hashlib.sha256(_canonical(doc).encode("utf-8")).hexdigest()


def _canonical_reason(reason: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(reason)
    out["accepted_evidence_ids"] = _ids(reason.get("accepted_evidence_ids") or ())
    for key in ("source_classes", "run_ids"):
        if isinstance(out.get(key), list):
            out[key] = sorted(out[key])
    if isinstance(out.get("run_identity_sha256"), list):
        out["run_identity_sha256"] = sorted(out["run_identity_sha256"])
    if isinstance(out.get("fixtures"), list):
        out["fixtures"] = sorted(out["fixtures"], key=lambda f: (f.get("fixture_id") or "", f.get("fixture_version") or ""))
    if isinstance(out.get("details"), list):
        out["details"] = sorted(out["details"],
                                key=lambda d: (str(d.get("accepted_evidence_id") or "").lower(), d.get("detail") or ""))
    return out


def canonical_reasons(reasons: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Reasons sorted by `(code, accepted_evidence_ids, canonical sorted-key compact JSON of extras)`, with each
    reason's list-valued extras in their closure-2 order. Every key, including resolver nulls, is kept."""
    canon = [_canonical_reason(r) for r in reasons]

    def key(r: dict[str, Any]) -> tuple[str, list[str], str]:
        extras = {k: v for k, v in r.items() if k not in ("code", "accepted_evidence_ids")}
        return (str(r.get("code") or ""), r["accepted_evidence_ids"], _canonical(extras))

    return sorted(canon, key=key)


def source_ids_of(rows: Iterable[LinkRow]) -> list[str]:
    """The `source_id` of every requested accepted row found in the requested tenant/Site; missing and foreign IDs
    contribute nothing (they stay in `evidence_ids` and the reasons)."""
    return _ids(r.evidence_gateway_source[1] for r in rows
                if r.in_scope and r.evidence_gateway_source is not None and r.evidence_gateway_source[1] is not None)


def public_dto(result: Mapping[str, Any], *, tenant_id: UUID | str, site_id: UUID | str,
               selected_revision_ids: Iterable[UUID | str], source_ids: Iterable[UUID | str],
               detail: bool = True) -> dict[str, Any]:
    """The public DTO for one resolver result (`classify` shape) of one Site's exact selected rows."""
    reasons = canonical_reasons(result["reasons"])
    evidence_ids = _ids(result["accepted_evidence_ids"])
    dto: dict[str, Any] = {
        "classification": result["state"],
        "state": result["state"],
        "source_ids": _ids(source_ids),
        "evidence_ids": evidence_ids,
        "basis_sha256": basis_sha256(tenant_id, site_id, selected_revision_ids, evidence_ids),
        "reasons": reasons,
    }
    if detail:
        dto["detail"] = {k: (reasons if k == "reasons" else result[k]) for k in DETAIL_KEYS}
    return dto


def w1_compatible(resolver_result: Mapping[str, Any], dto: Mapping[str, Any]) -> dict[str, Any]:
    """The W1 reader shape: every existing resolver top-level field stays present and typed as before (the Site
    pages read them directly), with the public keys added. `state` is unchanged (it equals `classification`) and
    the top-level `reasons` become the canonical list, equal to `detail.reasons`."""
    out = dict(resolver_result)
    out.update({k: dto[k] for k in _PUBLIC_KEYS})
    if "detail" in dto:
        out["detail"] = dto["detail"]
    return out


SOURCE_CLASS_MISMATCH = "SOURCE_CLASS_MISMATCH"


# --- Ruling 2: the selected-ID set of each represented row (never a page, prior head or all history). ---------

def finding_row_selection(finding_revision_id: UUID | str) -> list[str]:
    """W1 Finding row/detail: `{finding_revision.id}`."""
    return _ids([finding_revision_id])


def consequence_row_selection(consequence_revision_id: UUID | str, finding_revision_id: UUID | str) -> list[str]:
    """W1 financial consequence row: `{financial_consequence_revision.id, its finding_revision_id}`."""
    return _ids([consequence_revision_id, finding_revision_id])


def cold_envelope_selection(selected_revision_ids: Iterable[UUID | str]) -> list[str]:
    """Cold selected envelope: every selected `ColdSelected.revision_id` of the requested analytics tuple."""
    return _ids(selected_revision_ids)


def cold_finding_row_selection(finding_revision_id: UUID | str, cold_episode_revision_id: UUID | str,
                               assessment_revision_id: UUID | str) -> list[str]:
    """Cold Finding row: its `finding_revision.id`, `cold_episode_revision.id` and the one
    `cold_episode_revision.assessment_revision_id`."""
    return _ids([finding_revision_id, cold_episode_revision_id, assessment_revision_id])


def cold_consequence_row_selection(cold_consequence_revision_id: UUID | str, finding_revision_id: UUID | str,
                                   cold_episode_revision_id: UUID | str,
                                   assessment_revision_id: UUID | str) -> list[str]:
    """Cold consequence row: the paired cold Finding row set plus its `cold_consequence_revision.id`."""
    return _ids([cold_consequence_revision_id,
                 *cold_finding_row_selection(finding_revision_id, cold_episode_revision_id, assessment_revision_id)])


def ev_envelope_selection(assessment_revision_id: UUID | str,
                          session_revision_ids: Iterable[UUID | str]) -> list[str]:
    """EV selected envelope: `{assessment_revision.id}` plus all of its stored `result.session_revision_ids`."""
    return _ids([assessment_revision_id, *session_revision_ids])


def ev_session_row_selection(assessment_revision_id: UUID | str, ev_session_revision_id: UUID | str) -> list[str]:
    """EV session row: `{assessment_revision.id, ev_session_revision.id}`."""
    return _ids([assessment_revision_id, ev_session_revision_id])


def ev_finding_row_selection(assessment_revision_id: UUID | str, ev_session_revision_id: UUID | str,
                             finding_revision_id: UUID | str) -> list[str]:
    """EV Finding row: `{assessment_revision.id, ev_session_revision.id, finding_revision.id}` (pinned session)."""
    return _ids([assessment_revision_id, ev_session_revision_id, finding_revision_id])


# --- Rulings 5 and 6: pending dual blocks and the estate projection. -------------------------------------------

def estate_projection(dto: Mapping[str, Any]) -> dict[str, Any]:
    """Ruling 6: an estate row's exact six public keys (no `detail`, no W1 top-level fields)."""
    return {k: dto[k] for k in _PUBLIC_KEYS}


def dual_blocks(selected: Mapping[str, Any] | None, pending: Mapping[str, Any] | None) -> dict[str, Any]:
    """Ruling 5: a cold/EV envelope's three sibling blocks. `selected` is the exact prior selected row's DTO (its
    computed digest); `pending` classifies the full newer accepted set and carries `basis_sha256: null` (build it
    with `cited_set(..., selected_revision_ids=[])`). With pending work `source_provenance` is the compatibility
    alias of `pending_source_provenance`; without it `source_provenance` equals `selected_source_provenance`.
    Neither block (no selected row, no pending set; Run 2 ruling 1, Run 3 q3 ruling 1) yields the literal
    six-key empty alias, equal to `cited_set(t, s, [], [], detail=False)`, and two null siblings."""
    if pending is not None and pending.get("basis_sha256") is not None:
        raise ValueError("A pending source_provenance block has no selected revision, so no digest.")
    if selected is None and pending is None:
        return {"source_provenance": {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [],
                                      "evidence_ids": [], "basis_sha256": None,
                                      "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]},
                "selected_source_provenance": None, "pending_source_provenance": None}
    alias: Mapping[str, Any] = pending if pending is not None else selected  # type: ignore[assignment]
    return {"source_provenance": dict(alias),
            "selected_source_provenance": None if selected is None else dict(selected),
            "pending_source_provenance": None if pending is None else dict(pending)}


class LinkRowsReads:
    """A `ProvenanceReads` over one link-row callable, for set-only reads (`cited_set`, `ev_selected`) inside a
    caller's transaction: e.g. `LinkRowsReads(lambda t, s, ids: link_rows_on(c, t, s, ids))` on the cold/EV
    snapshot connection `c`. Revision reads are not available through it and raise."""

    def __init__(self, link_rows: Callable[[UUID, UUID, list[str]], Iterable[LinkRow]]) -> None:
        self._link_rows = link_rows

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[LinkRow]:
        return list(self._link_rows(tenant_id, site_id, evidence_ids))

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID,
                                  finding_revision_id: UUID) -> list[str] | None:
        raise NotImplementedError("LinkRowsReads serves set-only reads; pass the ledger reads for revisions.")

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID
                           ) -> tuple[str, list[str], list[str]] | None:
        raise NotImplementedError("LinkRowsReads serves set-only reads; pass the ledger reads for revisions.")


class _RecordingReads:
    """Forwards to the caller's reads and keeps the link rows of the last `link_rows` call, so the resolver's own
    single read also yields `source_ids` (no second query, same connection and snapshot)."""

    def __init__(self, reads: ProvenanceReads) -> None:
        self._reads = reads
        self.rows: list[LinkRow] = []

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[LinkRow]:
        self.rows = list(self._reads.link_rows(tenant_id, site_id, evidence_ids))
        return self.rows

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID,
                                  finding_revision_id: UUID) -> list[str] | None:
        return self._reads.finding_revision_evidence(tenant_id, site_id, finding_revision_id)

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID
                           ) -> tuple[str, list[str], list[str]] | None:
        return self._reads.consequence_inputs(tenant_id, site_id, consequence_revision_id)


class PublicProvenance:
    """`I-shared-provenance-dto`: the exact-ID resolver behind the public DTO. Read-only."""

    def __init__(self, reads: ProvenanceReads) -> None:
        self._reads = reads

    def cited_set(self, tenant_id: UUID, site_id: UUID, cited_ids: Iterable[UUID | str],
                  selected_revision_ids: Iterable[UUID | str], *, detail: bool = True) -> dict[str, Any]:
        """The DTO for one Site's full cited accepted-ID set, classified by `SourceProvenanceResolver.resolve`."""
        rec = _RecordingReads(self._reads)
        result = SourceProvenanceResolver(rec).resolve(tenant_id, site_id, cited_ids)
        return public_dto(result, tenant_id=tenant_id, site_id=site_id, selected_revision_ids=selected_revision_ids,
                          source_ids=source_ids_of(rec.rows), detail=detail)

    def finding_revision(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID,
                         selected_revision_ids: Iterable[UUID | str] | None = None) -> dict[str, Any] | None:
        """W1 compatible DTO for one selected FindingRevision's own cited set (exact `finding_revision_evidence`);
        None when it is not in the Site. `selected_revision_ids` defaults to ruling 2's W1 Finding row set
        `{finding_revision.id}`; a cold/EV/estate Finding row passes its own ruling-2 set."""
        if selected_revision_ids is None:
            selected_revision_ids = finding_row_selection(finding_revision_id)
        rec = _RecordingReads(self._reads)
        result = SourceProvenanceResolver(rec).finding_revision(tenant_id, site_id, finding_revision_id)
        if result is None:
            return None
        dto = public_dto(result, tenant_id=tenant_id, site_id=site_id, selected_revision_ids=selected_revision_ids,
                         source_ids=source_ids_of(rec.rows))
        return w1_compatible(result, dto)

    def consequence_revision(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID,
                             selected_revision_ids: Iterable[UUID | str] | None = None) -> dict[str, Any] | None:
        """W1 compatible DTO for one consequence revision (its Finding's cited set plus its own power IDs), with the
        resolver's fail-closed Finding conflict kept; None when it is not in the Site. `selected_revision_ids`
        defaults to ruling 2's W1 consequence row set `{consequence_revision.id, its finding_revision_id}`."""
        rec = _RecordingReads(self._reads)
        result = SourceProvenanceResolver(rec).consequence_revision(tenant_id, site_id, consequence_revision_id)
        if result is None:
            return None
        if selected_revision_ids is None:
            selected_revision_ids = consequence_row_selection(consequence_revision_id, result["finding_revision_id"])
        dto = public_dto(result, tenant_id=tenant_id, site_id=site_id, selected_revision_ids=selected_revision_ids,
                         source_ids=source_ids_of(rec.rows))
        return w1_compatible(result, dto)

    def ev_selected(self, tenant_id: UUID, site_id: UUID, cited_ids: Iterable[UUID | str],
                    selected_revision_ids: Iterable[UUID | str], persisted_class: str | None, *,
                    detail: bool = True) -> dict[str, Any]:
        """Ruling 4: a selected EV read's DTO. The exact full cited set (`assessment_revision.evidence_ids`, or a
        row's exact accepted uses) is resolved first; `persisted_class` is the selected row's stored
        `result.source_provenance.class`. Any inequality with the resolver `state` (null included, and resolver
        UNKNOWN against a persisted positive class) is a mismatch: `classification = state = UNKNOWN`, every
        canonical resolver reason kept, plus `{code: SOURCE_CLASS_MISMATCH, accepted_evidence_ids: <full sorted
        cited set>, persisted_class}`; `detail.state`/`detail.reasons` follow, the other seven keys keep the
        resolver's values. No selected row (empty `selected_revision_ids`) means no comparison. Nothing stored is
        written."""
        cited = _ids(cited_ids)
        selected = _ids(selected_revision_ids)
        rec = _RecordingReads(self._reads)
        result = dict(SourceProvenanceResolver(rec).resolve(tenant_id, site_id, cited))
        if selected and persisted_class != result["state"]:
            result["state"] = UNKNOWN
            result["reasons"] = list(result["reasons"]) + [
                {"code": SOURCE_CLASS_MISMATCH, "accepted_evidence_ids": cited, "persisted_class": persisted_class}]
        return public_dto(result, tenant_id=tenant_id, site_id=site_id, selected_revision_ids=selected,
                          source_ids=source_ids_of(rec.rows), detail=detail)
