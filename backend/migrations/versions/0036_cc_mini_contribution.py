"""CC-M (owner Q14): the mini scenario kind CHECK admits `PRODUCTIVE_USE_CONTRIBUTION` (D1, roadmap R4).

`.agent/build-spec-commercial-2026-10-27.md` "CC-M". Chains to exactly `0035_w5_ev_work`. No new table, column or
index: the named 0030 `mini_scenario_revision_kind_check` is dropped and recreated with the new kind added.

Downgrade locks `mini_scenario_revision` in ACCESS EXCLUSIVE mode, refuses while any revision uses the new kind,
then restores the exact 0030 four-kind CHECK.
"""

from alembic import op

revision = "0036_cc_mini_contribution"
down_revision = "0035_w5_ev_work"
branch_labels = None
depends_on = None

TABLE = "mini_scenario_revision"
KIND_CHECK = "mini_scenario_revision_kind_check"
NEW_KIND = "PRODUCTIVE_USE_CONTRIBUTION"
REFUSED = "Downgrade of 0036_cc_mini_contribution refused: PRODUCTIVE_USE_CONTRIBUTION scenario revisions exist."

WIDEN = f"""
ALTER TABLE {TABLE} DROP CONSTRAINT {KIND_CHECK};
ALTER TABLE {TABLE} ADD CONSTRAINT {KIND_CHECK}
  CHECK (kind IN ('STOP_SOC','PRODUCTIVE_LOAD','TARIFF_ONLY','OTHER','{NEW_KIND}'));
"""

REFUSE_IF_USED = (
    f"LOCK TABLE {TABLE} IN ACCESS EXCLUSIVE MODE;\n"
    f"DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM {TABLE} WHERE kind = '{NEW_KIND}') THEN\n"
    f"        RAISE EXCEPTION '{REFUSED}';\n    END IF;\nEND;\n$$;\n"
)

RESTORE = f"""
ALTER TABLE {TABLE} DROP CONSTRAINT {KIND_CHECK};
ALTER TABLE {TABLE} ADD CONSTRAINT {KIND_CHECK} CHECK (kind IN ('STOP_SOC','PRODUCTIVE_LOAD','TARIFF_ONLY','OTHER'));
"""


def upgrade() -> None:
    op.execute(WIDEN)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(RESTORE)
