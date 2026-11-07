"""DIESEL-K2 (`.agent/build-sheet-DIESEL-1.md` §9c.2, ruling DIESEL-1-R3c): fuel delivery and tank dip records.

`operational_record` (0027) admits two more kinds, `FUEL_DELIVERY` and `TANK_DIP`, and one nullable column, `asset_id`,
the fuel tank a fuel record concerns:

- the kind CHECK keeps its 0027 name and adds the two kinds;
- `asset_id` is a scoped foreign key onto `asset_scope_unique` (0001); its default MATCH SIMPLE leaves a NULL
  `asset_id` unchecked, so the four existing kinds are untouched;
- a fuel kind names a tank and no other kind does (`operational_record_fuel_asset`);
- a fuel record is an instant with a quantity in litres (`operational_record_fuel_quantity`);
- a delivery is above 0 L and names its ticket digest (`operational_record_delivery_ticket`);
- one partial index serves the as-known fuel read per tank and occurrence.

Adding a nullable column fires none of the 0027 append-only triggers; no row is rewritten.

Downgrade refuses while any fuel record exists (rows are append-only, so they cannot be removed), then drops the index,
the three CHECKs, the FK and the column, and restores the four-kind CHECK under the same name.

Revision ID: 0054_operational_fuel_records
Revises: 0053_fuel_cost_2
Create Date: 2026-11-07
"""

from alembic import op
from sqlalchemy import text

revision = "0054_operational_fuel_records"
down_revision = "0053_fuel_cost_2"
branch_labels = None
depends_on = None

KINDS_0027 = ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")
FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")
KINDS_0054 = KINDS_0027 + FUEL_KINDS
REFUSED = "0054 downgrade requires no FUEL_DELIVERY or TANK_DIP operational records"


def _in(values: tuple[str, ...]) -> str:
    return ",".join(f"'{v}'" for v in values)


UPGRADE = f"""
ALTER TABLE operational_record DROP CONSTRAINT operational_record_kind_check;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_kind_check
    CHECK (kind IN ({_in(KINDS_0054)}));
ALTER TABLE operational_record ADD COLUMN asset_id uuid NULL;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_asset_fk
    FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES asset(tenant_id, site_id, id);
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_asset
    CHECK ((kind IN ({_in(FUEL_KINDS)})) = (asset_id IS NOT NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_quantity
    CHECK (kind NOT IN ({_in(FUEL_KINDS)}) OR (quantity IS NOT NULL AND unit = 'L' AND period_end IS NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_delivery_ticket
    CHECK (kind <> 'FUEL_DELIVERY' OR (quantity > 0 AND source_document_sha256 IS NOT NULL));
CREATE INDEX operational_record_asset ON operational_record (tenant_id, site_id, asset_id, occurred_at)
    WHERE asset_id IS NOT NULL;
"""

DOWNGRADE = f"""
DROP INDEX operational_record_asset;
ALTER TABLE operational_record DROP CONSTRAINT operational_record_delivery_ticket;
ALTER TABLE operational_record DROP CONSTRAINT operational_record_fuel_quantity;
ALTER TABLE operational_record DROP CONSTRAINT operational_record_fuel_asset;
ALTER TABLE operational_record DROP CONSTRAINT operational_record_asset_fk;
ALTER TABLE operational_record DROP COLUMN asset_id;
ALTER TABLE operational_record DROP CONSTRAINT operational_record_kind_check;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_kind_check
    CHECK (kind IN ({_in(KINDS_0027)}));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("LOCK TABLE operational_record IN ACCESS EXCLUSIVE MODE"))
    if bind.execute(text(f"SELECT EXISTS (SELECT 1 FROM operational_record WHERE kind IN ({_in(FUEL_KINDS)}))")
                    ).scalar():
        raise RuntimeError(REFUSED)
    op.execute(DOWNGRADE)
