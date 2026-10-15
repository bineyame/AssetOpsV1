"""S4-05a phase 1: immutable pre-admission source publication and its batch link.

`D-2026-10-15-s405-stored-demo-provenance` (`.agent/architect-S4-05-answers.md` Q1, rule 8, Follow-up M1).
Two insert-only tables, written at runtime only by the existing evidence-ledger writer
(`evidence/adapters/postgres_evidence_ledger.py`); this migration owns their DDL and no ninth writer exists.

- `evidence_publication`: a server-authorized SYSTEM designation committed before admission of one exact
  Batch V2. It pins tenant/Site, gateway/source, external batch ID and the canonical payload SHA-256, and
  either the authored fixture/spec ID and version (`AUTHORED_DEMONSTRATION`) or the server-recorded run ID
  and run identity digest (`REGISTERED_SIMULATION`), with the server-resolved actor, authorization basis,
  channel, trigger and recorded time. One publication per Site batch slot (the same scope as
  `ingestion_batch_external_unique`).
- `batch_publication_link`: written in the admission transaction that inserts the batch. Its composite
  foreign keys pin the link to a publication and a batch with the same tenant, Site, gateway, source,
  external batch ID and payload digest, so a link can only join an exact commitment.

Accepted evidence inherits the link through `accepted_evidence.batch_id` (already append-only, 0005).
Both new tables refuse UPDATE and DELETE by trigger. No backfill: existing batches stay unbound.

Revision ID: 0014_evidence_publication
Revises: 0013_schedule_state
Create Date: 2026-10-15
"""

from __future__ import annotations

from alembic import op

revision = "0014_evidence_publication"
down_revision = "0013_schedule_state"
branch_labels = None
depends_on = None

SCHEMA = """
ALTER TABLE ingestion_batch ADD CONSTRAINT ingestion_batch_commitment_unique
    UNIQUE (tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, id);

CREATE TABLE evidence_publication (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NOT NULL,
    external_batch_id text NOT NULL,
    payload_sha256 text NOT NULL,
    source_class text NOT NULL,
    fixture_id text,
    fixture_version text,
    run_id text,
    run_identity_sha256 text,
    actor_kind text NOT NULL,
    actor_id text NOT NULL,
    authorization_basis text NOT NULL,
    channel text NOT NULL,
    publication_trigger text NOT NULL,
    recorded_at timestamptz NOT NULL,
    CONSTRAINT evidence_publication_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT evidence_publication_gateway_fk FOREIGN KEY (tenant_id, site_id, gateway_id)
        REFERENCES gateway(tenant_id, site_id, id),
    CONSTRAINT evidence_publication_source_fk FOREIGN KEY (tenant_id, site_id, gateway_id, source_id)
        REFERENCES source(tenant_id, site_id, gateway_id, id),
    CONSTRAINT evidence_publication_slot_unique UNIQUE (site_id, external_batch_id),
    CONSTRAINT evidence_publication_scope_unique UNIQUE (tenant_id, site_id, id),
    CONSTRAINT evidence_publication_commitment_unique
        UNIQUE (tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, id),
    CONSTRAINT evidence_publication_digest CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT evidence_publication_batch_id CHECK (length(external_batch_id) > 0),
    CONSTRAINT evidence_publication_class CHECK (
        (source_class = 'AUTHORED_DEMONSTRATION'
            AND fixture_id IS NOT NULL AND fixture_version IS NOT NULL
            AND length(fixture_id) > 0 AND length(fixture_version) > 0
            AND run_id IS NULL AND run_identity_sha256 IS NULL)
        OR (source_class = 'REGISTERED_SIMULATION'
            AND run_id IS NOT NULL AND run_identity_sha256 IS NOT NULL
            AND length(run_id) > 0 AND run_identity_sha256 ~ '^[0-9a-f]{64}$'
            AND fixture_id IS NULL AND fixture_version IS NULL)),
    CONSTRAINT evidence_publication_system_actor CHECK (actor_kind = 'SYSTEM' AND length(actor_id) > 0
        AND length(authorization_basis) > 0 AND length(publication_trigger) > 0),
    CONSTRAINT evidence_publication_channel CHECK (channel IN ('SYSTEM_CLI', 'SYSTEM_FIXTURE', 'SYSTEM_LAB_RELEASE'))
);

CREATE TABLE batch_publication_link (
    batch_id uuid PRIMARY KEY,
    publication_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    gateway_id uuid NOT NULL,
    source_id uuid NOT NULL,
    external_batch_id text NOT NULL,
    payload_sha256 text NOT NULL,
    linked_at timestamptz NOT NULL,
    CONSTRAINT batch_publication_link_publication_unique UNIQUE (publication_id),
    CONSTRAINT batch_publication_link_batch_fk
        FOREIGN KEY (tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, batch_id)
        REFERENCES ingestion_batch(tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, id),
    CONSTRAINT batch_publication_link_publication_fk
        FOREIGN KEY (tenant_id, site_id, gateway_id, source_id, external_batch_id, payload_sha256, publication_id)
        REFERENCES evidence_publication(tenant_id, site_id, gateway_id, source_id, external_batch_id,
                                        payload_sha256, id)
);

CREATE FUNCTION source_provenance_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% rows are immutable source provenance', TG_TABLE_NAME USING ERRCODE = 'restrict_violation';
END $$;
CREATE TRIGGER evidence_publication_immutable BEFORE UPDATE OR DELETE ON evidence_publication
    FOR EACH ROW EXECUTE FUNCTION source_provenance_immutable();
CREATE TRIGGER batch_publication_link_immutable BEFORE UPDATE OR DELETE ON batch_publication_link
    FOR EACH ROW EXECUTE FUNCTION source_provenance_immutable();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


# Never delete immutable provenance to make a downgrade fit; refuse instead (0012 precedent).
REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM evidence_publication) THEN
        RAISE EXCEPTION 'Downgrade of 0014_evidence_publication refused: source publications exist. Immutable provenance is never deleted; 0013 cannot represent it.';
    END IF;
END;
$$;
"""


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(
        """
        DROP TABLE IF EXISTS batch_publication_link, evidence_publication;
        DROP FUNCTION IF EXISTS source_provenance_immutable();
        ALTER TABLE ingestion_batch DROP CONSTRAINT IF EXISTS ingestion_batch_commitment_unique;
        """
    )
