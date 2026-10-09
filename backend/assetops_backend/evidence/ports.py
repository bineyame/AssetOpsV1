"""The evidence store port. Signatures speak domain records only.

No path, file handle, serialization format or store-specific exception appears
here (`.ai/ARCHITECTURE.md` Configuration Persistence), so the JSON adapter can
be replaced without touching ingestion or the read model.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from assetops_backend.evidence.models import (
    BatchProgress,
    ConfigurationBasis,
    MappingRegistration,
    SiteEvidence,
)


class EvidenceStoreError(Exception):
    """Base class for the evidence port's error vocabulary."""


class EvidenceStoreUnavailable(EvidenceStoreError):
    """The store cannot be read or written, or holds a document it cannot read."""


class EvidenceStore(Protocol):
    def load_site(self, site_id: str) -> SiteEvidence:
        """Everything accepted for a Site; an empty `SiteEvidence` if nothing is."""
        ...

    def save_site(self, evidence: SiteEvidence) -> None:
        """Replace a Site's evidence in ONE atomic write (records + progress)."""
        ...

    def list_sites(self) -> Sequence[str]:
        """The Site ids that have an evidence document."""
        ...

    def get_mapping(self, mapping_set_id: str, mapping_version: int) -> MappingRegistration | None:
        ...

    def register_mapping(self, registration: MappingRegistration) -> MappingRegistration:
        """Write once. If one exists already it is returned unchanged."""
        ...

    def get_configuration(self, site_id: str, foundation_version: int) -> ConfigurationBasis | None:
        ...

    def register_configuration(self, basis: ConfigurationBasis) -> ConfigurationBasis:
        """Write once. If one exists already it is returned unchanged."""
        ...

    def list_configurations(self, site_id: str) -> Sequence[ConfigurationBasis]:
        ...

    def clear_derived(self) -> None:
        """Empty every per-Site evidence document; keep the immutable registries."""
        ...

    def canonical_root(self) -> str:
        """The canonical resolved local root this store reads and writes (S2-02 Q26
        store-root identity).
        Never served by a product route."""
        ...


def find_batch(store: EvidenceStore, batch_id: str) -> BatchProgress | None:
    """A batch's progress, wherever its Site is."""
    for site_id in store.list_sites():
        for progress in store.load_site(site_id).batches:
            if progress.batch_id == batch_id:
                return progress
    return None
