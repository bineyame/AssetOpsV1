"""The single composition module for the evidence store.

The one place allowed to import `assetops_backend.evidence.adapters.*`; every
other caller receives the `EvidenceStore` port by injection.
"""

from __future__ import annotations

from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
from assetops_backend.evidence.ledger import EvidenceLedger
from assetops_backend.evidence.ports import EvidenceStore


def build_evidence_store() -> EvidenceStore:
    """Choose the adapter that persists accepted evidence."""
    return JsonEvidenceStore()


def build_evidence_ledger(database_url: str | None) -> EvidenceLedger:
    """The central Batch V2 evidence ledger (S2-02). Lazy: no connection until first use."""
    return PostgresEvidenceLedger(database_url)
