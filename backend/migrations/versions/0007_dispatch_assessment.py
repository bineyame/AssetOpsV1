"""S3-01 phase 2: durable analytic runs and immutable assessment revisions.

Technical design section 1 ("Assessments, claims and work") and
`D-2026-10-11-s3-dispatch-interval-assessment` ("Revisions and jobs").

- `analytic_run`: one reproducible computation over one input set. Idempotent
  on `(site_id, analytic_id, model_version, window_start, window_end,
  input_sha256)`; stores the knowledge cutoff, cohort selection, configuration
  digest and source/receipt watermarks. Written once, complete, in the same
  commit as its revisions and the job completion; append-only.
- `analytic_run_evidence`: the exact accepted evidence ID set of a run.
- `assessment_revision`: append-only conclusion under a stable
  `assessment_key`; a new revision only when the basis changed.
- `analytic_run_assessment`: which revision each run selected for each key
  (a key whose basis did not change points at its existing revision).
- `recompute_job.last_error`: the reason a leased job failed (retry/FAILED).

Every row carries `(tenant_id, site_id)` with same-Site composite foreign keys.

Revision ID: 0007_dispatch_assessment
Revises: 0006_gateway_access
Create Date: 2026-10-11
"""

from __future__ import annotations

from alembic import op

revision = "0007_dispatch_assessment"
down_revision = "0006_gateway_access"
branch_labels = None
depends_on = None


ASSESSMENT = """
ALTER TABLE recompute_job ADD COLUMN last_error text NULL;

CREATE TABLE analytic_run (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    analytic_id text NOT NULL,
    model_version text NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    knowledge_cutoff timestamptz NOT NULL,
    input_sha256 text NOT NULL,
    cohort_status text NOT NULL,
    cohort_sha256 text NOT NULL,
    cohort jsonb NOT NULL,
    configuration_sha256 text NOT NULL,
    foundation_revision_ids jsonb NOT NULL,
    binding_set_revision_ids jsonb NOT NULL,
    role_coverage jsonb NOT NULL,
    watermarks jsonb NOT NULL,
    selection text NOT NULL CHECK (selection IN ('DEFAULT', 'EXPLICIT')),
    job_id uuid NULL,
    status text NOT NULL CHECK (status = 'COMPLETED'),
    started_at timestamptz NOT NULL,
    completed_at timestamptz NOT NULL,
    CONSTRAINT analytic_run_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT analytic_run_job_fk FOREIGN KEY (job_id) REFERENCES recompute_job(id),
    CONSTRAINT analytic_run_window CHECK (window_start < window_end),
    CONSTRAINT analytic_run_basis_unique UNIQUE (site_id, analytic_id, model_version, window_start, window_end,
                                                 input_sha256),
    CONSTRAINT analytic_run_site_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX analytic_run_site_window ON analytic_run (site_id, analytic_id, window_start DESC);

CREATE TABLE analytic_run_evidence (
    run_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    PRIMARY KEY (run_id, evidence_id),
    CONSTRAINT analytic_run_evidence_run_fk FOREIGN KEY (tenant_id, site_id, run_id)
        REFERENCES analytic_run(tenant_id, site_id, id),
    CONSTRAINT analytic_run_evidence_evidence_fk FOREIGN KEY (tenant_id, site_id, evidence_id)
        REFERENCES accepted_evidence(tenant_id, site_id, id)
);
CREATE INDEX analytic_run_evidence_evidence ON analytic_run_evidence (evidence_id);

CREATE TABLE assessment_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    analytic_id text NOT NULL,
    model_version text NOT NULL,
    assessment_key text NOT NULL,
    revision_no integer NOT NULL CHECK (revision_no >= 1),
    analytic_run_id uuid NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    claim_level text NOT NULL,
    result jsonb NOT NULL,
    evidence_ids jsonb NOT NULL,
    basis_sha256 text NOT NULL,
    created_at timestamptz NOT NULL,
    CONSTRAINT assessment_revision_run_fk FOREIGN KEY (tenant_id, site_id, analytic_run_id)
        REFERENCES analytic_run(tenant_id, site_id, id),
    CONSTRAINT assessment_revision_key_unique UNIQUE (site_id, analytic_id, assessment_key, revision_no),
    CONSTRAINT assessment_revision_site_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX assessment_revision_site_window ON assessment_revision (site_id, analytic_id, window_start DESC);

CREATE TABLE analytic_run_assessment (
    run_id uuid NOT NULL,
    assessment_revision_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    scope text NOT NULL CHECK (scope IN ('WINDOW', 'INTERVAL')),
    PRIMARY KEY (run_id, assessment_revision_id),
    CONSTRAINT analytic_run_assessment_run_fk FOREIGN KEY (tenant_id, site_id, run_id)
        REFERENCES analytic_run(tenant_id, site_id, id),
    CONSTRAINT analytic_run_assessment_revision_fk FOREIGN KEY (tenant_id, site_id, assessment_revision_id)
        REFERENCES assessment_revision(tenant_id, site_id, id)
);

CREATE TRIGGER analytic_run_append_only BEFORE UPDATE OR DELETE ON analytic_run
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER analytic_run_evidence_append_only BEFORE UPDATE OR DELETE ON analytic_run_evidence
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER assessment_revision_append_only BEFORE UPDATE OR DELETE ON assessment_revision
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER analytic_run_assessment_append_only BEFORE UPDATE OR DELETE ON analytic_run_assessment
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""


def upgrade() -> None:
    op.execute(ASSESSMENT)


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS analytic_run_assessment, assessment_revision, analytic_run_evidence,
            analytic_run CASCADE;
        ALTER TABLE recompute_job DROP COLUMN IF EXISTS last_error;
        """
    )
