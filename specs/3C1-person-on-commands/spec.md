# 3C1: the signed-in person on every work and action command (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1. Lane C (the person, decisions, calibration), the next
unit after `3C0a`.
- **Structure:** P1, approved with the pack (OD-20): `decision-loop-specification.md` §8.
- **Decisions:** `rulings.md` (D-3C1.1 to D-3C1.7).
- **Reviewer guide:** `reviewer-guide.md`.
- **Questions:** `handshake.md` before the build, then `mid-build-questions.md`.
- **Inventory:** the command inventory behind this spec was surveyed on 20 Nov and is cited by `file:line` below.

Non-screen. 3 units; D-3C1.7 says how it splits if the handshake finds more. Discovery review (W5): a schema change on
protected command tables, and authorisation.

## 0. Before you start

- **Branch.** `task/3C1-person-on-commands` off `main`, after this spec branch merges. Worktree
  `/opt/assetecon/AssetOpsV1-3c1`.
- **Python.** The shared `.venv` imports `main`, so put this tree first on `PYTHONPATH` and check the module paths:
  ```bash
  cd /opt/assetecon/AssetOpsV1-3c1
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts; print(assetops_backend.__file__, assetops_contracts.__file__)"
  ```
  The packet records this output.
- **Read:**
  - this spec and `rulings.md`;
  - `decision-loop-specification.md` §8;
  - `backend/assetops_backend/accounts/principal.py` and `model.py:35-48`;
  - `main.py:267`, `:347-351`, `:578-694`;
  - `action_api.py` and `actions/service.py:260-520`;
  - `actions/lifecycle.py:44-58`;
  - `domain_work_api.py`, `work/domain_intent.py:30-80`;
  - `work_api.py:60-210`, `work/model.py:250-292`, `work/service.py:120-480`, `work/operational_entry.py`;
  - migrations `0016_action_store.py:125-140`, `0019_verification_core.py:215-240`, `0027_w4_work_cases.py`,
    `0033_w5_cold_work.py:25-90`.
- **Databases.** Only `*_test` databases, through the harness (`ASSETOPS_TEST_DATABASE_URL=...@127.0.0.1:55432/assetops_test`).
  Every Postgres file runs through `tools/heavy-slot.sh --db -- <command>`. Never touch ports 5490 or 8990, the
  walkthrough DB or Docker.
- **Migration.** Name it `0064_person_on_commands`. `3A1` writes `0063`; whichever merges second is renumbered at merge
  preparation.
- **Collisions with the other lanes.**
  - `3A1` (lane A) shares the migration head and `tools/checks/configuration-persistence.ps1`. 3C1 needs no new writer
    registration, because the existing writers keep their tables.
  - `3B1` (lane B) adds one call in `main.py`. 3C1 edits `main.py`'s router wiring, so merge `main` before review.
  - The UI lanes and DS1m touch only mock-up files.

## 1. Outcome and why

When a person is signed in, every work and action command is recorded under that person, authorised by their role,
and never by a service principal or a browser-sent actor:
- trial actions: accept, apply, observe;
- domain actions: create, intent, case link;
- W4 work: cases, events, revisions, maintenance records, plans, operational records, and the operational entry.

When no one is signed in, today's behaviour is unchanged, until the switch below is turned on. `3C0b` (the sign-in
page) turns it on, so today's screens keep their commands (D-BW1.3).

This answers step 3C's gate: is every command, from every role, recorded under the authenticated person? It also
unblocks `3C2` (each Action's creator, owner and due date), `3B4` and steps 5 to 7.

## 2. The person path, and the switch

For each route in §3, the first step after the route's existing Site-scope check is:

1. `person = person_from_request(request, accounts)`.
   - A store error answers 503, with the route's existing unavailable code.
   - `accounts` is threaded from `create_app` into each router builder as a new keyword argument, `accounts`.
2. **No person.**
   - If `require_person()` is on: answer 401 `PERSON_REQUIRED`.
   - Otherwise: today's path, byte for byte (the service principal, the client-sent `actor`, and `SYSTEM_DEMO` for
     actions).
3. **A person.**
   - The person's tenant must be the Site's tenant. Otherwise answer 404, with the route's existing not-found code,
     as if the Site did not exist.
   - The person must hold one of the command's roles (§3). A `SITE_MANAGER` grant counts only for its own Site.
     Otherwise answer 403 `PERSON_ROLE_REQUIRED`, with `params={"roles": [...]}`.
   - A body that sends `actor` (or any key today refused as client authority) is refused 422 with the route's existing
     client-actor code: `CLIENT_AUTHORITY_FORBIDDEN` for actions, and `WORK_INPUT_INVALID` with field `actor` for
     work and domain routes.
   - The server composes the actor:
     - `actor_kind` = `USER`;
     - `actor_id` = `person:<person_id>`;
     - `attestation` = `person=<person_id>;session=<session_id>;role=<the role that admitted it>`;
     - `person_id` = the person's ID;
     - for actions, `source_channel` = `PERSON_API` and `authorization_basis` = `PERSON_ROLE:<role>`;
     - for work and domain routes, `authorization_basis` = `PERSON_ROLE:<role>`.
   - The service principal, the demo grant file and the `SITE_WORK_WRITE` gate do not apply on this path.
4. **The switch.** `require_person()` reads `ASSETOPS_REQUIRE_PERSON`.
   - Unset or `off`: off. `on`: on. Anything else: `ConfigurationError` at `create_app`.
   - It lives in `accounts/principal.py`.
   - 3C1 ships it off. `3C0b` turns it on in the same merge as the sign-in page.

The command hash includes the actor (`work/model.py:266`, `work/domain_action.py:439`), so the same body sent by two
people is two commands. That is intended (D-3C1.4).

## 3. Commands and roles (`accounts/permissions.py`, D-3C1.2)

`COMMAND_ROLES: Mapping[str, tuple[str, ...]]` is one literal table. The roles come from
`decision-loop-specification.md` §8's "who may do what"; it is configurable later by role (owner, 20 Nov, item 5).

| Command key | Route (handler) | Roles |
|---|---|---|
| `action.accept` | POST `/api/sites/{site_code}/findings/{finding_id}/recommendation/accept` (`action_api.py:153`) | SITE_MANAGER |
| `action.apply` | POST `.../actions/{action_id}/apply` (`:173`) | SITE_MANAGER |
| `action.observe` | POST `.../actions/{action_id}/observations` (`:200`) | SITE_MANAGER, FIELD_TECHNICIAN |
| `domain.create` | POST `.../domain-work/actions` (`domain_work_api.py:69`) | SITE_MANAGER, FINANCE_AND_COMMERCIAL_LEAD |
| `domain.intent` | POST `.../domain-work/actions/{action_id}/intents` (`:75`) | SITE_MANAGER |
| `domain.case_link` | POST `.../domain-work/actions/{action_id}/case-links` (`:81`) | SITE_MANAGER |
| `work.case_create` | POST `.../work/cases` (`work_api.py:163`) | SITE_MANAGER, FIELD_TECHNICIAN |
| `work.case_event` | POST `.../work/cases/{case_id}/events` (`:169`) | SITE_MANAGER |
| `work.case_revision` | POST `.../work/cases/{case_id}/revisions` (`:175`) | SITE_MANAGER |
| `work.maintenance_record` | POST `.../work/cases/{case_id}/records` (`:181`) | SITE_MANAGER, FIELD_TECHNICIAN |
| `work.maintenance_plan` | POST `.../work/plans` (`:187`) | SITE_MANAGER |
| `work.operational_record` | POST `.../work/operational-records` (`:193`) | SITE_MANAGER, FIELD_TECHNICIAN |
| `work.operational_entry` | POST `.../work/operational-entries` (`:199`) | SITE_MANAGER, FIELD_TECHNICIAN |

**The admitting role.** When several of the person's grants qualify, it is the first matching role in this table's
order for that command.

**Outside this unit.** These routes keep their current paths unchanged (D-3C1.3):
- verification plan, later-selection and evaluation (they remain system steps until `8a`);
- financial assumptions;
- mini, cold and EV decision writes (step 6, `6a`).

## 4. Migration `0064_person_on_commands`

The tables in scope:
- actions: `action_event`;
- domain actions: `domain_action`, `domain_action_intent`, `domain_action_case_link`;
- W4: `work_case`, `work_case_revision`, `work_event`, `maintenance_plan`, `maintenance_record`, `operational_record`.

For each of them:
- `ALTER TABLE <t> ADD COLUMN person_id uuid NULL`;
- `ALTER TABLE <t> ADD CONSTRAINT <t>_person_fk FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account
  (tenant_id, id)`;
- `ALTER TABLE <t> ADD CONSTRAINT <t>_person_actor CHECK ((actor_kind = 'USER') = (person_id IS NOT NULL))`.

Then widen the existing CHECKs:
- `action_event`: `actor_kind IN ('SYSTEM','USER')`. The `actor_id` CHECK admits `^person:[0-9a-f-]{36}$` when the
  kind is `USER`. The `source_channel` CHECK adds `PERSON_API`. The SYSTEM_JOB coupling (0019:229-236) is unchanged
  for SYSTEM rows.
- The three domain tables: `actor_kind IN ('SERVICE','USER')`.
- The W4 tables already allow `USER` (0027).
- Any CHECK on `attestation` or `authorization_basis` that refuses the §2 forms is widened to admit exactly them, and
  nothing else.

The pre-flight lists every constraint by name, from `pg_constraint` on a migrated clone, in `handshake.md`.

**Upgrade.** It first refuses, with `RAISE EXCEPTION 'Upgrade 0064 refused: USER rows without a person exist in <t>'`,
if any in-scope table has an `actor_kind = 'USER'` row. None exist today (survey).

**Downgrade.** Refused if any `person_id` is not null; otherwise it drops the added constraints and columns and
restores the old CHECKs.

The chain change-log triggers on these tables are unaffected: adding a column changes no trigger.

## 5. Code

- **`accounts/permissions.py` (new).** `COMMAND_ROLES`, and `admit(person, command, site_id) -> str` (the admitting
  role), which raises `PersonRefused(403, "PERSON_ROLE_REQUIRED", roles)`.
- **`accounts/principal.py`.** Adds `require_person()` and `person_actor(person, role) -> PersonActor(actor_kind,
  actor_id, attestation, person_id, authorization_basis)`.
- **The routers.** `action_api.py`, `domain_work_api.py` and `work_api.py` gain the `accounts` keyword and §2's step
  before their existing gate. `create_app` passes `accounts` to all three.
- **The services.** They take an optional `person_actor`.
  - When it is given, the service skips the service-principal and capability gates and writes the person's columns.
  - `actions/service.py` `accept`, `apply` and `observe` write `action_event` with the person's actor in place of
    `SYSTEM_DEMO`.
  - `work/service.py` `_actor_cols` and `work/domain_intent.py` `_actor_row` add `person_id`.
  - The adapters' INSERT column lists gain `person_id`.
  - The operational entry composes `PersonActor` in place of `ENTRY_ACTOR` when a person is signed in.
- **Words** (`i18n/messages.py`, a `# 3C1` block):
  - `PERSON_REQUIRED`: "Sign in to continue."
  - `PERSON_ROLE_REQUIRED`: "Your role cannot do this here."
- **No change to reads.** `actor_id` reads `person:<uuid>`, and `3C2` and `3C3` show the person's name.

## 6. Tests

**No database** (`backend/tests/test_3c1_person_commands.py`). Use `TestClient(create_app(accounts=<memory service
from test_3c0a_accounts_api's helper>, ...), base_url="https://testserver")`, with fake work, domain and action
services that record what they receive.
- For each of the 13 commands:
  - a signed-in person with the role reaches the service with the composed `PersonActor`;
  - without the role: 403 `PERSON_ROLE_REQUIRED`;
  - a SITE_MANAGER of another Site: 403;
  - another tenant's person: the route's 404;
  - a body with `actor`: 422.
- With no person and the switch off, each command reaches today's path unchanged (the existing tests stay green).
  With the switch on: 401 `PERSON_REQUIRED`.
- A bad `ASSETOPS_REQUIRE_PERSON` refuses `create_app`.

**Postgres** (pooled, `--db`; `backend/tests/test_3c1_person_commands_postgres.py`):
- The migration's columns, FKs and CHECKs exist.
- A USER row without `person_id` fails, and a SERVICE row with one fails.
- A person from another tenant fails the FK.
- A signed-in person, on a real store, creates a work case, records an operational record, creates a domain action,
  and accepts a trial action. Each row carries `actor_kind = 'USER'`, `person_id`, and the §2 attestation and basis.
- The upgrade refusal triggers on a planted USER row in a pre-0064 clone.
- The downgrade is refused with a person row, and down then up works on an empty clone.

**Regression.** These existing files pin today's path and must pass unchanged:
- `test_w401_work_api.py`, `test_w502_domain_intent_api.py`, `test_s6_action_rule.py`, `test_own_g3_operational_entry.py`;
- pooled: `test_s6_action_store_postgres.py`, `test_s6_action_apply_postgres.py`, `test_w401_work_service_postgres.py`,
  `test_w502_domain_intent_postgres.py`, `test_own_g3_operational_entry_postgres.py`, `test_pg_harness.py`.

Commands:
```bash
$PY -m pytest backend/tests/test_3c1_person_commands.py backend/tests/test_w401_work_api.py backend/tests/test_w502_domain_intent_api.py backend/tests/test_s6_action_rule.py backend/tests/test_own_g3_operational_entry.py -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh --db -- $PY -m pytest backend/tests/test_3c1_person_commands_postgres.py backend/tests/test_s6_action_store_postgres.py backend/tests/test_s6_action_apply_postgres.py backend/tests/test_w401_work_service_postgres.py backend/tests/test_w502_domain_intent_postgres.py backend/tests/test_own_g3_operational_entry_postgres.py backend/tests/test_pg_harness.py -q
pwsh -NoProfile -File tools/check-all.ps1
python3 tools/select-tests.py --base main      # "full" (migration, main.py): not run while building; the merge's full tier runs it
```

## 7. Done (questions)

1. With a person signed in, is every one of the 13 commands recorded under that person (`USER`, `person_id`,
   attestation, basis), authorised by their role, and never by a browser-sent actor?
2. Is a person without the role, of another Site, or of another tenant refused with the stated codes?
3. With no person and the switch off, is every existing test green and every stored byte as today?
4. Does the switch, when on, refuse an unsigned command with 401?
5. Does the database refuse a USER row without a person and a person of another tenant?
6. Is nothing outside these files changed (`git diff --stat main...HEAD`)?
   - the migration;
   - `accounts/permissions.py` and `accounts/principal.py`;
   - the three routers, `main.py`'s wiring, the services and adapters named in §5;
   - the words;
   - the two test files, the packet and the finish bookkeeping.

## 8. Out of scope

- The refusal switched on (`3C0b`).
- Actions' creator, owner and due date (`3C2`).
- Showing the person's name (`3C2`, `3C3`).
- Verification, financial and decision writes (D-3C1.3).
- The "system never chooses" refusal for the system path (`6a`).
