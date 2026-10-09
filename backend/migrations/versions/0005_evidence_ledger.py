"""S2-02 phase 1: registered identity hardening and the central evidence ledger.

Identity (S2-01a amendment to `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary`,
S2-02 AC4): before any evidence is accepted,

* `asset.asset_code` (with the asset's id, tenant, Site and created_at) becomes
  immutable at the database boundary. Rows that already drifted are reconciled
  by refusal, not by guessing: the migration refuses, naming them, when a bound
  asset's code is absent from its binding set's Foundation revision or a Site's
  asset code is absent from every Foundation revision of that Site.
* a gateway's tenant, Site, mode and registration time, and a source's tenant,
  Site and gateway affiliation, become immutable (technical design section 1).
* a Site's tenant and type become immutable once accepted evidence exists for it.

External IDs (`gateway_external_id`, `source_external_id`) remain mutable
current-row names: pinned snapshots hold their published spelling (0004), and
acceptance resolves only immutable registered UUIDs. See S2-02 questions-1.

Ledger (technical design section 1 "Ingestion and evidence ledger"):
`ingestion_batch`, `accepted_evidence`, `evidence_rejection`,
`ingestion_disposition`, `batch_refusal` and `recompute_job`. Every row carries
`(tenant_id, site_id)` with same-Site composite foreign keys. Evidence,
rejection, disposition and refusal rows are append-only; a batch row may only
advance its counters and status; a recompute job may only change its window
while PENDING and its lease/status fields.

Revision ID: 0005_evidence_ledger
Revises: 0004_snapshot_canonical_bytes
Create Date: 2026-10-09
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0005_evidence_ledger"
down_revision = "0004_snapshot_canonical_bytes"
branch_labels = None
depends_on = None


_DRIFTED_BOUND_ASSETS = """
SELECT b.id::text, a.asset_code
FROM signal_binding_revision b
JOIN signal_binding_set_revision s ON s.id = b.binding_set_revision_id
JOIN foundation_revision f ON f.id = s.foundation_revision_id
JOIN asset a ON a.id = b.asset_id
WHERE NOT EXISTS (
    SELECT 1 FROM jsonb_array_elements(COALESCE(f.content->'components', '[]'::jsonb)) c
    WHERE c->>'component_id' = a.asset_code
)
ORDER BY 1
"""

_DRIFTED_SITE_ASSETS = """
SELECT a.id::text, a.asset_code
FROM asset a
WHERE EXISTS (SELECT 1 FROM foundation_revision f WHERE f.site_id = a.site_id)
  AND NOT EXISTS (
    SELECT 1 FROM foundation_revision f,
         jsonb_array_elements(COALESCE(f.content->'components', '[]'::jsonb)) c
    WHERE f.site_id = a.site_id AND c->>'component_id' = a.asset_code
)
ORDER BY 1
"""


IDENTITY = """
CREATE FUNCTION asset_identity_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id OR NEW.asset_code IS DISTINCT FROM OLD.asset_code
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'asset identity is immutable: id, tenant, Site, asset_code and created_at cannot change'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER asset_identity_immutable BEFORE UPDATE ON asset
    FOR EACH ROW EXECUTE FUNCTION asset_identity_immutable();

CREATE FUNCTION gateway_identity_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id OR NEW.mode IS DISTINCT FROM OLD.mode
       OR NEW.registered_at IS DISTINCT FROM OLD.registered_at THEN
        RAISE EXCEPTION 'gateway registration is immutable: id, tenant, Site, mode and registered_at cannot change'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER gateway_identity_immutable BEFORE UPDATE ON gateway
    FOR EACH ROW EXECUTE FUNCTION gateway_identity_immutable();

CREATE FUNCTION source_identity_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id OR NEW.gateway_id IS DISTINCT FROM OLD.gateway_id
       OR NEW.registered_at IS DISTINCT FROM OLD.registered_at THEN
        RAISE EXCEPTION 'source registration is immutable: id, tenant, Site, gateway and registered_at cannot change'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER source_identity_immutable BEFORE UPDATE ON source
    FOR EACH ROW EXECUTE FUNCTION source_identity_immutable();
"""


LEDGER = """
ALTER TABLE source ADD CONSTRAINT source_scope_unique UNIQUE (tenant_id, site_id, gateway_id, id);
ALTER TABLE signal_binding_revision
    ADD CONSTRAINT binding_revision_scope_unique UNIQUE (tenant_id, site_id, id);

CREATE TABLE ingestion_batch (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NOT NULL,
    external_batch_id text NOT NULL,
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    schema_version integer NOT NULL,
    source_mode text NOT NULL CHECK (source_mode IN ('LIVE','SIMULATED')),
    foundation_revision_id uuid NOT NULL,
    binding_set_revision_id uuid NOT NULL,
    snapshot_sha256 text NOT NULL,
    batch_text text NOT NULL,
    status text NOT NULL CHECK (status IN ('IN_PROGRESS','COMPLETED')),
    total_count integer NOT NULL CHECK (total_count > 0),
    processed_count integer NOT NULL DEFAULT 0,
    accepted_count integer NOT NULL DEFAULT 0,
    duplicate_count integer NOT NULL DEFAULT 0,
    rejected_count integer NOT NULL DEFAULT 0,
    conflict_count integer NOT NULL DEFAULT 0,
    received_at timestamptz NOT NULL,
    completed_at timestamptz NULL,
    CONSTRAINT ingestion_batch_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT ingestion_batch_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT ingestion_batch_source_fk FOREIGN KEY (tenant_id, site_id, gateway_id, source_id)
        REFERENCES source(tenant_id, site_id, gateway_id, id),
    CONSTRAINT ingestion_batch_foundation_fk FOREIGN KEY (tenant_id, site_id, foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT ingestion_batch_binding_set_fk FOREIGN KEY (tenant_id, site_id, binding_set_revision_id)
        REFERENCES signal_binding_set_revision(tenant_id, site_id, id),
    CONSTRAINT ingestion_batch_external_unique UNIQUE (site_id, external_batch_id),
    CONSTRAINT ingestion_batch_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT ingestion_batch_counts CHECK (
        processed_count <= total_count
        AND processed_count = accepted_count + duplicate_count + rejected_count + conflict_count
    ),
    CONSTRAINT ingestion_batch_completion CHECK (
        (status = 'COMPLETED') = (processed_count = total_count)
        AND (status = 'COMPLETED') = (completed_at IS NOT NULL)
    )
);
CREATE INDEX ingestion_batch_site_received ON ingestion_batch (site_id, received_at DESC);

CREATE TABLE accepted_evidence (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    batch_id uuid NOT NULL,
    ordinal integer NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NOT NULL,
    message_id text NOT NULL,
    sequence_epoch text NOT NULL,
    sequence bigint NOT NULL,
    device_id text NOT NULL,
    signal_id text NOT NULL,
    asset_id uuid NULL,
    role text NOT NULL,
    family text NOT NULL,
    measurement text NOT NULL,
    source_time timestamptz NOT NULL,
    published_at timestamptz NOT NULL,
    received_at timestamptz NOT NULL,
    interval_start timestamptz NULL,
    interval_end timestamptz NULL,
    quality text NOT NULL,
    unavailable_reason text NULL,
    original_value_text text NULL,
    original_unit text NOT NULL,
    normalized_value_text text NULL,
    normalized_unit text NOT NULL,
    conversion_kind text NOT NULL,
    envelope_sha256 text NOT NULL CHECK (envelope_sha256 ~ '^[0-9a-f]{64}$'),
    envelope_text text NOT NULL,
    foundation_revision_id uuid NOT NULL,
    binding_set_revision_id uuid NOT NULL,
    binding_revision_id uuid NOT NULL,
    configuration_outdated boolean NOT NULL,
    source_mode text NOT NULL CHECK (source_mode IN ('LIVE','SIMULATED')),
    CONSTRAINT accepted_evidence_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT accepted_evidence_batch_fk FOREIGN KEY (tenant_id, site_id, batch_id)
        REFERENCES ingestion_batch(tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_source_fk FOREIGN KEY (tenant_id, site_id, gateway_id, source_id)
        REFERENCES source(tenant_id, site_id, gateway_id, id),
    CONSTRAINT accepted_evidence_asset_fk FOREIGN KEY (tenant_id, site_id, asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_foundation_fk FOREIGN KEY (tenant_id, site_id, foundation_revision_id)
        REFERENCES foundation_revision(tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_binding_set_fk FOREIGN KEY (tenant_id, site_id, binding_set_revision_id)
        REFERENCES signal_binding_set_revision(tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_binding_fk FOREIGN KEY (tenant_id, site_id, binding_revision_id)
        REFERENCES signal_binding_revision(tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_message_unique UNIQUE (site_id, gateway_id, source_id, message_id),
    CONSTRAINT accepted_evidence_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT accepted_evidence_published_after_source CHECK (published_at >= source_time)
);
CREATE INDEX accepted_evidence_site_time ON accepted_evidence (site_id, source_time DESC);
CREATE INDEX accepted_evidence_channel_time ON accepted_evidence (site_id, device_id, signal_id, source_time);
CREATE INDEX accepted_evidence_binding_time ON accepted_evidence (site_id, binding_revision_id, source_time);
CREATE INDEX accepted_evidence_batch ON accepted_evidence (batch_id);

CREATE TABLE evidence_rejection (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    batch_id uuid NOT NULL,
    ordinal integer NOT NULL,
    message_id text NULL,
    kind text NOT NULL,
    field text NOT NULL,
    detail text NOT NULL,
    envelope_sha256 text NOT NULL CHECK (envelope_sha256 ~ '^[0-9a-f]{64}$'),
    conflicts_with_evidence_id uuid NULL,
    received_at timestamptz NOT NULL,
    CONSTRAINT evidence_rejection_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT evidence_rejection_batch_fk FOREIGN KEY (tenant_id, site_id, batch_id)
        REFERENCES ingestion_batch(tenant_id, site_id, id),
    CONSTRAINT evidence_rejection_conflict_fk FOREIGN KEY (tenant_id, site_id, conflicts_with_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT evidence_rejection_unique UNIQUE (batch_id, ordinal, kind, envelope_sha256),
    CONSTRAINT evidence_rejection_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT evidence_rejection_conflict_kind CHECK (
        (kind = 'MESSAGE_CONFLICT') = (conflicts_with_evidence_id IS NOT NULL)
    )
);
CREATE INDEX evidence_rejection_site_received ON evidence_rejection (site_id, received_at DESC);
CREATE INDEX evidence_rejection_batch_ordinal ON evidence_rejection (batch_id, ordinal);

CREATE TABLE ingestion_disposition (
    batch_id uuid NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    message_id text NOT NULL,
    decision text NOT NULL CHECK (decision IN ('ACCEPTED','DUPLICATE','REJECTED','CONFLICT')),
    accepted_evidence_id uuid NULL,
    rejection_id uuid NULL,
    decided_at timestamptz NOT NULL,
    PRIMARY KEY (batch_id, ordinal),
    CONSTRAINT ingestion_disposition_batch_fk FOREIGN KEY (tenant_id, site_id, batch_id)
        REFERENCES ingestion_batch(tenant_id, site_id, id),
    CONSTRAINT ingestion_disposition_evidence_fk FOREIGN KEY (tenant_id, site_id, accepted_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT ingestion_disposition_rejection_fk FOREIGN KEY (tenant_id, site_id, rejection_id)
        REFERENCES evidence_rejection(tenant_id, site_id, id),
    CONSTRAINT ingestion_disposition_reference CHECK (
        (decision IN ('ACCEPTED','DUPLICATE')) = (accepted_evidence_id IS NOT NULL)
        AND (decision IN ('REJECTED','CONFLICT')) = (rejection_id IS NOT NULL)
    )
);
CREATE INDEX ingestion_disposition_batch_decision ON ingestion_disposition (batch_id, decision);

CREATE TABLE batch_refusal (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    external_batch_id text NULL,
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    kind text NOT NULL,
    field text NOT NULL,
    detail text NOT NULL,
    received_at timestamptz NOT NULL,
    CONSTRAINT batch_refusal_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT batch_refusal_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT batch_refusal_identity UNIQUE NULLS NOT DISTINCT
        (tenant_id, site_id, external_batch_id, payload_sha256, kind)
);
CREATE INDEX batch_refusal_site_received ON batch_refusal (site_id, received_at DESC);

CREATE TABLE recompute_job (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    domain text NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    cause_evidence_id uuid NULL,
    status text NOT NULL CHECK (status IN ('PENDING','LEASED','DONE','FAILED')),
    available_at timestamptz NOT NULL,
    lease_until timestamptz NULL,
    attempts integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL,
    CONSTRAINT recompute_job_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT recompute_job_cause_fk FOREIGN KEY (tenant_id, site_id, cause_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id),
    CONSTRAINT recompute_job_window CHECK (window_start < window_end)
);
CREATE INDEX recompute_job_pending ON recompute_job (status, available_at) WHERE status = 'PENDING';
CREATE INDEX recompute_job_site_window ON recompute_job (site_id, window_start);

CREATE FUNCTION ledger_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% rows are append-only', TG_TABLE_NAME USING ERRCODE = 'restrict_violation';
END $$;
CREATE TRIGGER accepted_evidence_append_only BEFORE UPDATE OR DELETE ON accepted_evidence
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER evidence_rejection_append_only BEFORE UPDATE OR DELETE ON evidence_rejection
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ingestion_disposition_append_only BEFORE UPDATE OR DELETE ON ingestion_disposition
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER batch_refusal_append_only BEFORE UPDATE OR DELETE ON batch_refusal
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();

CREATE FUNCTION ingestion_batch_progress_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'ingestion_batch rows are never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF (to_jsonb(NEW) - ARRAY['status','processed_count','accepted_count','duplicate_count',
                              'rejected_count','conflict_count','completed_at'])
       IS DISTINCT FROM
       (to_jsonb(OLD) - ARRAY['status','processed_count','accepted_count','duplicate_count',
                              'rejected_count','conflict_count','completed_at']) THEN
        RAISE EXCEPTION 'ingestion_batch identity, bytes and references are immutable'
            USING ERRCODE = 'restrict_violation';
    END IF;
    IF OLD.status = 'COMPLETED' AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION 'a completed ingestion_batch is final' USING ERRCODE = 'restrict_violation';
    END IF;
    IF NEW.processed_count < OLD.processed_count OR NEW.accepted_count < OLD.accepted_count
       OR NEW.duplicate_count < OLD.duplicate_count OR NEW.rejected_count < OLD.rejected_count
       OR NEW.conflict_count < OLD.conflict_count THEN
        RAISE EXCEPTION 'ingestion_batch progress only advances' USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER ingestion_batch_progress_only BEFORE UPDATE OR DELETE ON ingestion_batch
    FOR EACH ROW EXECUTE FUNCTION ingestion_batch_progress_only();

CREATE FUNCTION recompute_job_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'recompute_job rows are never deleted' USING ERRCODE = 'restrict_violation';
    END IF;
    IF NEW.id IS DISTINCT FROM OLD.id OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.site_id IS DISTINCT FROM OLD.site_id OR NEW.domain IS DISTINCT FROM OLD.domain
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.cause_evidence_id IS DISTINCT FROM OLD.cause_evidence_id THEN
        RAISE EXCEPTION 'recompute_job identity is immutable' USING ERRCODE = 'restrict_violation';
    END IF;
    IF (NEW.window_start IS DISTINCT FROM OLD.window_start OR NEW.window_end IS DISTINCT FROM OLD.window_end)
       AND (OLD.status <> 'PENDING' OR NEW.window_start > OLD.window_start OR NEW.window_end < OLD.window_end) THEN
        RAISE EXCEPTION 'a recompute window only widens, and only while PENDING' USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER recompute_job_mutation BEFORE UPDATE OR DELETE ON recompute_job
    FOR EACH ROW EXECUTE FUNCTION recompute_job_mutation();

CREATE FUNCTION site_type_fixed_after_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.id IS DISTINCT FROM OLD.id THEN
        RAISE EXCEPTION 'Site identity is immutable' USING ERRCODE = 'restrict_violation';
    END IF;
    IF NEW.site_type IS DISTINCT FROM OLD.site_type
       AND EXISTS (SELECT 1 FROM accepted_evidence e WHERE e.site_id = OLD.id) THEN
        RAISE EXCEPTION 'Site type is fixed once accepted evidence exists' USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER site_type_fixed_after_evidence BEFORE UPDATE ON site
    FOR EACH ROW EXECUTE FUNCTION site_type_fixed_after_evidence();
"""


def _refuse_drift() -> None:
    bind = op.get_bind()
    problems = [
        f"binding {row[0]} names asset code {row[1]!r}, absent from its Foundation revision"
        for row in bind.execute(text(_DRIFTED_BOUND_ASSETS))
    ] + [
        f"asset {row[0]} code {row[1]!r} is absent from every Foundation revision of its Site"
        for row in bind.execute(text(_DRIFTED_SITE_ASSETS))
    ]
    if problems:
        raise RuntimeError(
            "0005 refuses to freeze asset identity over drifted rows (S2-02 AC4). Restore each "
            "code from the Foundation revision it was registered from, then rerun: "
            + "; ".join(problems)
        )


def upgrade() -> None:
    _refuse_drift()
    op.execute(IDENTITY)
    op.execute(LEDGER)


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS recompute_job, ingestion_disposition, evidence_rejection,
            accepted_evidence, batch_refusal, ingestion_batch CASCADE;
        DROP TRIGGER IF EXISTS site_type_fixed_after_evidence ON site;
        DROP TRIGGER IF EXISTS asset_identity_immutable ON asset;
        DROP TRIGGER IF EXISTS gateway_identity_immutable ON gateway;
        DROP TRIGGER IF EXISTS source_identity_immutable ON source;
        DROP FUNCTION IF EXISTS site_type_fixed_after_evidence(), recompute_job_mutation(),
            ingestion_batch_progress_only(), ledger_append_only(), asset_identity_immutable(),
            gateway_identity_immutable(), source_identity_immutable();
        ALTER TABLE signal_binding_revision DROP CONSTRAINT IF EXISTS binding_revision_scope_unique;
        ALTER TABLE source DROP CONSTRAINT IF EXISTS source_scope_unique;
        """
    )
