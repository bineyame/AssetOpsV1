# 3C1b review: the signed-in person on trial actions

## Round 1 (discovery, W5): `task/3C1b-person-actions` at `ab993e2e9`

Reviewer (Claude, fresh), 2026-11-21. Diff `main...ab993e2e9` (base `28263c47b`; `main` has gained docs only since).

### Summary

- **Verdict: ACCEPT.** No High or Medium. Three Lows, none blocking; one merge condition on Q-3C1b-2 (below).
- Authority holds: accept, apply and observe run the person step after open scope and before the grant 403 and the
  body; the actor is `USER`/`person:<id>`/`PERSON_API`/`PERSON_ROLE:<role>`, composed by the server; the grant file
  still scopes and supplies `triggering_fixture`; `actor_id` joins the digest only on the person path. My forged
  requests were all refused (below).
- Migration 0070 is self-contained, asserts the three old definitions, restores the exact 0016/0019 texts, and its
  downgrade and the upgrade refusal pass on Postgres. The renumber is mechanical (file name, `revision`,
  `down_revision`, the state line); 3A6, 3A7 and 3C2 do not touch `action_event`.
- The one edited test (`test_3c1a_person_work.py`) weakens nothing: the full-table equality now also covers the three
  `action.*` rows. D-SC1.28: no catalogue key or new sentence is added. One existing literal is duplicated (L3).
- Defaults: **Q-3C1b-1 confirm. Q-3C1b-2 confirm, provided 3C1b merges with (or after) its SC-1 text commit, which
  must also cover the stored publish note and the capability block (L1). Q-3C1b-3 confirm.**

### Findings

**L1 (Low; sweep of the Q-3C1b-2 class, not an acceptance gap).** `backend/assetops_backend/actions/capability.py:35`,
and the frontend's `SYSTEM_DEMONSTRATION` constant (`frontend/src/sites/actionPresentation.tsx:17`, used 8 times in
`SiteRecommendation.tsx`, `SiteAction.tsx`, `SiteFoundationChange.tsx`).
- **What is wrong.** Q-3C1b-2 lists three places that still say "SYSTEM demonstration" on a person's act. There are
  more. `Capability.wire()` (served as `system_demo_capability` on the recommendation and Action reads) states
  `actor_kind: "SYSTEM"`, `actor_id: "service:assetops-action-demonstration"`, `label: "SYSTEM demonstration"` as the
  actor the command will record, which is now false for a signed-in caller. It is a structured claim, not only a
  word. The screens also hard-code "Accept trial (SYSTEM demonstration)", "Apply trial (SYSTEM demonstration)" and
  "SYSTEM demonstration command" on the Foundation change.
- **Why it matters.** The stored record is right (`action_event` names the person), so nothing is misattributed in
  the data. But the screen and the read contract describe the actor as the system. The packet's pending list is the
  hand-off to SC-1/3C2, and it is incomplete.
- **Fix.** Add the capability block's actor fields and the frontend constant to the packet's pending list (item 4).
  No code change in 3C1b: the frontend is out of this non-screen slice, and replacing the words is new text
  (D-SC1.28).

**L2 (Low; test gap).** `backend/tests/test_3c1b_person_actions_postgres.py:189-198`.
- **What is wrong.** The plants cover the coupling's channel and basis clauses, but not its event-kind clause
  (`kind IN ('ACCEPTED','APPLIED','FAILED','OBSERVED')` for USER rows). DB plant D1 drops the whole coupling, so a
  plant that drops only the kind clause would pass every test.
- **Why it matters.** Spec §5.1 makes the kind clause part of R8: a person must not be able to record RESOLVED or
  RESOLUTION_WITHDRAWN, which are the evaluator's.
- **Fix.** One more plant: `({**good, "kind": "RESOLVED"}, "action_event_person_coupling")` (the copied row's other
  columns may need the matching `observation_code` null; if another check fires first, pick the row and columns so
  the coupling is the only one violated).

**L3 (Low; preference, D-SC1.28 hygiene).** `backend/assetops_backend/action_api.py:96-97`.
- **What is wrong.** The tenant refusal re-types the unknown-Site sentence (`f"No imported Site {site_code!r} in this
  tenant."`) instead of sharing the one in `open_scope` (`:116`). It is not new wording, and the byte-equality test
  pins the two together, but it is a second hand-built occurrence that SC-1a's guard may count.
- **Fix.** A small `unknown_site(site_code)` helper used by both places. Optional; 3C1a has the same shape.

### The three defaults (one line each for the Architect)

- **Q-3C1b-1 (USER label and statements `null` until SC-1a): confirm.** Honest: nothing on screen claims a person
  did or did not act. The event log falls back to `actor_kind` (`SiteAction.tsx:1295`), so it reads "USER"; the
  observe statement and the change `label`/`statement` are not rendered by the UI. The spec's "stated wording" test
  becomes a `null` test, which is the only form D-SC1.28 allows.
- **Q-3C1b-2 ("SYSTEM demonstration" still said on a person's act): confirm, as Low, on one condition.** The read
  label, the refusal sentence and the capability block (L1) are read-time words: wrong for a signed-in caller, but
  fixable in place by the text commit, and the actor of record is correct. The stored Foundation publish note
  (`service.py:554`) is different: it is persisted on the new Foundation revision, so every person's apply written
  before the text commit keeps "SYSTEM demonstration application" for good. That is acceptable only if no person's
  apply is stored under the old note in a database that matters: 3C1b should merge with (or after) its SC-1 text
  commit, as D-SC1.28 "Merge and review" already says for a unit with pending text. If the coordinator merges 3C1b
  before that commit, treat the stored note as Medium.
- **Q-3C1b-3 (stored rows through the real router and stores; `create_app` a wiring probe): confirm.** All three
  routes share one `build_action_router` call in `create_app`, and the probe proves all three inputs reach it: the
  other-tenant person gets the unknown-Site 404 (so `accounts` arrives; without it the answer would be
  `FINDING_NOT_FOUND`), a signed SITE_MANAGER reaches the service, and the switch gives 401. The stored-row proof runs
  the real `PostgresActionStore`, S1 publish and Postgres account store, including FAILED.

### Checklist

- **Scope (§7.6).** 17 files: §5's code (`permissions.py` rows, `action_api.py`, `lifecycle.py`, `ports.py`,
  `service.py`, the store, `main.py` one call), the migration, two new test files, the one 3C1a table-test edit and
  bookkeeping. Nothing else.
- **Today's path byte for byte.** Every service and store change is keyed on `actor is None`/`SYSTEM_DEMO`: the
  service passes no `actor` keyword and no `actor_id` in the payload when there is no person, the store's default is
  `SYSTEM_DEMO` (whose `person_id` is `None`), and `event_wire`/`_change_wire` return today's text for SYSTEM rows.
  `person_id` is not in `EVENT_COLUMNS`. Verification, evaluator and fuel-verification writes are untouched
  (D-3C1.3). No other module reads `action_event`'s actor columns (chain, estate and work readers checked).
- **Order.** Access, unknown Site 404, store 503, account 503, 401, tenant 404, role 403, then the Finding/Action 404,
  grant 403, body 422. A person without the role is refused before the body is read, so an `actor` key in such a
  body gets 403, not 422 (probe below); that matches 3C1a.
- **Migration.** Lock first; refuses on a USER row; three checks asserted by `pg_get_constraintdef` and replaced under
  their names; `person_fk`, `person_actor` and `person_coupling` added; `evaluator_job` unchanged. Downgrade refuses
  on any `person_id`, drops in reverse, re-adds the 0016/0019 texts and re-asserts them. A USER row cannot exist
  without `person_id` (`person_actor`), so restoring `actor_kind = 'SYSTEM'` cannot fail on downgrade.
- **Carry-overs from 3C1a.** L1: no "is head" equality (the test uses `assert_at_head` only after `upgrade head`).
  L2: messages built from `revision`, module found by glob. Both applied.
- **Persistence guard.** The configuration-persistence guard needed no change: the store is `action_event`'s only
  writer and 3C1b adds no writer registration; `check-architecture.ps1` passes.

### Forged requests (my probes, no database; scratch file deleted)

All against the router built as in `test_3c1b_person_actions.py`, 12 passed:
- body keys on an accept, unsigned: `actor_kind`, `actor_id`, `authorization_basis` give 422
  `CLIENT_AUTHORITY_FORBIDDEN`; `person_id`, `role`, `source_channel`, `triggering_fixture`, `session_id` give 422
  `COMMAND_INVALID` (closed shape); signed in as Fatma (FT) the same bodies are refused too; nothing is written;
- a forged cookie with the switch on: 401; a forged cookie plus `x-person-id` and `Authorization: Bearer` headers with
  the switch off: today's SYSTEM row;
- Fatma applying at Kobo: 403; Peter (SM at Kobo) accepting at Kisiwa: 403 `PERSON_ROLE_REQUIRED`;
- Peter accepting after an unsigned accept of the same recommendation: 409 (never a replay of the SYSTEM event);
- an FT with an `actor` body on a Finding outside the grant: 403 `PERSON_ROLE_REQUIRED` (role before grant and body).

### Checks run

- **Module paths.** `assetops_backend` and `assetops_contracts` resolve to the worktree; `fixtures` (namespace)
  resolves to the worktree first.
- **No database**, at `ab993e2e9`, tree clean: `test_3c1b_person_actions.py`, `test_s6_action_rule.py`,
  `test_3c1a_person_work.py`, `test_3c0a_accounts_api.py`: **267 passed**.
- **Postgres**, through `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --db` on `assetops_test`, at `ab993e2e9`, tree
  clean before and after: `test_3c1b_person_actions_postgres.py` and `test_s6_action_apply_postgres.py`:
  **17 passed** (5 new + 12 S6 apply), 63 s; only this review file untracked. This is the unchanged-tree confirmation the dispatch asked for (the builder's first `pg-new.log`
  overlapped the no-DB plant script).
- **`check-architecture.ps1`** (with `ASSETOPS_GUARD_PYTHON`): passed. **`check-agent-workflow.ps1`**: passed.
- **Cited, not rerun.** Builder's pooled run at `52ad95110` (112 passed; `ab993e2e9` differs from it only in docs);
  plants 7/7 no-DB and 3/3 DB (the DB plant script holds the db lock for its whole run, so its edits did not overlap
  the pooled run); check-all 40/40.

### Not verified, and residual risk the packet does not name

- **Merge order with SC-1a** (see Q-3C1b-2). The packet does not say whether 3C1b merges before or after its pending
  text commit. That choice decides whether the stored publish note can be written wrongly.
- **`_applied_kind`** (`service.py:638`) uses `next(...)` with no default: a change whose `applied_event_id` is not
  among the Action's events would raise `StopIteration` and answer 500, where today the change read succeeds. The
  data model makes that impossible (the change is written in the APPLIED event's transaction), so this is noted, not
  a finding.
- **3C0b.** Once the switch is on, every trial action needs a SITE_MANAGER (or FT for observe) signed in at the
  Site; the demo walkthrough's scripted accept/apply must then sign in. Nothing else reads the switch.
- **The full pooled regression list at `ab993e2e9`** was not rerun by me (cited above).

## Round 2 (text commit, W5 discovery of the new commits): `task/3C1b-person-actions` at `e2daa4c5c`

Reviewer (Claude, fresh), 2026-11-21. Scope: `163611071..e2daa4c5c`: the main merge `c328a4094` (migration renamed
0071 on 0068), the text commit `8c945689a`, and the docs commits `cd8acf7ea` and `e2daa4c5c`.

### Summary

- **Verdict: ACCEPT.** No High or Medium findings. Four Lows, none blocking, plus two merge notes (migration re-point
  and the `index-3.md` conflict).
- The six `action.*` statements: each SYSTEM variant is byte-identical to `main`. I rendered them against `main`'s
  literals, and the unknown-Site 404 against `f"{code!r}"` for 11 codes with quotes, backslashes, braces, a tab,
  U+200B, U+202E and an empty string. No USER variant names a person. No hand-built English is added on the
  changed paths: the guard is OK and the five baseline entries were pruned, none added.
- Q-3C1b-2's merge condition is met. A person's apply stores the person's note (pg test reads `change_note`). The
  Action read's `label` follows the ACCEPTED event. The capability block and the 403 body state the caller's actor.
- Q1 accept (L4 records the process gap). Q2 agree. Q3 is safe; see below and L1/L2.
- L2's test catches the plant. With `'RESOLVED'` added to the coupling's kind list in a throwaway worktree, the test
  fails at `test_3c1b_person_actions_postgres.py:228` (`DID NOT RAISE`). Every other test still passed under that
  plant, including the definitions test, so this block is the only guard on the kind clause.
- check-all at `e2daa4c5c`: **All 42 guards passed** (blocking; 0 advisory, 0 warned), 164.9 s wall.

### Findings

**L1 (Low; test gap, Q3).** `backend/tests/test_3c1b_person_actions.py` (the recommendation-read capability
parametrization) and the Action read.
- **What is wrong.** The packet says that when the account store is down, a read succeeds with null actor fields.
  No test covers this. The parametrization covers switch-off unsigned, a person, FT, switch-on unsigned and another
  tenant, but not the store being down. The per-caller Action read block is pinned only in the Postgres test.
- **Evidence (my probe, throwaway worktree).** With `BrokenAccounts` and peter's cookie, the recommendation read gives
  200 with `actor_kind`, `actor_id` and `label` all null and `allowed: true`. The same caller's accept gives 503.
- **Fix.** Add one row, `("peter", store down) -> none`, using the existing `BrokenAccounts`/`Down`.

**L2 (Low; residual risk on Q3, a preference).** `backend/assetops_backend/action_api.py:118-128` (`would_record`).
- **What is wrong.** Before this commit the reads never touched the account store. Now each recommendation read calls
  `person_step` once, and each Action read calls it twice (APPLY, OBSERVE). With a cookie, that is up to five
  account-store queries per call. `person_step` turns only the `accounts_unavailable` types into a refusal. Any other
  exception from the account store (for example a programming error) now turns a read that used to succeed into a
  500.
- **Why it is still safe.** Without a cookie, `AccountService.resolve(None)` returns before any store query, so the
  unsigned path (today's bytes) cannot be affected. There is no auth bypass: `would_record` only feeds the block, and
  every command re-runs `person_of`. There is no leak: the only difference a caller sees is about their own cookie
  (null instead of SYSTEM), and nothing about another tenant.
- **Fix (optional).** Resolve the person once per read and derive both commands' actors from that one principal.

**L3 (Low; honesty edges of the null block).** Three places:
- `frontend/src/sites/actionClient.ts:36-45`: `SystemDemoCapability` still types `actor_kind`, `actor_id` and
  `label` as non-null `string`. No screen reads them today, so nothing breaks.
- `frontend/src/sites/actionPresentation.tsx:198` (`granted()`): gates the control on `allowed` only. A caller whose
  command would refuse (null actor, `allowed: true`) still sees the control. This predates the commit; the block is
  now more honest than before (it used to claim SYSTEM). The screen slice that closes round-1 L1 should gate on
  `actor_kind !== null` and fix the types.
- `backend/assetops_backend/actions/service.py:718`: `accepted_by` falls back to SYSTEM when no ACCEPTED event is
  found. That cannot happen today, because every Action is written with its ACCEPTED event. A silent SYSTEM default
  would mislabel rather than fail. `next(...)` without a default (as `change()` does at `:649`) is the stricter form.

**L4 (Low; process, Q1).** `specs/SC-1-statement-composer/rulings.md` D-SC1.28 ("its modules join `ADOPTED`").
- **What is wrong.** `action_api.py`, `service.py` and `capability.py` are not adopted. That departs from the letter of
  D-SC1.28. The departure was accepted as a coordinator default, not by an Architect ruling.
- **Why it is acceptable.** Adopting these modules would convert older baselined text (SC-1b/c scope). The backend
  ratchet still refuses any new hand-built text in them: the packet's P7 plant gave `HAND_BUILT_NEW`, and the guard
  is OK at head.
- **Fix.** One line in the owner-away decisions log (or an Architect note) so SC-1b/c knows these three modules are
  theirs to adopt.

### Q2 (honesty clauses): agree

Spec §5.5's "Recorded by a signed-in person" is the label, and it is used as the label everywhere. The observe note
and the change statement keep their "changes no ... state / claims no effect" and "No measured effect, saving or
verification is claimed" clauses. Dropping those would weaken the no-claim statement on exactly the person's acts.

### Merge notes (not findings)

- **Migration 0071.** `backend/migrations/versions/0071_person_on_actions.py:31` has
  `down_revision = "0068_structure_finding"`. Both siblings also point at 0068: 3A7's
  `0069_commercial_reconciliation` and 3C2's `0070_agreed_action` (3C2's own state line already plans to re-point
  0070 onto 0069). At 3C1b's merge, set `down_revision` to the single `alembic heads` value on `main` at that moment:
  `"0070_agreed_action"` if both have merged, otherwise whichever one has. Keep the file name and
  `revision = "0071_person_on_actions"`; no message or test changes (both are built from `revision` or found by
  glob). Update the stale numbering prose too: the module docstring (`:22-23`) and the `.ai/state/work.md` line
  ("down_revision 0068 until ..."). Neither sibling touches `action_event`, so 0071's `_assert_check` "before"
  texts still hold. Then confirm a single head and run the 3C1b Postgres file plus `test_3b4_observer_postgres.py`
  (its downgrade to 0067 passes through 0071's downgrade).
- **`index-3.md` conflict.** All three branches create `.ai/state/index-3.md`, so expect add/add conflicts:
  - 3C1b and 3A7 (`task/3A7-month-reconciled`) split the same way. Both keep `index-2.md` through 178, both start
    `index-3.md` at line 179 (3C1b and 3A7 respectively), and their header prose differs.
  - 3C2 (`task/3C2-agreed-change`) moved lines 160-178 out of `index-2.md` into `index-3.md` (its 179 is 3C2), and
    cut `index-2.md` to 5,286 bytes. Against 3C1b that is a modify/modify conflict on `index-2.md` (header "of 3" and
    the moved block) plus an add/add on `index-3.md`.
  - `INDEX.md` and `index-1.md` get the same one-line edit on every branch, so they merge clean.
  - `.ai/state/work.md` gets an append-at-end conflict with 3C2.
  - Resolve by keeping whichever split lands first and appending each later slice as the next number (180, 181) with
    that file's header. Re-check the 8,000-byte cap afterwards.

### Checks run (evidence `/opt/assetecon/evidence/3C1b/review-text/`)

- `heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` at `e2daa4c5c` (clean tree):
  `All 42 guards passed (blocking; 0 advisory, 0 warned)`, 164.9 s wall. This includes
  `Statement catalogue (SC-1)` OK (0 adopted) and its self-test (72 of 72 plants). Log: `check-all.log`.
- **L2 plant.** Detached throwaway worktree at `e2daa4c5c` (removed after), `heavy-slot.sh --db`, `assetops_test`
  routed by the harness. 0071's kind list gained `'RESOLVED'`. Result:
  `test_each_planted_actor_fails_on_its_constraint` FAILED at `:228` `DID NOT RAISE DBAPIError`;
  `test_the_constraints_exist_with_their_definitions` passed. Log: `l2-plant-and-q3-probe.log`.
- **Q3 probe** (same run, no database): the recommendation read with the store down gives 200 and a null block, and
  the accept gives 503. My Action-read half failed on my own fake-store wiring (`KeyError`), so it proves nothing
  either way. The Action read uses the same `would_record`.
- **Byte check** (no database, the shared venv with this worktree first on `sys.path`): the SYSTEM variants and the
  publish note equal `main`'s literals; the 404 equals `f"{c!r}"` for all 11 codes.
- Not rerun: the builder's no-DB 663 and Postgres 61 counts at `8c945689a`. The Postgres log was lost, as the packet
  says; check-all at head covers the guards.

### Not verified, and residual risk

- The re-pointed migration and the merged index files can only be checked at merge time (see the merge notes).
- Frontend words ("Accept trial (SYSTEM demonstration)") still say SYSTEM for a signed-in person. This is round-1 L1,
  listed open in the packet, and belongs to a screen slice.
