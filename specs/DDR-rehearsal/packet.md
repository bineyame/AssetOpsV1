# DDR review packet (build)

Builder (Claude), 2026-11-21. Branch `task/DDR-rehearsal`, worktree `/opt/assetecon/AssetOpsV1-ddr`, base `main`
06a5b9e3e or later merged in (holds 3C2 unit 2: `git grep -n StoreAgreedActions --
backend/assetops_backend/deep_dive/composition.py` shows lines 12 and 42). Spec rev 3, rulings D-DDR.1-15, reviewer
guide rev 3. `USER_REVIEW_REQUIRED`: no for the build (a non-product check). The owner walks the rehearsed screen
after spec §5 (coordinator).

## Outcome

`python -m assetops_backend.rehearsal_check --tenant lakeside-power --month 2026-10` reads what each of the twelve
runbook steps leaves and prints ten gate lines (codes and facts only); the Postgres test runs the twelve steps through
their commands and shows the checker's first failing gate move G2 -> G3 -> G5 -> G6 -> G7 -> G8 -> G10 -> none.

## Files

- Product: `backend/assetops_backend/rehearsal_check.py` (new); `structure_snapshot/store.py` and
  `structure_snapshot/adapters/postgres_structure_snapshot_store.py` (`portfolio_history`, §2.3). Nothing else under
  `backend/assetops_backend/` or `contracts/` (test 5).
- Fixtures: `backend/tests/fixtures/ddr/` (board budget XLSX, profile, expected records, generator,
  `lakeside-2026-10.expect.json`).
- Tests: `backend/tests/test_ddr_rehearsal_check.py` (tests 6 memory, 7, 8), `backend/tests/test_ddr_rehearsal_postgres.py`
  (tests 1, 3, 4, 5, 6 Postgres), `backend/tests/test_on1_served_tenant.py` (section 3 table only).
- Runbook: `Docs/engineering/operator-deep-dive-runbook.md` and `specs/ON1-operator-tenant/runbook.md` (identical).
- Spec folder: `mid-build-questions.md` (MB1-MB3), `handoff.md` (phase 1), this packet.

## Acceptance (spec §7)

1. Runbook alone, new profile, no code change: test 1 runs S1-S12 through each command's `main(argv)` (S3 by
   subprocess), every exit 0; test 5 passes (only the allowed product files).
2. Step 5's gate to the cent, "not yet reconciled" until the corrected statement: test 1's S7 body has World A's
   figures (tiles, by-Site rows and totals, cash) and every money word ", not yet reconciled"; S10 equals the
   expectation file's `screen` on §3.4's compared keys (G9 PASS) with Kisiwa's notice.
3. Fails naming the step when skipped or bypassed: test 3 (no S5 -> G5 `STATEMENT_FIELD`, no S6 -> G6
   `AFTER_NEXT_STATEMENT`, no S8 -> G7 `STATEMENT_MISSING`, no S9 -> G8 `BEFORE_STATEMENT`, emulated budget -> G3
   `READER_MISSING`, no S2 -> S4 exit 2 `PROFILE_NOT_ADMITTED` and G2 `PROFILE_MISSING`); test 4 (records without an
   upload -> G3; `--by service:shortcut` -> G6).
4. The agreed change is an Action shown on the screen: test 1 after S11 and S12 is exit 0 with ten PASS lines; S12's
   `actions.rows[0].title` is S11's title; after S9 G10 is `ACTION_MISSING`.
5. Each gate checks its person, real clock: G2 admitter, G3 submitter/accepter, G5/G7 recorder, G6/G8 builder, G10
   creator/owner; tests 8(a), 8(b), 4(b); test 1 runs on the real clock (`record_action` clock injected at real now).
6. Plants and mid-build count: every plant fails (below); mid-build count 3 (MB1 answered; MB2, MB3 open with
   defaults applied).

## Checks run (revision `00a1d5002` unless noted)

- `pytest tests/test_ddr_rehearsal_check.py tests/test_on1_served_tenant.py` (no DB): 24 passed.
- Postgres, `tools/heavy-slot.sh --db --wait-seconds 3000 -- pwsh -NoProfile -File tools/run-host-tests.ps1 --
  backend/tests/test_ddr_rehearsal_postgres.py`, at `e128707a6`: 10 passed, 2 failed in 122.15 s (module wall time;
  cap 245 s). The two failures were test-side and are fixed in `00a1d5002`: test 4a asserted `ACCEPTED` where 3A1
  answers `STORED`, and the emulated-budget skip case raised the screen's 500 (PF1 below) out of `TestClient`.
  Rerun of those two cases at `00a1d5002`: 2 passed, 10 deselected (`-k "emulated_budget or test_4a"`), in the heavy slot; log `/opt/assetecon/evidence/DDR-rehearsal/build-2026-11-21/F.log`.
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): passed. `tools/check-agent-workflow.ps1`: passed.
- `tools/checks/statement_catalogue.py`: OK (no `HAND_BUILT_NEW`; the module is not in the baseline or allow file).
- Fast check-all: All 42 guards passed (blocking; 0 advisory, 0 warned); log `/opt/assetecon/evidence/DDR-rehearsal/build-2026-11-21/check-all.log`.
- Logs: `/opt/assetecon/evidence/DDR-rehearsal/build-2026-11-21/`.

## Plants (each applied, its test run, reverted)

| # | Result |
|---|---|
| P1 | test 4a fails (rc 1). Note for the reviewer: the first failing gate under P1 was G4 `FIGURE` (KISIWA-001 revenue), not G3 `READER_MISSING` as the test asserts. The test fails, so the plant is caught, but G3 itself may not see P1's fault; log `G.log` |
| P2, P3, P4 | test 3 fails: the no-S5, no-S6 and no-S9 cases each fail their assertion (no step skipped is detected otherwise) |
| P5 | test 1 fails (two lines, not ten); test 8(a) fails |
| P6 | test 1 fails (progress: S4 -> G4, `TARGET`) |
| P7 | test 1 fails: S4 exit 2 `EXPORT_PATHS_MIXED` |
| P8, P14, P16 | phase 1 (handoff): tests 6, 7, 9 fail |
| P9 | test 8(e) fails |
| P10 | test 8(c) fails |
| P11 | test 8(a) fails |
| P12 | test 8(b) fails |
| P13 | test 8(d) fails |
| P15 | test 8(g) fails |
| P17 | test 8(f) fails |

## Known deviations

- MB1 (answered): runbook section 6 runs `source_profile list`; ON1's `EXPECTED` has 13 entries.
- MB2: G2 expects the stored status `ILLUSTRATIVE` (3A6 sets the row's status from the database; `ADMITTED` is the
  command's output state).
- MB3: Tariff arrives with the emulated billing export, so four screen literals drop "tariff" (Revenue drawer texts,
  two not-available rows).
- The expectation file's `screen` was transcribed from 5c's World A fixture by a scratch script of named textual edits
  (World B's reconciled words and standing from 5c's Postgres test 9(c), including "(Declared)"; §3.4's names, order,
  fuel text and setup row), then MB3's four literals by hand. Never from a run. Only MB3's literals differed from the
  first rehearsal read.
- A tenant lookup that fails before the gates exits 2 `READ_FAILED` (not in §2.1's list). `NO_DATABASE` and
  `NO_KEY_DIR` are checked even when reads are injected (the environment is the command's input; test 8 sets both).
- G6's upper bound is the organisation statement right after the first; G7's statement and G8's bound are the latest.

## Product finding (for the Architect; not fixed in DDR)

- **PF1 (fixed in 5c's r5, on main).** With the emulated `budget.csv` loaded the screen answered 500 (`VOCABULARY_UNKNOWN deep_dive.driver_detail actual_quantity`); after r5 the emulated-budget case asserts S7 and S10 answer 200 and G3 `READER_MISSING profile.ddr-board-budget.v1`.

## Residual risk and review focus

- G9's compared keys against §3.4 (`SCREEN_KEYS`, `rehearsal_check.py`); MB3's literals; D-WK.12's one-figure read of
  the `screen`.
- Tests 3 and 4 share the module's pooled database; each case empties the tenant closure first.

## Review round 1 fixes (`2a62754c2`, main with 5c r5 merged in at `ffba4bdb2`)

- M1: test 4a submits S4's files without acceptance, ingests each upload's own batch through `CommercialRecords.ingest`,
  declines the uploads, asserts every reader's kind (CHARGE, RECEIPT, EXPENSE, BUDGET_LINE) exists and no upload is
  held, then asserts G3 `("READER_MISSING", {"reader": "billing-illustrative-1"})` and G4 not failing.
- L1: `test_l1_g9_compares_exactly_the_spec_keys` pins `SCREEN_KEYS` and the file's `screen` keys to §3.4. Plant
  (drop `not_available`): the test fails.
- L2: as PF1 above. L3: `test_l3_every_rehearsal_database_line_is_a_test_name` (regex over both runbook copies).
- L4: G3 checks SUBMITTER and ACCEPTER on every accepted upload of a reader; `test_l4_...` (plant: first upload only)
  fails.
- r5's `bridge.scale` and step `bar` added to the expectation file's `screen` by hand from 5c's updated World A fixture.
- No-DB: 27 passed. Postgres full file (heavy slot, `--db`): 12 passed in 140.62 s. Faithful P1 (G3 passes when records of
  each reader's kind exist and never reads uploads): test 4a fails (no gate fails at all, so G3 is the only gate that sees
  the fault). M1 closed, coordinator-verified. Log `/opt/assetecon/evidence/DDR-rehearsal/build-2026-11-21/chain3.log`.
  Check-all: All 42 guards passed (blocking; 0 advisory, 0 warned)..

## Rehearsal run (§5.1), 22 Nov

- G9 failed on the 22 Nov rehearsal (`SCREEN` at `$.cash.text`): the expectation file predated 5c cash fix r6 (D-5C.29). A key-by-key diff of World A's served screen (same path as G9, `Stores.screen`) against the file's `screen` found one drifted path, `$.cash.text`; the cash table (rows, Billed column, total) already matched. Refreshed that one string to "Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in transit and $668.00 is still outstanding." The fixture SHAs are unchanged (the XLSX and profile did not change).
- Rerun of the checker only, on the existing `assetops_rehearsal_ddr1_test` with this branch's file: G1 to G10 all PASS, exit 0 (`/opt/assetecon/evidence/DDR-rehearsal/run-2026-11-22/check-rerun.log`).
- DDR test files on `fix/ddr-expect-r6`: 26 passed, 1 failed. The failure is `test_5_no_code_for_the_new_layout`, which diffs `main...HEAD` and expects DDR's own branch changes (`rehearsal_check.py`, the profile); on a branch off post-merge main it fails by construction, not because of the cash text.
