"""CC-M (owner Q14): the append-only `trial_cost_comparison_revision` table (D2, roadmap R3).

`.agent/build-spec-commercial-2026-10-27.md` "CC-M" table and Q-C42. Chains to exactly `0036_cc_mini_contribution`.
One row is one post-trial commercial reassessment revision of a verification outcome (formula
`trial-fuel-comparison/1`). It uses 0019's `SHA`, `KEY` and `DEMO_ACTOR` column pattern (copied here; 0019 is not
edited). Rows are immutable: the 0027 `w4_append_only()` function refuses UPDATE and DELETE. The writer
(`financials/adapters/postgres_trial_comparison_store.py`) and its persistence-guard rule land with CC-D2.

- The outcome must belong to the Action: FK `(action_id, verification_outcome_id)` -> `verification_outcome
  (action_id, id)`.
- A revision chain per outcome: `revision_no` > 0 and unique per outcome; `supersedes_revision_id` is required iff
  `revision_no > 1` and must name a revision of the same outcome.
- `state` is one of the three reassessment states; `reason` is set iff `state = 'UNAVAILABLE'`, and is one of the
  eleven reasons.

Downgrade drops the table (and its trigger).
"""

from alembic import op

revision = "0037_cc_trial_cost_comparison"
down_revision = "0036_cc_mini_contribution"
branch_labels = None
depends_on = None

TABLE = "trial_cost_comparison_revision"
FORMULA = "trial-fuel-comparison/1"
STATES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE")
#: The CC-D2 `REASSESSMENT_REASONS` tuple, in precedence order.
REASONS = ("OUTCOME_INCONCLUSIVE", "WINDOW_INCOMPLETE", "NOT_COMPARABLE", "SOURCE_NOT_COHERENT",
           "EVIDENCE_REPLAY_MISMATCH", "GENERATOR_KWH_UNKNOWN", "ZERO_DEMAND", "SFC_MISSING", "SFC_DIFFERS",
           "PRICE_MISSING", "PRICE_BASIS_DIFFERS")

SHA = "CHECK ({} ~ '^[0-9a-f]{{64}}$')"
KEY = "CHECK (length({}) BETWEEN 8 AND 128)"
# 0019's S6-01 SYSTEM demonstration actor columns.
DEMO_ACTOR = """
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    source_channel text NOT NULL CHECK (source_channel = 'SYSTEM_DEMONSTRATION_API'),
    authorization_basis text NOT NULL CHECK (length(authorization_basis) BETWEEN 1 AND 500),
    triggering_service text NOT NULL CHECK (length(triggering_service) BETWEEN 1 AND 128),
    triggering_fixture text NOT NULL CHECK (length(triggering_fixture) BETWEEN 1 AND 128),"""


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


SCHEMA = f"""
CREATE TABLE {TABLE} (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    action_id uuid NOT NULL,
    verification_outcome_id uuid NOT NULL,
    revision_no integer NOT NULL,
    supersedes_revision_id uuid NULL,
    formula text NOT NULL,
    state text NOT NULL,
    reason text NULL,
    result jsonb NOT NULL,
    intervention_cost jsonb NOT NULL,
    price_revision_id uuid NULL,
    basis_sha256 text NOT NULL {SHA.format('basis_sha256')},
    {DEMO_ACTOR}
    idempotency_key text NOT NULL {KEY.format('idempotency_key')},
    payload_sha256 text NOT NULL {SHA.format('payload_sha256')},
    recorded_at timestamptz NOT NULL,
    CONSTRAINT {TABLE}_revision_no_check CHECK (revision_no > 0),
    CONSTRAINT {TABLE}_chain_check CHECK ((revision_no = 1) = (supersedes_revision_id IS NULL)),
    CONSTRAINT {TABLE}_formula_check CHECK (formula = '{FORMULA}'),
    CONSTRAINT {TABLE}_state_check CHECK (state IN ({_in(STATES)})),
    CONSTRAINT {TABLE}_reason_check CHECK (reason IS NULL OR reason IN ({_in(REASONS)})),
    CONSTRAINT {TABLE}_reason_state_check CHECK ((state = 'UNAVAILABLE') = (reason IS NOT NULL)),
    CONSTRAINT {TABLE}_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT {TABLE}_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
        REFERENCES action(tenant_id, site_id, id),
    CONSTRAINT {TABLE}_outcome_fk FOREIGN KEY (action_id, verification_outcome_id)
        REFERENCES verification_outcome(action_id, id),
    CONSTRAINT {TABLE}_revision_no_unique UNIQUE (verification_outcome_id, revision_no),
    CONSTRAINT {TABLE}_outcome_id_unique UNIQUE (verification_outcome_id, id),
    CONSTRAINT {TABLE}_supersedes_fk FOREIGN KEY (verification_outcome_id, supersedes_revision_id)
        REFERENCES {TABLE}(verification_outcome_id, id),
    CONSTRAINT {TABLE}_basis_unique UNIQUE (verification_outcome_id, basis_sha256),
    CONSTRAINT {TABLE}_idempotency_unique UNIQUE (action_id, idempotency_key)
);
CREATE INDEX {TABLE}_order ON {TABLE} (tenant_id, site_id, action_id, recorded_at);
CREATE TRIGGER {TABLE}_immutable BEFORE UPDATE OR DELETE ON {TABLE}
    FOR EACH ROW EXECUTE FUNCTION w4_append_only();
"""


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(f"DROP TABLE {TABLE}")
