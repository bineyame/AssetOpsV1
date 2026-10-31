"""OUT-E E1: empty merge revision.

Joins the productive-use and trial cost check schema with the declared objectives table.
"""

revision = "0039_merge_objectives_cc"
down_revision = ("0037_cc_trial_cost_comparison", "0038_out_objectives")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
