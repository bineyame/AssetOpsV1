"""W4-02 unit 5: the mini-depth adapter over the reviewed W3-01 `PublicProvenance` API.

`D-2026-10-20-w4-02-buildspec` closure 1 Q6/Q18. The selected block resolves the union of the exact selected
revisions' **full** accepted-ID sets with those sorted, distinct revision UUIDs as the basis selection; the pending
block resolves every cutoff-visible accepted row of the hours with a live overlapping job, with no selected revision
(`basis_sha256: null`). Both are read on the caller's snapshot connection. Lane B's shared DTO file is not edited;
the default W4-02 response omits `detail`. A resolver failure propagates to the caller's 503, never a guessed UNKNOWN.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable
from uuid import UUID

from assetops_backend.evidence.public_provenance import LinkRowsReads, PublicProvenance, dual_blocks

#: `(connection, tenant_id, site_id, evidence_ids) -> link rows`, injected from `evidence/composition.py`.
LinkRowsOn = Callable[[Any, UUID, UUID, list[str]], Iterable[Any]]


def mini_blocks(c: Any, link_rows: LinkRowsOn, tenant_id: UUID, site_id: UUID, *,
                selected_revision_ids: Iterable[UUID | str],
                selected_evidence_ids: Iterable[UUID | str],
                pending_evidence_ids: Iterable[UUID | str] | None) -> dict[str, Any]:
    """The three sibling blocks of one mini envelope (`source_provenance` aliases pending, else selected)."""
    public = PublicProvenance(LinkRowsReads(lambda t, s, ids: link_rows(c, t, s, ids)))
    revisions = sorted({str(r).lower() for r in selected_revision_ids})
    selected = None
    if revisions:
        selected = public.cited_set(tenant_id, site_id, sorted({str(i).lower() for i in selected_evidence_ids}),
                                    revisions, detail=False)
    pending = None
    if pending_evidence_ids is not None:
        pending = public.cited_set(tenant_id, site_id, sorted({str(i).lower() for i in pending_evidence_ids}), [],
                                   detail=False)
    return dual_blocks(selected, pending)


__all__ = ["LinkRowsOn", "mini_blocks"]
