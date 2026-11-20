# 5a unit 1 packet: budget lines as target lines

Implementer (Claude), 2026-11-20. Branch `task/5a-targets`, worktree `/opt/assetecon/AssetOpsV1-5a`, base `main`
`880ba4dbf`. Spec `spec.md` rev 2 §2 and §5 (step 1 and 2), §6 tests 1, 2 and 10; rulings D-5A.1 to D-5A.4, D-5A.14.
P5 approved: `owner/owner-p5-approved-and-defaults-2026-11-20.md` (D-5A.12 met). Units 2 and 3 not started (wait for
`4b1`). **Mid-build questions: 1** (`mid-build-questions.md` Q1, test 10). USER_REVIEW_REQUIRED: false for unit 1
(no screen; the target figures the owner judges come in units 2 and 3).

## Files

- New: `backend/assetops_backend/structure/targets/__init__.py`, `.../structure/targets/lines.py`,
  `backend/tests/test_5a_targets.py`, `backend/tests/fixtures/targets_lakeside.json`.
- Docs: `spec.md` status line, `mid-build-questions.md` (Q1), `specs/INDEX.md` row, `.ai/state/data.md` + `index-2.md`.
- No existing module edited, no migration. **Overlap with `4b1`:** none in code (4b1 edits `structure/registry.py`,
  `rows_mini_grid.py`, `evaluate.py`; this unit only reads `REGISTRIES`, `FactorRow.is_leaf`, `.money`). Possible text
  conflicts only in `specs/INDEX.md` and `.ai/state/index-2.md` (appended line 155).

Module paths (PYTHONPATH = worktree backend, backend/tests, contracts, simulator, ...):
`/opt/assetecon/AssetOpsV1-5a/backend/assetops_backend/__init__.py`, `.../AssetOpsV1-5a/contracts/assetops_contracts/__init__.py`,
`.../AssetOpsV1-5a/simulator/assetops_simulator/__init__.py`.

## Acceptance (unit 1 part of §7)

- Q2 (each used target names its line and declarer; says when no person declared it): test 1(a) checks every
  `TargetLine` field for Kobo (`om`/`staff` `loader:ds3`, `person_id` None; node lines `person:5a00...0001`), revision
  and intake ids against the store; 2(d) the portfolio `staff` line. 1(b): an unchanged re-upload by person 2 leaves
  `om` with `loader:ds3` (D-5A.14).
- Q4 (two versions or two lines never picked or summed): 2(a) `BUDGET_VERSIONS:budget-2026-v1,budget-2026-v2`, no
  lines, five factors blocked, six unused; a non-factor second-version line still blocks (rule 1 before 2, R7); 2(b)
  `om-extra` gives `{"om": "DUPLICATE_DECLARATION"}`, and 3A4's own duplicate (value None) too; 2(c)
  `CURRENCY_MISSING` (revenue revised without currency) and `CURRENCY_ON_QUANTITY` (`diesel_l` node with USD).
- Extra: `known_at` before step 2 gives `om`, `staff` only; a missing intake raises `budget line without its intake`.
- Q8 (scope): see Files. `grep -n "float(" structure/targets/` returns nothing (test 11 itself is unit 3).

## Checks (revision `26dbbe483` plus docs)

- Focused + regression (no database; not pooled per `backend/TESTING.md`): `pytest test_5a_targets.py
  test_3a4_commercial_months.py test_3b3_structure_evaluate.py` -> `110 passed in 1.37s` (11 are 5a's).
  `test_4b1_stated_nodes.py` is not on `main` yet. No Postgres test in unit 1 (spec §9: unit 3).
- Planted violations (`/opt/assetecon/evidence/5a-targets/u1/plants.txt`; plant, run, `git checkout` revert):
  V1 sum two lines -> fails 2(b); V2 pick latest version -> fails both 2(a); V9a declarer from source system -> fails
  1(a), 1(b), 2(d), known_at; V9b drop person parse -> fails 1(a), 2(d); V14 latest intake touching the lines -> fails
  1(a), 1(b), known_at, missing-intake. Tree clean after.
- `python tools/select-tests.py --base main` -> `mode: full (531 of 531 backend test files)`, "full because:
  backend/tests/fixtures/targets_lakeside.json" (any fixture change selects full). **Full suite not run**: the brief
  schedules full suites through the coordinator; the new fixture is read only by `test_5a_targets.py` (grep).
- Fast check-all: first run (`.../u1/check-all.txt`, 78 s) failed 2 of 40: dependency-direction (test 10's simulator
  import -> Q1) and the spec index (packet not yet written; then a wrong row path, fixed). Final run on the committed
  tree: `.../u1/check-all-3.txt` -> `All 40 guards passed`, 73.9 s wall; estate and pool self-tests skipped (unchanged).

## Known deviations

- Test 10 (DS1b parity) stopped: `backend/tests` may not import `assetops_simulator` (dependency-direction guard).
  The fixture's step 1 was produced from `build_records` output and matches §5's six values; the parity assertion
  waits for Q1's ruling (suggested home: `simulator/tests/world/`).
- Rule 1 "version_ref None with no lines": read as no candidates; with one version whose only lines are non-factors
  the version is still reported (conservative; no test depends on it).

## Residual risk and review focus

- One `latest_revisions` read per Site read, always made (also when nothing is used).
- Declarer join key `(factor_id, version_ref, line_ref, currency, provenance)`; two revisions on one key raise (cannot
  happen for a used line, since 3A4 would have grouped them as a duplicate).
- Focus: rule order in `_classify`, the join, D-5A.14's behaviour.
