"""3A7 (spec §3; D-3A7.14, D-3A7.15): the reconciliation service over the Postgres commercial store.

It reaches the store only through `commercial.composition.build_commercial_reads` (the months service and the store
it reads), so it imports no adapter, and it opens no file: the owner-file reader is a parameter the command builds
from the owner root (D-3A7.15). `commercial/composition.py` is unchanged (D-3A4.8: commercial never imports
`structure`).
"""
from __future__ import annotations

from typing import Callable

from assetops_backend.commercial.composition import build_commercial_reads
from assetops_backend.structure.reconciliation import CommercialReconciliation


def build_commercial_reconciliation(database_url: str, *, owner_file: Callable[[str], bytes | None] | None = None
                                    ) -> tuple[CommercialReconciliation, Callable[[], None]]:
    """The service and the `dispose` of the store under it. Without `owner_file` no tolerance can be set."""
    reads = build_commercial_reads(database_url)
    return CommercialReconciliation(reads.months, reads.store, owner_file=owner_file), reads.dispose
