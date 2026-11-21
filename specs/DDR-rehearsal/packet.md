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

Run 2026-11-21 23:41Z to 23:55Z (22 Nov, server-local). Database `assetops_rehearsal_ddr1_test`; key folder
`/opt/assetecon/keys/assetops_rehearsal_ddr1_test` (mode 0700). **R = `bfe073171fbb31886473f5805c1454d9b4c5571c`**
(`main`; alembic head `0071_person_on_actions`). Commands run from `/opt/assetecon/AssetOpsV1` (the checkout the venv's
editable `assetops_backend` points at), every database step inside `tools/heavy-slot.sh --db --label ddr`; no `PG*`
exported; nothing served. Logs: `/opt/assetecon/evidence/DDR-rehearsal/run-2026-11-22/` (one `<step>.log` each,
`times.txt`, `coord-*.txt|log`).

**Result: G9 FAIL (`SCREEN`, `$.cash.text`); G1-G8 and G10 PASS. The run stopped there (S12 is the last step).**

### Steps (wall time is the command's own, inside the slot; exit)

| Step | Runbook | Wall | Exit | Output (short) |
|---|---|---|---|---|
| Coord. 2 | create + `alembic upgrade head` | 451.3 s (mostly waiting for a heavy slot: both busy) | 0 | at head `0071_person_on_actions` |
| Coord. 3 | `install -d -m 700 "$KEY_DIR"` | 0.01 s | 0 | mode 700 |
| S1 digest | 4 | 0.36 s | 0 | 64-char digest |
| S1 check | 4 | 1.27 s | 0 | plan; `roles_digest` = `DIGEST` |
| S1 apply | 4 | 2.33 s | 0 | tenant id recorded (evidence `tenant-id.txt`) |
| S1 set-password x3 | 4 | 2.60 s | 0 | one id per person |
| S2 admit + list | 6 | 2.93 s | 0 | `ADMITTED`, `profile.ddr-board-budget.v1`, 16 rows; `admitted_by` = Wanjiru |
| S3 write + replace | 7 | 0.96 s | 0 | billing, collections, expenses, board budget xlsx (+ `unwritten.json`) |
| S4 load | 7 | 2.25 s | 0 | 4 uploads ACCEPTED (120, 113, 15, 16 records; 0 refused) |
| S5 draft figures | 8 | 1.43 s | 0 | `NOT_MATCHED`, opens false (fuel −105.00 vs 51.00 allowed) |
| S6 prepare | 9 | 4.34 s | 0 | snapshot A, 3 Sites, none excluded |
| S7 read | 10 | n/a | not run | no server for this tenant (serving is §5.2) |
| S8 final figures | 8 | 1.38 s | 0 | `MATCHED`, opens true |
| S9 prepare | 9 | 4.39 s | 0 | snapshot B |
| S10 read | 10 | n/a | not run | as S7 |
| S11 action | 11 | 1.01 s | 0 | Action Open, owner Peter, by Amina (executive) |
| S12 read | 10 | n/a | not run | as S7 |
| S12 check | 11 | 7.52 s | **4** | `DDR_GATE_FAILED G9 SCREEN` |

Analyst time for S1-S12 commands: about 33 s of command time; about 4 min 35 s elapsed from digest to the check's end (slot waits
and reading outputs).

### Checker output (verbatim)

```
DDR_GATE_FAILED G9 SCREEN
{"gate": "G1", "step": "S1", "state": "PASS", "code": null, "facts": {}}
{"gate": "G2", "step": "S2", "state": "PASS", "code": null, "facts": {}}
{"gate": "G3", "step": "S4", "state": "PASS", "code": null, "facts": {}}
{"gate": "G4", "step": "S4", "state": "PASS", "code": null, "facts": {}}
{"gate": "G5", "step": "S5", "state": "PASS", "code": null, "facts": {}}
{"gate": "G6", "step": "S6", "state": "PASS", "code": null, "facts": {}}
{"gate": "G7", "step": "S8", "state": "PASS", "code": null, "facts": {}}
{"gate": "G8", "step": "S9", "state": "PASS", "code": null, "facts": {}}
{"gate": "G9", "step": null, "state": "FAIL", "code": "SCREEN", "facts": {"path": "$.cash.text"}}
{"gate": "G10", "step": "S11", "state": "PASS", "code": null, "facts": {}}
```

**Likely cause (coordinator reading, not fixed, not worked around).** The expectation file
`backend/tests/fixtures/ddr/lakeside-2026-10.expect.json` (last changed in `2a62754c2`) still holds the pre-r6 cash
sentence: "In October, $8,870.00 was collected against $9,785.00 expected; $668.00 is still outstanding and $150.00
is paid but in transit." 5c cash fix r6 (`8bac2bed4`, D-5C.29, an ancestor of R) rewrote that sentence as billed =
collected + in transit + outstanding and took "expected" out of it. So the screen on `main` no longer says what the
file expects. G9 stops at the first differing path, so other drifted `cash` keys (if any) are not yet known. Needs an
Architect call: refresh `screen.cash` from r6's sentence (and re-run DDR's Postgres file), then re-run only the
checker on this database (no rebuild needed: the run's records are intact).

### Where the runbook was unclear

1. **`DB_PASSWORD`** is used from step 2 on but the runbook never says where its value comes from. The shell held no
   `ASSETOPS_PG_PASSWORD`; used the compose default (`docker-compose.yml`).
2. **`DIR`** is listed as a variable but never assigned. Used a scratch folder outside the repository; it was deleted
   at the end of this run, so step 12's `rm -rf -- "$DIR"` has nothing left to remove.
3. **"The project's Python on the path"**: commands say `python`, step 2 says `../.venv/bin/python`. Put `.venv/bin`
   first on `PATH`. The venv's `assetops_backend` is an editable install of `/opt/assetecon/AssetOpsV1/backend`, so
   "the repository root" must be that checkout; run from another worktree, `-m assetops_backend...` would still run
   the main checkout's code.
4. **set-password**: the runbook says it reads the password on standard input but not what to choose or where to keep
   it for the people who will sign in. Generated three random passwords, kept at
   `/opt/assetecon/evidence/DDR-rehearsal/run-2026-11-22/signin-passwords.txt` (mode 0600; not shown here). Its
   output (a bare id per person) is not explained.
5. **check's plan**: the `people` list shows index 0 with `OPERATOR_EXECUTIVE`, but the `roles` list has no grant for
   index 0. The runbook says to read "each role"; an analyst cannot tell whether the executive will be granted. (G1
   passed and S11 recorded the Action as the executive, so it was.)
6. **apply's output**: the runbook says it "prints the same plan as done"; it prints the same plan still saying
   `create` everywhere, with only the tenant `id` filled in. An analyst may not read that as done.
7. **`unwritten.json`**: step 7's write leaves this file in `DIR` (31 entries, codes `NOT_ON_PATH_VERTICAL` and
   `NOT_A_MONTH_RECORD`); the runbook does not mention it or say whether it matters. The loader skipped it.
8. **Step 10 (S7, S10, S12's read)**: the runbook says open the page or call the API, but never says how the tenant
   gets served. Not run (serving is §5.2); G9 reads the screen in the checker. Until a serving step exists in the
   runbook, an analyst following it alone cannot do step 10.
9. The spec's S2 row says admit's output carries `admitted_by`; it is `list`'s output, as the runbook says (runbook
   right; spec table wording only).
10. The two runbook copies are identical from the first heading; the specs copy adds one leading comment line (as
    D-ON1.19 says).
