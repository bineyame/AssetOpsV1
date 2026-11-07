"""DIESEL-K3 (`.agent/build-sheet-DIESEL-1.md` §9d.4, ruling DIESEL-1-R3d): the `fuel-balance-1` night windows.

One append-only row per assessed night per tank and revision. A new revision is written only when the inputs, as
known, change (`input_sha256`). Rows are never updated or deleted (`ledger_append_only`). The table is not a
chain-event producer (0044 `PRODUCERS` unchanged); K4 links its Finding to a window by `id`.

Downgrade refuses while any row exists, then drops the trigger, the index and the table.

Revision ID: 0055_fuel_balance_window
Revises: 0054_operational_fuel_records
Create Date: 2026-11-07
"""

from alembic import op
from sqlalchemy import text

revision = "0055_fuel_balance_window"
down_revision = "0054_operational_fuel_records"
branch_labels = None
depends_on = None

REFUSED = "0055 downgrade requires no fuel_balance_window rows"

UPGRADE = """
CREATE TABLE fuel_balance_window (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    tank_asset_id uuid NOT NULL,
    generator_asset_id uuid NOT NULL,
    night_date date NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    revision integer NOT NULL CHECK (revision >= 1),
    parameter_version text NOT NULL CHECK (parameter_version = 'fuel-balance-1/v1'),
    recorded_at timestamptz NOT NULL,
    state text NOT NULL CHECK (state IN ('UNEXPLAINED','BELOW_MATERIALITY','WITHIN_MARGIN','EXCESS','NOT_ASSESSED')),
    reason text NULL CHECK (reason IN ('NO_SENSOR_ACCURACY','SFC_MISSING','NO_LOAD_RATE_MISSING','MISSING_OPENING',
        'MISSING_CLOSING','FUEL_LEVEL_CONFLICT','GENERATOR_KWH_UNKNOWN','IDLE_SECONDS_UNKNOWN')),
    residual_low text NULL,
    residual_high text NULL,
    gap_minutes integer NOT NULL CHECK (gap_minutes >= 0),
    gap_spans jsonb NOT NULL,
    limitations jsonb NOT NULL,
    terms jsonb NOT NULL,
    evidence_ids jsonb NOT NULL,
    record_ids jsonb NOT NULL,
    input_sha256 text NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT fuel_balance_window_revision_unique UNIQUE (tenant_id, site_id, tank_asset_id, night_date, revision),
    CONSTRAINT fuel_balance_window_tank_fk FOREIGN KEY (tenant_id, site_id, tank_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_generator_fk FOREIGN KEY (tenant_id, site_id, generator_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_closed CHECK (window_end > window_start
        AND recorded_at >= window_end + interval '30 minutes'),
    CONSTRAINT fuel_balance_window_reason CHECK ((state = 'NOT_ASSESSED') = (reason IS NOT NULL)),
    CONSTRAINT fuel_balance_window_band CHECK ((state = 'NOT_ASSESSED') = (residual_low IS NULL)
        AND (residual_low IS NULL) = (residual_high IS NULL))
);
CREATE INDEX fuel_balance_window_night
    ON fuel_balance_window (tenant_id, site_id, tank_asset_id, night_date, recorded_at);
CREATE TRIGGER fuel_balance_window_immutable BEFORE UPDATE OR DELETE ON fuel_balance_window
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

DOWNGRADE = """
DROP TRIGGER fuel_balance_window_immutable ON fuel_balance_window;
DROP INDEX fuel_balance_window_night;
DROP TABLE fuel_balance_window;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("LOCK TABLE fuel_balance_window IN ACCESS EXCLUSIVE MODE"))
    if bind.execute(text("SELECT EXISTS (SELECT 1 FROM fuel_balance_window)")).scalar():
        raise RuntimeError(REFUSED)
    op.execute(DOWNGRADE)
