# 6h review packet: named-option levers for every Site type

Task `specs/6h-named-option-levers/spec.md` rev 1 (rulings D-P6.59 to D-P6.67). Branch `task/6h-named-option-levers`,
base `19c8b2b3b`. Commits (oldest first): b3137c352 parity golden (before any 6h code), c2a48dc1b 6h1, 228396235 6h3,
ec9781664 6h2 (+ the 6h4 service, stores, CLI), 95a4d3d93, 80cea82ae, ff59da645, 93e47614a. Part order 6h1, 6h3, 6h2, 6h4.
`USER_REVIEW_REQUIRED: true`. Layout evidence: not run (no screen; backend only).

## Outcome
Every Site type has decision levers; a `STATED_OPTIONS` option is valued by the same `evaluate_options` from a document's
stated level (an option record) or names the record or simulation it lacks. Protective levers end `BOUNDS_NOT_CHECKED`
and recommend nothing. Mwea N1 reads 1670.00 over 4 months; Thika T1 -100.00 and uncovered nights -26; Kasarani K2 630.00.

## Files
`structure/{levers,check,difference,evaluate,rows_*}.py`, `decisions/{records,models,evaluate,run}.py`,
`decisions/adapters/postgres_decision_store.py`, `accounts/permissions.py`, `i18n/statements/en/{decision,decision_lever}.py`,
`prepare_decision.py`, new `state_option_record.py`, `migrations/versions/0073_named_option_levers.py`; tests
`test_6h_{parity,levers,prepare,words,evaluate,run,option_record,migration_postgres,run_postgres}.py`,
`capture_6h_parity.py`, `golden/6h_parity.json`, `option_fixtures.py` (N1/T1/K2/S1, `named_decision`, `record_of`).

## Acceptance (spec section 11)
1 Every Site type has a lever and every pinned Finding a path: `check_lever_paths` in `check_all` (test_6h_levers).
2 One set of functions: no structure named in `evaluate.py` (grep). 3 N1 1670.00 (test_6h_evaluate N1, Postgres N1).
4 Protective decisions: value and purpose-factor change, CONDITIONAL, no rank (T1, K2). 5 Missing record named, never 0
(N1m, T1, missing-base test). 6 Parity golden: 6c results and Kobo's prepare equal byte for byte (test_6h_parity; one
exemption, Q4). 7 T1o: an unrecorded own leaf makes value null.

## Checks (host runner, worktree; real output)
- 6h tests, pure: test_6h_{parity,levers,prepare,words,evaluate,run,option_record} green. Postgres
  (test_6h_migration_postgres + test_6h_run_postgres): 13 passed.
- Comparison set: every backend test file importing a touched module, plus every 6a, 6c, 0K4d, 3b6 file, excluding the new
  6h files (46 pure files, 23 Postgres files). Pure: base `19c8b2b3b` 2 failed, 2714 passed, 1 skipped (2m30s); branch
  2 failed, 2714 passed, 1 skipped (2m20s). The same two fail on both (pre-existing: test_3b1
  `test_t1_leaf_sources_absence_and_words_equal_the_manifest`, test_3b3 `test_t6_each_state_yields_its_leaf_value_on_its_own_record`,
  `dispatch-3.3` vs `3.2`). Postgres: base 145 passed (6m32s), branch 145 passed (6m44s).
- Guards: `tools/check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON`) after adding `option_record` to the decision-store writer
  table list in `tools/checks/configuration-persistence.ps1` (it refused the new INSERT before; deviation 9);
  `tools/check-agent-workflow.ps1` passed.

## Plants (section 10.3; each applied, test run, reverted; all fail)
| Plant | Fails |
|---|---|
| stated delta = record value | T1, T1b |
| records by factor alone, newest of any option | T1, T1o |
| missing base read as 0 | `test_a_held_record_over_a_missing_base_level_is_missing_never_zero` |
| OUTCOME_FACTOR not forced into scope | T1, T1o (KeyError) |
| `also` dropped | T1, T1b |
| `bounds_required` ignored | T1, K2 |
| D-P6.60 leaf misses removed | T1, T1o |
| D-P6.61 evidence from `out` only | T1, T1e (Postgres T1 asserts DECLARED; not re-run) |
| `LeafChange.currency` not collected | N1, N1k |
| grid branches 6 to 13 for every lever | test_6h_levers planted named lever, branch 15 |
| branch 16 removed | `test_1_each_branch_15_to_22_refuses[16]` |
| `check_lever_paths` skipped for a pin with no lever | `test_1_a_pin_with_no_lever_and_not_pending_refuses` |
| oldest record read instead of newest | `test_the_newest_record_per_option_and_factor_is_read` |
| `--emulated` ignored | option_record tests (N1e at evaluator level reads the stored origin) |
| `STUDY_NOT_FOR_LEVER` removed | `test_a_study_given_to_a_stated_lever_is_refused...` |
| a 6c result changed | test_6h_parity |
Test-first: the parity golden, 6h1 and 6h3 tests were written first. For 6h2 and 6h4 the evaluator code was written
before its tests were run (the tests were written to the spec literals and passed first time); each plant above shows
the tests can fail.

## Known deviations
1 `test_6a_migration_postgres.py` head assertions became one-head checks (not in section 10.2 item 9; unavoidable once 0073 exists).
2 `test_6a_decisions.py::_planted` plants among every real lever and `_two_pin` keeps `unexplained_l`'s own lever: with
the real rows listing named levers a one-lever map trips branch 1/4 first. Codes and texts refuse as before.
3 `GENERATOR_REDUNDANCY` title/question says "evening supply with no standby generator" (SC-1 bans `one`, `single`).
4 `decision_lever.option_label` is `evidence: "served"` (percent slots need a served or inline evidence form).
5 Three more existing tests changed, none in item 9, each an allow-list the new code must join: `test_6a_decisions`
`SENTENCES` (five new refusal sentences), `test_3c1a_person_work` command roles (`decision.option_record`),
`test_sc1_statements` shipped catalogue (`decision_lever.*`).
6 `decision/evaluate.py` passes `also=` only when the lever's purpose factor is a row of the registry and only when
non-empty: 6c's planted registries lack it, and three 6c tests monkeypatch `difference(registry, base, changes)`.
7 Refusal sentences use counts as slots (`{value_places}`, `{least}`, `{chars}`: the catalogue bans number words and digits
in literals); the text reads as the spec's. `BAD_CURRENCY`'s sentence is the existing one (3 capital letters).
8 `test_6h_parity.py` sets aside `source_class` of one recorded case (Q4).
9 `tools/checks/configuration-persistence.ps1`: `option_record` joins `$decisionRecordTables` (the writer guard's one-INSERT-per-table rule).

## Questions (defaults taken; non-blocking)
Q1 deviation 3 wording (as built). Q2 `check_lever_paths(levers=...)` is accepted and unused (spec signature).
Q3 `prepare` memory/Postgres parity is covered by test 6 of the prepare tests. Q4 D-P6.61's premise: one recorded 6c
case, `test_4_a_node_with_no_value_is_named_by_its_own_missing_leaves`, monkeypatches `difference` with a double that
returns Deltas carrying no origins while its changed leaf carries `demo-simulated`; the row's source class now reads
SIMULATED (golden RECORDED). No real `difference` result differs. Default: that key's `source_class` alone is
compared as absent; every other field byte for byte. Architect to confirm or rule (refresh is barred inside the slice).

## Residual risk and review focus
The first real EV and cold-chain values need records stated by Finance (none exist in the demo data); `charging_schedule`
names five missing simulations (S1). Index number is now 204 (renumbered in the review-Lows fix round). Focus: `_value_option`
(D-P6.60/61 apply to every option), `stated_changes` (D-P6.65 base level), the BOUNDS rewrite order after R1 to R4.

## Fix round (review Lows)
- L1: state index line renumbered 199 to 204 (main holds 199-203); the merge of main resolved the conflict. work.md does not exist in the folder; packet reference updated.
- L2: `test_6h_migration_postgres.py` now asserts `get_heads() == ["0073_named_option_levers"]`.
- L3: E3 in `decisions/run.py` refuses `LEVER_UNKNOWN` when a STATED_OPTIONS option key is not in the lever's catalogue; test `test_a_stored_option_key_that_left_the_catalogue_is_refused_not_crashed` (written first, failed with StopIteration).
- L5: spec §5.4 now says a lever without words fails test 7.
- L7: `6h-handoff.md` deleted. L4, L6: no change. A1-A4 left to the Architect, no rulings recorded.
