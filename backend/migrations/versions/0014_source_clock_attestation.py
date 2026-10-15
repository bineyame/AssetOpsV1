"""LR-01 phase 1: append-only source clock attestation events.

One table, `source_clock_attestation`: each row is one versioned event of one attestation (`RECORDED`, then
`REPLACED`, `EXPIRED` or `REVOKED`), scoped to tenant/Site/registered source/sequence epoch, naming its
authority, simulated label, proven maximum UTC error (an admission ceiling of 60 seconds) and half-open
validity `[valid_from, valid_to)`, with the SYSTEM attester, channel and idempotency key that recorded it.
LR-01 has no real-source path: the only proof class is `SIMULATED`
(`D-2026-10-15-lr01-source-time-cohort`).

Written at runtime only by `assetops_backend/analytics/adapters/postgres_assessment_store.py` (INSERT only,
together with the affected-window requeue in the same transaction). A trigger refuses UPDATE and DELETE.

Revision ID: 0014_source_clock_attestation
Revises: 0013_schedule_state
Create Date: 2026-10-15
"""

from __future__ import annotations

from alembic import op

revision = "0014_source_clock_attestation"
down_revision = "0013_schedule_state"
branch_labels = None
depends_on = None


SCHEMA = """
CREATE TABLE source_clock_attestation (
    id uuid PRIMARY KEY,
    attestation_id uuid NOT NULL,
    version integer NOT NULL CHECK (version >= 1),
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    source_id uuid NOT NULL REFERENCES source(id),
    sequence_epoch text NOT NULL CHECK (length(sequence_epoch) > 0),
    event_kind text NOT NULL CHECK (event_kind IN ('RECORDED','REPLACED','EXPIRED','REVOKED')),
    proof_class text NOT NULL CHECK (proof_class IN ('SIMULATED')),
    authority text NOT NULL CHECK (length(authority) > 0),
    label text NOT NULL CHECK (length(label) > 0),
    max_utc_error_ms integer NOT NULL CHECK (max_utc_error_ms BETWEEN 0 AND 60000),
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NOT NULL,
    reason text NULL,
    recorded_at timestamptz NOT NULL,
    recorded_by text NOT NULL,
    authorization_basis text NOT NULL,
    channel text NOT NULL CHECK (channel IN ('SYSTEM_CLI','SYSTEM_FIXTURE')),
    idempotency_key text NOT NULL CHECK (length(idempotency_key) > 0),
    request_sha256 text NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT source_clock_attestation_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT source_clock_attestation_validity CHECK (valid_from < valid_to),
    CONSTRAINT source_clock_attestation_first CHECK ((version = 1) = (event_kind = 'RECORDED')),
    CONSTRAINT source_clock_attestation_revoke_reason CHECK (event_kind <> 'REVOKED' OR reason IS NOT NULL),
    CONSTRAINT source_clock_attestation_version_unique UNIQUE (attestation_id, version),
    CONSTRAINT source_clock_attestation_idempotency UNIQUE (tenant_id, site_id, idempotency_key)
);
CREATE INDEX source_clock_attestation_site ON source_clock_attestation (tenant_id, site_id, recorded_at);

CREATE FUNCTION source_clock_attestation_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'source_clock_attestation is append-only: record a REPLACED, EXPIRED or REVOKED event';
END;
$$;
CREATE TRIGGER source_clock_attestation_append_only BEFORE UPDATE OR DELETE ON source_clock_attestation
    FOR EACH ROW EXECUTE FUNCTION source_clock_attestation_append_only();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS source_clock_attestation")
    op.execute("DROP FUNCTION IF EXISTS source_clock_attestation_append_only()")
