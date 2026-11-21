# 4d packet: the monthly litre split

Branch `task/4d-litre-split` (base `main` b8b812f23), commits 45a4d4693 (unit 1), 8843b9fb6 (unit 2) and c17257a79
(unit 3), plus the docs commit. Spec rev 2, rulings D-4D.1-15. No migration, no new intake, no route, no screen.
`USER_REVIEW_REQUIRED: true` (analytics and money semantics); the merge waits for the review. **Mid-build questions: 1**
(`mid-build-questions.md` Q1, nothing stopped).

## Files (module paths)
- New: `assetops_backend.structure.litres.{rules,source,inputs,composition}`, `backend/tests/test_4d_litre_split.py`
  and `test_4d_litre_split_postgres.py`.
- Edited (all on the §0 list): `structure/sources.py` (three rows PROVIDED, `LITRE_LEAVES`), `structure/composition.py`
  (the fourth builder), `PostgresFuelBalanceStore.read_at`, `PostgresAssessmentStore.dispatch_spans` and `dispose`.
- W6 sweep (test lines that pinned HELD_NOT_CALCULATED): `test_3b3_structure_evaluate.py` `STATE_TABLE` (:76) and
  `PROVIDED_CAUSE` (:86, the leaves read alone give NOT_CONNECTED; this line is not on §0's list but the same pin),
  `test_4b_money_leaves.py` `STATE_TABLE` (:55-62). No 3B7a test pins them. `specs/3B3-structure-read/spec.md:209`
  is a merged slice's record, left as is. `structure/attribution/` diff: empty.

## Done questions (spec §7)
1. Yes. KOBO-OCT gives 730.000 / 330.000 / 120.000 L (indeterminate 10.000, burned 1180, modelled 1060), and V1-V26
   their literals or notes (tests 1, 2).
2. Yes as numbers: `fuel_cost` −600.00 splits −37.50 / −412.50 / −150.00 through 5b, root −562.00, 5b unchanged;
   Kisiwa and Mto `NOT_SPLIT`/`DETAIL_NOT_AVAILABLE` with `GENERATOR_OR_TANK_NOT_DECLARED`; portfolio fuel −755.00
   3 of 3, `diesel_l` 1180.000 against 700, 1 of 3 (test 6). The litre rows' effects are `Decimal("-600.00000")`
   etc. (Q1).
3. Yes. Every litre is MODELLED with origin `unknown`; INDETERMINATE and unclassified running is necessary
   (V24, P1, P16); test 3 checks necessary + candidate against the test's own slot sum.
4. Yes. Each case gives the note naming its missing record and the value None (V2, V4, V5, V10, V11, V13, V18, V19,
   V25, V26).
5. Yes. MONTH_OPEN (V12); NOT_ASSESSED, UNAVAILABLE, an unknown class and overlap give NOT_CALCULATED_YET
   (V8, V15, V21, V23); STALE_PROJECTION, FAILED and PENDING give NOT_ASSESSED (test 10).
6. Yes. All 20 plants fail (below).
7. Yes. `git diff main...HEAD --stat` shows the §0 files, the package, the two test files and the docs.
8. No: 1 (Q1).

## Checks (real output)
- `test_4d_litre_split.py`: 65 passed. Before any code it failed at collection, for each unit's tests.
- `heavy-slot.sh --db -- run-host-tests.ps1`: 4d Postgres, 3B3, 3B7a, 4b, 5a, 5b, AR3, K3 and S3 dispatch (both
  kinds): 369 passed, 3 failed, 1 skipped (5b's branch check), 68 s. The 3 failures were `ImportError`s
  (`fixtures.TWIN_TANK_TEMPLATE`, `probe_kisiwa_fuel`) because `host/tests` and `tools` were not on PYTHONPATH.
  With those on the path, the K3 files gave 28 passed.
- Plants P1-P20 were applied one at a time and restored with `git checkout`, leaving the tree clean. Each failed its
  named test. P11 failed Postgres test 2 (`NotNullViolation`, not "read-only transaction"). The plant script is
  outside the repo. Test 3 does not catch P1, because the invariant still holds; test 1 catches it.
- check-all, fast: all 40 guards passed in 83 s. `check-architecture` passed (with `ASSETOPS_GUARD_PYTHON`).
  `check-agent-workflow` passed.
- `select-tests --base main` chose 384 of 550 files for a Docker run. That run is not done here: Docker is excluded
  by the dispatch. The coordinator schedules it.
- Layout evidence: not run. Nothing is layout-sensitive (no UI).

## Known deviations and residual risk
- Q1: money effects carry five places through 5b. 5c must format them.
- Rule 5 over the window reads only the days the adapter holds, `[lo − 24 h, hi + 24 h)`. When the opening dip lies
  in the first 3 h of that range, the day before it is not read.
- `candidate_l` names the no-load revision only when a CANDIDATE span had idle time (D-4D.9, "when idle time was
  used").
- Live structure reads now run `select_dispatch_days_on` over 34 days per MINI_GRID Site-month (P6; this is
  3B7b's concern).

## Review focus
`rules.py` precedence against §2.3; `inputs.py` K3 curve choice and `valid`; `dispatch_spans` CURRENT-only spans.
