"""W5-02a K1a: the cold domain Action root, its declared intent and its explicit W4 case link.

`.agent/W5-02-build-spec.md` "K1 migration", "Backend wire, validation and lineage (K1a-K1c)" and the Architect
pre-flight ruling A1/A4. Chains to `0032_w5_cold_scenarios`. Creates three append-only tables:

- `domain_action`: the immutable public root under the shared Action code namespace (`action_code_seq`, `ACT-`).
- `domain_action_intent`: declared success criteria (exactly four, `domain_action_intent_criteria_count_chk`) and
  an attested basis; a linear same-Action supersession chain (one root, one successor per version).
- `domain_action_case_link`: an explicit attested link to one W4 case at an exact revision and event. A BEFORE
  INSERT trigger refuses a revision or event that is not of the named case (direct SQL included).

Every table is append-only on W4's `w4_append_only()` (`<table>_no_mutation`). `reject_cross_domain_action_code()`
backs the BEFORE INSERT triggers `w1_action_cross_domain_code` (W1 `action`) and `domain_action_cross_domain_code`:
under a transaction-scoped advisory lock on `(tenant, code)` it refuses a code present in the other table with
SQLSTATE 23505 and constraint `action_cross_domain_code_conflict`.

Downgrade takes ACCESS EXCLUSIVE locks (child first), refuses any stored domain Action row, then drops the
triggers (the W1 collision trigger included), tables and functions. No cascade, no deletion.
"""

from alembic import op

revision = "0033_w5_cold_work"
down_revision = "0032_w5_cold_scenarios"
branch_labels = None
depends_on = None

#: Child-to-parent lock, refusal and drop order.
TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action")

_ACTOR = """
 actor_kind text NOT NULL CHECK (actor_kind = 'SERVICE'),
 actor_id text NOT NULL CHECK (length(btrim(actor_id)) BETWEEN 1 AND 128),
 attestation text NOT NULL CHECK (length(btrim(attestation)) BETWEEN 1 AND 1000),
 idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
 payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),"""

SCHEMA = f"""
CREATE TABLE domain_action (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 action_no bigint NOT NULL CHECK (action_no >= 1),
 action_code text NOT NULL CHECK (action_code ~ '^ACT-[0-9]{{6,}}$'),
 domain text NOT NULL CHECK (domain = 'COLDCHAIN'),
 origin_finding_id uuid NOT NULL, origin_finding_revision_id uuid NOT NULL,
 title text NOT NULL CHECK (title = btrim(title) AND length(title) BETWEEN 1 AND 160),
 owner_label text NULL CHECK (owner_label IS NULL OR (owner_label = btrim(owner_label)
                                                     AND length(owner_label) BETWEEN 1 AND 160)),
 due_at timestamptz NULL, raised_at timestamptz NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),{_ACTOR}
 CONSTRAINT domain_action_due CHECK (due_at IS NULL OR (due_at >= raised_at AND due_at <= raised_at + interval '365 days')),
 CONSTRAINT domain_action_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
 CONSTRAINT domain_action_finding_fk FOREIGN KEY (tenant_id, site_id, origin_finding_id)
   REFERENCES finding(tenant_id, site_id, id),
 CONSTRAINT domain_action_finding_revision_fk FOREIGN KEY (tenant_id, site_id, origin_finding_id, origin_finding_revision_id)
   REFERENCES finding_revision(tenant_id, site_id, finding_id, id),
 CONSTRAINT domain_action_scope UNIQUE (tenant_id, site_id, id),
 CONSTRAINT domain_action_code UNIQUE (tenant_id, action_code),
 CONSTRAINT domain_action_no UNIQUE (action_no),
 CONSTRAINT domain_action_once UNIQUE (site_id, idempotency_key)
);
CREATE INDEX domain_action_site_raised ON domain_action (tenant_id, site_id, raised_at DESC, id);
CREATE TABLE domain_action_intent (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, action_id uuid NOT NULL,
 supersedes_id uuid NULL,
 declared_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 criteria jsonb NOT NULL, basis jsonb NOT NULL,{_ACTOR}
 CONSTRAINT domain_action_intent_criteria_count_chk
   CHECK (jsonb_typeof(criteria) = 'array' AND jsonb_array_length(criteria) = 4),
 CONSTRAINT domain_action_intent_basis_chk CHECK (jsonb_typeof(basis) = 'object'),
 CONSTRAINT domain_action_intent_not_self CHECK (supersedes_id IS NULL OR supersedes_id <> id),
 CONSTRAINT domain_action_intent_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
   REFERENCES domain_action(tenant_id, site_id, id),
 CONSTRAINT domain_action_intent_action_id UNIQUE (action_id, id),
 CONSTRAINT domain_action_intent_prev_fk FOREIGN KEY (action_id, supersedes_id)
   REFERENCES domain_action_intent(action_id, id),
 CONSTRAINT domain_action_intent_scope UNIQUE (tenant_id, site_id, id),
 CONSTRAINT domain_action_intent_once UNIQUE (action_id, idempotency_key),
 CONSTRAINT domain_action_intent_one_successor UNIQUE (supersedes_id)
);
CREATE UNIQUE INDEX domain_action_intent_root ON domain_action_intent (action_id) WHERE supersedes_id IS NULL;
CREATE INDEX domain_action_intent_order ON domain_action_intent (action_id, recorded_at, id);
CREATE TABLE domain_action_case_link (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, action_id uuid NOT NULL,
 case_id uuid NOT NULL, case_revision_id uuid NOT NULL, case_event_id uuid NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),{_ACTOR}
 CONSTRAINT domain_action_case_link_action_fk FOREIGN KEY (tenant_id, site_id, action_id)
   REFERENCES domain_action(tenant_id, site_id, id),
 CONSTRAINT domain_action_case_link_case_fk FOREIGN KEY (tenant_id, site_id, case_id)
   REFERENCES work_case(tenant_id, site_id, id),
 CONSTRAINT domain_action_case_link_revision_fk FOREIGN KEY (tenant_id, site_id, case_revision_id)
   REFERENCES work_case_revision(tenant_id, site_id, id),
 CONSTRAINT domain_action_case_link_revision_case_fk FOREIGN KEY (case_id, case_revision_id)
   REFERENCES work_case_revision(case_id, id),
 CONSTRAINT domain_action_case_link_event_fk FOREIGN KEY (tenant_id, site_id, case_event_id)
   REFERENCES work_event(tenant_id, site_id, id),
 CONSTRAINT domain_action_case_link_scope UNIQUE (tenant_id, site_id, id),
 CONSTRAINT domain_action_case_link_once UNIQUE (action_id, idempotency_key),
 CONSTRAINT domain_action_case_link_exact UNIQUE (action_id, case_id, case_revision_id, case_event_id)
);
CREATE INDEX domain_action_case_link_case ON domain_action_case_link (tenant_id, site_id, case_id, recorded_at, id);
CREATE FUNCTION domain_action_case_link_consistency() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM work_case_revision r WHERE r.tenant_id = NEW.tenant_id AND r.site_id = NEW.site_id
                 AND r.id = NEW.case_revision_id AND r.case_id = NEW.case_id)
     OR NOT EXISTS (SELECT 1 FROM work_event e WHERE e.tenant_id = NEW.tenant_id AND e.site_id = NEW.site_id
                    AND e.id = NEW.case_event_id AND e.case_id = NEW.case_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'domain_action_case_link_case_consistency',
      MESSAGE = 'A domain Action case link names a revision or event of another case.';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER domain_action_case_link_consistency BEFORE INSERT ON domain_action_case_link
  FOR EACH ROW EXECUTE FUNCTION domain_action_case_link_consistency();
CREATE FUNCTION reject_cross_domain_action_code() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(NEW.tenant_id::text || ':' || NEW.action_code, 0));
  IF TG_TABLE_NAME = 'action' THEN
    IF EXISTS (SELECT 1 FROM domain_action d WHERE d.tenant_id = NEW.tenant_id AND d.action_code = NEW.action_code) THEN
      RAISE EXCEPTION USING ERRCODE = '23505', CONSTRAINT = 'action_cross_domain_code_conflict',
        MESSAGE = 'Action code already belongs to another Action.';
    END IF;
  ELSIF EXISTS (SELECT 1 FROM action a WHERE a.tenant_id = NEW.tenant_id AND a.action_code = NEW.action_code) THEN
    RAISE EXCEPTION USING ERRCODE = '23505', CONSTRAINT = 'action_cross_domain_code_conflict',
      MESSAGE = 'Action code already belongs to another Action.';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER w1_action_cross_domain_code BEFORE INSERT ON action
  FOR EACH ROW EXECUTE FUNCTION reject_cross_domain_action_code();
CREATE TRIGGER domain_action_cross_domain_code BEFORE INSERT ON domain_action
  FOR EACH ROW EXECUTE FUNCTION reject_cross_domain_action_code();
""" + "".join(
    f"CREATE TRIGGER {t}_no_mutation BEFORE UPDATE OR DELETE ON {t}\n"
    "  FOR EACH ROW EXECUTE FUNCTION w4_append_only();\n" for t in reversed(TABLES)
)

REFUSED = "Downgrade of 0033_w5_cold_work refused: domain Action rows exist."

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF "
    + "\n       OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in TABLES)
    + f" THEN\n        RAISE EXCEPTION '{REFUSED}';\n"
    "    END IF;\nEND;\n$$;\n"
)

DROP = (
    "DROP TRIGGER w1_action_cross_domain_code ON action;\n"
    "DROP TRIGGER domain_action_cross_domain_code ON domain_action;\n"
    "DROP TRIGGER domain_action_case_link_consistency ON domain_action_case_link;\n"
    + "".join(f"DROP TRIGGER {t}_no_mutation ON {t};\n" for t in TABLES)
    + "".join(f"DROP TABLE {t};\n" for t in TABLES)
    + "DROP FUNCTION reject_cross_domain_action_code();\n"
    "DROP FUNCTION domain_action_case_link_consistency();\n"
)


def upgrade() -> None:
    op.execute(SCHEMA)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED)
    op.execute(DROP)
