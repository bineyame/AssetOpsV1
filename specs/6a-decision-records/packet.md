# 6a packet: decisions, options and their records

Task: `specs/6a-decision-records/spec.md` (rev 2; 3.25 u). Branch `task/6a-decision-records`, built on `main` `8821c9484`
(`main` now `c8643fbd1`; no migration since). Implementer: Claude, 22 Nov 2026. Not merged. `USER_REVIEW_REQUIRED: true`.

## Gates
- **P** met (owner, 22 Nov). **A**: `main`'s head is `0071_person_on_actions`; the file is `0072_decision_records`
  (`down_revision = "0071_person_on_actions"`). **B** at merge: renumber on any newer head, one `alembic heads`.
- **S**: both greps hit (`PINS` at `structure/pins.py:37`; `def tenant_by_slug` at `accounts/service.py:129`).

## Commits (6; `git log main..HEAD`)
`ce7d50b91` migration 0072 and test 6 · `f1345ee0f` 3C2 test 6 CASCADE · `dc4cb1c88`, `428e65f0a` unit 2 (levers,
`check_levers`, `records.py`, statements) · unit 3: adapter, composition, three commands, writer guard, people move,
tests 7 and 8 (one commit, with this packet).

## Tests and gates (host runner; Postgres through `tools/heavy-slot.sh --db`)
- `test_6a_decisions.py` (tests 1-5, 9, sentences) and `test_6a_commands.py` (test 8, 43 cases), with
  `test_3c2_agreed_actions.py`: 227 passed, 31 s.
- Postgres: `test_6a_decisions_postgres.py` (test 7, 9), `test_6a_migration_postgres.py` (test 6, 4),
  `test_3c2_agreed_actions_postgres.py`, `test_3c1b_person_actions_postgres.py`: 25 passed, 50 s.
- Fast check-all at `4a232a2f2` (frontend/node_modules symlinked, then removed): **43 of 43** guards passed, 326 s wall
  (the estate self-test ran because the persistence guard changed; SC-1 self-test 78 of 78 plants).
- **Pre-existing on `main`, not 6a's:** `test_3b1_structure_registry.py::test_t1_leaf_sources_absence_and_words_equal_the_manifest`
  and `test_3b3_structure_evaluate.py::test_t6_each_state_yields_its_leaf_value_on_its_own_record`.
- Layout evidence: not applicable (no screen, no served string; D-P6.9).

## Plants (each fails its named test, then reverted)
Drop deferred trigger `decision_has_no_action` (6: 2 failed) · include current point as an option (3) · first one-off
instead of latest (4) · site manager may choose (5) · `KEPT_AS_IS` read after an Action (5, and test 8) · non-leaf in
`changes` (2) · `UNDER_WAY` read before `KEPT_AS_IS` (5 and 8: 2 failed) · a key per code `decision.refused.bad_period`
(8: `KEY_FORM`; a dropped variant: `NOT_EXHAUSTIVE`) · guard: `UPDATE decision_choice` in the adapter (fails, names the
line), and `INSERT INTO decision` in another module (fails: second writer, driver outside the adapter). The lock-less
prepare race (test 7b, scratch monkeypatch) still gives one row via `decision_once`. Plant "heading from the lever when a
Finding is set" is test 3's `test_3_the_heading_follows_the_pinned_factor...`.

## Constraint names (handshake R4)
Listed in `tests/test_6a_migration_postgres.py` (`CHECKS`, `UNIQUES`, `FKS`, `INDEXES`, top of file); asserted by name,
except `option_effect_missing_check` (Q1) and the `*_tenant_id_unique` and three ordering indexes (catalogue only).

## Files outside spec §2 to §4's list
Unit 2: `tests/test_3c1a_person_work.py` (`SPEC_ROLES`), `tests/test_sc1_statements.py`, `tests/statement_cases/decision.py`,
`tools/checks/statement_catalogue.py` (`records.py` in `ADOPTED`). Unit 3: `decisions/cli.py` (the commands' shared
refusal line, flag parsers and compose-and-run; keeps the three commands thin), `tests/test_3c2_agreed_actions.py`
(World body, I7), `tools/checks/configuration-persistence.ps1` (the writer block plus a `decisions` row in `$domains`).

## Deviations
1. 3C2 test 6 truncates `agreed_action` with `CASCADE` (0072's FK blocks a plain TRUNCATE before the trigger runs);
   the assertion names `agreed_action rows are append-only`. "3C2's tests pass unchanged" holds otherwise.
2. I7: 3C2's `World` now builds on `LakesidePeople` (clock argument added), so it also holds Hassan; its tests
   pass unchanged, but the file's `World` body changed.
3. The commands read display names through `DecisionService.for_tenant` (one-off and choose read the whole tenant),
   since the service returns rows without names. A `name_of` method would be cheaper; not designed here.
4. `PostgresDecisionStore` wraps every SQLAlchemy error, a deferred-trigger refusal included, as `StoreUnavailable`
   (3C2's pattern); `MemoryDecisionStore` raises `DecisionRefused("RECORD_INVALID")` for the same cases.

## Open questions
- **Q1** (default applied): `option_effect_missing_check` is shadowed by `option_effect_change_or_missing`, which
  runs first and raises `cannot get array length of a non-array` (22023) on a non-array; the row is refused, not by the
  named check. Test 6b asserts that message (`SHADOWED`). Alternative: guard the rule with `jsonb_typeof` or rename it.
- Q2: keep deviation 4 as is, or give both stores one error for a refused record? (6c writes runs through it.)

## Review focus
Spec §7 questions 1-6; the two deferred triggers; the guard's nested `CAST(:name AS jsonb)` pattern (I6); the lock and
`decision_once` race; names, never emails, in every command line and the read.
