# 3C1b packet: the signed-in person on trial actions

Implementer (Claude), 2026-11-21. Branch `task/3C1b-person-actions`, worktree `/opt/assetecon/AssetOpsV1-3c1b`, base
`main` `28263c47b`. Not merged. Owner-away filler (`specs/OWNER-AWAY/decisions-2026-11-21.md` row 10).
`USER_REVIEW_REQUIRED`: false; D-3C1.10 (the site manager may observe) is already ruled.

## Commits

- `8e6e0e86d` person step on accept/apply/observe, `PersonEventActor`, store actor through all four writes,
  migration `0070_person_on_actions`, both test files, the 3C1a role-table test rows, pre-flight questions.
- `52ad95110` Postgres test fixes (the other-tenant person takes a Site-free role; assertion text).
- Docs commit: this packet, spec status, `specs/INDEX.md`, state entry and index line.

## Pre-flight (mid-build-questions.md, count 3 for 3C1b)

§5 fits `main` except: **Q-3C1b-1** (USER label wording vs D-SC1.28), **Q-3C1b-2** (three SYSTEM wordings §5.5 does
not name), **Q-3C1b-3** (no harness composes Actions in `create_app`). Each is built on its proposed default.

## Text rule D-SC1.28: which applies

Both: refusals use **existing codes and keys only** (`PERSON_REQUIRED`/`person.person_required`,
`PERSON_ROLE_REQUIRED`/`person.person_role_required`, `CLIENT_AUTHORITY_FORBIDDEN`, `ACTION_STORE_UNAVAILABLE`, the
route's unknown-Site 404). No catalogue key, constant or f-string sentence is added. **Pending statements** for the
SC-1 text commit after SC-1a (served as `null` until then; tests assert `null`, never words):
1. event `actor.label` for a USER row: "Recorded by a signed-in person" (spec §5.5);
2. the observe `statement` for a person's note;
3. the change artifact's `label` and `statement` for a person's apply;
4. (Q-3C1b-2, unchanged now) the Action read `action.label`, the stored Foundation publish note ("SYSTEM demonstration
   application of reserve-trial-1"), and the `CLIENT_AUTHORITY_FORBIDDEN` sentence.

## Migration number

`0070_person_on_actions`, **provisional**: `down_revision = "0066_structure_snapshot"` (head on `main`); 3A6 (0067),
3A7 (0068) and 3C2 hold numbers ahead. Self-contained: messages are built from `revision`; the tests glob
`*_person_on_actions.py` and read both ids from the module. Renumber at merge = file name, `revision`,
`down_revision`, and the state line.

## Done (spec §7)

| # | Answer | Proof (`test_3c1b_person_actions*.py`) |
|---|---|---|
| 1 | Yes: the three commands run `person_step` after open scope, before the 404/grant 403; actor, channel `PERSON_API`, basis `PERSON_ROLE:<role>` composed by the server; grant scope and `triggering_fixture` kept (R3) | `…listed_role_is_recorded…`, `…outside_the_grant…`, pg `…stored_under_the_person` |
| 2 | Yes: 403 `PERSON_ROLE_REQUIRED` + `params.roles`; other Site 403; other tenant = unknown-Site 404 byte for byte | `…without_a_listed_role…`, `…another_site…`, `…another_tenant…`; pg `create_app` probe |
| 3 | Yes: same person, new session, 200; a second person's identical accept 409 `ACTION_ACCEPTANCE_CONFLICT`, apply/observe key 409 `IDEMPOTENCY_KEY_CONFLICT` (R2) | `…second_persons…` (3 commands), pg |
| 4 | Yes: unsigned path stores SYSTEM bytes, digest without `actor_id`, store called without `actor` | `…switch_off…`, regression below |
| 5 | Yes: USER without person, person on SYSTEM, mismatched id, wrong channel/basis, SYSTEM on `PERSON_API`, bad id, other-tenant FK each fail | pg `test_each_planted_actor_fails_on_its_constraint` |
| 6 | Yes, plus one existing test edited (below) | `git diff --stat 28263c47b..HEAD` |

Order on the action routes: access, unknown Site 404, store 503, account-store 503, 401 (switch on), tenant 404,
role 403, then today's Finding/Action 404, grant 403, body 422. The step runs `enabled=True`: a trial action's feature
gate is its grant, checked next by the service (D-3C1.11, D-3C1.12). Verification routes stay SYSTEM (D-3C1.3).

## Existing test edited (class: a literal table equality)

`test_3c1a_person_work.py`: `SPEC_ROLES` gains the three `action.*` rows (as 3A2 added its `commercial.*` rows), and
line 482 excludes `action.` keys from the work-command set. No assertion removed. No other existing test changed.

## Known deviations

- Q-3C1b-3: the person accept, apply (APPLIED and FAILED) and observe are stored through the real router over the
  real `PostgresActionStore`, S1 publish and Postgres account store; `create_app` is proved to pass the person inputs
  (401 with the switch on, other-tenant 404, signed person reaching the service's 404), not a full accept inside it.
- Q-3C1b-2: the stored publish note on a person's apply still says "SYSTEM demonstration"; flagged for SC-1/3C2.
- `change()` (GET a change artifact) now reads the Action's events once to find the APPLIED event's actor kind.

## Checks

Evidence `/opt/assetecon/evidence/3C1b/run1/` (logs). Module paths (`modpaths.txt`): `assetops_backend`,
`assetops_contracts` and `fixtures` resolve to `/opt/assetecon/AssetOpsV1-3c1b`.

- **No database** at `8e6e0e86d`: `test_3c1b_person_actions.py` + `test_s6_action_rule.py`, `test_3c1a_person_work.py`,
  `test_3c0a_accounts_api.py`, `test_w401_work_api.py`, `test_w502_domain_intent_api.py`,
  `test_own_g3_operational_entry.py`: **322 passed, 16 skipped**, 34.8 s (`nodb-regression.log`).
- **Postgres new file** at `52ad95110`: **5 passed** (18 s; 11 min wall waiting for the db slot) (`pg-new2.log`).
- **Pooled** at `52ad95110` (`heavy-slot.sh --db` + `run-host-tests.ps1`, `assetops_test`): the new file, §5's seven
  regression files, 3C1a/3C0a pooled, `test_w502_domain_action_index_postgres.py`, `test_k2_fuel_records_postgres.py`
  and the downgrade sweep over `action_event` (`test_ch3_lifecycle`, `test_w401_migration`, `test_w504_ev_intent`):
  **112 passed, 0 failed**, 414 s (15.5 min wall) (`pg-pooled.log`).
- **Plants**, each reverted, tree clean after: no-DB 7/7 caught (`plants-nodb.log`: person step skipped 11 failed,
  store ignores actor 7, `actor_id` out of digest 8, USER gets SYSTEM label 7, tenant as 403 3, apply admits FT 3,
  SYSTEM basis on person 6); DB 3/3 caught (`plants-db.log`: no coupling 3 failed, no `person_id` written 1,
  downgrade keeps the widened channel 1).
- **check-all** (fast, incl. architecture seams, configuration-persistence and agent workflow): **All 40 guards
  passed**, 132 s (`check-all.log`). The persistence guard needed no change.
- Not run: `select-tests.py --base main` full tier (the merge's).

Process note: the first Postgres run (`pg-new.log`, 2 failed) overlapped the no-DB plant script, which edited
`service.py` while it ran (plant N3 made a second person's digest equal); one failure was that, the other a real test
bug (a SITE_MANAGER grant needs a Site), fixed in `52ad95110`. Every later run had the tree unchanged.

## Text commit (D-SC1.28, after SC-1a)

Implementer (Claude), 2026-11-21. `main` merged at `e5a283228` (SC-1a merge `fcb655f2c` is an ancestor) in
`c328a4094`; text commit `8c945689a`; this packet section in the docs commit after it.

**Migration renumbered.** `0071_person_on_actions`, `down_revision = "0068_structure_finding"` (head on `main`).
3A7 holds 0069 and 3C2 holds 0070: at merge preparation `down_revision` is re-pointed to whichever of them has
merged (D-3A1.12). Self-contained as before (messages from `revision`, tests glob the module).

**Statements** (`backend/assetops_backend/i18n/statements/en/action.py`, cases `backend/tests/statement_cases/action.py`).
Each takes `actor` (a `State`, the event's `actor_kind`); every SYSTEM variant is the text `main` served, byte for
byte; every USER variant names no person (3C2 adds names).

| Key | Where it is served | USER text |
|---|---|---|
| `action.actor_label` | event `actor.label`, change `label`, Action read `action.label`, capability `label` | Recorded by a signed-in person |
| `action.observe_note` | observe `statement` | A state-neutral note recorded by a signed-in person; it changes no application or verification state and claims no effect. |
| `action.change_statement` | change artifact `statement` (by the APPLIED event's actor) | The Site Foundation reserve was changed by a signed-in person. No measured effect, saving or verification is claimed. |
| `action.publish_note` | `foundation_revision.change_note` written by apply (stored; rendered in `DEFAULT_LOCALE`); `action_code` and `rule` (`reserve_trial.RULE_ID`) are `Name`s | `<code>: application of reserve-trial-1 by a signed-in person (a policy-sensitivity trial, not a predicted saving)` |
| `action.client_authority_forbidden` | 422 `CLIENT_AUTHORITY_FORBIDDEN` on accept/apply/observe (verification routes stay SYSTEM) | A client cannot name an actor or grant authority; the server records the signed-in person. |
| `action.unknown_site` | the action routes' unknown-Site 404 and the other-tenant person's (one `unknown_site` helper, review L3); `site` is `Name(repr(code))`, so the bytes are today's for every code | (one variant) |

**Q-3C1b-2's merge condition.** The stored publish note follows the actor (USER apply stores the person's note; pg
test reads `change_note`). The Action read's `label` is its ACCEPTED event's actor. The capability block (review L1):
`Capability.wire(recorded)` states the actor the command records **for this caller**: today's SYSTEM actor (no person,
switch off: byte-equal), the signed-in person (`USER`, `person:<id>`, person label), or `null` kind, id and label when
the command would refuse the caller (switch on and nobody, another tenant, no listed role, account store down). The
reads get it from `would_record` (the person step without its answers; a read is never refused by it). The 403
`SYSTEM_DEMO_CAPABILITY_DENIED` block states the command's actor the same way. `allowed` is still the grant's (R3).

**Guard.** `Statement catalogue (SC-1)`: OK, no baseline or allow addition; `--prune` removed five entries the
conversion made stale (`open_scope` 404, `body_of` sentence, `apply.attempt` note, `_change_wire` and `observe`
sentences). The 3C1b modules are not added to `ADOPTED`: `action_api.py`, `service.py` and `capability.py` hold
older baselined text (SC-1b/SC-1c debt), and adopting them would convert text outside this unit.

**Lows.** L1: done for the backend (above); the frontend `SYSTEM_DEMONSTRATION` button words stay (a screen
slice; listed open). L2: the kind clause cannot be reached by a planted row while `action_event_evaluator_job`
stands (it already refuses an evaluator kind off `SYSTEM_JOB`, and Postgres checks it first), so the plant drops that
check inside a rolled-back transaction and a person's RESOLVED row must fail on `action_event_person_coupling`.
L3: done (statement + shared helper).

**Existing tests edited.** `test_sc1_statements.py::test_t8_shipped_catalogue_loads` (a literal key-set equality)
gains the six `action.*` keys. In `test_3c1b_person_actions*.py` the `null` assertions become the wording; the
outside-grant 403 test now compares the bodies without the three actor fields and pins those fields per caller.

**Bookkeeping.** `.ai/state/index-2.md` went over its 8,000-byte cap with both sides' lines, so the 3C1b line moved
to a new `index-3.md` (`INDEX.md` lists it; headers say "of 3").

### Checks (text commit; evidence `/opt/assetecon/evidence/3C1b/text1/`)

- **No database** at `8c945689a`: `test_3c1b_person_actions.py`, `test_sc1_statements.py`, `test_s6_action_rule.py`,
  `test_3c1a_person_work.py`, `test_3c0a_accounts_api.py`: **663 passed** (34 s; one failure on the first run, T8's
  key set, fixed in the same commit before this count).
- **Postgres** at `8c945689a` (`heavy-slot.sh --db`, `assetops_test`): `test_3c1b_person_actions_postgres.py` plus
  §5's pooled regression (`test_s6_action_store`, `_apply`, `_verification_plan`, `_action_records`,
  `test_out_e3_trial_comparison`, `test_polish_pa1_trial_history`, `test_pg_harness`): **61 passed, 0 failed**,
  193 s (6.5 min wall with the slot wait). The log was lost (a shared scratch folder was cleared); the summary line
  is as printed.
- **Plants** (no database; each reverted, tree clean after): 8/8 caught. P1 person label reworded (10 failed), P2
  label ignores the actor (7), P3 publish note always SYSTEM (1), P4 capability ignores the caller (5), P5 authority
  sentence ignores the actor (3), P6 a refusal read as SYSTEM (3), P7 the hand-built 404 back in `open_scope`
  (guard `HAND_BUILT_NEW`), P8 a variant without a case (guard `CASE_MISSING`). The L2 DB plant was not planted
  separately: the copied row differs from an admitted person row only in its kind, so only the kind clause can
  refuse it on the coupling.
