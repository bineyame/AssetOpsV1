"""CH-9b1 (build sheet CH-9b, ruling CH9b1-R Q1 = B): a domain Action raised from a mini opportunity.

- `domain_action` admits `MINI` (the 0035 precedent): `domain_action_domain_chk` becomes
  `IN ('COLDCHAIN','EV_CHARGING','MINI')`.
- `domain_action` gains `origin_opportunity_id` / `origin_opportunity_revision_id`. The Finding pair loses NOT NULL
  only (no row is rewritten). `domain_action_one_origin` holds exactly one complete pair, and
  `domain_action_mini_origin` ties `MINI` to the opportunity pair (a Cold or EV Action keeps its Finding origin).
  The pair FKs name `mini_opportunity` and the exact study revision of that opportunity.
- `mini_opportunity_revision` gains `UNIQUE (tenant_id, site_id, opportunity_id, id)` for that pair FK (Q4).
- `chain_action_thread` gains `origin_opportunity_id`; `origin_finding_id` loses NOT NULL; `chain_action_thread_one_origin`
  holds exactly one. The target trigger matches the stored Action's own origin pair, and the `chain_action` view
  projects the opportunity origin as two appended columns (existing columns and their order are unchanged).
- `action` is not touched.

The changed tables already carry their 0047 `chain_input_change` triggers (`domain_action`, `chain_action_thread`);
no new table is added.

Downgrade locks the tables (child first), refuses while any opportunity-origin Action or link exists, then restores
the 0042 trigger and view, the NOT NULLs, the 0035 domain CHECK and drops the added key.
"""

from alembic import op

revision = "0051_action_opportunity_origin"
down_revision = "0050_chain_response_expiry"
branch_labels = None
depends_on = None

TABLES = ("chain_action_thread", "domain_action_case_link", "domain_action_intent", "domain_action",
          "mini_opportunity_revision")
REFUSED = "Downgrade of 0051_action_opportunity_origin refused: opportunity-origin Actions exist."

_TARGET_FN = """
CREATE OR REPLACE FUNCTION chain_action_thread_target() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.action_kind = 'MINI_TRIAL' AND NOT EXISTS (
       SELECT 1 FROM action a WHERE a.tenant_id = NEW.tenant_id AND a.site_id = NEW.site_id AND a.id = NEW.action_id
         AND a.origin_finding_id = NEW.origin_finding_id) THEN
    RAISE EXCEPTION 'chain_action_thread: MINI_TRIAL action % is not in this tenant and Site', NEW.action_id;
  END IF;
  IF NEW.action_kind = 'DOMAIN_INTENT' AND NOT EXISTS (
       SELECT 1 FROM domain_action d WHERE d.tenant_id = NEW.tenant_id AND d.site_id = NEW.site_id
         AND d.id = NEW.action_id AND d.origin_finding_id IS NOT DISTINCT FROM NEW.origin_finding_id
         AND d.origin_opportunity_id IS NOT DISTINCT FROM NEW.origin_opportunity_id) THEN
    RAISE EXCEPTION 'chain_action_thread: DOMAIN_INTENT action % is not in this tenant and Site', NEW.action_id;
  END IF;
  RETURN NEW;
END;
$$;
"""

_VIEW = """
CREATE OR REPLACE VIEW chain_action AS
  SELECT a.id, a.tenant_id, a.site_id, a.action_code, 'MINI_TRIAL'::text AS kind,
         l.thread_id, a.origin_finding_id, a.origin_finding_revision_id,
         CAST(NULL AS uuid) AS origin_opportunity_id, CAST(NULL AS uuid) AS origin_opportunity_revision_id
    FROM action a LEFT JOIN chain_action_thread l ON l.action_kind = 'MINI_TRIAL' AND l.action_id = a.id
  UNION ALL
  SELECT d.id, d.tenant_id, d.site_id, d.action_code, 'DOMAIN_INTENT'::text,
         l.thread_id, d.origin_finding_id, d.origin_finding_revision_id,
         d.origin_opportunity_id, d.origin_opportunity_revision_id
    FROM domain_action d LEFT JOIN chain_action_thread l ON l.action_kind = 'DOMAIN_INTENT' AND l.action_id = d.id;
"""

UPGRADE = """
ALTER TABLE mini_opportunity_revision ADD CONSTRAINT mini_opportunity_revision_opportunity_scope
  UNIQUE (tenant_id, site_id, opportunity_id, id);
ALTER TABLE domain_action DROP CONSTRAINT domain_action_domain_chk;
ALTER TABLE domain_action ADD CONSTRAINT domain_action_domain_chk CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING', 'MINI'));
ALTER TABLE domain_action ADD COLUMN origin_opportunity_id uuid NULL, ADD COLUMN origin_opportunity_revision_id uuid NULL;
ALTER TABLE domain_action ALTER COLUMN origin_finding_id DROP NOT NULL,
  ALTER COLUMN origin_finding_revision_id DROP NOT NULL;
ALTER TABLE domain_action ADD CONSTRAINT domain_action_one_origin CHECK (
  (origin_finding_id IS NOT NULL AND origin_finding_revision_id IS NOT NULL
   AND origin_opportunity_id IS NULL AND origin_opportunity_revision_id IS NULL)
  OR (origin_finding_id IS NULL AND origin_finding_revision_id IS NULL
   AND origin_opportunity_id IS NOT NULL AND origin_opportunity_revision_id IS NOT NULL));
ALTER TABLE domain_action ADD CONSTRAINT domain_action_mini_origin
  CHECK ((domain = 'MINI') = (origin_opportunity_id IS NOT NULL));
ALTER TABLE domain_action ADD CONSTRAINT domain_action_opportunity_fk
  FOREIGN KEY (tenant_id, site_id, origin_opportunity_id) REFERENCES mini_opportunity (tenant_id, site_id, id);
ALTER TABLE domain_action ADD CONSTRAINT domain_action_opportunity_revision_fk
  FOREIGN KEY (tenant_id, site_id, origin_opportunity_id, origin_opportunity_revision_id)
  REFERENCES mini_opportunity_revision (tenant_id, site_id, opportunity_id, id);
ALTER TABLE chain_action_thread ADD COLUMN origin_opportunity_id uuid NULL;
ALTER TABLE chain_action_thread ALTER COLUMN origin_finding_id DROP NOT NULL;
ALTER TABLE chain_action_thread ADD CONSTRAINT chain_action_thread_one_origin
  CHECK ((origin_finding_id IS NULL) <> (origin_opportunity_id IS NULL));
""" + _TARGET_FN + _VIEW

REFUSE_IF_USED = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM domain_action WHERE origin_opportunity_id IS NOT NULL)\n"
    "       OR EXISTS (SELECT 1 FROM chain_action_thread WHERE origin_opportunity_id IS NOT NULL) THEN\n"
    f"        RAISE EXCEPTION '{REFUSED}';\n    END IF;\nEND;\n$$;\n"
)

RESTORE = """
DROP VIEW chain_action;
CREATE VIEW chain_action AS
  SELECT a.id, a.tenant_id, a.site_id, a.action_code, 'MINI_TRIAL'::text AS kind,
         l.thread_id, a.origin_finding_id, a.origin_finding_revision_id
    FROM action a LEFT JOIN chain_action_thread l ON l.action_kind = 'MINI_TRIAL' AND l.action_id = a.id
  UNION ALL
  SELECT d.id, d.tenant_id, d.site_id, d.action_code, 'DOMAIN_INTENT'::text,
         l.thread_id, d.origin_finding_id, d.origin_finding_revision_id
    FROM domain_action d LEFT JOIN chain_action_thread l ON l.action_kind = 'DOMAIN_INTENT' AND l.action_id = d.id;
CREATE OR REPLACE FUNCTION chain_action_thread_target() RETURNS trigger LANGUAGE plpgsql AS $$
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
ALTER TABLE chain_action_thread DROP CONSTRAINT chain_action_thread_one_origin;
ALTER TABLE chain_action_thread DROP COLUMN origin_opportunity_id;
ALTER TABLE chain_action_thread ALTER COLUMN origin_finding_id SET NOT NULL;
ALTER TABLE domain_action DROP CONSTRAINT domain_action_opportunity_revision_fk,
  DROP CONSTRAINT domain_action_opportunity_fk, DROP CONSTRAINT domain_action_mini_origin,
  DROP CONSTRAINT domain_action_one_origin;
ALTER TABLE domain_action DROP COLUMN origin_opportunity_revision_id, DROP COLUMN origin_opportunity_id;
ALTER TABLE domain_action ALTER COLUMN origin_finding_id SET NOT NULL,
  ALTER COLUMN origin_finding_revision_id SET NOT NULL;
ALTER TABLE domain_action DROP CONSTRAINT domain_action_domain_chk;
ALTER TABLE domain_action ADD CONSTRAINT domain_action_domain_chk CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING'));
ALTER TABLE mini_opportunity_revision DROP CONSTRAINT mini_opportunity_revision_opportunity_scope;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(REFUSE_IF_USED + RESTORE)
