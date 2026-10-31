"""OUT-D U1: the append-only `outcome_objective_revision` table (declared outcome objectives).

`.agent/build-sheet-OUT-D.md` §3 U1. Chains to exactly `0035_w5_ev_work`; it uses neither 0036 nor 0037, so the
CC-M migrations merge later through an empty merge revision (OUT-E). One row is one declared revision of the objective
of one site-level outcome. `unit`, `measure_kind`, `comparison` and `window_rule` are fixed per measure by the pure
`outcomes.objectives.MEASURES`; the CHECKs below bound them. A leading measure never carries money; only
`currency/km` carries a currency. Rows are immutable: the 0027 `w4_append_only()` function refuses UPDATE and DELETE.
The sole writer is `objectives/adapters/postgres_objective_store.py` (configuration-persistence rule 8).

- A revision chain per (site, outcome): `revision_no` > 0 and unique; `supersedes_revision_id` is required iff
  `revision_no > 1` and must name a revision of the same site and outcome.
- The idempotency key is unique per Site.

Downgrade drops the table (and its trigger).
"""

from alembic import op

revision = "0038_out_objectives"
down_revision = "0035_w5_ev_work"
branch_labels = None
depends_on = None

TABLE = "outcome_objective_revision"
MEASURE_KEYS = ("avoidable_generator_minutes", "productive_use_kwh", "unserved_critical_kwh",
                "backup_start_failures", "interrupted_sessions", "energy_cost_per_km")
MEASURE_KINDS = ("VALUE", "LEADING")
COMPARISONS = ("AT_MOST", "AT_LEAST")
UNITS = ("min/day", "kWh/month", "kWh", "failures", "sessions", "currency/km")
WINDOW_RULES = ("BOARD_DAY", "BOARD_WINDOW")
SOURCES = ("DECLARED", "RECORDED")
CHANNELS = ("SYSTEM_CLI", "SYSTEM_FIXTURE")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


SCHEMA = f"""
CREATE TABLE {TABLE} (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    outcome_key text NOT NULL CHECK (outcome_key ~ '^(MG|CC|EV)-[1-9]$'),
    revision_no integer NOT NULL CHECK (revision_no > 0),
    supersedes_revision_id uuid NULL,
    measure_key text NOT NULL CHECK (measure_key IN ({_in(MEASURE_KEYS)})),
    measure_kind text NOT NULL CHECK (measure_kind IN ({_in(MEASURE_KINDS)})),
    comparison text NOT NULL CHECK (comparison IN ({_in(COMPARISONS)})),
    target numeric NOT NULL CHECK (target >= 0),
    unit text NOT NULL CHECK (unit IN ({_in(UNITS)})),
    currency text NULL CHECK (currency ~ '^[A-Z]{{3}}$'),
    window_rule text NOT NULL CHECK (window_rule IN ({_in(WINDOW_RULES)})),
    source text NOT NULL CHECK (source IN ({_in(SOURCES)})),
    source_note text NOT NULL CHECK (length(source_note) BETWEEN 1 AND 500),
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    authorization_basis text NOT NULL CHECK (length(authorization_basis) BETWEEN 1 AND 500),
    source_channel text NOT NULL CHECK (source_channel IN ({_in(CHANNELS)})),
    idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{{64}}$'),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT {TABLE}_chain_check CHECK ((revision_no = 1) = (supersedes_revision_id IS NULL)),
    CONSTRAINT {TABLE}_money_check CHECK ((unit = 'currency/km') = (currency IS NOT NULL)),
    CONSTRAINT {TABLE}_leading_no_money CHECK (measure_kind = 'VALUE' OR currency IS NULL),
    CONSTRAINT {TABLE}_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT {TABLE}_no_unique UNIQUE (tenant_id, site_id, outcome_key, revision_no),
    CONSTRAINT {TABLE}_id_unique UNIQUE (tenant_id, site_id, outcome_key, id),
    CONSTRAINT {TABLE}_supersedes_fk FOREIGN KEY (tenant_id, site_id, outcome_key,
        supersedes_revision_id) REFERENCES {TABLE}(tenant_id, site_id, outcome_key, id),
    CONSTRAINT {TABLE}_idempotency_unique UNIQUE (tenant_id, site_id, idempotency_key)
);
CREATE INDEX {TABLE}_read ON {TABLE} (tenant_id, site_id, outcome_key, recorded_at);
CREATE TRIGGER {TABLE}_immutable BEFORE UPDATE OR DELETE ON {TABLE}
    FOR EACH ROW EXECUTE FUNCTION w4_append_only();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(f"DROP TABLE {TABLE}")
