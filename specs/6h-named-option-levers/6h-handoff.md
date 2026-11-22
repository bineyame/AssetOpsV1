# 6h handoff (partial): golden, 6h1 and 6h3 done; 6h2 and 6h4 next

Branch `task/6h-named-option-levers`, worktree `/opt/assetecon/AssetOpsV1-6h`, base `19c8b2b3b`. Stopped near the
context budget, by the brief.

## Done (commits)

- `b3137c352` parity golden (D-P6.67), first commit, before any 6h change: `backend/tests/capture_6h_parity.py`
  runs every non-static test function of `test_6c_difference.py` / `test_6c_evaluate.py` in process with the module
  names `difference` and `evaluate_options` wrapped (`functools.wraps`, so the signature test still reads the real
  signature) and records each result field by field, plus 6a `World().prepare()` (ids zeroed where random).
  `backend/tests/golden/6h_parity.json` (40 cases, 42 calls); `test_6h_parity.py` compares. Green at every commit.
- `c2a48dc1b` 6h1: `levers.py` (`LeverOption`, `ChangeSource`, `STUDY`/`RECORD`, `OPTION_KINDS`, `GENERATORS`,
  `CHANGE_SOURCE_KINDS`, `NO_ACTION_WORDS`, new `Lever` fields; generator lever gets STUDY sources and
  `KEEP_SETTINGS`); `check.py` grid branches 6-13 under `if generator == "SETTING_GRID"`, `_named_fault` 15-22;
  `records.py` `STATED_OPTIONS` const, P7 branch, `RUN_OUTCOMES` + `BOUNDS_NOT_CHECKED`; `prepare_decision.py`
  `--current` optional; migration `0073_named_option_levers.py` (checks + `option_record` + triggers + guarded
  downgrade). Tests `test_6h_levers.py`, `test_6h_prepare.py`, `test_6h_migration_postgres.py` (16 passed with 6a's).
- `228396235` 6h3 (built before 6h2: 6h2's fixtures name catalogue levers): nine levers via `_named(...)` in
  `LEVERS`; registry `levers` on the twelve §5.2 rows (helpers gained `levers=`); `check_lever_paths` +
  `PENDING_LEVERS` in `check_all` after `check_levers`; `i18n/statements/en/decision_lever.py` (generated; loads);
  `test_6h_words.py`; P1 in `test_6h_prepare.py`.

Last focused run: test_6h_levers, test_6h_prepare, test_6h_words, test_6h_parity, test_6a_decisions,
test_6a_commands, test_3b6_cold_ev_structures, test_6c_difference, test_6c_evaluate all green (pure, host runner).

## Deviations so far (for the packet's Known Deviations)

1. `test_6a_migration_postgres.py`: the two head assertions (`get_heads() == [0072]`, `_heads() == {0072}`) became
   one-head checks; not in §10.2 item 9, unavoidable once 0073 exists (3c2's test did the same earlier).
2. `test_6a_decisions.py` `_planted` now plants among every real lever (`{**LEVERS, lever_id: lever}`) and
   `_two_pin` keeps `unexplained_l`'s own lever: with the §5.2 rows listing named levers, a one-lever map trips
   branch 1/4 on the real rows first. D-P6.63's "refuse as today" holds for codes and texts after this change only.
3. `GENERATOR_REDUNDANCY` title/question: "evening supply with no standby generator" (spec: "on one generator";
   SC-1 bans `one` and `single`). Owner/Architect may reword.
4. `decision_lever.option_label` is `evidence: "served"` (percent slots need a served or inline evidence form).
5. Part order 6h1, 6h3, 6h2, 6h4.

Questions with defaults (non-blocking): Q1 deviation 3 wording (default as built); Q2 `check_lever_paths(levers=...)`
is accepted and unused (spec signature; rows name levers); Q3 `prepare` memory/Postgres parity is covered by test 6.

## Next: 6h2 (spec §4) then 6h4 (§6)

- `structure/difference.py`: `LeafChange.currency: str | None = None` last field; in `_Difference.delta` drop the
  `not isinstance(part, LeafChange)` guard (L~215); `difference(..., *, also=())` scope = changed leaves + nodes in
  `run.over` within the union closure of `OUTCOME_FACTOR` and each `also` factor + `OUTCOME_FACTOR` always
  (a factor resting on no changed leaf: `d_ref` already returns 0). Then edit
  `test_6c_difference.py::test_1_stated_records_are_never_read` per §10.2 item 9.
- `structure/evaluate.py`: add `_origin_union` to `__all__`.
- `decisions/models.py`: `stated_changes(lever, option, base, records)` per §4.2 (use the catalogue option from
  `lever.options` by `option.option_key`). `OptionRecordRow` dataclass (fields as §6.1 table) in `records.py`.
- `decisions/evaluate.py` `_value_option` (L~117): pass `also=(lever.purpose_factor,)` when lever given; D-P6.60 leaf
  misses after `_missing_inputs`, before ONE_OFF; D-P6.61 evidence and source class; after R1-R4 in
  `evaluate_options` the `bounds_required` rewrite (outcome `BOUNDS_NOT_CHECKED` even with nothing valued).
- `decisions/run.py`: `option_inputs` new signature/branch (§4.1); E2 `STUDY_NOT_FOR_LEVER`; E3 modelled tuple; skip
  the study block for STATED_OPTIONS (study None, identity None); E5 `latest_option_records`.
- `decision.refused` (`i18n/statements/en/decision.py`) + `REFUSAL_EXIT`: the six codes (§6.2 sentences).
- Fixtures N1/T1/K2/S1 in `option_fixtures.py`; `test_6h_evaluate.py` with the §10.1 literals; run test 8 after
  every change. 6h4: `state_option_record`, `COMMANDS["option_record"]`, `accounts/permissions.py`
  `decision.option_record`, `_covering_role(roles, site_id, command)`, both stores (`add_option_record`,
  `latest_option_records`), CLI `state_option_record.py`, `test_6h_option_record.py`, `test_6h_run_postgres.py`.
- Then: every §10.3 plant shown failing; test scope (6a, 6c, 0K4d, 3b6 and every file importing a touched module)
  vs main; guards (`tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON`, `tools/check-agent-workflow.ps1`,
  check-all fast); `packet.md`; state entry (next number in `.ai/state/index-3.md`); spec `Status: in_review`.

## Risks

- `_value_option`'s new evidence/source-class rule applies to every option; test 8 is the check (stop and return to
  the Architect if a row differs in evidence or source class only).
- `option_inputs` refusal of an unknown generator must stay after the new branch.
