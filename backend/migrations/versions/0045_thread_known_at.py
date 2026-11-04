"""CH-3 (ruling CH3-R, D-b): bitemporal thread visibility.

- `finding_thread_event.cause_known_at`: the recorded time of the fact that caused the event (`action_event`,
  `verification_outcome`, the work event, `domain_action`, or the Finding / opportunity revision's `created_at`).
- `finding_thread_occurrence.source_known_at`: the placed Finding or opportunity revision's `created_at`.

Both are nullable and written at insert only (the tables stay append-only on `ledger_append_only()`; adding a
nullable column with no default rewrites no row and fires no row trigger). An event or occurrence is visible at
cutoff k when `coalesce(<known column>, <row time>) <= k`, so a backfilled row carries its cause's own time rather
than the backfill's.

Migration order (CH3-R): `down_revision` is 0042; CH-1b, merging second, re-points its 0044 onto this one.
Downgrade refuses while any row carries a value in either column, so no recorded time is silently dropped.
"""

from alembic import op

revision = "0045_thread_known_at"
down_revision = "0042_chain_threads"
branch_labels = None
depends_on = None

UPGRADE = """
ALTER TABLE finding_thread_event ADD COLUMN cause_known_at timestamptz NULL;
ALTER TABLE finding_thread_occurrence ADD COLUMN source_known_at timestamptz NULL;
"""

REFUSE_IF_USED = """
LOCK TABLE finding_thread_event, finding_thread_occurrence IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM finding_thread_event WHERE cause_known_at IS NOT NULL)
       OR EXISTS (SELECT 1 FROM finding_thread_occurrence WHERE source_known_at IS NOT NULL) THEN
        RAISE EXCEPTION 'Downgrade of 0045_thread_known_at refused: recorded cause times exist';
    END IF;
END;
$$;
"""

DROP = """
ALTER TABLE finding_thread_occurrence DROP COLUMN source_known_at;
ALTER TABLE finding_thread_event DROP COLUMN cause_known_at;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED + DROP)
