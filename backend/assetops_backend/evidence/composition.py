"""The single composition module for the evidence store.

The one place allowed to import `assetops_backend.evidence.adapters.*`; every
other caller receives the `EvidenceStore` port by injection.
"""

from __future__ import annotations


from assetops_backend.evidence.adapters import gateway_credential_file
from assetops_backend.evidence.adapters.authored_fixture_specs import AuthoredFixtureSpecs
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.adapters.legacy_comparison_file import ComparisonReportFiles
from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
from assetops_backend.evidence.ledger import EvidenceLedger
from assetops_backend.evidence.ports import EvidenceStore
from assetops_backend.evidence.source_provenance import SourceProvenanceResolver


def build_evidence_store() -> EvidenceStore:
    """Choose the adapter that persists accepted evidence."""
    return JsonEvidenceStore()


def build_evidence_ledger(database_url: str | None) -> EvidenceLedger:
    """The central Batch V2 evidence ledger (S2-02). Lazy: no connection until first use."""
    return PostgresEvidenceLedger(database_url)


def build_authored_fixture_specs() -> AuthoredFixtureSpecs:
    """S4-05a: the server's authored fixture/spec registry for source publication."""
    return AuthoredFixtureSpecs()


def build_source_provenance(database_url: str | None) -> SourceProvenanceResolver:
    """S4-05a phase 2: the exact-revision source provenance resolver (read-only). Lazy like the ledger."""
    return SourceProvenanceResolver(PostgresEvidenceLedger(database_url))


class _ColdReplayReader:
    """W2-02 review L5: exactly the ledger's two SELECT-only `cold_replay_*` reads, no writer method."""

    __slots__ = ("_ledger",)

    def __init__(self, ledger: PostgresEvidenceLedger) -> None:
        self._ledger = ledger

    def cold_replay_rows(self, tenant_id, site_id, run_id: str) -> dict:
        return self._ledger.cold_replay_rows(tenant_id, site_id, run_id)

    def cold_replay_run_referenced(self, tenant_id, site_id, run_id: str) -> bool:
        return self._ledger.cold_replay_run_referenced(tenant_id, site_id, run_id)


def build_cold_replay_reader(database_url: str | None) -> _ColdReplayReader:
    """W2-02: the cold replay reader, narrowed to the SELECT-only `cold_replay_*` reads. Lazy."""
    return _ColdReplayReader(PostgresEvidenceLedger(database_url))


def build_gateway_access(database_url: str | None) -> PostgresGatewayAccess:
    """Gateway credentials, provisioning steps and central diagnostics (S2-02 phase 2).
    Lazy: no connection until first use."""
    return PostgresGatewayAccess(database_url)


def build_comparison_reports() -> ComparisonReportFiles:
    """Immutable legacy comparison reports (S2-02 phase 3a); the newest decides the Evidence cutover."""
    return ComparisonReportFiles()


def build_performance_comparison_reports() -> ComparisonReportFiles:
    """Immutable S3-01 Performance comparison reports, beside (never mixed with) the Evidence ones."""
    from assetops_backend.evidence.adapters.json_evidence_store import EVIDENCE_STORE_ROOT

    return ComparisonReportFiles(EVIDENCE_STORE_ROOT / "migration-performance")


# The protected gateway credential file: prepare (new unique versioned protected
# path, durable and verified owner-only; it is the final issued path) -> caller
# commits, or discards the unissued file. No post-commit rename (Q16).
CredentialFileRefused = gateway_credential_file.CredentialFileRefused
prepare_gateway_credential_file = gateway_credential_file.prepare
discard_gateway_credential_file = gateway_credential_file.discard
