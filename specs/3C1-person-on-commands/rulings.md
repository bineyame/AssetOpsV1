# 3C1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-8.md`. Handshake
answers go below, under "Handshake answers (round 1)".

## D-3C1.1 The person path is added beside today's path, behind one switch

- **Ruling.**
  - When a person is signed in, the command goes through the person path.
  - When no one is signed in, the command goes through today's path, unless `ASSETOPS_REQUIRE_PERSON=on`.
  - The switch ships off. `3C0b` turns it on.
- **Why.** D-BW1.3 holds the refusal until the sign-in page exists. A switch built and tested now makes `3C0b` a
  configuration change, not new code.

## D-3C1.2 Role per command is one literal table

- **Ruling.** `COMMAND_ROLES` maps each command to its roles, taken from `decision-loop-specification.md` §8. A
  Site manager's grant counts only for its own Site.
- **Why.** The design's permission table is the source. One table makes it configurable by role later, as the owner
  asked on 20 Nov (item 5), with no code spread across routes.
- **Owner's view welcome.** Whether a field technician may raise a work case. The default is yes: incidents are found
  in the field.

## D-3C1.3 Verification, financial and decision writes keep their paths

- **Ruling.** Verification steps, price entry and the mini, cold and EV decision writes are not in 3C1.
- **Why.**
  - Verification steps are the system's own work until the three verdicts (`8a`). The design says the system records,
    and a person does not.
  - Price entry is a setting, which needs step 7b's thresholds.
  - Decision writes are rebuilt in `6a`, on the new decision records.
  - Changing them now would be changed twice.

## D-3C1.4 The person is in the command's identity

- **Ruling.** The actor stays in the command hash.
- **Why.** Two people sending the same body are two commands, each recorded under its person. Merging them would hide
  one person's act.

## D-3C1.5 `USER` is the person's actor kind everywhere

- **Ruling.** The actor kind is `USER`, with `person_id` and `actor_id` `person:<uuid>`. The database enforces that
  `USER` holds exactly when `person_id` is set.
- **Why.** The W4 and decision tables already use `USER`. One word across tables keeps reads simple, and the
  constraint makes it impossible to record a "user" without a person.

## D-3C1.6 A cross-tenant person sees "not found"

- **Ruling.** A signed-in person of another tenant gets the route's not-found answer.
- **Why.** It is the same answer as for a Site that does not exist, so the answer reveals nothing about another
  operator's Sites (the 3C0a isolation rule).

## D-3C1.7 The split if the handshake grows it

- **Ruling.** If the pre-flight finds more than 4 units of work, the slice splits:
  - `3C1a`: work and domain commands;
  - `3C1b`: trial actions.
  The migration splits the same way.
- **Why.** W4 sets a limit of 6 units. The action tables carry the strictest CHECKs, so they are the part most likely
  to grow.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling.

**The Highs**
- **R1: adopted.** The hashed actor is the kind and the person only; the session and the role stay out of the hash.
  D-3C1.4 is corrected below (D-3C1.8).
- **R3: adopted, as proposed.** The demo grant file's record scope, its 404s and `triggering_fixture` stay on the
  person path. The person replaces only the actor, the channel and the basis (D-3C1.11).
- **R4: adopted.** No columns are added beyond `person_id`:
  - domain rows carry the role inside the attestation;
  - action events carry it in `authorization_basis`;
  - spec §2 gives the table per family.
- **R6: adopted, strictly** (D-3C1.12):
  - the gates' feature switches still apply to people;
  - the entry switch still applies;
  - the grant scope still applies to trial actions;
  - spec §1 says the person path is live as each unit merges.

**The rest**
- **R2: adopted.** On the person path, `actor_id` joins the trial-action digests.
- **R5:**
  - (a) adopted: the executive does not apply.
  - (b) a SITE_MANAGER may record readings and completions. This is labelled a design deviation (D-3C1.10).
  - (c) `case_event` roles are keyed by event kind: COMPLETE and COMMENT also admit the field technician.
  - (d) `domain.intent` follows `domain.create`.
  - (e) stated in §2: only Site managers are bound to a Site.
- **R7: adopted.** Labels and statements come from `actor_kind`. SYSTEM rows stay byte-equal; USER rows get neutral
  text.
- **R8: adopted.** `actor_id` is coupled to `person_id` on every table, and `action_event` gets one coupling check.
- **R9: adopted.** Each route uses its own existing codes, with no field added. A cross-tenant 404 is byte-equal to
  the route's unknown-Site 404.
- **R10: adopted.** With `accounts` None there is no person. The switch is read once in `create_app`.
- **R11: adopted, with one change.** No `application/json` requirement on the person path: today's shapes and the
  `SameSite=Strict` cookie suffice, and adding it would change today's routes.
- **R12: done.** `mid-build-questions.md` is reset.
- **P1: adopted.** The named constraints are discovered with an asserted definition, and the downgrade restores the
  exact texts.
- **P2: adopted.** Lock first. `person_id` stays out of `EVENT_COLUMNS` and the read lists.
- **P3: adopted.**
- **P4: adopted.**
- **P5: adopted.**
- **P6: adopted.** `WorkGate` carries the person-step inputs. The action router gets keyword arguments. All of them
  default to off.
- **P7: adopted.** The routers are tested directly; `create_app` wiring is proven in the Postgres files.
- **P8: adopted.**
- **P9: adopted.**
- **P10: adopted.** The split is ruled now: 3C1a is 3 units, 3C1b is 2. `plan_model.py` is re-run. `3C0b` depends on
  both (D-3C1.13).

**Open after round 1:** none.

## D-3C1.8 Hash identity is the person, not the session (corrects D-3C1.4)

- **Ruling.** As R1. Idempotency keys stay unique per Site or per case. A second person reusing a key gets the
  duplicate-key 409.
- **Why.** Putting the session in the hash would refuse a person's own retry after signing in again. And two people
  are not "two commands" when the key is shared, so D-3C1.4's claim was wrong.

## D-3C1.9 Each route keeps its own refusal codes and envelopes

- **Ruling.** As R9.
- **Why.** Existing clients and tests read those envelopes. A person path that answers in a different shape would be a
  second contract on the same route.

## D-3C1.10 Design deviation: the site manager may record readings and completions

- **Ruling.** `observe`, maintenance records, operational records, the operational entry and a case's COMPLETE and
  COMMENT events admit SITE_MANAGER as well as FIELD_TECHNICIAN. §8 of the design gives "record readings, dips,
  completion" to the field technician only.
- **Why.** At small Sites the manager often records the reading. The figures are unaffected, and the record still
  names who did it. The owner may narrow this; it is one table (item 5: "configurable by role").

## D-3C1.11 The trial-action grant scope stays on the person path

- **Ruling.** As R3.
- **Why.** The grant file is what limits trial actions to the fixture's Findings and supplies `triggering_fixture`.
  Dropping it would open trial actions on any Finding, which is a scope decision for step 6, not this unit.

## D-3C1.12 The person path opens no write that is closed today

- **Ruling.** Feature switches and gates still apply to signed-in people.
- **Why.** Sign-in is live (3C0a). Without this, any onboarded person could write where today's composition writes
  nothing. That is a security change no slice has approved.

## D-3C1.13 The split, and 3C0b's dependency

- **Ruling.** `3C1a` (work and domain, 3 units) comes first; `3C1b` (trial actions, 2 units) follows. `3C0b` depends on
  both.
- **Why.** The work was about 5 units, and the trial-action part carries the R2, R3 and R7 changes. `3C0b`'s switch
  would otherwise refuse unsigned trial actions that have no person path.

## Mid-build answers

### Q1 (3C1a, §4 regression list): two older migration tests assume their own migration is head

- **Ruling.** Yes, 3C1a edits exactly these two tests, and no others. "Must pass unchanged" in §4 means no assertion
  is weakened or removed; it does not forbid fixing a test that measures "head" as if its own migration were head,
  when the spec's required FK and column make that reading false. The other 12 swept files stay untouched.
- **`test_3c0a_accounts_postgres.py::test_downgrade_refused_with_an_account_then_down_and_up`.** Change the one
  statement to `TRUNCATE <same TABLES list> CASCADE`. Not "downgrade to 0062 first": that would run 0063's downgrade
  (and its refusal) inside a test about 0062's refusal. TRUNCATE does not fire the append-only triggers, and the
  referencing tables (`work_case` and the other eight) are empty in the test DB, so CASCADE removes no rows the test
  relies on. Every assertion stays as written.
- **`test_k2_fuel_records_postgres.py::test_migration_up_down_up_on_empty_table`.** Keep `up = shape(engine)` as the
  head-shape and assert it as now, then:
  1. before the first downgrade, `command.downgrade(config, MIGRATION)` and take `at_k2 = shape(engine)`;
  2. `command.downgrade(config, PREVIOUS)`; compute every `cols - cols_down`, `indexes - indexes_down` and
     `set(defs) - set(defs_down)` assertion from `at_k2`, not `up`; the expected sets are unchanged;
  3. `command.upgrade(config, "head")` and keep the final `assert shape(engine) == up`, which still proves
     down-and-up is lossless at head.
  The test now says "k2's migration adds exactly these", true at any later head, and no assertion is loosened.
- **Class and sweep.** A migration test must compare at its own revision, never at head. The builder's 14-file sweep
  is the sweep; record in the packet that both files were edited, why, and that §4's list otherwise ran unchanged.
  Add this to the reviewer guide as a checked item: no other test file in the diff.
