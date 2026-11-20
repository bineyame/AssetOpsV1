"""3C1a (`specs/3C1-person-on-commands/spec.md` §4; R4, R8, P1, P2): the signed-in person on work and domain rows.

Nine tables gain one nullable column, `person_id`, and two constraints each:

- `<t>_person_fk`: `(tenant_id, person_id)` references `operator_account (tenant_id, id)`, so a person of another
  tenant cannot be recorded;
- `<t>_person_actor` (R8): `actor_kind = 'USER'` holds exactly when `person_id` is set, and then
  `actor_id = 'person:' || person_id`.

The three domain tables' generated 0033 kind checks (`actor_kind = 'SERVICE'`) are found by name and asserted by
definition (`pg_get_constraintdef`, as 0035 does), then replaced under the same name by `IN ('SERVICE','USER')`. The
W4 kind checks already admit `USER` and the length checks need no change (P1).

Upgrade: lock the nine tables child-first in ACCESS EXCLUSIVE mode (P2), then refuse while any `USER` row exists
(such a row has no person). Downgrade: the same lock, refused while any `person_id` is set; otherwise it drops what
the upgrade added and re-adds the exact 0033 kind checks under their names.

Numbered by D-3A1.12: whichever of 3C1a and 3A1 merges first keeps 0063; tests read `revision` and `down_revision`
from this module.
"""

from alembic import op

revision = "0063_person_on_work"
down_revision = "0062_operator_accounts"
branch_labels = None
depends_on = None

#: Child-to-parent lock, refusal and drop order (P2).
TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action", "operational_record",
          "maintenance_record", "maintenance_plan", "work_event", "work_case_revision", "work_case")
DOMAIN_TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action")
#: The 0033 definition each domain kind check must have before it is widened, as `pg_get_constraintdef` prints it.
SERVICE_ONLY = "CHECK ((actor_kind = 'SERVICE'::text))"
UPGRADE_REFUSED = "Upgrade refused: USER rows without a person exist in"
DOWNGRADE_REFUSED = "Downgrade of 0063_person_on_work refused: person rows exist in"
DISCOVERY_FAILED = "0063_person_on_work: unexpected actor kind check on"

LOCK = f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;\n"


def _refuse_if(condition: str, message: str) -> str:
    checks = "".join(
        f"    IF EXISTS (SELECT 1 FROM {t} WHERE {condition}) THEN\n"
        f"        RAISE EXCEPTION '{message} {t}';\n    END IF;\n" for t in TABLES)
    return f"DO $$\nBEGIN\n{checks}END;\n$$;\n"


def _kind_check(table: str) -> str:
    return f"{table}_actor_kind_check"


def _assert_kind_check(table: str, definition: str) -> str:
    """Exactly one CHECK with this definition on the table, and it carries the expected name (P1)."""
    doubled = definition.replace("'", "''")
    return f"""
DO $$
DECLARE
  found text[];
BEGIN
  SELECT array_agg(conname ORDER BY conname) INTO found FROM pg_constraint
   WHERE conrelid = '{table}'::regclass AND contype = 'c' AND pg_get_constraintdef(oid) = '{doubled}';
  IF coalesce(array_length(found, 1), 0) <> 1 OR found[1] <> '{_kind_check(table)}' THEN
    RAISE EXCEPTION '{DISCOVERY_FAILED} {table} (found %)', found;
  END IF;
END $$;
"""


def _person_constraints(table: str) -> str:
    return (f"ALTER TABLE {table} ADD COLUMN person_id uuid NULL;\n"
            f"ALTER TABLE {table} ADD CONSTRAINT {table}_person_fk FOREIGN KEY (tenant_id, person_id) "
            f"REFERENCES operator_account (tenant_id, id);\n"
            f"ALTER TABLE {table} ADD CONSTRAINT {table}_person_actor CHECK ((actor_kind = 'USER') = "
            f"(person_id IS NOT NULL) AND (person_id IS NULL OR actor_id = 'person:' || person_id::text));\n")


UPGRADE = (LOCK + _refuse_if("actor_kind = 'USER'", UPGRADE_REFUSED)
           + "".join(_person_constraints(t) for t in TABLES)
           + "".join(_assert_kind_check(t, SERVICE_ONLY)
                     + f"ALTER TABLE {t} DROP CONSTRAINT {_kind_check(t)};\n"
                     f"ALTER TABLE {t} ADD CONSTRAINT {_kind_check(t)} CHECK (actor_kind IN ('SERVICE', 'USER'));\n"
                     for t in DOMAIN_TABLES))

DOWNGRADE = (LOCK + _refuse_if("person_id IS NOT NULL", DOWNGRADE_REFUSED)
             + "".join(f"ALTER TABLE {t} DROP CONSTRAINT {_kind_check(t)};\n"
                       f"ALTER TABLE {t} ADD CONSTRAINT {_kind_check(t)} CHECK (actor_kind = 'SERVICE');\n"
                       for t in DOMAIN_TABLES)
             + "".join(f"ALTER TABLE {t} DROP CONSTRAINT {t}_person_actor;\n"
                       f"ALTER TABLE {t} DROP CONSTRAINT {t}_person_fk;\n"
                       f"ALTER TABLE {t} DROP COLUMN person_id;\n" for t in TABLES)
             + "".join(_assert_kind_check(t, SERVICE_ONLY) for t in DOMAIN_TABLES))


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
