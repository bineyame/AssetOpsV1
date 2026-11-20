# 3C1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, at `2f5f2ce3c`. Read: `spec.md`, `rulings.md`, `reviewer-guide.md`,
`decision-loop-specification.md` §8, 3C0a's `principal.py`, `model.py`, `service.py`, `composition.py` and migration
0062; checked against the three routers, `actions/service.py`, `actions/lifecycle.py`, the action store adapter,
`work/model.py`, `work/service.py`, `work/domain_intent.py`, `work/domain_action.py`, `work/operational_entry.py`,
`main.py` and migrations 0016, 0019, 0027, 0033, 0035 and 0044. The constraint list in P1 comes from `pg_constraint` on
`assetops_test` at head `0062_operator_accounts`: a read-only SELECT through `tools/heavy-slot.sh --db`.

**The Architect's expected questions.** All are real:
- the constraint names: P1;
- apply and the executive: R5(a). The answer is no;
- the demo grant file: R3;
- observe and the field technician: R5(b);
- the command hash: R1, R2;
- the split: P10;
- how `accounts` reaches the routers: P6.

Severity: **High** blocks coding until answered. **Medium** changes what is built or tested. **Low** is a wording or
coverage fix. **(done)** marks a question whose answer changes what counts as done.

- **R1 (High, done). §2, D-3C1.4: the session ID would go into the command hash, and "two commands" is not what
  happens.**
  - *Evidence.* The hashed actor is `{kind, id, attestation}` (`work/model.py:265-267`), and domain commands use the
    same canonical (`work/domain_action.py:438-443`). §2 makes the attestation `person=…;session=…;role=…`.
    Idempotency keys are unique per Site or per case, not per actor: `work_case_create_once`, `work_event_once`,
    `maintenance_plan_once` and `operational_record_once` (`0027:31,112,141,192`), and `domain_action_once` (`0033:59`).
    A retry is matched by key, and a different hash is refused (`work/service.py:127-130,186-189`).
  - *Why it matters.* The same person retrying the same command after signing in again, or after a grant change,
    gets `WORK_EVENT_DUPLICATE_KEY` 409 instead of the 200 replay. A second person sending the same body (same key)
    is also refused 409. They do not get "two commands", as D-3C1.4 says.
  - *Proposed.* On the person path, the hashed actor is `{kind: "USER", id: "person:<uuid>"}`. The stored
    attestation keeps the session and role, but they stay out of the hash. `Actor.canonical()` for SERVICE is
    unchanged, so every existing hash stays byte-identical. Reword D-3C1.4: the same key from another person is
    refused 409 with the route's duplicate-key code, and different keys are two commands, as today. Tests:
    - one person, two sessions, same body: 200 replay;
    - a second person, same key: 409.

- **R2 (Medium, done). D-3C1.4 does not hold for trial actions: their digest leaves out the actor.**
  - *Evidence.* The accept, observe and apply payloads hash only the command fields (`actions/service.py:395-401,
    469-471, 510-513`). Replay is matched by recommendation key (`:402-404`) or by idempotency key (`:472-475`).
  - *Why it matters.* If Halima sends the same accept that Peter already sent, she gets 200 `replayed` with Peter's
    event. She is told it is recorded, and nothing is recorded under her.
  - *Proposed.* On the person path only, add `actor_id` to the payload digest. A second person then gets 409
    `ACTION_ACCEPTANCE_CONFLICT` or `IDEMPOTENCY_KEY_CONFLICT`. SYSTEM digests are unchanged. The other choice is to
    rule that action replays ignore the actor, and say so in D-3C1.4.

- **R3 (High, done). §2 "the demo grant file does not apply": that file also scopes the records and supplies a
  NOT NULL column.**
  - *Evidence.*
    - The capability allows a command only on Findings listed in the fixture's records (`actions/capability.py:1-9`).
    - `triggering_fixture` is NOT NULL, 1 to 128 characters (`0016:138`). It is written from `granted.fixture_id`
      (`actions/service.py:429, 486, 538`; `postgres_action_store.py:491-506`).
    - `authorize_accept` and `authorize_action` also give the Finding and Action 404s (`actions/service.py:271-285`).
  - *Why it matters.* If the person path skips the grant, three things follow:
    - a signed-in Site manager can accept the reserve trial on any Finding the rule evaluates, not only the fixture's;
    - the row has no fixture value;
    - the 404 order changes.
  - *Proposed.* The person path keeps the 404s and the record-membership check, and takes `fixture_id` from it. It
    replaces only the actor, the channel and the basis. The refusal stays 403 `SYSTEM_DEMO_CAPABILITY_DENIED`. The
    other choice is to make `triggering_fixture` nullable for USER rows and rule what a person may act on. That
    widens 3C1.

- **R4 (High, done). §2 and §6 name columns that do not exist.**
  - *Evidence.*
    - The three domain tables have `actor_kind`, `actor_id` and `attestation`, but no `authorization_basis`
      (`0033:31-36`; `work/domain_intent.py:41-42`).
    - `action_event` has `authorization_basis`, but no `attestation` (`0016:122-160`).
  - *Why it matters.* §6's Postgres test ("each row carries … the §2 attestation and basis") cannot pass for domain
    actions or trial actions as written.
  - *Proposed.* Add no columns. Domain rows carry the role only inside the attestation. Action events carry
    `PERSON_ROLE:<role>` only in `authorization_basis`. Amend §2 and §6 to say so per table. The other choice is to
    add the columns in 0064. That adds two more widenings and more downgrade text.

- **R5 (Medium, done). §3 against the design's people (§8 "Who may do what").**
  - (a) *Apply and the executive.* The design gives "Apply a setting change; assign work" to the site manager only.
    Leave the executive out, as §3 does.
  - (b) *Observe and the field technician.* "Record readings, dips, completion" is the field technician's row and
    nobody else's. §3 adds SITE_MANAGER to `action.observe`, `work.maintenance_record`, `work.operational_record` and
    `work.operational_entry`. That widens §8. Either label it as a deviation in D-3C1.2 with its reason, or drop it.
    The observe note (`DEMO_REVIEW_NOTE`) is a review note, not a reading, so SITE_MANAGER is defensible there.
  - (c) *`work.case_event` is one key for six kinds* (`work/model.py:125`). COMPLETE is "completion", which belongs
    to the field technician, but §3 gives the route to SITE_MANAGER only. Musa could record a maintenance record but
    could not complete the request. Proposed: key by event kind. `work.case_event.COMPLETE` and
    `work.case_event.COMMENT` admit SITE_MANAGER and FIELD_TECHNICIAN; the other kinds admit SITE_MANAGER.
  - (d) *Domain actions.* `domain.create` admits FINANCE_AND_COMMERCIAL_LEAD, but `domain.intent` does not. Joseph
    could create an Action and could not declare its intent. Proposed: `domain.intent` follows `domain.create`, and
    `domain.case_link` (linking work) stays SITE_MANAGER.
  - (e) *Site binding.* Only SITE_MANAGER grants are tied to a Site (`0062:75`; `accounts/model.py:44-48`). The field
    technician and the finance lead therefore act at every Site of their tenant. Say so in §2.

- **R6 (High, done). §1 "today's behaviour is unchanged" covers only requests with no person. A signed-in person
  gets writes that are closed today, before 3C0b.**
  - *Evidence.* Sign-in is already live (3C0a). The product composition injects no work or domain principal, so a
    write there is 403 (`main.py:651-652, 668`). The entry route is open only when `ASSETOPS_OPERATIONAL_ENTRY=on`
    (`host/lab_app.py:61-86`). Trial commands need the grant file (R3).
  - *Why it matters.* Once 3C1 merges, any onboarded person can write work, domain and trial commands in the product
    composition, with the switch off. For the operational entry, that is past a feature switch that is off. The
    reviewer guide's Risks name only `3C0b`.
  - *Proposed.*
    - State in §1 that the person path is live as soon as 3C1 merges.
    - On the entry route, keep the feature switch for people too: with no entry principal composed, a person also
      gets 403 `WORK_WRITE_FORBIDDEN`.
    - Keep R3's record scope for trial actions.

- **R7 (Medium, done). Reads would call a person's act a "SYSTEM demonstration".**
  - *Evidence.*
    - `event_wire` sets `label` to `SYSTEM_DEMO.label` on every event (`actions/service.py:221-228`).
    - The observe response says "A state-neutral SYSTEM demonstration note" (`:491`).
    - The apply note and change statement say SYSTEM demonstration (`:534-535, :594`).
  - *Why it matters.* The provenance of a person's event would be wrong. §5 says "no change to reads".
  - *Proposed.* Take the label and statements from `actor_kind`: SYSTEM rows keep today's text byte for byte, and
    USER rows get neutral text with no name (3C2 adds names). The other choice is to rule that these stay until 3C3,
    and record it as a known gap.

- **R8 (Medium, done). §4: the CHECK does not tie `actor_id` to `person_id`.**
  - *Why it matters.* `(actor_kind='USER') = (person_id IS NOT NULL)` would admit `actor_id = person:A` with
    `person_id = B`.
  - *Proposed.* `<t>_person_actor CHECK ((actor_kind = 'USER') = (person_id IS NOT NULL) AND (person_id IS NULL OR
    actor_id = 'person:' || person_id::text))` on all ten tables. On `action_event`, one coupling CHECK:
    - SYSTEM rows have a `service:` ID and today's channels;
    - USER rows have a `person:` ID, `PERSON_API`, a command in (ACCEPT, APPLY, OBSERVE), and
      `authorization_basis ~ '^PERSON_ROLE:[A-Z_]+$'`.

- **R9 (Medium, done). §2: the refusal codes, as named, do not match today's envelopes.**
  - *Evidence.*
    - Work refusals carry `{code, message}` and no field (`work_api.py:61-63`; `WorkRefused(code)`).
    - The domain routes refuse a bad body shape with `DOMAIN_INTENT_INVALID` (`work/domain_intent.py:80`), not
      `WORK_INPUT_INVALID`.
    - The trial-action route answers an unknown Site with a plain-string 404 detail and no code (`action_api.py:76-78`).
  - *Proposed.*
    - Each route refuses a client actor with its own existing shape-refusal code, and no field is added.
    - A cross-tenant person's 404 is byte-equal to that route's unknown-Site 404.
    - Tests compare the whole body.

- **R10 (Medium). §2 step 1 and §2.4: when no account service is composed, and when the switch is read.**
  - *Evidence.* `accounts` is None when no `DATABASE_URL` is set and none is injected (`main.py:348-349`).
    `person_from_request(request, None)` would raise.
  - *Proposed.*
    - When `accounts` is None, there is no person. With the switch on, that is 401 `PERSON_REQUIRED`.
    - `require_person()` is read once in `create_app`, next to `session_cookie_secure()`, and passed to the routers
      as a bool. It is never read per request.

- **R11 (Low). Edge cases worth one line in §2.**
  - An expired or revoked cookie resolves to no person (`accounts/service.py:101-118`). With the switch off, the
    command silently goes down today's path.
  - When a cookie is present and the account store is down, the command answers 503 even with the switch off.
  - The person path could require `application/json`, as the account routes do (`accounts_api.py:60-63`). The cookie
    is `SameSite=Strict` (`:137-139`), so this is extra protection, not a gap.

- **R12 (Low). `mid-build-questions.md` holds DS1b's two questions (count 2).** It is a stale copy. Reset it to the
  empty template with count 0.

## Implementer pre-flight

Pre-flight (Claude, acting as the implementer), against `main` at `2f5f2ce3c`. These are numbered P1, P2 …, not I1,
as the dispatch asked.

- **P1 (Medium, done). The constraints to widen, by name** (`pg_constraint` on `assetops_test` at `0062`). All test
  rows were zero, so the claim that "no USER rows exist" can be checked only on the walkthrough database. I did not
  touch it. 0064's upgrade refusal covers that case.
  - *Widen these:*
    - `action_event_actor_kind_check`: `CHECK (actor_kind = 'SYSTEM')`;
    - `action_event_actor_id_check`: `CHECK (actor_id ~ '^service:[a-z0-9-]+$')`;
    - `action_event_source_channel_check`: `CHECK (source_channel = ANY (ARRAY['SYSTEM_DEMONSTRATION_API','SYSTEM_JOB']))`;
    - `domain_action_actor_kind_check`, `domain_action_intent_actor_kind_check` and
      `domain_action_case_link_actor_kind_check`: `CHECK (actor_kind = 'SERVICE')`.
  - *Leave these as they are:*
    - every `<t>_actor_id_check`, `<t>_attestation_check` and `<t>_authorization_basis_check`. They are length bounds
      of 1-128, 1-1000 and 1-500, and §2's forms fit: the actor ID is 43 characters, the basis at most 37, and the
      attestation about 140;
    - `action_event_authorization_basis_check` (1-500);
    - `action_event_evaluator_job`: for PERSON_API rows both sides are false, and the plan and outcome are NULL, so
      it passes unchanged;
    - the seven W4 `<t>_actor_kind_check`, which already admit `USER`.
  - *Method.* Drop and re-add them by name, but first assert that each name has today's definition, using the
    `pg_get_constraintdef` discovery precedent (`0035:32-47`). The downgrade re-adds the exact 0016, 0019 and 0033
    definitions under the same names, so that 0019's own downgrade (`0019:274-282`) still finds them.

- **P2 (Medium). Migration safety on the ten tables.**
  - `ADD COLUMN person_id uuid NULL` with no default changes only the catalog. The append-only triggers are
    row-level BEFORE UPDATE OR DELETE (`0027:198-208`, `0033`), so no trigger fires.
  - The chain triggers are statement-level and do not depend on columns (`0044:90-100`).
  - ADD CHECK and ADD FOREIGN KEY validate by a scan. Existing rows pass, because both sides are false.
  - The FK target `operator_account (tenant_id, id)` is UNIQUE (`0062:37`). Constraint names stay under 63 bytes
    (the longest is `domain_action_case_link_person_actor`).
  - Proposed: `LOCK TABLE … IN ACCESS EXCLUSIVE MODE`, child first, before the USER-row probe (the 0033 downgrade
    precedent), so the probe and the ALTERs see the same rows.
  - *Reads stay byte-equal only if the read column lists are untouched.* The work adapter lists its columns
    (`postgres_work_store.py:33-37`). Its `SELECT *` sites are inside LATERAL subqueries with explicit outer lists
    (`postgres_global_read.py:52,65,78`; `postgres_fuel_records.py:28`), and the lineage body picks named keys
    (`work/service.py:555-563`). But `EVENT_COLUMNS` (`postgres_action_store.py:57-60`) feeds `event_wire`, which
    serialises the whole row. Do not add `person_id` to `EVENT_COLUMNS`, or every event read gains
    `"person_id": null`.
  - Raw-insert tests leave out `person_id` and stay valid: `test_w502_domain_action_index_postgres.py:46-49`,
    `test_k6a_fuel_action_origin_postgres.py:208,232` and `test_polish_pa1_trial_history_postgres.py:34-37`.

- **P3 (Medium). The trial-action store hard-codes the actor.**
  - `_insert_event` writes `SYSTEM_DEMO`'s kind, ID, channel and basis (`postgres_action_store.py:491-506`).
  - The actor has to be passed through the port and the adapter into four writes: accept (`:278-350`), observe
    (`:353`), APPLIED (`:430-440`) and FAILED (`:463-489`).
  - A FAILED event on the person path is the person's act too.
  - The `action` root row has no actor columns, so it needs no change.

- **P4 (Medium, done). Work and domain bodies require `actor`.**
  - `actor` is a required key in every closed shape (`work/service.py:25-36`; `domain_action.py:301,380,408`), and
    `_actor` reads `body["actor"]` (`work/service.py:120-121`; `domain_intent.py:32-33`).
  - The person path needs the same shapes without `actor`, a key present means 422 (R9), the actor is built by the
    server, and R1 says how it is hashed.
  - Today's `authorize()` refusal of a USER actor (`work/model.py:281-282`) must stay as it is. It is pinned by
    `test_w401_work_service_postgres.py:224` and `test_w502_domain_intent_postgres.py:177`.
  - A case create writes three rows (`work_case`, `work_case_revision`, `work_event`; `work/service.py:199-216`), and
    each one needs `person_id`.

- **P5 (Medium). The operational entry.**
  - `compose_entry` puts `ENTRY_ACTOR` into the body (`operational_entry.py:27,128`), and the entry principal is
    checked before the body (`work_api.py:200-203`).
  - The person path composes the entry without `actor`. Per R6, it keeps the entry-principal check as the feature
    switch.

- **P6 (Medium). How `accounts` reaches the routers.**
  - The work and domain routers share `WorkGate` (`work_api.py:66-104`), and `main.py:669-672` builds the domain
    router's gate inline. Proposed: put `accounts`, the switch bool and the account store's unavailable types on
    `WorkGate`, so that W4 and domain have one person step. Give `build_action_router` the same three as keyword
    arguments. Put one `person_step(...)` helper in `accounts/permissions.py`.
  - The account store raises `ACCOUNTS_UNAVAILABLE` (`accounts/composition.py:12-13`). No router's `down` tuple has
    it, so without it a store error is a raw 500, not §2's 503.
  - All the new keywords default to None or off, so the existing direct callers stay unchanged:
    - ten test files;
    - `tools/w502_cold_work_walkthrough.py` and `tools/w504_ev_work_walkthrough.py`;
    - `global_work_api.py`, which uses `WorkGate`.

- **P7 (Medium, done). §6's no-database tests cannot run through `create_app`.**
  - `create_app` has no parameter to inject a work, domain or action service (`main.py:238-268`). It builds them only
    from `DATABASE_URL`.
  - Without a database, the Site scope answers 404 or 503 before any person step (`test_w502_domain_intent_api.py:125-132`).
  - Proposed: the no-database file builds the three routers directly with fakes, as `test_w401_work_api.py:37-64`
    and `test_own_g3_operational_entry.py:181` do, together with the 3C0a in-memory `AccountService`. The Postgres
    file proves the `create_app` wiring, for at least one command per router.

- **P8 (Low). The `main.py` collision with 3B1.**
  - 3B1 adds one call and one import at the top of `create_app` (3B1 spec §5). 3C1 reads the switch near
    `main.py:348-351` and adds keywords at `:623-675`.
  - The change is textual only, and both raise `ConfigurationError` at start-up.
  - Merge `main` before review, as the spec says, and re-run `test_3c0a_accounts_api.py` and the 3B1 start-up test
    after the merge.

- **P9 (Low). Tests must run the worktree's own packages.**
  - The `.venv` editable finders are appended to `sys.meta_path`, so `PYTHONPATH` wins, and §0's check prints the
    proof.
  - `pg_harness` migrates from `Path(__file__).parents[1]` (`pg_harness.py:61,139`), so a run from the worktree
    builds its template with the worktree's 0064.
  - `heavy-slot.sh` passes the environment through, apart from `GIT_*` (`heavy-slot.sh:68`).
  - Run from the worktree as the working directory, with that tree's `tools/heavy-slot.sh`.

- **P10 (Medium). The estimate is about 5 units, not 3.** Rule the split (D-3C1.7) now.
  - The work:
    - (1) migration 0064, with the discovery step, the refusals and the downgrade, plus the schema tests;
    - (2) `permissions.py`, `principal.py`, the switch, the person step on `WorkGate` and the action router, the
      `main.py` wiring and the no-database router tests;
    - (3) the person variants of the work service (six commands and the entry) and the domain service (three), with
      the hash rule;
    - (4) the trial-action service, the port and the adapter: the actor through four writes, the fixture scope (R3),
      the read labels (R7) and the `action_event` coupling CHECK;
    - (5) the end-to-end Postgres tests.
  - Proposed:
    - **3C1a**: work and domain commands, ten commands on nine tables, 3 units;
    - **3C1b**: trial actions, three commands on `action_event`, 2 units.
  - Split 0064 the same way. R2, R3 and R7 then stop only 3C1b. `3C0b` must wait for both, because the switch must
    not refuse unsigned trial actions while their person path does not exist.

**Highs:** R1, R3, R4, R6.
