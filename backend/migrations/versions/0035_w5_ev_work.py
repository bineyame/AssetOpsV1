"""W5-04a unit V1a: the domain Action root admits `EV_CHARGING` (EV Work and declared intent).

`.agent/W5-04-build-spec.md` "V1 migration" and "V1 selection, clock and schema", readiness rulings 2-4. Chains to
exactly `0034_w5_ev_scenarios`. No new table, column or index (pre-flight 7: 0033 `domain_action_site_raised`
serves the Site index):

- The 0033 table-level CHECK `domain = 'COLDCHAIN'` was generated unnamed. Its actual name is discovered in
  `pg_constraint` (table `domain_action`, `contype = 'c'`, expression equivalent to the cold-only check); exactly one
  match is required, then that name is dropped and the named `domain_action_domain_chk` admits
  `('COLDCHAIN','EV_CHARGING')`.
- `domain_action_intent_criteria_count_chk` keeps the array type and widens the length to IN (3, 4). The typed
  service enforces exactly four COLDCHAIN or three EV_CHARGING criteria; the DB rejects only 0-2 and 5+.

Downgrade locks `domain_action_case_link`, `domain_action_intent`, `domain_action` (child first) in ACCESS EXCLUSIVE
mode, refuses while any EV root exists (intent and link rows cannot exist without their root under the 0033 FKs),
then restores the named cold-only `domain_action_domain_chk` and the exact four-criteria check.
"""

from alembic import op

revision = "0035_w5_ev_work"
down_revision = "0034_w5_ev_scenarios"
branch_labels = None
depends_on = None

#: Child-to-parent lock order (readiness ruling 4).
TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action")
DOMAIN_CHECK = "domain_action_domain_chk"
COUNT_CHECK = "domain_action_intent_criteria_count_chk"
REFUSED = "Downgrade of 0035_w5_ev_work refused: EV domain Action rows exist."
DISCOVERY_FAILED = "0035_w5_ev_work: expected exactly one cold-only domain CHECK on domain_action"

#: Readiness ruling 3: the generated 0033 CHECK, found by table, type and normalized expression.
DISCOVER_AND_WIDEN = f"""
DO $$
DECLARE
  found text[];
BEGIN
  SELECT array_agg(conname ORDER BY conname) INTO found FROM pg_constraint
   WHERE conrelid = 'domain_action'::regclass AND contype = 'c'
     AND pg_get_constraintdef(oid) = 'CHECK ((domain = ''COLDCHAIN''::text))';
  IF coalesce(array_length(found, 1), 0) <> 1 THEN
    RAISE EXCEPTION '{DISCOVERY_FAILED} (found %)', coalesce(array_length(found, 1), 0);
  END IF;
  EXECUTE format('ALTER TABLE domain_action DROP CONSTRAINT %I', found[1]);
END $$;
ALTER TABLE domain_action ADD CONSTRAINT {DOMAIN_CHECK} CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING'));
ALTER TABLE domain_action_intent DROP CONSTRAINT {COUNT_CHECK};
ALTER TABLE domain_action_intent ADD CONSTRAINT {COUNT_CHECK}
  CHECK (jsonb_typeof(criteria) = 'array' AND jsonb_array_length(criteria) IN (3, 4));
"""

REFUSE_IF_EV = (
    f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"
    "DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM domain_action WHERE domain = 'EV_CHARGING') THEN\n"
    f"        RAISE EXCEPTION '{REFUSED}';\n    END IF;\nEND;\n$$;\n"
)

RESTORE = f"""
ALTER TABLE domain_action DROP CONSTRAINT {DOMAIN_CHECK};
ALTER TABLE domain_action ADD CONSTRAINT {DOMAIN_CHECK} CHECK (domain = 'COLDCHAIN');
ALTER TABLE domain_action_intent DROP CONSTRAINT {COUNT_CHECK};
ALTER TABLE domain_action_intent ADD CONSTRAINT {COUNT_CHECK}
  CHECK (jsonb_typeof(criteria) = 'array' AND jsonb_array_length(criteria) = 4);
"""


def upgrade() -> None:
    op.execute(DISCOVER_AND_WIDEN)


def downgrade() -> None:
    op.execute(REFUSE_IF_EV)
    op.execute(RESTORE)
