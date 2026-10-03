"""The single composition module for the evidence store.

The one place allowed to import `assetops_backend.evidence.adapters.*`; every
other caller receives the `EvidenceStore` port by injection.
"""

from __future__ import annotations

from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.ports import EvidenceStore


def build_evidence_store() -> EvidenceStore:
    """Choose the adapter that persists accepted evidence."""
    return JsonEvidenceStore()
