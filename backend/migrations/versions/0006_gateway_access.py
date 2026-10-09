"""S2-02 phase 2: gateway upload credentials, provisioning audit and central diagnostics.

Credential (`D-2026-10-09-s2-pilot-gateway-upload-credential`): one opaque
high-entropy bearer secret per registered gateway, issued once into protected
gateway configuration. The server keeps only a public `selector` and a one-way
SHA-256 `verifier`; the raw secret is never a column here. A credential row is
immutable except that `revoked_at` may be set once. `gateway.credential_ref`
names the current selector (it rotates; technical design section 1).

Provisioning audit: `gateway_access_event` records each operator step (issue,
rotate, revoke, enable/disable gateway, enable/disable source). Append-only.
`gateway.diagnostic_cadence_seconds` is the registered declared diagnostic
cadence (60 s, the frozen demo value of `D-2026-10-09-s2-gateway-diagnostic-semantics`)
from which central freshness is derived.

Diagnostics (technical design section 1, `gateway_diagnostic`): the central
operational-health table, separate from `accepted_evidence`. Append-only;
`UNIQUE(gateway_id, sequence_epoch, diagnostic_sequence)`; the server sets
`received_at`. `diagnostic_text` keeps the exact canonical bytes so an
identical retry returns the stored row and a changed body is refused with an
audited `gateway_diagnostic_refusal` row.

Revision ID: 0006_gateway_access
Revises: 0005_evidence_ledger
Create Date: 2026-10-09
"""

from __future__ import annotations

from alembic import op

revision = "0006_gateway_access"
down_revision = "0005_evidence_ledger"
branch_labels = None
depends_on = None


ACCESS = """
ALTER TABLE gateway ADD COLUMN diagnostic_cadence_seconds integer NOT NULL DEFAULT 60
    CHECK (diagnostic_cadence_seconds BETWEEN 10 AND 86400);

CREATE TABLE gateway_credential (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    selector text NOT NULL UNIQUE CHECK (selector ~ '^[0-9a-f]{32}$'),
    verifier_sha256 text NOT NULL CHECK (verifier_sha256 ~ '^[0-9a-f]{64}$'),
    issued_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    CONSTRAINT gateway_credential_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT gateway_credential_revocation CHECK (revoked_at IS NULL OR revoked_at >= issued_at)
);
CREATE INDEX gateway_credential_gateway ON gateway_credential (gateway_id, issued_at DESC);

CREATE FUNCTION gateway_credential_revoke_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'gateway_credential rows are never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF (to_jsonb(NEW) - 'revoked_at') IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at')
       OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at) THEN
        RAISE EXCEPTION 'gateway_credential rows are immutable except a single revocation'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER gateway_credential_revoke_only BEFORE UPDATE OR DELETE ON gateway_credential
    FOR EACH ROW EXECUTE FUNCTION gateway_credential_revoke_only();

CREATE TABLE gateway_access_event (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NULL,
    credential_selector text NULL,
    kind text NOT NULL CHECK (kind IN ('CREDENTIAL_ISSUED','CREDENTIAL_REVOKED',
        'GATEWAY_ENABLED','GATEWAY_DISABLED','SOURCE_ENABLED','SOURCE_DISABLED')),
    actor text NOT NULL,
    recorded_at timestamptz NOT NULL,
    CONSTRAINT gateway_access_event_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT gateway_access_event_source_fk FOREIGN KEY (tenant_id, site_id, gateway_id, source_id)
        REFERENCES source(tenant_id, site_id, gateway_id, id),
    CONSTRAINT gateway_access_event_shape CHECK (
        (kind LIKE 'SOURCE_%') = (source_id IS NOT NULL)
        AND (kind LIKE 'CREDENTIAL_%') = (credential_selector IS NOT NULL))
);
CREATE INDEX gateway_access_event_gateway ON gateway_access_event (gateway_id, recorded_at);

CREATE TABLE gateway_diagnostic (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    sequence_epoch text NOT NULL,
    diagnostic_sequence bigint NOT NULL CHECK (diagnostic_sequence >= 0),
    observed_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    last_device_contact_by_source jsonb NOT NULL,
    queue_count bigint NOT NULL CHECK (queue_count >= 0),
    oldest_queue_age_seconds bigint NULL CHECK (oldest_queue_age_seconds >= 0),
    disk_pressure text NOT NULL CHECK (disk_pressure IN ('OK','WARN','STOP')),
    clock_offset_ms bigint NULL,
    mapping_error_count bigint NOT NULL CHECK (mapping_error_count >= 0),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    diagnostic_text text NOT NULL,
    CONSTRAINT gateway_diagnostic_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT gateway_diagnostic_identity UNIQUE (gateway_id, sequence_epoch, diagnostic_sequence)
);
CREATE INDEX gateway_diagnostic_site_received ON gateway_diagnostic (site_id, received_at DESC);
CREATE INDEX gateway_diagnostic_gateway_received ON gateway_diagnostic (gateway_id, received_at DESC);

CREATE TABLE gateway_diagnostic_refusal (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    sequence_epoch text NULL,
    diagnostic_sequence bigint NULL,
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    kind text NOT NULL,
    field text NOT NULL,
    detail text NOT NULL,
    received_at timestamptz NOT NULL,
    CONSTRAINT gateway_diagnostic_refusal_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT gateway_diagnostic_refusal_identity UNIQUE NULLS NOT DISTINCT
        (gateway_id, sequence_epoch, diagnostic_sequence, payload_sha256, kind)
);

CREATE TRIGGER gateway_access_event_append_only BEFORE UPDATE OR DELETE ON gateway_access_event
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER gateway_diagnostic_append_only BEFORE UPDATE OR DELETE ON gateway_diagnostic
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER gateway_diagnostic_refusal_append_only BEFORE UPDATE OR DELETE ON gateway_diagnostic_refusal
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""


def upgrade() -> None:
    op.execute(ACCESS)


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS gateway_diagnostic_refusal, gateway_diagnostic, gateway_access_event,
            gateway_credential CASCADE;
        DROP FUNCTION IF EXISTS gateway_credential_revoke_only();
        ALTER TABLE gateway DROP COLUMN IF EXISTS diagnostic_cadence_seconds;
        """
    )
