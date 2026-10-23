"""W5-03b unit E5: authored EV scenario store (`ev_scenario` root plus append-only `ev_scenario_revision`).

`.agent/W5-03-build-spec.md`: "E5 exact persisted schema and wire contract", "E5 consolidated correction" and the
K2 lane-2 ruling. Chains to exactly `0033_w5_cold_work`. Mirrors W5-01b C4 (`0032_w5_cold_scenarios`): one global
`ev_scenario_public_no_seq`, the Site-scoped root, the append-only revision table (no observed-outcome column), the
`ev_scenario_site_order` revision index and two `<table>_immutable` append-only triggers on the existing
`ledger_append_only()`. Exact keys, decimal grammar, ISO currency and selected-ID membership are service rules; SQL
only requires both JSON columns to be objects.

Downgrade takes ACCESS EXCLUSIVE locks on both tables (child first), refuses any stored scenario history, then drops
triggers, the index, the revision table, the root and the sequence last. No cascade, no deletion, no relabelling.
"""

from alembic import op

revision = "0034_w5_ev_scenarios"
down_revision = "0033_w5_cold_work"
branch_labels = None
depends_on = None

#: Child-to-parent lock, refusal and drop order.
TABLES = ("ev_scenario_revision", "ev_scenario")
INDEXES = ("ev_scenario_site_order",)

SCHEMA = """
CREATE SEQUENCE ev_scenario_public_no_seq;
CREATE TABLE ev_scenario (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL DEFAULT nextval('ev_scenario_public_no_seq'),
 create_key text NOT NULL, create_payload_sha256 text NOT NULL, create_actor_id text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 actor_kind text NOT NULL, actor_id text NOT NULL,
 CONSTRAINT ev_scenario_pkey PRIMARY KEY (id),
 CONSTRAINT ev_scenario_create_key_check CHECK (length(create_key) BETWEEN 8 AND 128),
 CONSTRAINT ev_scenario_create_payload_sha256_check CHECK (create_payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT ev_scenario_create_actor_id_check CHECK (length(btrim(create_actor_id)) BETWEEN 1 AND 128),
 CONSTRAINT ev_scenario_site_fk FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 CONSTRAINT ev_scenario_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT ev_scenario_public_no_uk UNIQUE (tenant_id,public_no),
 CONSTRAINT ev_scenario_create_key_uk UNIQUE (tenant_id,site_id,create_key)
);
CREATE TABLE ev_scenario_revision (
 id uuid NOT NULL, tenant_id uuid NOT NULL, site_id uuid NOT NULL, scenario_id uuid NOT NULL,
 revision_no integer NOT NULL, supersedes_revision_id uuid NULL,
 name text NOT NULL, kind text NOT NULL,
 assumptions jsonb NOT NULL, authored_basis jsonb NOT NULL, basis_sha256 text NOT NULL,
 formula_version text NOT NULL, correction_reason text NULL,
 actor_kind text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL, attestation text NOT NULL,
 idempotency_key text NOT NULL, payload_sha256 text NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CONSTRAINT ev_scenario_revision_pkey PRIMARY KEY (id),
 CONSTRAINT ev_scenario_revision_revision_no_check CHECK (revision_no>0),
 CONSTRAINT ev_scenario_revision_name_check CHECK (length(btrim(name)) BETWEEN 1 AND 160),
 CONSTRAINT ev_scenario_revision_kind_check CHECK (kind IN ('GROSS_TARIFF_CONTEXT')),
 CONSTRAINT ev_scenario_revision_formula_check CHECK (formula_version = 'AUTHORED_ONLY/1'),
 CONSTRAINT ev_scenario_revision_chain_check
   CHECK ((revision_no=1 AND supersedes_revision_id IS NULL AND correction_reason IS NULL)
       OR (revision_no>1 AND supersedes_revision_id IS NOT NULL
           AND length(btrim(correction_reason)) BETWEEN 1 AND 2000)),
 CONSTRAINT ev_scenario_revision_basis_sha256_check CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT ev_scenario_revision_payload_sha256_check CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
 CONSTRAINT ev_scenario_revision_idempotency_key_check CHECK (length(idempotency_key) BETWEEN 8 AND 128),
 CONSTRAINT ev_scenario_revision_actor_check
   CHECK (length(btrim(actor_kind))>0 AND length(btrim(actor_id))>0
      AND length(btrim(authorization_basis))>0 AND length(btrim(attestation))>0),
 CONSTRAINT ev_scenario_revision_assumptions_check CHECK (jsonb_typeof(assumptions) = 'object'),
 CONSTRAINT ev_scenario_revision_authored_basis_check CHECK (jsonb_typeof(authored_basis) = 'object'),
 CONSTRAINT ev_scenario_revision_scenario_fk FOREIGN KEY (tenant_id,site_id,scenario_id)
   REFERENCES ev_scenario(tenant_id,site_id,id),
 CONSTRAINT ev_scenario_revision_previous_fk FOREIGN KEY (tenant_id,site_id,supersedes_revision_id)
   REFERENCES ev_scenario_revision(tenant_id,site_id,id),
 CONSTRAINT ev_scenario_revision_scope_uk UNIQUE (tenant_id,site_id,id),
 CONSTRAINT ev_scenario_revision_no_uk UNIQUE (scenario_id,revision_no),
 CONSTRAINT ev_scenario_revision_previous_uk UNIQUE (scenario_id,supersedes_revision_id),
 CONSTRAINT ev_scenario_revision_key_uk UNIQUE (scenario_id,idempotency_key)
);
CREATE INDEX ev_scenario_site_order
  ON ev_scenario_revision(tenant_id,site_id,recorded_at DESC,id);
""" + "".join(
    f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t}\n"
    "    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n" for t in reversed(TABLES)
)

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF "
    + "\n       OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in TABLES)
    + " THEN\n        RAISE EXCEPTION 'Downgrade of 0034_w5_ev_scenarios refused: EV scenario history exists';\n"
    "    END IF;\nEND;\n$$;\n"
)

DROP = (
    "".join(f"DROP TRIGGER {t}_immutable ON {t};\n" for t in TABLES)
    + "".join(f"DROP INDEX {i};\n" for i in INDEXES)
    + "".join(f"DROP TABLE {t};\n" for t in TABLES)
    + "DROP SEQUENCE ev_scenario_public_no_seq;\n"
)


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DROP)
