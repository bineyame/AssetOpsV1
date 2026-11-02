"""WALK1-3b: the checked-day minimum of a declared monthly objective (build sheet WALK1 Addendum 2 §A2.5).

- `outcome_objective_revision` gains a nullable `min_checked_days integer`: how many days of the month must have
  measured coverage before the month-to-date pace is judged. NULL means the code default
  (`outcomes.objectives.DEFAULT_MIN_CHECKED_DAYS`, 3); there is no backfill.
- CHECK `outcome_objective_revision_min_checked_days_range`: NULL or 1 to 28 (28 is the shortest month, so the minimum
  can always be reached).
- CHECK `outcome_objective_revision_min_checked_days_monthly`: NULL unless the measure is `productive_use_kwh`, the only
  per-month measure. Widen this list when another monthly measure exists.
- A changed minimum is a new objective revision (the table stays append-only; the 0038 trigger is unchanged).

Downgrade refuses while any row carries a minimum, then drops the column (and its two CHECKs).

Revision ID: 0041_walk1_objective_min_days
Revises: 0040_walk1_productive_price
Create Date: 2026-11-02
"""
from alembic import op

revision = "0041_walk1_objective_min_days"
down_revision = "0040_walk1_productive_price"
branch_labels = None
depends_on = None

UPGRADE = r"""
ALTER TABLE outcome_objective_revision ADD COLUMN min_checked_days integer NULL;
ALTER TABLE outcome_objective_revision ADD CONSTRAINT outcome_objective_revision_min_checked_days_range
  CHECK (min_checked_days IS NULL OR (min_checked_days BETWEEN 1 AND 28));
ALTER TABLE outcome_objective_revision ADD CONSTRAINT outcome_objective_revision_min_checked_days_monthly
  CHECK (min_checked_days IS NULL OR measure_key = 'productive_use_kwh');
"""

DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM outcome_objective_revision WHERE min_checked_days IS NOT NULL) THEN
    RAISE EXCEPTION 'Downgrade of 0041_walk1_objective_min_days refused: an objective declares a minimum of checked days';
  END IF;
END $$;
ALTER TABLE outcome_objective_revision DROP CONSTRAINT outcome_objective_revision_min_checked_days_monthly;
ALTER TABLE outcome_objective_revision DROP CONSTRAINT outcome_objective_revision_min_checked_days_range;
ALTER TABLE outcome_objective_revision DROP COLUMN min_checked_days;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
