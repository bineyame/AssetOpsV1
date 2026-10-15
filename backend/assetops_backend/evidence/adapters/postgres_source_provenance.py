"""Read-only PostgreSQL rows for the S4-05a source provenance resolver (`evidence/source_provenance.py`).

Every query is scoped by tenant and Site and only SELECTs. The provenance chain is joined LEFT and unscoped past
the accepted row, so a link or publication that does not agree with the scoped batch commitment comes back for
the resolver to name as broken, never silently dropped. Another tenant's rows are never reported: an ID found
only outside the tenant is simply not found.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.evidence.source_provenance import LinkRow

_LINKS = text(
    "SELECT CAST(q.id AS text) AS requested_id, e.id IS NOT NULL AS in_scope, "
    "EXISTS (SELECT 1 FROM accepted_evidence o WHERE o.id = q.id AND o.tenant_id = :t "
    "AND o.site_id <> :s) AS in_tenant_elsewhere, "
    "CAST(e.batch_id AS text) AS batch_id, CAST(e.gateway_id AS text) AS e_gateway, "
    "CAST(e.source_id AS text) AS e_source, "
    "CAST(b.id AS text) AS b_id, CAST(b.tenant_id AS text) AS b_tenant, CAST(b.site_id AS text) AS b_site, "
    "CAST(b.gateway_id AS text) AS b_gateway, CAST(b.source_id AS text) AS b_source, "
    "b.external_batch_id AS b_ext, b.payload_sha256 AS b_sha, "
    "CAST(l.batch_id AS text) AS l_batch, CAST(l.publication_id AS text) AS l_pub, "
    "CAST(l.tenant_id AS text) AS l_tenant, CAST(l.site_id AS text) AS l_site, "
    "CAST(l.gateway_id AS text) AS l_gateway, CAST(l.source_id AS text) AS l_source, "
    "l.external_batch_id AS l_ext, l.payload_sha256 AS l_sha, "
    "CAST(p.id AS text) AS p_id, CAST(p.tenant_id AS text) AS p_tenant, CAST(p.site_id AS text) AS p_site, "
    "CAST(p.gateway_id AS text) AS p_gateway, CAST(p.source_id AS text) AS p_source, "
    "p.external_batch_id AS p_ext, p.payload_sha256 AS p_sha, p.source_class, p.fixture_id, "
    "p.fixture_version, p.run_id, p.run_identity_sha256 "
    "FROM unnest(CAST(:ids AS uuid[])) AS q(id) "
    "LEFT JOIN accepted_evidence e ON e.tenant_id = :t AND e.site_id = :s AND e.id = q.id "
    "LEFT JOIN ingestion_batch b ON b.tenant_id = e.tenant_id AND b.site_id = e.site_id AND b.id = e.batch_id "
    "LEFT JOIN batch_publication_link l ON l.batch_id = e.batch_id "
    "LEFT JOIN evidence_publication p ON p.id = l.publication_id")


def _commitment(r, prefix: str) -> tuple[str, ...] | None:
    if getattr(r, f"{prefix}_tenant") is None:
        return None
    return tuple(getattr(r, f"{prefix}_{k}") for k in ("tenant", "site", "gateway", "source", "ext", "sha"))


class PostgresSourceProvenanceReads:
    """`ProvenanceReads` over a migrated PostgreSQL database."""

    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _read(self, work):
        if not self._database_url:
            raise LedgerUnavailable("DATABASE_URL is not set, so source provenance cannot be read.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        with self._engine.connect() as connection:
            return work(connection)

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[LinkRow]:
        def work(c: Connection) -> list[LinkRow]:
            rows = c.execute(_LINKS, {"t": tenant_id, "s": site_id, "ids": [str(i) for i in evidence_ids]}).all()
            return [LinkRow(
                requested_id=r.requested_id, in_scope=r.in_scope, in_tenant_elsewhere=r.in_tenant_elsewhere,
                batch_id=r.batch_id,
                evidence_gateway_source=None if r.e_gateway is None else (r.e_gateway, r.e_source),
                batch=_commitment(r, "b"), link_publication_id=r.l_pub, link=_commitment(r, "l"),
                publication=_commitment(r, "p"), source_class=r.source_class, fixture_id=r.fixture_id,
                fixture_version=r.fixture_version, run_id=r.run_id, run_identity_sha256=r.run_identity_sha256)
                for r in rows]
        return self._read(work)

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID,
                                  finding_revision_id: UUID) -> list[str] | None:
        def work(c: Connection) -> list[str] | None:
            p = {"t": tenant_id, "s": site_id, "r": finding_revision_id}
            if c.execute(text("SELECT 1 FROM finding_revision WHERE tenant_id = :t AND site_id = :s AND id = :r"),
                         p).first() is None:
                return None
            return self._cited(c, p)
        return self._read(work)

    @staticmethod
    def _cited(c: Connection, p: dict) -> list[str]:
        return list(c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM finding_revision_evidence WHERE tenant_id = :t "
            "AND site_id = :s AND finding_revision_id = :r ORDER BY evidence_id"), p).scalars())

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID
                           ) -> tuple[str, list[str], list[str]] | None:
        def work(c: Connection) -> tuple[str, list[str], list[str]] | None:
            p = {"t": tenant_id, "s": site_id, "c": consequence_revision_id}
            finding_revision_id = c.execute(text(
                "SELECT CAST(finding_revision_id AS text) FROM financial_consequence_revision "
                "WHERE tenant_id = :t AND site_id = :s AND id = :c"), p).scalar_one_or_none()
            if finding_revision_id is None:
                return None
            cited = self._cited(c, {"t": tenant_id, "s": site_id, "r": finding_revision_id})
            power = list(c.execute(text(
                "SELECT CAST(evidence_id AS text) FROM financial_consequence_power_interval WHERE tenant_id = :t "
                "AND site_id = :s AND consequence_revision_id = :c ORDER BY evidence_id"), p).scalars())
            return finding_revision_id, cited, power
        return self._read(work)
