# 3C2 review packet: commit 1 (the agreed change recorded as an Action, codes only)

Branch `task/3C2-agreed-change` (worktree `/opt/assetecon/AssetOpsV1-3c2`), off `task/3A6-source-profiles` at
`166942e7d` (D-3A6.26 precedent). Not merged; 3C2 merges after 3A6, SC-1a and 3A7. `USER_REVIEW_REQUIRED: false`.

## Gate A

- (1) `git grep -n "def tenant_by_slug" 166942e7d -- backend/assetops_backend/accounts/service.py`:
  `service.py:129`. Present on the base.
- (2) Base head `0067_source_profile`; `0068` is 3A7's. File `0069_agreed_action.py`, `revision =
  "0069_agreed_action"`, `down_revision = "0067_source_profile"` (the number skips 0068 so the file needs no rename,
  only its parent, at gate B). Test 6's hand pair is `("0069_agreed_action", "0067_source_profile")`.
- **Gate B (at merge):** `down_revision` becomes `0068_commercial_reconciliation` (or the live head), with
  `HAND_PAIR` in `test_3c2_agreed_actions_postgres.py`; `alembic heads` must show one head.

## Commits

| Commit | What |
|---|---|
| `ec47d56fa` | migration, `actions/agreed.py`, adapter, `agreed_composition.py` (moves to `actions/composition.py`, re-export left, D-3C2.15), `record_action.py`, permission line, tests 1 to 8 |
| `42de02e06` | **HELD FOR OWNER at merge (owner-away row 5):** the `agreed_action` writer block in `configuration-persistence.ps1`, nothing else |
| `be9efbaab` | 3C1a's role-table test lists `action.agree` (as 3A6 listed its command) |
| docs commit | spec folder from `main`, Status `in_review`, MB1, handoff, built state |
| `04c749565` | 3C0a's downgrade test truncates in replica mode (see Known Deviations) |

## Codes only (D-3C2.14)

State `OPEN`/`OVERDUE` (`state_code`); a refusal writes `<CODE>\n` to stderr, exit 2 (3 for `ACTIONS_UNAVAILABLE`);
the JSON line's `state` is the code. No messages keys, no sentences. The epilog (static chrome) is the only text.
Commit 2 per `handoff.md`.

## Checks (revision `04c749565` unless noted)

- Unit, `test_3c2_agreed_actions.py`: 54 passed (9.8 s).
- No-database regression (3C2, 3C0a service/api/passwords, 3C1a, 3A6 two files, `test_s6_action_rule`): 373 passed,
  1 failed (`test_command_roles_is_the_spec_table`, fixed in `be9efbaab`, then `test_3c1a_person_work.py` 147 passed).
- Postgres `test_3c2_agreed_actions_postgres.py` via `heavy-slot.sh --db` + `run-host-tests.ps1`: 6 passed (12.8 s).
- Postgres regression (3C0a x2, 3C1a, 3A6, S6 action x3, ON1 onboarding): 59 passed, 1 failed, 148 s wall
  (`test_downgrade_refused_with_an_account_then_down_and_up`: its `TRUNCATE ... CASCADE` reaches `agreed_action`;
  fixed in `04c749565`; rerun: `test_3c0a_accounts_postgres.py` 17 passed, 15.4 s).
- Fast `check-all` (8 m 54 s): FAIL on three items, all known: configuration-persistence (MB1's one line); the estate
  guard self-tests (3 failed: each asserts a clean baseline and sees MB1's line); decision index (`D-SC1.21`,
  `D-SC1.28` unresolved on the 3A6 base, clears when SC-1a merges). Every other item passed.
- `check-agent-workflow.ps1`: passed.

## The guard, shown failing (scratch copy, `check-architecture.ps1 -Only configuration-persistence.ps1`)

Baseline: exit 1, MB1's line only.
- `UPDATE agreed_action SET title = :t` added to the adapter: exit 1, "The agreed-change store runs only one plain
  INSERT INTO agreed_action (no UPDATE, DELETE, TRUNCATE, upsert, SELECT source or other table);
  ...postgres_agreed_action_store.py:21: UPDATE agreed_action SET title = :t WHERE id = :i."
- `INSERT INTO agreed_action (id, title) VALUES (:i, :t)` in `actions/adapters/postgres_action_store.py`: exit 1,
  "Only backend/assetops_backend/actions/adapters/postgres_agreed_action_store.py writes agreed-change table
  'agreed_action'; ...postgres_action_store.py:98: ..." (plus the Action store's own insert-only rule).

## Plants (reviewer guide; scratch copy, each reverted)

No database, all fail their tests: P1, P2, P3, P4 (service re-run read and store identity both removed: test 1
re-runs), P5, P6, P8, P9, P11, P12, P13, P14, P15, P17, P18, P19, P20, P22 (creator and owner each), P23, P26, P27.
P10 is the guard above. P16 is unit 2. Database plants (in place, `git checkout` after each, inside one `--db` job):
P7 (row trigger removed: test 6 UPDATE did not raise), P21 (TRUNCATE trigger removed: test 6 TRUNCATE did not
raise), P24 (catch removed: test 7b returns nothing), P25 (lock removed: test 7c sees no advisory wait). Not caught: 0.

## Known Deviations

- **3C0a and 3C1a tests touched** (outside §0's collision list): the 3C1a role table gains `action.agree`; 3C0a's
  downgrade test TRUNCATEs in `session_replication_role = replica`, because D-3C2.13's TRUNCATE trigger refuses the
  cascade from `operator_account`. `ASSETOPS_TEST_CLEANUP=truncate` would refuse the same way (as `chain_input_change`
  already does); the default DELETE cleanup is unaffected.
- `AgreedActionView.state_code` (not `state_words`) in commit 1; the field the 5c mapping reads lands in commit 2.
- `build_agreed_actions(url, *, clock=...)`: an optional clock so `main(clock=...)` composes its own engine (test 7a);
  DDR G10's call is unchanged. `main` also maps an account-store error to `ACTIONS_UNAVAILABLE` (exit 3).
- The adapter wraps driver errors as `StoreUnavailable` (defined in `agreed.py`), so the service maps steps 4, 7
  and 9 without importing the driver.

## Open

- **MB1 answered, B (D-3C2.15):** composition moves into `actions/composition.py`, re-exported by `agreed_composition.py`; test 5 retargeted; no guard change beyond the writer block. Code not yet moved.
- **Owner approval at merge:** the writer block (`42de02e06`), owner-away row 5.
- **R-AUTH** (residual): `record_action` is a trusted act, not a sign-in; `--as` names the person, `created_by_script`
  true; a person records on screen once 3C3 lands (D-3C2.12).
