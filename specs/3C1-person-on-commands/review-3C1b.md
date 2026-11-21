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
