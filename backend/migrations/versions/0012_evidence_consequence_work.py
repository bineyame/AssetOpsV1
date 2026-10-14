"""S4-02c phase 1: accepted generator-power evidence enqueues durable consequence work, atomically.

Packet `tasks/S4-02c-evidence-consequence-work.md` "Acceptance, work and worker contract" items 1-2, plan fix
round 1 (H2, H3, L2, M4, M5) and re-review carries N6/N8.

- `financial_consequence_work` gains the cause `EVIDENCE_ACCEPTED` and a nullable `accepted_evidence_id` with a
  tenant/Site-scoped FK to the exact `accepted_evidence` row. The cause shape is an explicit three-arm CHECK:
  an assumption row carries only the assumption locator; a FindingRevision row only the Finding locator; an
  evidence row the exact accepted ID plus Finding and FindingRevision locators and a non-empty half-open
  `[affected_from, affected_to)` (the reading's interval). Other causes' locators are null.
- `UNIQUE (finding_revision_id)` becomes a partial unique index for `FINDING_REVISION_APPENDED` only, so an
  evidence row may name the same FindingRevision; the 0011 FindingRevision trigger is replaced with the matching
  `ON CONFLICT ... WHERE` target. Evidence rows are unique per `(accepted_evidence_id, finding_revision_id)`.
- `AFTER INSERT ON ingestion_disposition` for `decision = 'ACCEPTED'` joins the stored, binding-derived
  `accepted_evidence.role` (never a client role). Only `generator_power` with a non-empty interval enqueues: one
  row per latest FindingRevision (highest `revision_no` of a Finding in the same tenant/Site) whose non-empty
  episode strictly overlaps the reading's half-open interval. It runs inside the ledger's `decide_chunk`
  transaction, so its failure rolls back the acceptance and disposition. DUPLICATE, CONFLICT, REJECTED and an
  exact batch replay insert no ACCEPTED disposition and so never enqueue.
- Both enqueue triggers take the same transaction-scoped Site advisory lock,
  `hashtextextended('financial_consequence_enqueue:' || site_id, 0)`, before they select or insert (review M4):
  at READ COMMITTED an acceptance that waited on a FindingRevision append sees its committed revision.
- `financial_consequence_work_attempt.no_op_reason`: a typed reason present only on a SUCCEEDED attempt with no
  consequence IDs (review L2); normal success or failure leaves it null. Attempt lookup is indexed by
  `(work_id, attempt_no DESC)`; pending selection keeps the 0011 `(tenant_id, site_id, enqueued_at)` index.

Upgrade keeps every 0011 work and attempt row (including the 0011 bootstrap rows) and backfills nothing for
historic acceptances (packet L4: a pre-0012 stale head reads `NO_WORK_RECORDED`). Downgrade refuses while any
`EVIDENCE_ACCEPTED` work row or `no_op_reason` exists (it never deletes append-only work), and otherwise
restores the 0011 trigger body, two-arm CHECK and `UNIQUE (finding_revision_id)`.

Revision ID: 0012_evidence_consequence_work
Revises: 0011_financial_consequences
Create Date: 2026-10-14
"""

from __future__ import annotations

from alembic import op

revision = "0012_evidence_consequence_work"
down_revision = "0011_financial_consequences"
branch_labels = None
depends_on = None

# Review N6: one expression, used verbatim by both enqueue triggers (a test compares the stored bodies).
ENQUEUE_LOCK = "PERFORM pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || NEW.site_id::text, 0));"

NO_OP_REASONS = ("FINDING_REVISION_SUPERSEDED", "EVIDENCE_ROLE_NOT_RELEVANT", "EVIDENCE_ASSET_NOT_RELEVANT",
                 "EVIDENCE_OUTSIDE_CANDIDATE_TIME")

SCHEMA = rf"""
ALTER TABLE financial_consequence_work DROP CONSTRAINT financial_consequence_work_cause_check;
ALTER TABLE financial_consequence_work DROP CONSTRAINT financial_consequence_work_cause_shape;
ALTER TABLE financial_consequence_work DROP CONSTRAINT financial_consequence_work_finding_revision_once;

ALTER TABLE financial_consequence_work ADD COLUMN accepted_evidence_id uuid NULL;
ALTER TABLE financial_consequence_work
    ADD CONSTRAINT financial_consequence_work_cause_check
        CHECK (cause IN ('ASSUMPTION_PUBLISHED','FINDING_REVISION_APPENDED','EVIDENCE_ACCEPTED')),
    ADD CONSTRAINT financial_consequence_work_cause_shape CHECK (
        (cause = 'ASSUMPTION_PUBLISHED' AND assumption_key IS NOT NULL AND assumption_revision_id IS NOT NULL
            AND finding_id IS NULL AND finding_revision_id IS NULL AND accepted_evidence_id IS NULL)
        OR (cause = 'FINDING_REVISION_APPENDED' AND finding_id IS NOT NULL AND finding_revision_id IS NOT NULL
            AND assumption_key IS NULL AND assumption_revision_id IS NULL AND accepted_evidence_id IS NULL)
        OR (cause = 'EVIDENCE_ACCEPTED' AND accepted_evidence_id IS NOT NULL AND finding_id IS NOT NULL
            AND finding_revision_id IS NOT NULL AND assumption_key IS NULL AND assumption_revision_id IS NULL
            AND affected_to IS NOT NULL AND affected_from < affected_to)),
    ADD CONSTRAINT financial_consequence_work_evidence_fk FOREIGN KEY (tenant_id, site_id, accepted_evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id);

CREATE UNIQUE INDEX financial_consequence_work_finding_revision_once
    ON financial_consequence_work (finding_revision_id) WHERE cause = 'FINDING_REVISION_APPENDED';
CREATE UNIQUE INDEX financial_consequence_work_evidence_once
    ON financial_consequence_work (accepted_evidence_id, finding_revision_id) WHERE cause = 'EVIDENCE_ACCEPTED';
CREATE INDEX financial_consequence_work_finding
    ON financial_consequence_work (tenant_id, site_id, finding_id) WHERE finding_id IS NOT NULL;

ALTER TABLE financial_consequence_work_attempt ADD COLUMN no_op_reason text NULL,
    ADD CONSTRAINT financial_consequence_attempt_no_op_reason CHECK (
        no_op_reason IS NULL OR (outcome = 'SUCCEEDED' AND consequence_revision_ids = '[]'::jsonb
            AND no_op_reason IN ({", ".join(f"'{r}'" for r in NO_OP_REASONS)})));
CREATE INDEX financial_consequence_attempt_latest
    ON financial_consequence_work_attempt (work_id, attempt_no DESC);

CREATE OR REPLACE FUNCTION financial_consequence_dirty_on_finding_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    {ENQUEUE_LOCK}
    INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, finding_revision_id,
                                            affected_from, affected_to)
    VALUES (NEW.tenant_id, NEW.site_id, 'FINDING_REVISION_APPENDED', NEW.finding_id, NEW.id, NEW.episode_start,
            NEW.episode_end)
    ON CONFLICT (finding_revision_id) WHERE cause = 'FINDING_REVISION_APPENDED' DO NOTHING;
    RETURN NULL;
END;
$$;

-- An accepted generator-power mean may change the technical input of every Finding whose latest revision's
-- episode overlaps it. Coarse on purpose: the worker rechecks and may no-op, but no possibly affected Finding is
-- omitted. Zero-width readings and zero-width episodes overlap nothing (half-open).
CREATE FUNCTION financial_consequence_dirty_on_evidence() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    ev record;
BEGIN
    SELECT e.role, e.interval_start, e.interval_end INTO ev FROM accepted_evidence e
    WHERE e.tenant_id = NEW.tenant_id AND e.site_id = NEW.site_id AND e.id = NEW.accepted_evidence_id;
    IF NOT FOUND OR ev.role <> 'generator_power' OR ev.interval_start IS NULL OR ev.interval_end IS NULL
            OR ev.interval_start >= ev.interval_end THEN
        RETURN NULL;
    END IF;
    {ENQUEUE_LOCK}
    INSERT INTO financial_consequence_work (tenant_id, site_id, cause, accepted_evidence_id, finding_id,
                                            finding_revision_id, affected_from, affected_to)
    SELECT NEW.tenant_id, NEW.site_id, 'EVIDENCE_ACCEPTED', NEW.accepted_evidence_id, r.finding_id, r.id,
           ev.interval_start, ev.interval_end
    FROM finding_revision r
    WHERE r.tenant_id = NEW.tenant_id AND r.site_id = NEW.site_id
      AND r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.tenant_id = r.tenant_id
                           AND x.site_id = r.site_id AND x.finding_id = r.finding_id)
      AND r.episode_start < r.episode_end
      AND r.episode_start < ev.interval_end AND r.episode_end > ev.interval_start
    ORDER BY r.episode_start, r.id
    ON CONFLICT (accepted_evidence_id, finding_revision_id) WHERE cause = 'EVIDENCE_ACCEPTED' DO NOTHING;
    RETURN NULL;
END;
$$;
CREATE TRIGGER financial_consequence_dirty_on_evidence AFTER INSERT ON ingestion_disposition
    FOR EACH ROW WHEN (NEW.decision = 'ACCEPTED') EXECUTE FUNCTION financial_consequence_dirty_on_evidence();
"""

# The 0011 trigger body and constraints, restored verbatim by downgrade.
RESTORE_0011 = r"""
DROP TRIGGER financial_consequence_dirty_on_evidence ON ingestion_disposition;
DROP FUNCTION financial_consequence_dirty_on_evidence();
DROP INDEX financial_consequence_attempt_latest;
ALTER TABLE financial_consequence_work_attempt DROP CONSTRAINT financial_consequence_attempt_no_op_reason,
    DROP COLUMN no_op_reason;
DROP INDEX financial_consequence_work_finding;
DROP INDEX financial_consequence_work_evidence_once;
DROP INDEX financial_consequence_work_finding_revision_once;
ALTER TABLE financial_consequence_work DROP CONSTRAINT financial_consequence_work_evidence_fk,
    DROP CONSTRAINT financial_consequence_work_cause_shape,
    DROP CONSTRAINT financial_consequence_work_cause_check,
    DROP COLUMN accepted_evidence_id;
ALTER TABLE financial_consequence_work
    ADD CONSTRAINT financial_consequence_work_cause_check
        CHECK (cause IN ('ASSUMPTION_PUBLISHED','FINDING_REVISION_APPENDED')),
    ADD CONSTRAINT financial_consequence_work_cause_shape CHECK (
        (cause = 'ASSUMPTION_PUBLISHED' AND assumption_key IS NOT NULL AND assumption_revision_id IS NOT NULL
            AND finding_id IS NULL AND finding_revision_id IS NULL)
        OR (cause = 'FINDING_REVISION_APPENDED' AND finding_id IS NOT NULL AND finding_revision_id IS NOT NULL
            AND assumption_key IS NULL AND assumption_revision_id IS NULL)),
    ADD CONSTRAINT financial_consequence_work_finding_revision_once UNIQUE (finding_revision_id);

CREATE OR REPLACE FUNCTION financial_consequence_dirty_on_finding_revision() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO financial_consequence_work (tenant_id, site_id, cause, finding_id, finding_revision_id,
                                            affected_from, affected_to)
    VALUES (NEW.tenant_id, NEW.site_id, 'FINDING_REVISION_APPENDED', NEW.finding_id, NEW.id, NEW.episode_start,
            NEW.episode_end)
    ON CONFLICT (finding_revision_id) DO NOTHING;
    RETURN NULL;
END;
$$;
"""

# Review M5: never delete append-only work to make a downgrade fit; refuse with a clear error instead.
REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM financial_consequence_work WHERE cause = 'EVIDENCE_ACCEPTED') THEN
        RAISE EXCEPTION 'Downgrade of 0012_evidence_consequence_work refused: EVIDENCE_ACCEPTED consequence work exists. Append-only work is never deleted; 0011 cannot represent it.';
    END IF;
    IF EXISTS (SELECT 1 FROM financial_consequence_work_attempt WHERE no_op_reason IS NOT NULL) THEN
        RAISE EXCEPTION 'Downgrade of 0012_evidence_consequence_work refused: work attempts record a no-op reason. Append-only attempts are never deleted; 0011 cannot represent them.';
    END IF;
END;
$$;
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(RESTORE_0011)
