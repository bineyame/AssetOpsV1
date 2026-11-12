"""PR-3 (D-PRICE.1): prices typed on the Site price page are saved on their own channel.

- `financial_assumption_revision` widens only its channel CHECK (0010's inline column CHECK) to add
  `SITE_ADMIN_ENTRY`: a price entered on screen through the server-configured entry service `service:operator-entry`,
  labelled "Entered by site admin". The actor CHECK (0010) is unchanged and still holds: a SYSTEM actor, no
  `author_id`, and a channel other than `HUMAN_API`.
- No new table, key or trigger: the revision insert already raises `price.revised` (0044) and queues consequence work
  (0011/0026).

Downgrade refuses while any revision has channel `SITE_ADMIN_ENTRY`, then restores the 0010 CHECK.

Revision ID: 0060_site_admin_price_entry
Revises: 0059_site_period_read
Create Date: 2026-11-12
"""
from alembic import op

revision = "0060_site_admin_price_entry"
down_revision = "0059_site_period_read"
branch_labels = None
depends_on = None

UPGRADE = r"""
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='financial_assumption_revision'::regclass
                AND conname='financial_assumption_revision_channel_check') THEN
   RAISE EXCEPTION '0060_site_admin_price_entry: the 0010 channel CHECK name is not installed';
 END IF;
END $$;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_channel_check;
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_channel_check
  CHECK (channel IN ('SYSTEM_CLI','SYSTEM_FIXTURE','HUMAN_API','SITE_ADMIN_ENTRY'));
"""

DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM financial_assumption_revision WHERE channel='SITE_ADMIN_ENTRY') THEN
    RAISE EXCEPTION 'Downgrade of 0060_site_admin_price_entry refused: a price entered by site admin exists';
  END IF;
END $$;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_channel_check;
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_channel_check
  CHECK (channel IN ('SYSTEM_CLI','SYSTEM_FIXTURE','HUMAN_API'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
