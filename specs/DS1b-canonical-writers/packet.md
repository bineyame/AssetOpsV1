# DS1b review packet: the generator's canonical record writers

Implementer (Claude), 2026-11-20. Spec `spec.md` rev 2, rulings D-DS1B.1 to D-DS1B.8 with handshake round 1
(R1 to R12, P1 to P12). Branch `task/DS1b-canonical-writers`, base `main` `b28326e48` (2a merged; T2 on main).
Worktree `/opt/assetecon/AssetOpsV1/.claude/worktrees/ds1b`. The spec's §0 named `/opt/assetecon/AssetOpsV1-ds1b`;
the dispatch named only "a new worktree", so the path differs and nothing else does. Discovery review (W5).
Not merged.

## Commits

| Commit | What |
|---|---|
| `f0e86e0c6` | T1-T9 tests, written first (W2) |
| `6691f3dee` | `world/records.py`, the `records` CLI (P1, P6), docstrings of `leaves.py`, `world/__init__.py`, `conftest.py` |
| `741099a9c` | `golden/records_v1.json`, written by `--update-golden` on the unchanged fixture view |
| `3ed5f3dee` | T5: asserts directly that no ADJUSTMENT is 0 (the R6 mutation had been caught only by the golden) |
| (finish) | this packet, `mid-build-questions.md`, spec status, `specs/INDEX.md` row, `.ai/state/data.md` + index line |

Scope (`git diff --stat b28326e48...HEAD`): only the files in reviewer guide §2 plus the finish bookkeeping.
`history.json`, `golden/history_v1.json`, the pack, the manifest and `world/history.py` are unchanged.

## What was built

- `records.py`: `STRUCTURE_KEY`, `ACTUAL_WRITERS` (field to `Writer(kind, code, ref, source_type)`), `PASS_THROUGH`
  (literal, spec §2.2 row for row), `READ_IN_EXPRESSION` (R4's set per structure key), `RecordsResult`,
  `build_records(view, history)`, `batch_file_name`, `money_text`. It imports only the standard library,
  `assetops_contracts.canonical` and the world modules (`leaves`, `months`, `view`).
- Output on the fixture: 7 batches, 142 records. Lakeside: expense_ledger 23 EXPENSE, budget_workbook 24. Harvest:
  expense_ledger 23, customer_invoicing 1 ADJUSTMENT (Thika October, -108.00), budget_workbook 40. Metro: expense_ledger 11,
  budget_workbook 20. There is no lakeside `billing_export` batch, because no mini-grid `liability` is present, so no
  empty batch is written (R6).
- **Unwritten counts** (341 rows): `NOT_A_MONTH_RECORD` 244, `NOT_READ_BY_A_LEAF` 43, `NOT_OWN_LINE` 36,
  `READ_IN_AN_EXPRESSION` 12, `ESTIMATED_NOT_RECEIVED` 3, `ZERO_NO_ROW` 3 (Thika actual `liability` 0 in Jul, Aug, Sep).

## Done criteria (spec §6)

| # | Question | Answer and evidence |
|---|---|---|
| 1 | 2a format, golden digests, same across processes | Yes. T1 re-parses every batch with no refusal, and digests equal the golden. T2 runs the CLI under `PYTHONHASHSEED` 1 and 2 with identical bytes, equal to the in-process batches. By hand on the pack manifest: `diff -r` was identical, and every file's sha256 equals the fixture golden. |
| 2 | Every line equals its input to the cent, Jul-Oct, nine Sites | Yes. T4 checks record by record: EXPENSE = field, ADJUSTMENT = -liability, BUDGET_LINE = own field. It covers all four months and nine codes. Hand check (probe P2): Kobo Oct `om` 600.00 / `staff` 500.00 (view 600.0 / 500.0), plan `om`/`staff` the same. Thika Sep `maint` 80.00 / `staff` 350.00 (history 8000 / 35000 cents), plan `crate_days` 8400, plan `liability` 0.00, actual `liability` 0 listed `ZERO_NO_ROW`. |
| 3 | Nothing written that the evaluator does not read; every unwritten field listed | Yes. T5 checks that, for every Site, month and side, written and listed are disjoint and their union equals the present fields. T3 derives `PASS_THROUGH`, `ACTUAL_WRITERS` and `READ_IN_EXPRESSION` from the manifest. P4: every BUDGET_LINE `factor_id` is a `PASS_THROUGH` leaf, and its `line_ref` is that leaf's first field. |
| 4 | `history.json` byte-identical; nothing outside §4 changes | Yes, see "Golden byte identity". |
| 5 | `source-emulated`, nothing stronger | Yes. T1 asserts the provenance and scans every output byte string (batches and `unwritten.json`) for `RECORDED`, `Recorded`, `field-integrated`, `observed-financial` and `bench-tested`: no hit. A by-hand grep of the manifest run's output also had no hit. |
| 6 | No estimate written; GAP-1 intact; no assumption overwritten (T9) | Yes. T5: `ESTIMATED_NOT_RECEIVED` is exactly Kisiwa `om`, Thika `maint` and Kasarani `maintenance` for 2026-10. T9 checks against `missing-records.json` (plan, ASSUMPTION): no October BUDGET_LINE names a listed leaf, and no `delivered_kwh`, `necessary_l` or `kwh_2200_2400` line exists in any month. `NOT_OWN_LINE` fields: `billed_kwh`, `diesel_l`, `offpeak_kwh`, `kwh`. |
| 7 | T2 merged | Yes. T2 is on `main` (merge `66ca6d0f8`, before base `b28326e48`). `tools/checks/neutral_tests.py` passes from the worktree (below). |

## Tests and checks (actual output, revision `3ed5f3dee` unless stated)

- `PYTHONPATH` = the worktree's `backend:backend/tests:contracts:simulator:gateway:field:host:tools`. Module paths
  checked first: `records.py`, `assetops_contracts/canonical/__init__.py` and `assetops_backend/__init__.py` all
  resolve under the worktree.
- `pytest simulator/tests/world -q` gave `122 passed in 5.22s` (wall 6 s, at `741099a9c`). The 26 DS1b tests
  are in `test_records.py`.
- `pytest backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py -q` gave `180 passed in 2.61s`.
- `.venv/bin/python tools/checks/neutral_tests.py` (T2's guard, from the worktree) exited 0 in 8 s:
  `487 passed`, `simulator/tests 481 passed`, `contracts/tests 6 passed`. The guard asserts the packages load from
  this tree.
- `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/check-all.ps1` (fast, at `3ed5f3dee`): exit 0, wall 78 s, `All 40 guards passed (blocking; 0 advisory, 0 warned)`, including `Neutral package tests (T2)`, its self-test and `Select-tests neutral cases (T2)`. Log: session scratchpad `ds1b/check-all.log`. On the finish commit `4e4e22158`: `check-agent-workflow.ps1` reported `Agent workflow check passed.`; `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the shared `.venv`, because the worktree has no `.venv`; without it the chain-structure guard refuses to run) reported `Architecture check passed.`, exit 0; `tools/check-decision-index.py` reported `OK (571 indexed decision IDs ...)`.
- `frontend/node_modules` is a symlink to the main checkout's copy (untracked, not committed).

### Guards fail on real violations (introduced, watched fail, reverted with `git checkout`)

| Mutation in `records.py` | Failing tests |
|---|---|
| R1: the first present alternative wins (the pre-R1 rule) | T1, T5 `unwritten_list`, T5 `zero_handling_and_no_totals`, **T9** |
| R2: ESTIMATED lines written | T1, T5 `unwritten_list` |
| R5: provenance `observed-financial` | T1 |
| R6: zero liability writes a row | T1, T5 `zero_handling` (after `3ed5f3dee`; before it, the golden only) |
| T3: `billed_kwh` dropped from `PASS_THROUGH`; `kwh` dropped from `READ_IN_EXPRESSION` | T3 `pass_through`, T3 `read_in_an_expression` |

## Golden byte identity

- `golden/history_v1.json` and `Docs/.../history.json` are untouched (`git diff b28326e48 --` is empty). DS1a's T1 and
  T2 pass inside the 122.
- By hand: `world_history.py generate`, from main's checkout (`b28326e48`) and from the worktree, on the pack manifest
  and on the fixture view, gave `cmp`-identical bytes. The worktree output also equals the committed `history.json`
  (sha256 `9cb1b6bf...fd4c9`).

## Honesty checks

- Estimates: three ESTIMATED October lines are listed, never written (R2, D-DS1B.7). GAP-1 stays in the store.
- Fallbacks: no budget line comes from a later alternative (R1). T9 checks this independently of the rule.
- Labels: `source-emulated` only, with the byte scan in T1 (R5). The references `om-contractor`, `payroll` and
  `finance-lead` are source text.
- Zeros: an actual `liability` of 0 gives no row. Thika's plan `liability` 0 gives a `0.00` BUDGET_LINE (R6).
- Inputs: `records.py` reads the view (via `ManifestView.from_document`) and the history only. T6 shows that neither
  input is mutated.

## Mid-build questions: 2

`mid-build-questions.md` Q1 (the reason for an ESTIMATED zero `liability`) and Q2 (whether exponent text such as
`"1e-05"` is decimal text). Neither case occurs in the fixture or the manifest (checked), so no output depends on the
answer. The provisional behaviour is named there, for the Architect to rule.

## Known deviations

- Reviewer probe P1 (`grep records.py` for `oracle|checks|expect|derived`) has one hit:
  `records.py:74 "expected_technical_loss_kwh"`. This is spec §2.2's own field name in the literal table, not a read
  of an expectations key.
- `records.py` exports a few names beyond §4's list: `Writer`, `READ_IN_EXPRESSION` (R4's set, which T3 derives),
  `money_text` and the reason constants. No contract change.
- The October month label is the view's `accounting_period` ("October is read from the view"). It equals
  `history.anchor_period` in the fixture and the manifest.

## Not verified

- The CLI was not run into `/opt/assetecon/generated/ds1b-<rev>/` (the coordinator's step, spec §4). The by-hand runs
  went into the session scratchpad.
- The full backend and frontend suites were not run (not scheduled). Fast check-all only.
- DS3 loading, 3A3 native files and 3A5 labels are downstream and untested here. The reconciliation risk of D-DS1B.8
  (finer 3A3 and DS2 records against these month lines) is for those slices.

## Review focus

T3's derivations (derived, not copied), T9's independence, the unwritten-list completeness test (T5), and the
CLI's refusal path (exit 3, nothing created).

`USER_REVIEW_REQUIRED`: the spec does not set it. The slice is non-screen and changes no direction, UI or narrative,
so the builder's reading is **not required**. The coordinator makes the call.

## Review round 1 follow-up

Tests only, except one guard in `records.py` (item 3). Commit `d9c94c4a4` (after `git merge main`, which brought MB1 and MB2).

- **L1.** `test_t3_actual_writers_derived_from_leaf_sources` now asserts spec §2.1's source-type column as a literal. Plant: COLD_CHAIN `liability` moved from `customer_invoicing` to `billing_export` fails T1 (golden) and T3 (new assertion); reverted.
- **MB2.** T7 gains `test_t7_exponent_text_is_normalised_mb2` (October plan `crate_days` `"1e+03"` is written as 1000, and no batch or unwritten byte string matches `[0-9][eE][-+]?[0-9]`) and `test_t7_exponent_text_out_of_bounds_refused_mb2` (`"1e+30"` is refused `DS1B_FORMAT`).
- **Overlap.** `build_records` refuses `DS1B_FORMAT PERIOD_IN_HISTORY <month>` when `accounting_period` is in `history.meta.months`. No new `DS1B_` code: `DS1B_FORMAT` is the code the duplicate would already have failed under. Test `test_t7_period_inside_history_months_refused`; plant (guard disabled) fails only that test; reverted.
- **Results.** `simulator/tests/world` 125 passed; `tools/checks/neutral_tests.py` 484 simulator + 6 contracts passed. `golden/records_v1.json` and `golden/history_v1.json` are unchanged from `943f49dac`; the generated history's SHA-256 equals the golden's `file_sha256`; `Docs/.../history.json` unchanged.
