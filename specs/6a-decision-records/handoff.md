# 6a handoff (partial: units 1 and 2 of 3 done)

Branch `task/6a-decision-records`, worktree `/opt/assetecon/AssetOpsV1-6a`, built on `main` 8821c9484. Not merged.
Implementer (Claude), 2026-11-22. Stopped after unit 1 by the dispatch's context rule (unit 2 is 1.25 u and would
not fit well under the 120k budget in this session).

## Done

- **Unit 1, commit 1** (`ce7d50b91`): `backend/migrations/versions/0072_decision_records.py` (gate A: `main`'s head
  `0071_person_on_actions`; `revision = "0072_decision_records"`, `down_revision = "0071_person_on_actions"`) and
  `backend/tests/test_6a_migration_postgres.py` (spec §6 test 6, four tests: 6a catalogue and chain, 6b every
  constraint on a hand row by name, 6c the two deferred triggers and SQLSTATE 23514, 6d append-only, downgrade,
  one head).
- **`f1345ee0f`**: `tests/test_3c2_agreed_actions_postgres.py` test 6 now runs `TRUNCATE agreed_action CASCADE`.
  0072's `decision_choice` references `agreed_action`, so a plain TRUNCATE is refused by the FK check before the
  append-only trigger runs (`cannot truncate a table referenced in a foreign key constraint`). The assertion is
  tightened to `agreed_action rows are append-only`. This is a known deviation from "3C2's tests pass unchanged".
- **Plant 1** (drop the deferred trigger `decision_has_no_action`, applied in place after the commit and reverted
  with `git checkout`): test 6a fails (trigger set differs) and test 6c fails (`DID NOT RAISE`). 2 failed, 2 passed.

## Tests (host runner, `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>`)

- `test_6a_migration_postgres.py`: 4 passed (10.3 s) at `ce7d50b91`.
- Adjacent: `test_6a_migration_postgres.py`, `test_3c2_agreed_actions_postgres.py`,
  `test_3c1b_person_actions_postgres.py`: 15 passed, 1 failed (the 3C2 TRUNCATE above), then
  `test_3c2_agreed_actions_postgres.py` 7 passed at `f1345ee0f`.
- Fast check-all at `f1345ee0f`: all 42 guards passed, 444 s wall of which 304 s waiting for a slot (rerun with main's `frontend/node_modules` symlinked, then removed). The first run
  failed 2 of 42 only because the fresh worktree had no `frontend/node_modules` (missing-claim scan needs `typescript`).

## Mid-build question (default applied)

- **Q1. `option_effect_missing_check` cannot fire by name.** Postgres runs a table's CHECKs in name order;
  `option_effect_change_or_missing` sorts first and calls `jsonb_array_length(missing)`, which raises
  `cannot get array length of a non-array` (SQLSTATE 22023) on a non-array. The row is still refused, but not by
  the named check (`option_evaluation` is unaffected: `..._missing_check` sorts before `..._value_or_missing`).
  Default applied: the spec's SQL as written; test 6b asserts that message for this one case (`SHADOWED`).
  Alternative for the Architect: guard the rule (`jsonb_typeof(missing) = 'array' AND ...`) or rename it.
- **Note (not a question).** `option_evaluation_comparison` passes a COMPARISON row whose `value` is NULL (NULL
  check result); `value_or_missing` then requires a non-empty `missing`. Built as written; 6c writes no-action's 0.

## Constraint names (for the packet; handshake R4)

Named in test 6 (`CHECKS`, `UNIQUES`, `FKS`, `INDEXES` at the top of the file); the FKs carry Postgres's default
names (`<table>_<columns>_fkey`). Unreachable by a hand row and asserted in the catalogue only: the
`*_tenant_id_unique` constraints (the primary key refuses a duplicate id first) and the three ordering indexes.

## Next

1. Unit 2 (spec §3.1 to §3.5; tests 1 to 5 and 9): `structure/levers.py`, `check_levers` (fourteen branches,
   D-P6.23 any-pin rule, between `check_pins()` and `check_observed()`), the registry row, `decisions/records.py`
   with the memory store and `site_by_id` (D-P6.20), role rule D-P6.24, statements `i18n/statements/en/decision.py`.
2. Unit 3 (§4; tests 7 and 8): adapter, composition, three commands, permissions, seven-pattern guard (I6), the
   `backend/tests/lakeside_people.py` move (I7).
3. Then the packet (`specs/6a-decision-records/packet.md`), spec `Status: in_review`, the `.ai/state/` entry.
   Gate B at merge: renumber on top of any newer head; one `alembic heads`.

## Live databases

None left: the host runner's routed clones (`*_pt<run>_*_test`) are dropped by the harness at the end of each run.

## Unit 2 (commit 2, done; 22 Nov)

- **Built:** `structure/levers.py` (pure), `check.check_levers` (14 branches, any-pin rule; between `check_pins` and
  `check_observed`), `candidate_l` lists the lever (docstring note, no version bump), `decisions/records.py` (rows,
  `DecisionStore` Protocol with `site_by_id`, `DecisionService` prepare / state_one_off / choose / for_tenant,
  `MemoryDecisionStore`, `refusal_sentence`, `REFUSAL_EXIT` incl. `BAD_UUID`, `NO_DATABASE`), statement
  `i18n/statements/en/decision.py`, `COMMAND_ROLES` rows for the three commands (`accounts/permissions.py`).
- **Tests:** `backend/tests/test_6a_decisions.py` (81 passed; tests 1-5, 9, sentences) and
  `backend/tests/lakeside_people.py` (the shared people incl. Hassan; 3C2's `World` NOT yet moved onto it: unit 3, I7).
  Edited to follow the additions: `test_3c1a_person_work.py` (`SPEC_ROLES` + `decision.` filter), `test_sc1_statements.py`
  (catalogue set), new `tests/statement_cases/decision.py` (one case per variant), `tools/checks/statement_catalogue.py`
  (`decisions/records.py` in `ADOPTED`).
- **Plants (each failed its test, reverted):** include current point (F-P1 count), first one-off instead of latest,
  non-executive choose, `KEPT_AS_IS` read after an Action (state order), a non-leaf in `changes` (test 2).
- **Fast check-all:** 42 of 42 passed (142 s; frontend/node_modules symlinked, removed).
- **Pre-existing failures on base `8821c9484` (also fail there; not mine):** `test_3b1_structure_registry.py::
  test_t1_leaf_sources_absence_and_words_equal_the_manifest` (manifest says dispatch-3.2, row says 3.3) and
  `test_3b3_structure_evaluate.py::test_t6_each_state_yields_its_leaf_value_on_its_own_record`.
- **Guard shape learned (for unit 3):** `ADOPTED` files may hold no text-like literal: no regex literals, no
  `x == "-"` string compares, no docstring prose that reads as a sentence in a function body, no `"Africa/..."`
  strings (a default of `"UTC"` is code form). Use `isdigit`/`find` style checks.
- **Deviations:** none beyond unit 1's. Q1 default stands.

## Next (unit 3, spec section 4)

Adapter (`decisions/adapters/postgres_decision_store.py`, with `site_by_id`), composition, `decision_prepare`,
`decision_one_off`, `decision_choose` commands, seven-pattern INSERT guard (I6), move `World`'s people onto
`tests/lakeside_people.py` (3C2's two test files must pass unchanged), tests 7 and 8; then the packet, spec
`Status: in_review`, `.ai/state/` entry. `records.py` already carries `refusal_sentence`, `REFUSAL_EXIT` and the
`StoreUnavailable` the adapter must raise.
