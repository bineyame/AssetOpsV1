"""3C1b (`specs/3C1-person-on-commands/spec.md` §5 step 1; R4, R8, P1, P2): the signed-in person on `action_event`.

`action_event` gains one nullable column, `person_id`, and:

- `action_event_person_fk`: `(tenant_id, person_id)` references `operator_account (tenant_id, id)`, so a person of
  another tenant cannot be recorded;
- `action_event_person_actor` (R8): `actor_kind = 'USER'` holds exactly when `person_id` is set, and then
  `actor_id = 'person:' || person_id`;
- `action_event_person_coupling` (R8): a SYSTEM row keeps a `service:` ID and today's channels; a USER row has a
  `person:` ID, the `PERSON_API` channel, one of the person's events (ACCEPTED, APPLIED, OBSERVED, and APPLY's
  FAILED outcome) and a `PERSON_ROLE:<role>` basis.

Three checks are found by name and asserted by definition (`pg_get_constraintdef`, as 0035 and 0064 do), then
replaced under the same name: `action_event_actor_kind_check` (SYSTEM or USER), `action_event_actor_id_check` (a
`service:` or a `person:` ID) and `action_event_source_channel_check` (today's channels plus `PERSON_API`).
`action_event_evaluator_job` is unchanged.

Upgrade: lock `action_event` in ACCESS EXCLUSIVE mode (P2), then refuse while any `USER` row exists (such a row has
no person). Downgrade: the same lock, refused while any `person_id` is set; otherwise it drops what the upgrade added
and re-adds the exact 0016/0019 texts under their names, so 0019's own downgrade still finds them.

Numbering (D-3A1.12): 0071. 3A7 holds 0069 and 3C2 holds 0070; the head on `main` at this merge is 0068, so
`down_revision` points at 0068 and is re-pointed at merge preparation to whichever of 0069/0070 has merged. The module is self-contained: renumbering changes only the file name,
`revision` and `down_revision` (every message is built from `revision`, and the tests find this module by
`*_person_on_actions.py` and read both ids from it).
"""

from alembic import op

revision = "0071_person_on_actions"
down_revision = "0068_structure_finding"
branch_labels = None
depends_on = None

TABLE = "action_event"
UPGRADE_REFUSED = "Upgrade refused: USER rows without a person exist in"
DOWNGRADE_REFUSED = f"Downgrade of {revision} refused: person rows exist in"
DISCOVERY_FAILED = f"{revision}: unexpected check on"

#: name -> (the definition before this migration, as `pg_get_constraintdef` prints it; the DDL that restores it;
#: the widened DDL). The "before" texts are 0016's (kind, id) and 0019's (channel).
CHECKS = {
    "action_event_actor_kind_check": (
        "CHECK ((actor_kind = 'SYSTEM'::text))",
        "actor_kind = 'SYSTEM'",
        "actor_kind IN ('SYSTEM','USER')"),
    "action_event_actor_id_check": (
        "CHECK ((actor_id ~ '^service:[a-z0-9-]+$'::text))",
        "actor_id ~ '^service:[a-z0-9-]+$'",
        "actor_id ~ '^service:[a-z0-9-]+$' OR actor_id ~ '^person:[0-9a-f-]{36}$'"),
    "action_event_source_channel_check": (
        "CHECK ((source_channel = ANY (ARRAY['SYSTEM_DEMONSTRATION_API'::text, 'SYSTEM_JOB'::text])))",
        "source_channel IN ('SYSTEM_DEMONSTRATION_API','SYSTEM_JOB')",
        "source_channel IN ('SYSTEM_DEMONSTRATION_API','SYSTEM_JOB','PERSON_API')"),
}

COUPLING = ("(actor_kind = 'SYSTEM' AND actor_id ~ '^service:[a-z0-9-]+$' "
            "AND source_channel IN ('SYSTEM_DEMONSTRATION_API','SYSTEM_JOB')) "
            "OR (actor_kind = 'USER' AND actor_id ~ '^person:[0-9a-f-]{36}$' AND source_channel = 'PERSON_API' "
            "AND kind IN ('ACCEPTED','APPLIED','FAILED','OBSERVED') "
            "AND authorization_basis ~ '^PERSON_ROLE:[A-Z_]+$')")

LOCK = f"LOCK TABLE {TABLE} IN ACCESS EXCLUSIVE MODE;\n"


def _refuse_if(condition: str, message: str) -> str:
    return (f"DO $$\nBEGIN\n    IF EXISTS (SELECT 1 FROM {TABLE} WHERE {condition}) THEN\n"
            f"        RAISE EXCEPTION '{message} {TABLE}';\n    END IF;\nEND;\n$$;\n")


def _assert_check(name: str, definition: str) -> str:
    """Exactly one CHECK with this definition on the table, and it carries the expected name (P1)."""
    doubled = definition.replace("'", "''")
    return f"""
DO $$
DECLARE
  found text[];
BEGIN
  SELECT array_agg(conname ORDER BY conname) INTO found FROM pg_constraint
   WHERE conrelid = '{TABLE}'::regclass AND contype = 'c' AND pg_get_constraintdef(oid) = '{doubled}';
  IF coalesce(array_length(found, 1), 0) <> 1 OR found[1] <> '{name}' THEN
    RAISE EXCEPTION '{DISCOVERY_FAILED} {TABLE}: {name} (found %)', found;
  END IF;
END $$;
"""


def _replace(name: str, ddl: str) -> str:
    return (f"ALTER TABLE {TABLE} DROP CONSTRAINT {name};\n"
            f"ALTER TABLE {TABLE} ADD CONSTRAINT {name} CHECK ({ddl});\n")


UPGRADE = (LOCK + _refuse_if("actor_kind = 'USER'", UPGRADE_REFUSED)
           + "".join(_assert_check(name, before) + _replace(name, widened)
                     for name, (before, _, widened) in CHECKS.items())
           + f"ALTER TABLE {TABLE} ADD COLUMN person_id uuid NULL;\n"
           f"ALTER TABLE {TABLE} ADD CONSTRAINT {TABLE}_person_fk FOREIGN KEY (tenant_id, person_id) "
           f"REFERENCES operator_account (tenant_id, id);\n"
           f"ALTER TABLE {TABLE} ADD CONSTRAINT {TABLE}_person_actor CHECK ((actor_kind = 'USER') = "
           f"(person_id IS NOT NULL) AND (person_id IS NULL OR actor_id = 'person:' || person_id::text));\n"
           f"ALTER TABLE {TABLE} ADD CONSTRAINT {TABLE}_person_coupling CHECK ({COUPLING});\n")

DOWNGRADE = (LOCK + _refuse_if("person_id IS NOT NULL", DOWNGRADE_REFUSED)
             + f"ALTER TABLE {TABLE} DROP CONSTRAINT {TABLE}_person_coupling;\n"
             f"ALTER TABLE {TABLE} DROP CONSTRAINT {TABLE}_person_actor;\n"
             f"ALTER TABLE {TABLE} DROP CONSTRAINT {TABLE}_person_fk;\n"
             f"ALTER TABLE {TABLE} DROP COLUMN person_id;\n"
             + "".join(_replace(name, restore) for name, (_, restore, _) in CHECKS.items())
             + "".join(_assert_check(name, before) for name, (before, _, _) in CHECKS.items()))


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
