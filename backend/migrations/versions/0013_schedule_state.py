"""S4-02d phase 1: bounded, mutable schedule state for the analytic/Finding worker tick.

Four tables, one row per environment or per Site (no unbounded tick rows), written at runtime only by
`assetops_backend/scheduling/adapters/postgres_schedule_store.py`, the eighth PostgreSQL writer ratified in
`D-2026-10-14-s402d-schedule-storage-and-install-gate`:

- `schedule_tick_head`: the environment tick's expiring claim, last start/success/failure, heartbeat, retry due,
  claim-skip count and the last tick's counts.
- `schedule_site_head`: one Site's expiring stage claim, current stage, last selected/processed/deferred counts,
  last failure and retry due, the last completed matcher fence and S4 outcome, and claim-skip counts.
- `schedule_cursor`: the environment's fair position in the (tenant_id, site_id) order.
- `schedule_enrolment`: explicit Site enrolment (a Site with no accepted evidence is selected only if enrolled).

Claims and deadlines are DB time (`clock_timestamp()`), set by the writer. No trigger; S3 jobs, Findings,
evidence and consequence rows stay under their own writers.

Revision ID: 0013_schedule_state
Revises: 0012_evidence_consequence_work
Create Date: 2026-10-14
"""

from __future__ import annotations

from alembic import op

revision = "0013_schedule_state"
down_revision = "0012_evidence_consequence_work"
branch_labels = None
depends_on = None


SCHEMA = """
CREATE TABLE schedule_tick_head (
    environment text PRIMARY KEY CHECK (length(environment) BETWEEN 1 AND 64),
    claim_token uuid NULL,
    claim_owner text NULL,
    claimed_at timestamptz NULL,
    lease_until timestamptz NULL,
    last_started_at timestamptz NULL,
    last_succeeded_at timestamptz NULL,
    last_failed_at timestamptz NULL,
    last_failure_code text NULL,
    last_failure_detail text NULL,
    heartbeat_at timestamptz NULL,
    retry_due_at timestamptz NULL,
    consecutive_failures integer NOT NULL DEFAULT 0,
    claim_skips integer NOT NULL DEFAULT 0,
    last_skipped_at timestamptz NULL,
    last_sites_selected integer NOT NULL DEFAULT 0,
    last_sites_processed integer NOT NULL DEFAULT 0,
    last_sites_deferred integer NOT NULL DEFAULT 0,
    last_excluded_with_work integer NOT NULL DEFAULT 0,
    last_reconcile_ms integer NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT schedule_tick_claim_shape CHECK ((claim_token IS NULL) = (lease_until IS NULL))
);

CREATE TABLE schedule_site_head (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    claim_token uuid NULL,
    claim_owner text NULL,
    claimed_at timestamptz NULL,
    lease_until timestamptz NULL,
    stage text NOT NULL DEFAULT 'IDLE' CHECK (stage IN ('IDLE', 'S3', 'S4', 'CONSEQUENCE')),
    stage_started_at timestamptz NULL,
    selected_count bigint NOT NULL DEFAULT 0,
    last_selected_at timestamptz NULL,
    last_completed_at timestamptz NULL,
    s3_processed integer NOT NULL DEFAULT 0,
    s3_deferred integer NOT NULL DEFAULT 0,
    consequence_processed integer NOT NULL DEFAULT 0,
    consequence_deferred integer NOT NULL DEFAULT 0,
    s4_outcome text NULL,
    s4_outcome_at timestamptz NULL,
    matched_fence jsonb NULL,
    matched_version text NULL,
    matched_at timestamptz NULL,
    fence_moved_streak integer NOT NULL DEFAULT 0,
    last_failure_stage text NULL,
    last_failure_code text NULL,
    last_failure_detail text NULL,
    last_failed_at timestamptz NULL,
    consecutive_failures integer NOT NULL DEFAULT 0,
    retry_due_at timestamptz NULL,
    claim_skips integer NOT NULL DEFAULT 0,
    last_skipped_at timestamptz NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, site_id),
    CONSTRAINT schedule_site_head_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT schedule_site_claim_shape CHECK ((claim_token IS NULL) = (lease_until IS NULL))
);

CREATE TABLE schedule_cursor (
    environment text PRIMARY KEY CHECK (length(environment) BETWEEN 1 AND 64),
    after_tenant_id uuid NULL,
    after_site_id uuid NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT schedule_cursor_shape CHECK ((after_tenant_id IS NULL) = (after_site_id IS NULL))
);

CREATE TABLE schedule_enrolment (
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    enrolled boolean NOT NULL,
    changed_by text NOT NULL,
    changed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, site_id),
    CONSTRAINT schedule_enrolment_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id)
);
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS schedule_enrolment, schedule_cursor, schedule_site_head, "
               "schedule_tick_head;")
