"""FUEL-1 A1 + A2 (`.agent/build-sheet-FUEL-1.md` §4.1, §4.2, §1.3): fuel-cost-2 and trial-fuel-comparison/2.

One migration carries both units' CHECK changes, so A2 adds none (no Alembic-head race).

- `financial_consequence_revision` (0011): `model_id` admits `fuel-cost-2`; three nullable columns record what
  fuel-cost-2 counted: `no_load_fuel_rate_l_per_h` (positive, finite), `no_load_fuel_rate_basis` (one of the three
  declared bases) and `idle_seconds` (>= 0). A `fuel-cost-1` row carries all three NULL. No row is rewritten.
- `trial_cost_comparison_revision` (0037): `formula` admits `trial-fuel-comparison/2`; the reason CHECK admits
  `IDLE_SECONDS_UNKNOWN` and `NO_LOAD_RATE_DIFFERS` (A2).

Downgrade refuses while any fuel-cost-2 consequence or trial-fuel-comparison/2 row exists, then drops the columns and
restores both tables' 0011 / 0037 CHECKs.

Revision ID: 0053_fuel_cost_2
Revises: 0052_verification_plan_domain
Create Date: 2026-11-07
"""

from alembic import op

revision = "0053_fuel_cost_2"
down_revision = "0052_verification_plan_domain"
branch_labels = None
depends_on = None

FC = "financial_consequence_revision"
TRIAL = "trial_cost_comparison_revision"
BASES = ("GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST")
#: 0037's reasons in its order, then A2's two (A2 places them after SFC_DIFFERS in its precedence tuple; a set
#: CHECK does not depend on order).
REASONS_0037 = ("OUTCOME_INCONCLUSIVE", "WINDOW_INCOMPLETE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT",
                "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "ZERO_DEMAND", "SFC_MISSING", "SFC_DIFFERS",
                "PRICE_MISSING", "PRICE_BASIS_DIFFERS")
REASONS_0053 = REASONS_0037 + ("IDLE_SECONDS_UNKNOWN", "NO_LOAD_RATE_DIFFERS")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


UPGRADE = f"""
ALTER TABLE {FC} DROP CONSTRAINT {FC}_model_id_check;
ALTER TABLE {FC} ADD CONSTRAINT {FC}_model_id_check CHECK (model_id IN ('fuel-cost-1', 'fuel-cost-2'));
ALTER TABLE {FC}
    ADD COLUMN no_load_fuel_rate_l_per_h numeric NULL
        CONSTRAINT {FC}_no_load_rate_check
        CHECK (no_load_fuel_rate_l_per_h > 0 AND no_load_fuel_rate_l_per_h < 'Infinity'::numeric),
    ADD COLUMN no_load_fuel_rate_basis text NULL
        CONSTRAINT {FC}_no_load_basis_check CHECK (no_load_fuel_rate_basis IN ({_in(BASES)})),
    ADD COLUMN idle_seconds integer NULL CONSTRAINT {FC}_idle_seconds_check CHECK (idle_seconds >= 0);
ALTER TABLE {FC} ADD CONSTRAINT {FC}_fuel_cost_1_no_idle CHECK (
    model_id <> 'fuel-cost-1'
    OR (no_load_fuel_rate_l_per_h IS NULL AND no_load_fuel_rate_basis IS NULL AND idle_seconds IS NULL));

ALTER TABLE {TRIAL} DROP CONSTRAINT {TRIAL}_formula_check;
ALTER TABLE {TRIAL} ADD CONSTRAINT {TRIAL}_formula_check
    CHECK (formula IN ('trial-fuel-comparison/1', 'trial-fuel-comparison/2'));
ALTER TABLE {TRIAL} DROP CONSTRAINT {TRIAL}_reason_check;
ALTER TABLE {TRIAL} ADD CONSTRAINT {TRIAL}_reason_check CHECK (reason IS NULL OR reason IN ({_in(REASONS_0053)}));
"""

DOWNGRADE = f"""
LOCK TABLE {FC}, {TRIAL} IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM {FC} WHERE model_id = 'fuel-cost-2') THEN
        RAISE EXCEPTION '0053 downgrade refused: fuel-cost-2 consequence revisions exist';
    END IF;
    IF EXISTS (SELECT 1 FROM {TRIAL} WHERE formula = 'trial-fuel-comparison/2'
               OR reason IN ('IDLE_SECONDS_UNKNOWN', 'NO_LOAD_RATE_DIFFERS')) THEN
        RAISE EXCEPTION '0053 downgrade refused: trial-fuel-comparison/2 rows exist';
    END IF;
END $$;
ALTER TABLE {TRIAL} DROP CONSTRAINT {TRIAL}_reason_check;
ALTER TABLE {TRIAL} ADD CONSTRAINT {TRIAL}_reason_check CHECK (reason IS NULL OR reason IN ({_in(REASONS_0037)}));
ALTER TABLE {TRIAL} DROP CONSTRAINT {TRIAL}_formula_check;
ALTER TABLE {TRIAL} ADD CONSTRAINT {TRIAL}_formula_check CHECK (formula = 'trial-fuel-comparison/1');

ALTER TABLE {FC} DROP CONSTRAINT {FC}_fuel_cost_1_no_idle;
ALTER TABLE {FC} DROP COLUMN idle_seconds, DROP COLUMN no_load_fuel_rate_basis,
    DROP COLUMN no_load_fuel_rate_l_per_h;
ALTER TABLE {FC} DROP CONSTRAINT {FC}_model_id_check;
ALTER TABLE {FC} ADD CONSTRAINT {FC}_model_id_check CHECK (model_id IN ('fuel-cost-1'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
