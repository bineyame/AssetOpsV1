# 3C1a and 3C1b: the signed-in person on work and action commands (implementer spec)

Status: 3C1a in_review (`task/3C1a-person-on-work`, packet `packet.md`); 3C1b not started.

Architect (Claude), 2026-11-20. **Rev 2**: handshake round 1 is folded in (`rulings.md` "Handshake answers
(round 1)", D-3C1.8 to D-3C1.13). The pre-flight estimated about 5 units, so the slice is split now (D-3C1.7, P10):

| Unit | Scope | Units | Order |
|---|---|---|---|
| **3C1a** | Work and domain commands: 10 commands on 9 tables | 3 | First |
| **3C1b** | Trial actions: 3 commands on `action_event` | 2 | After 3C1a merges (it reuses `permissions.py` and `principal.py`) |

Both are lane C. The structure is P1, approved with the pack (OD-20): `decision-loop-specification.md` §8. Both are
non-screen and get a discovery review (W5). Each unit has its own branch, packet and review.

`3C0b` waits for **both** units. Its switch must not refuse unsigned trial actions while they have no person path
(P10).

## 0. Before you start (both units)

- **Branches.**
  - `task/3C1a-person-work`, off `main` after this ruling branch merges. Worktree `/opt/assetecon/AssetOpsV1-3c1a`.
  - `task/3C1b-person-actions`, off `main` after 3C1a merges. Worktree `/opt/assetecon/AssetOpsV1-3c1b`.
- **Python.** The shared `.venv` imports `main`, so put this tree's own packages first on `PYTHONPATH` and check the
  module paths:
  ```bash
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts, fixtures; print(assetops_backend.__file__, assetops_contracts.__file__, fixtures.__file__)"
  ```
  Run from the worktree, with that tree's `tools/heavy-slot.sh` (P9). Record the output in the packet.
- **Read:** this spec, `rulings.md`, `decision-loop-specification.md` §8, 3C0a's `accounts/` package, and the code at
  the lines cited below.
- **Databases.** Only `*_test` databases, through the harness. Every Postgres file runs through
  `tools/heavy-slot.sh --db -- <command>`. Never touch ports 5490 or 8990, the walkthrough database or Docker.
- **Migrations.** 3C1a writes the person migration for its 9 tables; 3C1b writes one for `action_event`. They are
  numbered by D-3A1.12: the first slice to merge takes the next number on the head, and any later one is renumbered
  at merge preparation. Tests read the head and `down_revision` from the migration modules.
- **Collisions.**
  - **3A1** (lane A) shares the migration head and the persistence guard. 3C1 adds no writer registration.
  - **3B1** (lane B) adds one call right after `main.py:341`. 3C1 edits `main.py` around `:348-351` and `:623-675`.
    Merge `main` before review, then re-run `test_3c0a_accounts_api.py` and the 3B1 start-up test (P8).

## 1. Outcome

When a person is signed in, each in-scope command is recorded under that person and authorised by their role. It is
never authorised by an actor the browser sends.

The person path is **live as soon as each unit merges** (R6), and it opens no write that is closed today:
- the feature switches still apply to people (§2, step 3);
- the trial actions keep the demo grant file's record scope (§5, step 2).

With no person, nothing changes until `ASSETOPS_REQUIRE_PERSON=on`, which `3C0b` turns on.

## 2. The person step (shared; built in 3C1a)

`accounts/permissions.py` holds `person_step(...)`.
- The work and domain routers reach it through `WorkGate`. `WorkGate` gains `accounts`, the switch bool and the
  account store's unavailable types (P6).
- The action router gains the same three as keyword arguments.
- Every new keyword defaults to None or off, so existing direct callers do not change.

For each in-scope route, after the route's existing Site-scope check:

1. **Find the person.** `person = person_from_request(request, accounts)` when `accounts` is not None. When
   `accounts` is None, there is no person (R10).
   - An account-store error answers 503 with the route's unavailable code, even with the switch off.
   - An expired or revoked cookie means no person (R11).
2. **No person.**
   - With the switch on: 401 `PERSON_REQUIRED`.
   - With it off: today's path, byte for byte.
   - The switch is read **once**, in `create_app`, beside `session_cookie_secure()`, and passed down as a bool (R10).
     `require_person()` reads `ASSETOPS_REQUIRE_PERSON`: unset or `off` is off, `on` is on, and anything else raises
     `ConfigurationError`.
3. **A person.**
   - **Feature switches still apply** (R6). The person replaces the *actor*, not the gate.
     - The work and domain routes need their gate's principal to be composed, as today. With none composed, the
       answer is 403 `WORK_WRITE_FORBIDDEN`.
     - The operational entry needs `operational_entry_principal`, as today.
   - **Tenant.** A person of another tenant gets a body **byte-equal** to that route's unknown-Site 404 (R9,
     D-3C1.6).
   - **Role.** The person must hold one of the command's roles (§3). Otherwise: 403 `PERSON_ROLE_REQUIRED`, with
     `params={"roles": [...]}`.
     - Only SITE_MANAGER grants are bound to a Site. The field technician and the finance lead act at every Site of
       their tenant (R5e).
     - When several roles match, the admitting role is the first in §3's order.
   - **No client actor** (R9). A body carrying `actor`, or any key today refused as client authority, gets the route's
     own existing shape-refusal code, with no field added: work `WORK_INPUT_INVALID`, domain `DOMAIN_INTENT_INVALID`,
     actions `CLIENT_AUTHORITY_FORBIDDEN`. The person path uses the same closed shapes, minus `actor` (P4).
   - **The server composes the actor** (R4):
     - `actor_kind` is `USER`;
     - `actor_id` is `person:<person_id>`;
     - `person_id` is the person's ID;
     - on the W4 and domain tables, `attestation` is `person=<id>;session=<session_id>;role=<role>`;
     - on the W4 tables, `authorization_basis` is `PERSON_ROLE:<role>`. The domain tables have no
       `authorization_basis`, so the role there lives only in the attestation.
     - on `action_event` (3C1b), `authorization_basis` is `PERSON_ROLE:<role>`. That table has no attestation.
   - **Hash identity** (R1, D-3C1.4 as corrected).
     - On the person path the hashed actor is `{kind: "USER", id: "person:<uuid>"}`. The session and the role stay
       out of the hash.
     - `Actor.canonical()` for SERVICE is unchanged, so every existing hash stays byte-identical.
     - The same person retrying after signing in again gets the 200 replay.
     - Idempotency keys stay unique per Site or per case, so another person sending the same key gets the route's
       duplicate-key 409.

**Words** (a `# 3C1` block):
- `PERSON_REQUIRED`: "Sign in to continue."
- `PERSON_ROLE_REQUIRED`: "Your role cannot do this here."

## 3. Commands and roles (`COMMAND_ROLES`; D-3C1.2 as amended)

| Command key | Route | Roles | Unit |
|---|---|---|---|
| `work.case_create` | POST `.../work/cases` (`work_api.py:163`) | SITE_MANAGER, FIELD_TECHNICIAN | 3C1a |
| `work.case_event.COMPLETE`, `work.case_event.COMMENT` | POST `.../work/cases/{id}/events` (`:169`), keyed by event kind (`work/model.py:125`) | SITE_MANAGER, FIELD_TECHNICIAN | 3C1a |
| `work.case_event.<other kinds>` | the same route | SITE_MANAGER | 3C1a |
| `work.case_revision` | `:175` | SITE_MANAGER | 3C1a |
| `work.maintenance_record` | `:181` | FIELD_TECHNICIAN, SITE_MANAGER | 3C1a |
| `work.maintenance_plan` | `:187` | SITE_MANAGER | 3C1a |
| `work.operational_record` | `:193` | FIELD_TECHNICIAN, SITE_MANAGER | 3C1a |
| `work.operational_entry` | `:199` | FIELD_TECHNICIAN, SITE_MANAGER | 3C1a |
| `domain.create` | `domain_work_api.py:69` | SITE_MANAGER, FINANCE_AND_COMMERCIAL_LEAD | 3C1a |
| `domain.intent` | `:75` | SITE_MANAGER, FINANCE_AND_COMMERCIAL_LEAD | 3C1a |
| `domain.case_link` | `:81` | SITE_MANAGER | 3C1a |
| `action.accept` | `action_api.py:153` | SITE_MANAGER | 3C1b |
| `action.apply` | `:173` | SITE_MANAGER | 3C1b |
| `action.observe` | `:200` | SITE_MANAGER, FIELD_TECHNICIAN | 3C1b |

**Design deviation (D-3C1.10).** The site manager may also record readings and completions, which §8 gives to the
field technician alone.

## 4. 3C1a: work and domain

**Migration**, on `work_case`, `work_case_revision`, `work_event`, `maintenance_plan`, `maintenance_record`,
`operational_record`, `domain_action`, `domain_action_intent` and `domain_action_case_link`:
1. **Lock first** (P2): `LOCK TABLE … IN ACCESS EXCLUSIVE MODE`, children first.
2. **Refuse USER rows.** If any `actor_kind = 'USER'` row exists:
   `RAISE EXCEPTION 'Upgrade refused: USER rows without a person exist in <t>'`.
3. **Person column and FK.**
   - `ADD COLUMN person_id uuid NULL`.
   - `ADD CONSTRAINT <t>_person_fk FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id)`.
   - `ADD CONSTRAINT <t>_person_actor CHECK ((actor_kind = 'USER') = (person_id IS NOT NULL) AND (person_id IS NULL OR
     actor_id = 'person:' || person_id::text))` (R8).
4. **Domain kind checks.** On the three domain tables, replace `domain_action_actor_kind_check`,
   `domain_action_intent_actor_kind_check` and `domain_action_case_link_actor_kind_check` with
   `actor_kind IN ('SERVICE','USER')`. Before dropping each one, assert its current definition with
   `pg_get_constraintdef`, as `0035:32-47` does.
5. **Left alone.** The W4 kind checks already allow `USER`. The length checks need no change (P1).

**Downgrade.** It is refused while any `person_id` is set. Otherwise it drops what the upgrade added and re-adds the
exact 0033 definitions under the same names.

**Code.**
- `work/service.py` and `work/domain_intent.py` take an optional `PersonActor`. When it is given:
  - the shapes drop `actor`;
  - the service-principal gate is replaced by §2;
  - `_actor_cols` and `_actor_row` add `person_id`.
- A case create writes `person_id` on all three of its rows (P4).
- The adapters' INSERT column lists gain `person_id`. **Read column lists do not change.**
- Today's `authorize()` refusal of a client USER actor stays.
- The operational entry composes the person's actor in place of `ENTRY_ACTOR` (P5).

**Tests without a database** (`backend/tests/test_3c1a_person_work.py`). Build the routers directly, with fakes and
3C0a's in-memory `AccountService`, as `test_w401_work_api.py:37-64` does (P7). For each of the 10 commands and each
`case_event` kind:
- **Role:** a person with a listed role is admitted; a person without one gets 403; a SITE_MANAGER of another Site
  gets 403.
- **Tenant:** another tenant gets a 404 byte-equal to the route's unknown-Site 404.
- **Client actor:** a body carrying `actor` gets the route's shape code.
- **Hash** (R1): the same person in two sessions, same body: 200 replay. Another person, same key: duplicate-key 409.
- **Switch:** with no person, the switch on gives 401 and the switch off gives today's path.
- **Feature switches** (R6): with no gate principal composed, a person gets 403 `WORK_WRITE_FORBIDDEN`; with the entry
  switch off, the entry route refuses the person the same way.
- **No accounts:** with `accounts` None, there is no person.

**Postgres tests** (`backend/tests/test_3c1a_person_work_postgres.py`):
- the constraints exist;
- each of these fails: a USER row without `person_id`, a `person_id` with SERVICE, an `actor_id` that does not match
  `person_id`, and a person of another tenant (the FK);
- through `create_app` with a real store, one work command and one domain command store `USER`, `person_id` and the
  §2 attestation and basis;
- the upgrade refusal fires on a planted USER row in a clone before the migration;
- the downgrade is refused while a person row exists, and down then up works.

**Regression (must pass unchanged).**
- Without a database: `test_w401_work_api.py`, `test_w502_domain_intent_api.py`, `test_own_g3_operational_entry.py`.
- Pooled: `test_w401_work_service_postgres.py`, `test_w502_domain_intent_postgres.py`,
  `test_own_g3_operational_entry_postgres.py`, `test_w502_domain_action_index_postgres.py`,
  `test_k6a_fuel_action_origin_postgres.py`, `test_3c0a_accounts_postgres.py`, `test_pg_harness.py`.

## 5. 3C1b: trial actions

1. **Migration**, on `action_event`.
   - The same lock, refusal, column, FK and person-check steps as §4.
   - Replace three checks:
     - `action_event_actor_kind_check` becomes `IN ('SYSTEM','USER')`;
     - `action_event_actor_id_check` becomes `^service:[a-z0-9-]+$` OR `^person:[0-9a-f-]{36}$`;
     - `action_event_source_channel_check` keeps the current channels and adds `PERSON_API`.

     Assert each current definition before dropping it. The downgrade re-adds the 0016/0019 texts under the same
     names, so 0019's own downgrade still finds them.
   - Add `action_event_person_coupling` (R8):
     - SYSTEM rows keep a `service:` ID and today's channels;
     - USER rows have a `person:` ID, `PERSON_API`, an event in (ACCEPT, APPLY, OBSERVE, and APPLY's FAILED
       outcome), and `authorization_basis ~ '^PERSON_ROLE:[A-Z_]+$'`.
   - `action_event_evaluator_job` is unchanged.
2. **The grant scope stays** (R3, D-3C1.11). On the person path, the demo grant file still decides:
   - which Findings and Actions a command may touch, with the same 404s and 403 `SYSTEM_DEMO_CAPABILITY_DENIED`;
   - `triggering_fixture`, taken from `granted.fixture_id`.

   The person replaces only the actor, the channel and the basis.
3. **Digest** (R2). On the person path only, `actor_id` joins the accept, observe and apply payload digests. A second
   person repeating Peter's accept therefore gets 409 `ACTION_ACCEPTANCE_CONFLICT` or `IDEMPOTENCY_KEY_CONFLICT`,
   never a replay of Peter's event. SYSTEM digests are unchanged.
4. **Store** (P3). `_insert_event` takes the actor from the port, through all four writes: accept, observe, APPLIED
   and FAILED. A FAILED event on the person path is the person's act. `person_id` is **not** added to `EVENT_COLUMNS`,
   so event reads stay byte-equal.
5. **Labels** (R7). `event_wire`'s `label`, the observe note and the apply statement come from `actor_kind`:
   - SYSTEM rows keep today's text, byte for byte;
   - USER rows read "Recorded by a signed-in person", with no name (3C2 adds names).

**Tests without a database** (`backend/tests/test_3c1b_person_actions.py`). Build the router directly. For each of the
3 commands:
- a person with a listed role is admitted;
- a person without one gets 403;
- a SITE_MANAGER of another Site gets 403;
- another tenant gets the route's 404;
- a body carrying `actor` gets 422;
- a Finding outside the grant gets the same 404 or 403 as today;
- a second person's identical accept gets 409;
- the USER label has the stated wording.

**Postgres tests** (`backend/tests/test_3c1b_person_actions_postgres.py`):
- the constraints and the coupling, each failing on a planted row;
- through `create_app`, an accept and an apply stored under the person, with `triggering_fixture` set;
- the upgrade refusal and the downgrade.

**Regression (must pass unchanged).**
- Without a database: `test_s6_action_rule.py`.
- Pooled: `test_s6_action_store_postgres.py`, `test_s6_action_apply_postgres.py`,
  `test_s6_verification_plan_postgres.py`, `test_s6_action_records_postgres.py`,
  `test_out_e3_trial_comparison_postgres.py`, `test_polish_pa1_trial_history_postgres.py`, `test_pg_harness.py`.

## 6. Commands (per unit)

```bash
env -u DATABASE_URL $PY -m pytest <the unit's no-database file and its no-database regression files> -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh --db -- $PY -m pytest <the unit's Postgres file and its pooled regression files> -q
pwsh -NoProfile -File tools/check-all.ps1
python3 tools/select-tests.py --base main      # "full": not run while building; the merge's full tier runs it
```

## 7. Done (questions, per unit)

1. With a person signed in, is every command of the unit recorded under that person and authorised by their role?
   Is no actor taken from the browser, and is no write opened past a feature switch or the grant scope?
2. Is a person without the role, at another Site, or of another tenant refused with the stated codes?
3. Does the same person's retry replay, and is a second person's use of the same key refused?
4. With no person and the switch off, is every existing test green and every stored byte as today?
5. Does the database refuse a USER row without a person, a mismatched `actor_id`, and a person of another tenant?
6. Is nothing changed outside §4's or §5's files, the words, the tests, the packet and the finish bookkeeping?

## 8. Out of scope

- Turning the switch on (`3C0b`, after both units).
- Names in reads (`3C2`, `3C3`).
- Verification, financial and decision writes (D-3C1.3).
