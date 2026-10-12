"""S3-01 phase 3: the append-only selection log of default dispatch runs.

A worker pass that assesses a window either creates a run or reuses the
existing run of an identical input set (`analytic_run` is idempotent). Reuse
leaves no row in `analytic_run`, so "latest run by completed_at" is not the
run the system last selected: after an input reverts to an earlier basis the
older run is current again (`D-2026-10-11-s3-phase-2-selection-and-read`, Q7).
`analytic_run_selection` records every DEFAULT selection, created or reused,
in commit order (`seq`), written in the same transaction as the job
completion. The phase-3 read and `reconcile` take the head per window from it.

Revision ID: 0008_assessment_selection
Revises: 0007_dispatch_assessment
Create Date: 2026-10-11
"""

from __future__ import annotations

from alembic import op

revision = "0008_assessment_selection"
down_revision = "0007_dispatch_assessment"
branch_labels = None
depends_on = None


SELECTION = """
CREATE TABLE analytic_run_selection (
    seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    analytic_id text NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    run_id uuid NOT NULL,
    job_id uuid NULL REFERENCES recompute_job(id),
    selected_at timestamptz NOT NULL,
    CONSTRAINT analytic_run_selection_run_fk FOREIGN KEY (tenant_id, site_id, run_id)
        REFERENCES analytic_run(tenant_id, site_id, id)
);
CREATE INDEX analytic_run_selection_window ON analytic_run_selection
    (site_id, analytic_id, window_start, window_end, seq DESC);

CREATE TRIGGER analytic_run_selection_append_only BEFORE UPDATE OR DELETE ON analytic_run_selection
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""


def upgrade() -> None:
    op.execute(SELECTION)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytic_run_selection CASCADE;")
