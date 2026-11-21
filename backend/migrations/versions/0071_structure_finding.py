"""3B4 (`specs/3B4-observer/` spec §4.1; D-3B4.7, D-3B4.11, D-3B4.24): the structure Finding domain and the
per-Site tolerance declarations.

- `finding_domain_subject` and `finding_revision_domain_minutes` are recreated exactly as 0056 left them plus one
  `structure` arm each (no subject or generator asset, NULL dispatch minutes). 0056's `_domain_checks` shape. No
  bounds CHECK: `episode_start`/`episode_end` are already NOT NULL and ordered (D-3B4.24).
- `structure_tolerance`: append-only declarations of a Site's tolerance on an observed leaf, written only by the
  Finding store with a plain INSERT (joins `$findingTables`).

Self-contained: it reads nothing of 0067 to 0070 (unmerged branches); gate B renumbers it on main's head at merge.
Downgrade refuses while any `structure` Finding/revision or tolerance row exists; otherwise it drops the trigger,
index and table and restores the two 0056 CHECKs.

Revision ID: 0071_structure_finding
Revises: 0066_structure_snapshot
Create Date: 2026-11-21
"""
from alembic import op
from sqlalchemy import text

revision = "0071_structure_finding"
down_revision = "0066_structure_snapshot"
branch_labels = None
depends_on = None

REFUSED = "0071 downgrade requires no structure Findings or tolerance declarations"

# The 0056 definitions, copied as literals and restored exactly by the downgrade.
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

STRUCTURE_SUBJECT_ARM = "OR (domain = 'structure' AND subject_asset_id IS NULL AND generator_asset_id IS NULL)"
STRUCTURE_MINUTES_ARM = ("OR (domain = 'structure' AND candidate_minutes IS NULL AND necessary_minutes IS NULL"
                         " AND indeterminate_minutes IS NULL)")

DOMAIN_SUBJECT_0071 = DOMAIN_SUBJECT_0056[:-1] + "\n        " + STRUCTURE_SUBJECT_ARM + ")"
DOMAIN_MINUTES_0071 = DOMAIN_MINUTES_0056[:-1] + "\n        " + STRUCTURE_MINUTES_ARM + ")"


def _domain_checks(subject: str, minutes: str) -> str:
    return f"""
ALTER TABLE finding
    DROP CONSTRAINT finding_domain_subject,
    ADD CONSTRAINT finding_domain_subject CHECK {subject};
ALTER TABLE finding_revision
    DROP CONSTRAINT finding_revision_domain_minutes,
    ADD CONSTRAINT finding_revision_domain_minutes CHECK {minutes};
"""


TOLERANCE_TABLE = r"""
CREATE TABLE structure_tolerance (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    structure_key text NOT NULL CHECK (structure_key ~ '^[A-Z][A-Z_]{1,39}$'),
    factor_id text NOT NULL CHECK (factor_id ~ '^[a-z][a-z0-9_]{0,63}$'),
    state text NOT NULL CHECK (state IN ('SET', 'CLEARED')),
    of_factor text NULL CHECK (of_factor IS NULL OR of_factor ~ '^[a-z][a-z0-9_]{0,63}$'),
    pct text NULL CHECK (pct IS NULL OR pct ~ '^[0-9]{1,3}(\.[0-9]{1,2})?$'),
    valid_from text NOT NULL CHECK (valid_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    recorded_at timestamptz NOT NULL,
    recorded_by uuid NOT NULL,
    recorded_role text NOT NULL CHECK (recorded_role IN ('FINANCE_AND_COMMERCIAL_LEAD', 'SITE_MANAGER')),
    recorded_by_script boolean NOT NULL,
    CONSTRAINT structure_tolerance_set CHECK ((state = 'SET') = (of_factor IS NOT NULL AND pct IS NOT NULL)),
    CONSTRAINT structure_tolerance_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id)
);
CREATE INDEX structure_tolerance_site ON structure_tolerance (tenant_id, site_id, factor_id, recorded_at);
CREATE TRIGGER structure_tolerance_immutable BEFORE UPDATE OR DELETE ON structure_tolerance
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
"""

DOWNGRADE = """
DROP TRIGGER structure_tolerance_immutable ON structure_tolerance;
DROP INDEX structure_tolerance_site;
DROP TABLE structure_tolerance;
"""


def upgrade() -> None:
    op.execute(_domain_checks(DOMAIN_SUBJECT_0071, DOMAIN_MINUTES_0071))
    op.execute(TOLERANCE_TABLE)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("LOCK TABLE finding, finding_revision, structure_tolerance IN ACCESS EXCLUSIVE MODE"))
    held = bind.execute(text(
        "SELECT EXISTS (SELECT 1 FROM finding WHERE domain = 'structure') "
        "OR EXISTS (SELECT 1 FROM finding_revision WHERE domain = 'structure') "
        "OR EXISTS (SELECT 1 FROM structure_tolerance)")).scalar()
    if held:
        raise RuntimeError(REFUSED)
    op.execute(DOWNGRADE)
    op.execute(_domain_checks(DOMAIN_SUBJECT_0056, DOMAIN_MINUTES_0056))
