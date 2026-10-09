"""PostgreSQL gateway access store: credentials, provisioning audit and diagnostics (S2-02 phase 2).

The third confined product writer (tools/checks/configuration-persistence.ps1
rule 8a). It inserts only `gateway_credential`, `gateway_access_event`,
`gateway_diagnostic` and `gateway_diagnostic_refusal` rows, and updates only
the operator-mutable registration fields: `gateway.credential_ref`,
`gateway.disabled_at`, `gateway.diagnostic_cadence_seconds`,
`gateway_credential.revoked_at` and `source.disabled_at`. The raw credential
secret never reaches this module: it receives only selector and verifier.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_backend.evidence.gateway_access import (
    CredentialRecord,
    DiagnosticIdentityConflict,
    GatewayHealthFacts,
    IssuedCredential,
    ProvisioningRefused,
    SourceRegistration,
    StoredDiagnostic,
)
from assetops_backend.evidence.ledger import GatewayPrincipal, LedgerUnavailable
from assetops_contracts.gateway_diagnostics import GatewayDiagnosticsV1


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class PostgresGatewayAccess:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect_engine(self) -> Engine:
        if not self._database_url:
            raise LedgerUnavailable("DATABASE_URL is not set, so gateway access cannot be checked.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _run(self, work, *, write: bool = False):
        engine = self._connect_engine()
        try:
            if write:
                with engine.begin() as connection:
                    return work(connection)
            with engine.connect() as connection:
                return work(connection)
        except (OperationalError, ProgrammingError) as error:
            raise LedgerUnavailable(f"Gateway access could not be read or written: {error.orig}") from error
        except DBAPIError as error:
            if error.connection_invalidated:
                raise LedgerUnavailable(str(error.orig)) from error
            raise

    # --- principal resolution ------------------------------------------------------

    def credential(self, selector: str) -> CredentialRecord | None:
        def work(c: Connection) -> CredentialRecord | None:
            row = c.execute(text(
                "SELECT k.selector, k.verifier_sha256, k.revoked_at IS NOT NULL AS revoked, "
                "g.tenant_id, g.site_id, g.id AS gateway_id, g.mode, g.disabled_at IS NOT NULL AS disabled "
                "FROM gateway_credential k JOIN gateway g "
                "ON g.tenant_id = k.tenant_id AND g.site_id = k.site_id AND g.id = k.gateway_id "
                "WHERE k.selector = :s"), {"s": selector}).first()
            if row is None:
                return None
            return CredentialRecord(
                selector=row.selector, verifier_sha256=row.verifier_sha256, revoked=row.revoked,
                tenant_id=row.tenant_id, site_id=row.site_id, gateway_id=row.gateway_id,
                gateway_mode=row.mode, gateway_disabled=row.disabled)

        return self._run(work)

    def sources(self, tenant_id: UUID, source_ids: tuple[UUID, ...]) -> dict[UUID, SourceRegistration]:
        if not source_ids:
            return {}

        def work(c: Connection) -> dict[UUID, SourceRegistration]:
            rows = c.execute(text(
                "SELECT id, gateway_id, site_id, disabled_at IS NOT NULL AS disabled FROM source "
                "WHERE tenant_id = :t AND id = ANY(:ids)"), {"t": tenant_id, "ids": list(source_ids)}).all()
            return {r.id: SourceRegistration(r.id, r.gateway_id, r.site_id, r.disabled) for r in rows}

        return self._run(work)

    # --- diagnostics ---------------------------------------------------------------

    @staticmethod
    def _stored(row) -> StoredDiagnostic:
        return StoredDiagnostic(
            diagnostic_id=row.id, gateway_id=row.gateway_id, sequence_epoch=row.sequence_epoch,
            diagnostic_sequence=row.diagnostic_sequence, payload_sha256=row.payload_sha256,
            diagnostic_text=row.diagnostic_text, received_at=row.received_at)

    _SELECT = ("SELECT id, gateway_id, sequence_epoch, diagnostic_sequence, payload_sha256, diagnostic_text, "
               "received_at FROM gateway_diagnostic ")

    def find_diagnostic(self, principal: GatewayPrincipal, epoch: str, sequence: int) -> StoredDiagnostic | None:
        def work(c: Connection):
            row = c.execute(text(self._SELECT + "WHERE tenant_id = :t AND site_id = :site AND gateway_id = :g "
                                 "AND sequence_epoch = :e AND diagnostic_sequence = :n"),
                            {"t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                             "e": epoch, "n": sequence}).first()
            return None if row is None else self._stored(row)

        return self._run(work)

    def insert_diagnostic(
        self, principal: GatewayPrincipal, diagnostic: GatewayDiagnosticsV1, diagnostic_text: str,
        received_at: datetime,
    ) -> tuple[StoredDiagnostic, bool]:
        contacts = {source: contact for source, contact in diagnostic.last_device_contact_by_source}

        def work(c: Connection):
            inserted = c.execute(text(
                "INSERT INTO gateway_diagnostic (id, tenant_id, site_id, gateway_id, sequence_epoch, "
                "diagnostic_sequence, observed_at, received_at, last_device_contact_by_source, queue_count, "
                "oldest_queue_age_seconds, disk_pressure, clock_offset_ms, mapping_error_count, payload_sha256, "
                "diagnostic_text) VALUES (:id, :t, :site, :g, :e, :n, :observed, :received, CAST(:contacts AS jsonb), "
                ":q, :age, :disk, :offset, :mapping, :sha, :body) "
                "ON CONFLICT (gateway_id, sequence_epoch, diagnostic_sequence) DO NOTHING RETURNING id"),
                {"id": uuid4(), "t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                 "e": diagnostic.sequence_epoch, "n": diagnostic.diagnostic_sequence,
                 "observed": _parse(diagnostic.observed_at), "received": received_at,
                 "contacts": json.dumps(contacts, sort_keys=True), "q": diagnostic.queue_count,
                 "age": diagnostic.oldest_queue_age_seconds, "disk": diagnostic.disk_pressure,
                 "offset": diagnostic.clock_offset_ms, "mapping": diagnostic.mapping_error_count,
                 "sha": diagnostic.payload_sha256, "body": diagnostic_text}).first()
            row = c.execute(text(self._SELECT + "WHERE gateway_id = :g AND sequence_epoch = :e "
                                 "AND diagnostic_sequence = :n"),
                            {"g": principal.gateway_id, "e": diagnostic.sequence_epoch,
                             "n": diagnostic.diagnostic_sequence}).one()
            stored = self._stored(row)
            if inserted is None and stored.diagnostic_text != diagnostic_text:
                raise DiagnosticIdentityConflict(stored)
            return stored, inserted is not None

        return self._run(work, write=True)

    def record_diagnostic_refusal(
        self, principal: GatewayPrincipal, *, epoch: str | None, sequence: int | None,
        payload_sha256: str, kind: str, field: str, detail: str, received_at: datetime,
    ) -> UUID:
        def work(c: Connection) -> UUID:
            params = {"t": principal.tenant_id, "site": principal.site_id, "g": principal.gateway_id,
                      "e": epoch, "n": sequence, "sha": payload_sha256, "kind": kind}
            c.execute(text(
                "INSERT INTO gateway_diagnostic_refusal (id, tenant_id, site_id, gateway_id, sequence_epoch, "
                "diagnostic_sequence, payload_sha256, kind, field, detail, received_at) VALUES "
                "(:id, :t, :site, :g, :e, :n, :sha, :kind, :field, :detail, :received) "
                "ON CONFLICT ON CONSTRAINT gateway_diagnostic_refusal_identity DO NOTHING"),
                {**params, "id": uuid4(), "field": field, "detail": detail, "received": received_at})
            return c.execute(text(
                "SELECT id FROM gateway_diagnostic_refusal WHERE gateway_id = :g "
                "AND sequence_epoch IS NOT DISTINCT FROM :e AND diagnostic_sequence IS NOT DISTINCT FROM :n "
                "AND payload_sha256 = :sha AND kind = :kind"), params).scalar_one()

        return self._run(work, write=True)

    def gateway_health(self, tenant_id: UUID, site_id: UUID) -> list[GatewayHealthFacts]:
        def work(c: Connection) -> list[GatewayHealthFacts]:
            gateways = c.execute(text(
                "SELECT id, gateway_external_id, mode, disabled_at IS NOT NULL AS disabled, "
                "diagnostic_cadence_seconds FROM gateway WHERE tenant_id = :t AND site_id = :s "
                "ORDER BY gateway_external_id"), {"t": tenant_id, "s": site_id}).all()
            facts = []
            for g in gateways:
                sources = c.execute(text(
                    "SELECT id, source_external_id, disabled_at IS NOT NULL AS disabled FROM source "
                    "WHERE tenant_id = :t AND site_id = :s AND gateway_id = :g ORDER BY source_external_id"),
                    {"t": tenant_id, "s": site_id, "g": g.id}).all()
                latest = c.execute(text(
                    self._SELECT + "WHERE tenant_id = :t AND site_id = :s AND gateway_id = :g "
                    "ORDER BY received_at DESC, diagnostic_sequence DESC LIMIT 1"),
                    {"t": tenant_id, "s": site_id, "g": g.id}).first()
                stored = None if latest is None else self._stored(latest)
                facts.append(GatewayHealthFacts(
                    gateway_id=g.id, gateway_external_id=g.gateway_external_id, mode=g.mode,
                    disabled=g.disabled, cadence_seconds=g.diagnostic_cadence_seconds,
                    sources=tuple((s.id, s.source_external_id, s.disabled) for s in sources),
                    latest=stored,
                    latest_fields=None if stored is None else json.loads(stored.diagnostic_text)))
            return facts

        return self._run(work)

    # --- operator provisioning ---------------------------------------------------------

    def _gateway(self, c: Connection, tenant_slug: str, site_code: str, gateway_external_id: str):
        row = c.execute(text(
            "SELECT g.tenant_id, g.site_id, g.id FROM gateway g "
            "JOIN tenant t ON t.id = g.tenant_id JOIN site s ON s.tenant_id = g.tenant_id AND s.id = g.site_id "
            "WHERE t.slug = :slug AND s.site_code_key = lower(:code) AND g.gateway_external_id = :g "
            "FOR UPDATE OF g"), {"slug": tenant_slug, "code": site_code, "g": gateway_external_id}).first()
        if row is None:
            raise ProvisioningRefused(
                f"gateway {gateway_external_id!r} is not registered to Site {site_code!r} in tenant {tenant_slug!r}")
        return row

    @staticmethod
    def _event(c: Connection, g, kind: str, actor: str, at: datetime, *, source_id=None, selector=None) -> None:
        c.execute(text(
            "INSERT INTO gateway_access_event (id, tenant_id, site_id, gateway_id, source_id, credential_selector, "
            "kind, actor, recorded_at) VALUES (:id, :t, :s, :g, :src, :sel, :kind, :actor, :at)"),
            {"id": uuid4(), "t": g.tenant_id, "s": g.site_id, "g": g.id, "src": source_id, "sel": selector,
             "kind": kind, "actor": actor, "at": at})

    def issue_credential(self, tenant_slug: str, site_code: str, gateway_external_id: str,
                         issued: IssuedCredential, *, actor: str, at: datetime,
                         enable_sources: Sequence[str] = (), cadence_seconds: int | None = None) -> list[str]:
        """In ONE transaction: store the new verifier, revoke every earlier active
        credential of the gateway (rotation; takes effect on the next request), point
        `credential_ref` at it, enable the gateway and exactly the named sources.
        Any refusal rolls all of it back, so the earlier credential stays usable and
        no identity becomes more enabled (Q8). Returns the revoked selectors."""

        def work(c: Connection) -> list[str]:
            g = self._gateway(c, tenant_slug, site_code, gateway_external_id)
            revoked = [r.selector for r in c.execute(text(
                "UPDATE gateway_credential SET revoked_at = :at WHERE gateway_id = :g AND revoked_at IS NULL "
                "RETURNING selector"), {"at": at, "g": g.id}).all()]
            for selector in revoked:
                self._event(c, g, "CREDENTIAL_REVOKED", actor, at, selector=selector)
            c.execute(text(
                "INSERT INTO gateway_credential (id, tenant_id, site_id, gateway_id, selector, verifier_sha256, "
                "issued_at) VALUES (:id, :t, :s, :g, :sel, :v, :at)"),
                {"id": uuid4(), "t": g.tenant_id, "s": g.site_id, "g": g.id, "sel": issued.selector,
                 "v": issued.verifier_sha256, "at": at})
            c.execute(text("UPDATE gateway SET credential_ref = :sel WHERE id = :g"),
                      {"sel": issued.selector, "g": g.id})
            self._event(c, g, "CREDENTIAL_ISSUED", actor, at, selector=issued.selector)
            self._gateway_enabled(c, g, True, actor, at, cadence_seconds)
            for source in enable_sources:
                self._source_enabled(c, g, gateway_external_id, source, True, actor, at)
            return revoked

        return self._run(work, write=True)

    def issue_outcome(self, tenant_slug: str, site_code: str, gateway_external_id: str,
                      issued: IssuedCredential, enable_sources: Sequence[str] = ()) -> str:
        """Q28 reconciliation after an ambiguous issue transaction: a fresh privileged
        read (the pool is discarded first, so no connection from the failed attempt is
        reused) of the scoped gateway, the selector's verifier and the named sources.

        `ISSUED`: the new verifier is stored, active, the gateway's `credential_ref`,
        the gateway and every named source enabled - the one transaction committed.
        `NOT_ISSUED`: no row carries the new selector, so that single transaction
        (which inserts it) definitively did not commit. `UNKNOWN`: the selector row
        exists but the rest does not match (for example a later rotation revoked it),
        so only an operator can reconcile. Raises `LedgerUnavailable` if the database
        still cannot be read."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

        def work(c: Connection) -> str:
            g = c.execute(text(
                "SELECT g.id, g.credential_ref, g.disabled_at IS NULL AS enabled FROM gateway g "
                "JOIN tenant t ON t.id = g.tenant_id JOIN site s ON s.tenant_id = g.tenant_id AND s.id = g.site_id "
                "WHERE t.slug = :slug AND s.site_code_key = lower(:code) AND g.gateway_external_id = :g"),
                {"slug": tenant_slug, "code": site_code, "g": gateway_external_id}).first()
            if g is None:
                return "UNKNOWN"
            row = c.execute(text(
                "SELECT verifier_sha256, revoked_at IS NULL AS active, gateway_id FROM gateway_credential "
                "WHERE selector = :s"), {"s": issued.selector}).first()
            if row is None:
                return "NOT_ISSUED"
            sources_enabled = all(c.execute(text(
                "SELECT disabled_at IS NULL FROM source WHERE gateway_id = :g AND source_external_id = :x"),
                {"g": g.id, "x": source}).scalar() for source in enable_sources)
            if (row.verifier_sha256 == issued.verifier_sha256 and row.active and row.gateway_id == g.id
                    and g.credential_ref == issued.selector and g.enabled and sources_enabled):
                return "ISSUED"
            return "UNKNOWN"

        return self._run(work)

    def revoke_credential(self, tenant_slug: str, site_code: str, gateway_external_id: str, selector: str,
                          *, actor: str, at: datetime) -> bool:
        def work(c: Connection) -> bool:
            g = self._gateway(c, tenant_slug, site_code, gateway_external_id)
            done = c.execute(text(
                "UPDATE gateway_credential SET revoked_at = :at WHERE gateway_id = :g AND selector = :sel "
                "AND revoked_at IS NULL RETURNING id"), {"at": at, "g": g.id, "sel": selector}).first()
            if done is not None:
                self._event(c, g, "CREDENTIAL_REVOKED", actor, at, selector=selector)
            return done is not None

        return self._run(work, write=True)

    def _gateway_enabled(self, c: Connection, g, enabled: bool, actor: str, at: datetime,
                         cadence_seconds: int | None) -> None:
        c.execute(text("UPDATE gateway SET disabled_at = :d WHERE id = :g"),
                  {"d": None if enabled else at, "g": g.id})
        if cadence_seconds is not None:
            c.execute(text("UPDATE gateway SET diagnostic_cadence_seconds = :c WHERE id = :g"),
                      {"c": cadence_seconds, "g": g.id})
        self._event(c, g, "GATEWAY_ENABLED" if enabled else "GATEWAY_DISABLED", actor, at)

    def _source_enabled(self, c: Connection, g, gateway_external_id: str, source_external_id: str,
                        enabled: bool, actor: str, at: datetime) -> None:
        source = c.execute(text(
            "UPDATE source SET disabled_at = :d WHERE gateway_id = :g AND source_external_id = :x "
            "RETURNING id"), {"d": None if enabled else at, "g": g.id, "x": source_external_id}).first()
        if source is None:
            raise ProvisioningRefused(
                f"source {source_external_id!r} is not registered to gateway {gateway_external_id!r}")
        self._event(c, g, "SOURCE_ENABLED" if enabled else "SOURCE_DISABLED", actor, at, source_id=source.id)

    def set_gateway_enabled(self, tenant_slug: str, site_code: str, gateway_external_id: str, enabled: bool,
                            *, actor: str, at: datetime, cadence_seconds: int | None = None) -> None:
        def work(c: Connection) -> None:
            g = self._gateway(c, tenant_slug, site_code, gateway_external_id)
            self._gateway_enabled(c, g, enabled, actor, at, cadence_seconds)

        self._run(work, write=True)

    def set_source_enabled(self, tenant_slug: str, site_code: str, gateway_external_id: str,
                           source_external_id: str, enabled: bool, *, actor: str, at: datetime) -> None:
        def work(c: Connection) -> None:
            g = self._gateway(c, tenant_slug, site_code, gateway_external_id)
            self._source_enabled(c, g, gateway_external_id, source_external_id, enabled, actor, at)

        self._run(work, write=True)
