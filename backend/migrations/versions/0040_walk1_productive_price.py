"""WALK1-3: declared price per kWh for productive users.

- `financial_assumption_revision` widens only its key/unit CHECKs for `productive_use_price_per_kwh`
  (`currency/kWh`) and adds a strictly positive value CHECK for it, exactly as 0026 widened them for the EV tariff.
  `financial_assumption_assignment` has no key CHECK (it is keyed through its revision FK), so it needs no change.
- No money table, work queue or trigger: estimated productive-use sales are computed at read time from accepted
  metered readings and this declared price, and never stored.

Downgrade refuses while any revision or assignment with the productive-use key exists, then restores the 0026 CHECKs.

Revision ID: 0040_walk1_productive_price
Revises: 0039_merge_objectives_cc
Create Date: 2026-11-02
"""
from alembic import op

revision = "0040_walk1_productive_price"
down_revision = "0039_merge_objectives_cc"
branch_labels = None
depends_on = None

UPGRADE = r"""
DO $$ BEGIN
 IF (SELECT count(*) FROM pg_constraint WHERE conrelid='financial_assumption_revision'::regclass
     AND conname IN ('financial_assumption_revision_assumption_key_check','financial_assumption_revision_unit_check',
                     'financial_assumption_revision_ev_positive'))<>3 THEN
   RAISE EXCEPTION '0040_walk1_productive_price: the 0026 assumption key/unit/positive CHECK names are not installed';
 END IF;
END $$;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_assumption_key_check;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_unit_check;
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_assumption_key_check
  CHECK (assumption_key IN ('diesel_price_per_litre','ev_gross_tariff_per_kwh','productive_use_price_per_kwh'));
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_unit_check
  CHECK ((assumption_key='diesel_price_per_litre' AND unit='currency/L') OR
         (assumption_key='ev_gross_tariff_per_kwh' AND unit='currency/kWh') OR
         (assumption_key='productive_use_price_per_kwh' AND unit='currency/kWh'));
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_productive_positive
  CHECK (assumption_key <> 'productive_use_price_per_kwh' OR value > 0);
"""

DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM financial_assumption_revision WHERE assumption_key='productive_use_price_per_kwh')
     OR EXISTS (SELECT 1 FROM financial_assumption_assignment WHERE assumption_key='productive_use_price_per_kwh') THEN
    RAISE EXCEPTION 'Downgrade of 0040_walk1_productive_price refused: a productive-use price exists';
  END IF;
END $$;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_productive_positive;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_assumption_key_check;
ALTER TABLE financial_assumption_revision DROP CONSTRAINT financial_assumption_revision_unit_check;
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_assumption_key_check
  CHECK (assumption_key IN ('diesel_price_per_litre','ev_gross_tariff_per_kwh'));
ALTER TABLE financial_assumption_revision ADD CONSTRAINT financial_assumption_revision_unit_check
  CHECK ((assumption_key='diesel_price_per_litre' AND unit='currency/L') OR
         (assumption_key='ev_gross_tariff_per_kwh' AND unit='currency/kWh'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
