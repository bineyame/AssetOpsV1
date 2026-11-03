"""CH-2 (build sheet CH-2 §2): Finding threads, their occurrences and events, and the Action-to-thread link.

- `finding_thread`: one row per `(tenant, site, mechanism, subject_kind, subject_ref)` key (design §4.3, AG-10).
- `finding_thread_occurrence`: each Finding or mini opportunity placed on a thread, numbered from 1; a Finding or
  opportunity is placed at most once.
- `finding_thread_event`: the thread's lifecycle events; CH-2 writes only the occurrence-driven OPEN and RECURRED.
- `chain_action_thread` (ruling R1): `action` and `domain_action` are append-only, so the thread link is its own
  append-only table instead of an added column. A BEFORE INSERT trigger (`chain_action_thread_target`) refuses a
  link whose MINI_TRIAL `action` or DOMAIN_INTENT `domain_action` target is missing in the same tenant and Site.
- `chain_action`: a view over both Action tables LEFT JOINed to the link (`thread_id` null = not linked yet).

Every table is append-only on `ledger_append_only()` (`<table>_immutable`). The schedule stage CHECK is unchanged:
the tick's `chain_threads` child runs under the Site's existing `S4` head stage (pre-flight P4).

Downgrade refuses while any of the four tables has a row; otherwise it drops the view, the triggers, the
indexes and the tables in reverse order.
"""

from alembic import op

revision = "0042_chain_threads"
down_revision = "0041_walk1_objective_min_days"
branch_labels = None
depends_on = None

TABLES = ("finding_thread", "finding_thread_occurrence", "finding_thread_event", "chain_action_thread")

UPGRADE = """
CREATE TABLE finding_thread (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  mechanism text NOT NULL CHECK (mechanism ~ '^[A-Z][A-Z0-9_]{1,62}$'),
  subject_kind text NOT NULL CHECK (subject_kind IN ('SITE','ASSET','CONNECTION','CUSTOMER')),
  subject_ref text NOT NULL,
  finding_type text NOT NULL,
  opened_at timestamptz NOT NULL,
  created_by text NOT NULL CHECK (created_by IN ('backfill','tick')),
  CONSTRAINT finding_thread_key UNIQUE (tenant_id, site_id, mechanism, subject_kind, subject_ref),
  CONSTRAINT finding_thread_scope UNIQUE (tenant_id, site_id, id),
  CONSTRAINT finding_thread_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id)
);

CREATE TABLE finding_thread_occurrence (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  occurrence_no int NOT NULL CHECK (occurrence_no >= 1),
  finding_id uuid NULL, opportunity_id uuid NULL,
  episode_start timestamptz NULL, episode_end timestamptz NULL,
  joined_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  evidence_class text NOT NULL CHECK (evidence_class IN ('MEASURED','RECORDED','DECLARED','MODELLED','EXTERNAL')),
  time_basis text NOT NULL DEFAULT 'story_time' CHECK (time_basis IN ('story_time','recorded_at')),
  CONSTRAINT finding_thread_occurrence_pkey PRIMARY KEY (thread_id, occurrence_no),
  CONSTRAINT occurrence_one_source CHECK ((finding_id IS NULL) <> (opportunity_id IS NULL)),
  CONSTRAINT occurrence_finding_once UNIQUE (finding_id),
  CONSTRAINT occurrence_opportunity_once UNIQUE (opportunity_id),
  CONSTRAINT occurrence_thread_fk FOREIGN KEY (tenant_id, site_id, thread_id)
    REFERENCES finding_thread (tenant_id, site_id, id),
  CONSTRAINT occurrence_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
    REFERENCES finding (tenant_id, site_id, id),
  CONSTRAINT occurrence_opportunity_fk FOREIGN KEY (tenant_id, site_id, opportunity_id)
    REFERENCES mini_opportunity (tenant_id, site_id, id)
);

CREATE TABLE finding_thread_event (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  thread_id uuid NOT NULL, seq int NOT NULL CHECK (seq >= 1),
  state text NOT NULL CHECK (state IN ('OPEN','ACTION_IN_HAND','CHANGE_APPLIED','RESOLVED_MONITORING',
                                       'CLOSED','RECURRED','REOPENED','WITHDRAWN')),
  cause_kind text NOT NULL CHECK (cause_kind IN ('OCCURRENCE','ACTION_EVENT','VERIFICATION_OUTCOME',
                                                 'DOMAIN_CASE','CLEAN_DAYS','WITHDRAWAL','SUPPORT_LOST')),
  cause_id text NOT NULL,
  effective_day date NOT NULL,
  policy_version text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT finding_thread_event_pkey PRIMARY KEY (thread_id, seq),
  CONSTRAINT thread_event_cause_once UNIQUE (thread_id, cause_kind, cause_id),
  CONSTRAINT thread_event_thread_fk FOREIGN KEY (tenant_id, site_id, thread_id)
    REFERENCES finding_thread (tenant_id, site_id, id)
);

CREATE TABLE chain_action_thread (
  tenant_id uuid NOT NULL, site_id uuid NOT NULL,
  action_kind text NOT NULL CHECK (action_kind IN ('MINI_TRIAL','DOMAIN_INTENT')),
  action_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  origin_finding_id uuid NOT NULL,
  linked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  linked_by text NOT NULL CHECK (linked_by IN ('backfill','tick')),
  CONSTRAINT chain_action_thread_pkey PRIMARY KEY (action_kind, action_id),
  CONSTRAINT chain_action_thread_thread_fk FOREIGN KEY (tenant_id, site_id, thread_id)
    REFERENCES finding_thread (tenant_id, site_id, id)
);

CREATE FUNCTION chain_action_thread_target() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.action_kind = 'MINI_TRIAL' AND NOT EXISTS (
       SELECT 1 FROM action a WHERE a.tenant_id = NEW.tenant_id AND a.site_id = NEW.site_id AND a.id = NEW.action_id
         AND a.origin_finding_id = NEW.origin_finding_id) THEN
    RAISE EXCEPTION 'chain_action_thread: MINI_TRIAL action % is not in this tenant and Site', NEW.action_id;
  END IF;
  IF NEW.action_kind = 'DOMAIN_INTENT' AND NOT EXISTS (
       SELECT 1 FROM domain_action d WHERE d.tenant_id = NEW.tenant_id AND d.site_id = NEW.site_id
         AND d.id = NEW.action_id AND d.origin_finding_id = NEW.origin_finding_id) THEN
    RAISE EXCEPTION 'chain_action_thread: DOMAIN_INTENT action % is not in this tenant and Site', NEW.action_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER chain_action_thread_target BEFORE INSERT ON chain_action_thread
  FOR EACH ROW EXECUTE FUNCTION chain_action_thread_target();

CREATE VIEW chain_action AS
  SELECT a.id, a.tenant_id, a.site_id, a.action_code, 'MINI_TRIAL'::text AS kind,
         l.thread_id, a.origin_finding_id, a.origin_finding_revision_id
    FROM action a LEFT JOIN chain_action_thread l ON l.action_kind = 'MINI_TRIAL' AND l.action_id = a.id
  UNION ALL
  SELECT d.id, d.tenant_id, d.site_id, d.action_code, 'DOMAIN_INTENT'::text,
         l.thread_id, d.origin_finding_id, d.origin_finding_revision_id
    FROM domain_action d LEFT JOIN chain_action_thread l ON l.action_kind = 'DOMAIN_INTENT' AND l.action_id = d.id;

CREATE INDEX finding_thread_site ON finding_thread (tenant_id, site_id);
CREATE INDEX finding_thread_event_head ON finding_thread_event (thread_id, seq DESC);
CREATE INDEX chain_action_thread_by_thread ON chain_action_thread (thread_id);
""" + "".join(
    f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t}\n"
    "    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();\n" for t in TABLES
)

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF "
    + "\n       OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in TABLES)
    + " THEN\n        RAISE EXCEPTION 'Downgrade of 0042_chain_threads refused: thread history exists';\n"
    "    END IF;\nEND;\n$$;\n"
)

DROP = (
    "DROP VIEW chain_action;\n"
    + "".join(f"DROP TRIGGER {t}_immutable ON {t};\n" for t in reversed(TABLES))
    + "DROP TRIGGER chain_action_thread_target ON chain_action_thread;\n"
    "DROP FUNCTION chain_action_thread_target();\n"
    "DROP INDEX chain_action_thread_by_thread;\n"
    "DROP INDEX finding_thread_event_head;\n"
    "DROP INDEX finding_thread_site;\n"
    + "".join(f"DROP TABLE {t};\n" for t in reversed(TABLES))
)


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED + DROP)
