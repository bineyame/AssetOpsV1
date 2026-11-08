"""DIESEL-K4a (`.agent/build-sheet-DIESEL-1.md` §9j.3, ruling DIESEL-1-R3j): the unexplained-fuel Finding domain
and its own money table.

- `finding_domain_subject` and `finding_revision_domain_minutes` are recreated exactly as 0025 left them plus one
  `fuel_balance` arm each (a tank subject, NULL generator, NULL dispatch minutes). 0025's `_domain_checks` shape.
- `fuel_residual_consequence_revision`: one append-only `fuel-residual-1` row per SUPPORTED fuel Finding revision
  (litres band at the declared diesel price, own basis). It is written only by the consequence store, it is never a
  `financial_consequence_revision` row, it is not a chain-event producer (0044 `PRODUCERS` unchanged) and has no
  outbox. The fuel-cost and cold triggers, `fuel_balance_window` and 0044 are untouched.

Downgrade refuses while any `fuel_balance` Finding/revision or consequence row exists; otherwise it drops the
trigger, index and table and restores the two 0025 CHECKs.

Revision ID: 0056_unexplained_fuel_finding
Revises: 0055_fuel_balance_window
Create Date: 2026-11-08
"""

from alembic import op
from sqlalchemy import text

revision = "0056_unexplained_fuel_finding"
down_revision = "0055_fuel_balance_window"
branch_labels = None
depends_on = None

REFUSED = "0056 downgrade requires no fuel_balance Findings or fuel residual consequences"

# The 0025 definitions, restored exactly by the downgrade.
DOMAIN_SUBJECT_0025 = """(
        (domain = 'mini_grid' AND generator_asset_id IS NOT NULL AND subject_asset_id IS NULL)
        OR (domain = 'cold_chain' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)
        OR (domain = 'ev_charging' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL))"""
DOMAIN_MINUTES_0025 = """(
        (domain = 'mini_grid' AND candidate_minutes IS NOT NULL AND necessary_minutes IS NOT NULL
            AND indeterminate_minutes IS NOT NULL AND candidate_minutes >= 0 AND necessary_minutes >= 0
            AND indeterminate_minutes >= 0)
        OR (domain = 'cold_chain' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL)
        OR (domain = 'ev_charging' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL))"""

DOMAIN_SUBJECT_0056 = """(
        (domain = 'mini_grid' AND generator_asset_id IS NOT NULL AND subject_asset_id IS NULL)
        OR (domain = 'cold_chain' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)
        OR (domain = 'ev_charging' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)
        OR (domain = 'fuel_balance' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL))"""
DOMAIN_MINUTES_0056 = """(
        (domain = 'mini_grid' AND candidate_minutes IS NOT NULL AND necessary_minutes IS NOT NULL
            AND indeterminate_minutes IS NOT NULL AND candidate_minutes >= 0 AND necessary_minutes >= 0
            AND indeterminate_minutes >= 0)
        OR (domain = 'cold_chain' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL)
        OR (domain = 'ev_charging' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL)
        OR (domain = 'fuel_balance' AND candidate_minutes IS NULL AND necessary_minutes IS NULL
            AND indeterminate_minutes IS NULL))"""


def _domain_checks(subject: str, minutes: str) -> str:
    return f"""
ALTER TABLE finding
    DROP CONSTRAINT finding_domain_subject,
    ADD CONSTRAINT finding_domain_subject CHECK {subject};
ALTER TABLE finding_revision
    DROP CONSTRAINT finding_revision_domain_minutes,
    ADD CONSTRAINT finding_revision_domain_minutes CHECK {minutes};
"""


CONSEQUENCE_TABLE = r"""
CREATE TABLE fuel_residual_consequence_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    fuel_balance_window_id uuid NOT NULL,
    model_id text NOT NULL CHECK (model_id = 'fuel-residual-1'),
    basis text NOT NULL CHECK (basis = 'UNEXPLAINED_FUEL_AT_DECLARED_PRICE'),
    litres_low text NOT NULL CHECK (litres_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    litres_high text NOT NULL CHECK (litres_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    state text NOT NULL CHECK (state IN ('PRICED','UNPRICED')),
    price_reason text NULL,
    price_revision_id uuid NULL,
    price_assignment_id uuid NULL,
    price_value numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    amount_low text NULL CHECK (amount_low IS NULL OR amount_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    amount_high text NULL CHECK (amount_high IS NULL OR amount_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    price_known_at timestamptz NOT NULL,
    basis_sha256 text NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT fuel_residual_priced CHECK ((state = 'PRICED') = (price_revision_id IS NOT NULL)
        AND (state = 'PRICED') = (price_value IS NOT NULL AND price_value >= 0 AND price_value < 'Infinity'::numeric)
        AND (state = 'PRICED') = (currency IS NOT NULL AND amount_low IS NOT NULL AND amount_high IS NOT NULL)
        AND (state = 'PRICED') = (price_reason IS NULL)),
    CONSTRAINT fuel_residual_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_price_fk FOREIGN KEY (tenant_id, site_id, price_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_window_fk FOREIGN KEY (fuel_balance_window_id) REFERENCES fuel_balance_window(id),
    CONSTRAINT fuel_residual_once UNIQUE (finding_revision_id),
    CONSTRAINT fuel_residual_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX fuel_residual_finding ON fuel_residual_consequence_revision (tenant_id, site_id, finding_id, recorded_at);
CREATE TRIGGER fuel_residual_consequence_revision_immutable BEFORE UPDATE OR DELETE
    ON fuel_residual_consequence_revision FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

DOWNGRADE = """
DROP TRIGGER fuel_residual_consequence_revision_immutable ON fuel_residual_consequence_revision;
DROP INDEX fuel_residual_finding;
DROP TABLE fuel_residual_consequence_revision;
"""


def upgrade() -> None:
    op.execute(_domain_checks(DOMAIN_SUBJECT_0056, DOMAIN_MINUTES_0056))
    op.execute(CONSEQUENCE_TABLE)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("LOCK TABLE finding, finding_revision, fuel_residual_consequence_revision "
                      "IN ACCESS EXCLUSIVE MODE"))
    held = bind.execute(text(
        "SELECT EXISTS (SELECT 1 FROM finding WHERE domain = 'fuel_balance') "
        "OR EXISTS (SELECT 1 FROM finding_revision WHERE domain = 'fuel_balance') "
        "OR EXISTS (SELECT 1 FROM fuel_residual_consequence_revision)")).scalar()
    if held:
        raise RuntimeError(REFUSED)
    op.execute(DOWNGRADE)
    op.execute(_domain_checks(DOMAIN_SUBJECT_0025, DOMAIN_MINUTES_0025))
