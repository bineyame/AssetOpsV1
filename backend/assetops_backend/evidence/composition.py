"""The single composition module for the evidence store.

The one place allowed to import `assetops_backend.evidence.adapters.*`; every
other caller receives the `EvidenceStore` port by injection.
"""

from __future__ import annotations


from assetops_backend.evidence.adapters import gateway_credential_file
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
from assetops_backend.evidence.ledger import EvidenceLedger
from assetops_backend.evidence.ports import EvidenceStore


def build_evidence_store() -> EvidenceStore:
    """Choose the adapter that persists accepted evidence."""
    return JsonEvidenceStore()


def build_evidence_ledger(database_url: str | None) -> EvidenceLedger:
    """The central Batch V2 evidence ledger (S2-02). Lazy: no connection until first use."""
    return PostgresEvidenceLedger(database_url)


def build_gateway_access(database_url: str | None) -> PostgresGatewayAccess:
    """Gateway credentials, provisioning steps and central diagnostics (S2-02 phase 2).
    Lazy: no connection until first use."""
    return PostgresGatewayAccess(database_url)


# The protected gateway credential file: prepare (new versioned protected path,
# verified owner-only) -> caller commits -> activate (atomic rename) or discard.
CredentialFileRefused = gateway_credential_file.CredentialFileRefused
prepare_gateway_credential_file = gateway_credential_file.prepare
activate_gateway_credential_file = gateway_credential_file.activate
discard_gateway_credential_file = gateway_credential_file.discard
