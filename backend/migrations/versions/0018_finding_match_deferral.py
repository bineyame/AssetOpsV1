"""S4 fix: a match pass records the windows it deferred.

`finding_episode.plan` skips a group when a window within the 20-minute continuity margin is missing or not
CURRENT (or an episode's closure is not decidable). The pass was still recorded at the Site-wide selection seq,
so `match_state` read the deferring window as matched and reads claimed complete discovery (S4-04 phase 1 H1,
`.agent/S5-01-deferred-cluster-check.md`). The pass now carries the starts of the windows it deferred, and
`match_state` reads such a window as not matched until a later pass matches it.

`finding_match_pass` stays insert-only (0009 trigger); the column is written only by the existing Finding store
writer (`analytics/adapters/postgres_finding_store.py`). Existing passes get an empty set (no backfill: they
are read as before; the next pass under a changed fence supersedes them).

Revision ID: 0018_finding_match_deferral
Revises: 0017_evidence_publication
Create Date: 2026-10-16
"""

from __future__ import annotations

from alembic import op

revision = "0018_finding_match_deferral"
down_revision = "0017_evidence_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE finding_match_pass ADD COLUMN deferred_window_starts timestamptz[] NOT NULL "
               "DEFAULT '{}';")


REFUSE_IF_USED = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM finding_match_pass WHERE cardinality(deferred_window_starts) > 0) THEN
        RAISE EXCEPTION 'Downgrade of 0018_finding_match_deferral refused: match passes record deferred windows. 0017 would read those windows as matched.';
    END IF;
END;
$$;
"""


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute("ALTER TABLE finding_match_pass DROP COLUMN IF EXISTS deferred_window_starts;")
