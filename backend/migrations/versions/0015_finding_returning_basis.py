"""LR-01 phase 2: a FindingRevision basis may return to an earlier one.

`0009_finding_store` made `(finding_id, basis_sha256, transition)` unique, so a Finding whose selected basis
went A -> B -> A (a clock attestation recorded, then revoked: the S3 selection returns to the earlier run) could
not append the third revision, and the Finding's latest revision stayed on B while the selection was A again.
Revisions stay immutable and append-only (`finding_revision_no_unique` is kept); the matcher's replay guard now
compares only with the Finding's latest revision (`postgres_finding_store._insert_revision`), under the existing
Site advisory lock and matcher fence. A non-unique index keeps the basis lookup.

Downgrade refuses while any Finding holds two revisions with the same basis and transition (the old constraint
could not be restored without deleting history).

Revision ID: 0015_finding_returning_basis
Revises: 0014_source_clock_attestation
Create Date: 2026-10-15
"""

from __future__ import annotations

from alembic import op

revision = "0015_finding_returning_basis"
down_revision = "0014_source_clock_attestation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE finding_revision DROP CONSTRAINT finding_revision_basis_unique")
    op.execute("CREATE INDEX finding_revision_basis_idx ON finding_revision (finding_id, basis_sha256, transition)")


def downgrade() -> None:
    op.execute("""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM finding_revision GROUP BY finding_id, basis_sha256, transition HAVING count(*) > 1)
    THEN
        RAISE EXCEPTION 'refused: a Finding holds a returning basis (two revisions with one basis and transition)';
    END IF;
END $$;
""")
    op.execute("DROP INDEX IF EXISTS finding_revision_basis_idx")
    op.execute("ALTER TABLE finding_revision ADD CONSTRAINT finding_revision_basis_unique "
               "UNIQUE (finding_id, basis_sha256, transition)")
