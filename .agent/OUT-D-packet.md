# OUT-D review packet: declared objectives and status

Task `tasks/OUT-D-declared-objectives.md` · branch `task/OUT-D-declared-objectives` (worktree `AssetOpsV1-outD`, from main
833e7c95, OUT-W merged in at f602e7b6) · contract `AssetOpsV1-plan2/.agent/build-sheet-OUT-D.md` · history
`.agent/OUT-D-phase-handoff.md`. USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge).

## Outcome delivered

Each Site outcome can carry a declared objective. Its status is judged against that objective (`outcome-status/2`), and
the board names it on screen with a "Declared objective" line and a Met / Missed / Not checked yet chip. The mini Assure
"Actual against plan" line counts met objectives. The Portfolio Assure card says how many Sites declared targets, and it
never says "no targets" for a Site it could not read.

## Units and commits

| Unit | Commits | What landed |
|---|---|---|
| U1 | 81e95e59 | Migration `0038_out_objectives` (append-only revisions, named CHECKs, site FK, UPDATE/DELETE trigger); 20 head-literal test files; writer guard registration |
| U2 | 16639d83, 91c8d6fd | Pure `outcomes/objectives.py` (MEASURES, `judge`); `outcomes/status.py` `/2` rules 4c/7/7b/7c; review L1-L3 |
| U3 | 1e2e0d02, 994a5462 | `objectives/` store (`declare`, `current`), `declare_objective.py` CLI, `backend/conversions/demo-objectives.json` (6 objectives); `objectives` config domain in the guard |
| U4 | 0f0e8a0d, f6be0782 | `site_outcomes/objective_facts.py`, composer readings, contributor, wire `objectives[]` + `objectives_read`, summary counts; U4 review fixes M1, M2, L1, L2 and the CC-1 On track test |
| U5 | 79c8d40a, da1df531 | Portfolio Assure clause; real-data Postgres test `test_out_d5_objectives_postgres.py`; register R580-R586 + R542 note |
| U6 | eeef72a8 | Captures `.agent/OUT-D-captures/`; task file, CODE_STATE, ACTIVE_CONTEXT |

## Acceptance (§8)

1. **Met.** 0038 round-trips. Every CHECK, the chain and the trigger refuse by name (`test_out_d1_schema_postgres.py`, 23
   passed). The writer guard registers the store and fails on both counters when the INSERT is removed (proven, reverted).
2. **Met.** The demo file declares 6 objectives idempotently (`test_out_d3_*`, 17 passed). CC-1 reads the chamber range,
   with a null `revision_id` (R584).
3. **Met on fakes; On track not reached on demo data (R585).** MISSED gives Needs attention. MET on a complete window gives
   On track: proven for MG-2 and, since f6be0782, for CC-1 on a cold board with no excursion. NOT_JUDGED gives Unknown
   after Opportunity. With no objective, the outcome reads "No objective declared". A failed objectives read is UNKNOWN /
   OBJECTIVES_NOT_READ.
4. **Met, except the count.** Each objective row shows "Declared objective" with its chip, and the mini Assure line counts
   met objectives (both captured). The Portfolio card says "targets declared at 1 site", not 3; see Known Deviations.
5. **Met.** On Kobo real data, the earlier reading at K1 keeps v1 after a v2 is declared later, and the current reading
   shows v2 (D5).
6. See Checks run.

## Real data (D5 Postgres test and captures)

- **Kobo, 2026-10-21.**
  - The dispatch day is unsettled (STALE_PROJECTION), so every row reads Unknown. MG-2 has 0 avoidable / 60 unclear
    minutes, and `unserved_kwh` is None.
  - All three objectives show Not checked yet. The capture shows Cost as "Supply cost per kWh: no generator time longer
    than needed · 0 min longer than needed on this day" with Not checked yet.
  - Assure reads "0 of 3 declared objectives met · 3 not checked yet". The summary count is 1.
  - K1 reproducibility holds.
- **GreenHarvest (policy 2-4°C).**
  - CC-1 is Missed: "chamber held between 2 and 4°C · above 4°C in this window".
  - CC-6 is Missed: "automatic start failed".
  - The row states are NOT_MEASURED / NEEDS_ATTENTION / NEEDS_ATTENTION / WATCH. The count is 1.
- **Depot, 6 Oct.**
  - EV-1 is Missed with "1 interrupted". EV-2 has no line (R583). The board is PARTIAL.
  - The estate summary returns 409 ESTATE_SELECTION_INCONSISTENT (R577).
- **Portfolio (s602b estate).** The Assure card reads "No verified result yet · targets declared at 1 site · no evidence gaps".

## Checks run

- **Focused at f6be0782:**
  - d4: 17 passed.
  - The U4 set (§5) plus d2, d3_declare, a1 and w2_summary_window: 221 passed.
  - OUT-C non-Postgres: 54 passed.
  - `tsc --noEmit`: clean.
  - Portfolio and board vitest: 52 passed.
  - The explicit related-file vitest list at U5: 16 files, 386 passed. `vitest related` crashes on a `.py` import, so I
    used the list.
- **check-all:** 11/11 at f6be0782, with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv.
- **Full vitest at eeef72a8:** 268 s. 144 files, of which 143 passed; 3531 tests passed and 3 failed. All three failures
  are the known `w1f4VerificationStructure` tests.
  - An earlier unplanned run of `src/sites` and `src/estate` also failed evEnergy R347 under load. It passed 12/12 alone,
    and the full run passed it.
- **Full backend:** `toolsun-backend-suite-in-container.ps1 -Tier all` at eeef72a8.
  - Run `20261031-030148-43b8cd`: 4 workers, postgres-test, wall 2295 s (38 min).
  - JUnit: 4458 tests, of which 4455 passed and 3 failed, with 0 errors and 0 skipped.
  - All 3 failures were in d5: `_same_key() takes 4 positional arguments but 5 were given`. This was test pollution.
    `test_out_d3_objective_store_postgres.py` saved `type(store)._same_key`, which is the unwrapped function, and restored
    it as a plain method, so later tests in the same worker called it with `self`.
  - Fixed in dd22af4f, which touches only that test file: it now saves `__dict__["_same_key"]`.
  - Rerun of d3 store and d5 in one worker, in the triggering order (run `20261031-034147-0a63eb`): 4 passed, 76 s.
  - The 20 head-literal Postgres files all passed in the full run: 266 tests, 0 skips.

    | File | Tests | File | Tests |
    |---|---|---|---|
    | d1 schema | 23 | w203 | 5 |
    | s1 bindings | 16 | w204 | 11 |
    | s2 ledger | 33 | w205a | 3 |
    | s405 | 21 | w206 | 7 |
    | s4 store | 13 | w207 | 14 |
    | s4 work | 13 | w401 | 2 |
    | w200 | 14 | w402 | 14 |
    | w201 | 18 | w403 | 11 |
    | w501 | 7 | w503 | 15 |
    | w502 | 11 | w504 | 15 |

  - check-all is 11/11 at dd22af4f.
- **Captures:** 48 of 50 claims passed. Both failures are the cold "app rendered" READY wait, as in OUT-B: the board had
  loaded and every row was measured. No page overflow, at 1425/1425 for 1440 and 390/390 for 390. The only console error
  is a favicon 404. Every DB was dropped, and every server was stopped by PID (`.agent/OUT-D-captures/README.txt`).

## Known deviations

- **R535:** `objective_site_count` is 1 per producer DB, never 3. No combined dataset holds all three Sites, so acceptance
  4's "3 sites" cannot be shown. It is proven on the fake `Boards` instead.
- **R585:** no On track appears anywhere on demo data.
  - Kobo's day is unsettled.
  - GreenHarvest and Depot miss their objectives.
  - The sheet expected Kobo MG-2 Missed. It reads Not checked yet because the day is unsettled. I recorded this and did
    not force it.
- **R577:** the Depot estate summary returns 409, so its count is asserted only when the summary is served.
- **U4 review M2 extends the summary wire.** It adds `objective_sites_unread`, and the board body carries
  `objectives_read`. The Architect ruled this on 2026-10-31.
- **U4 review L1 adds an explainer paragraph** that is not in the mock. It is marked as a MOCK DEVIATION in
  `OutcomeBoard.tsx` and falls under R580.
- **The verdict helpers live in `board.py`**, and the composer helpers in `objective_facts.py`, to satisfy the import
  purity test. The U4 review accepted this.
- **The U3 guard adds an `objectives` configuration-domain entry.** The adapter-isolation rule demanded it. It is a
  tightening, not a loosening.
- **Capture DB names** are `*_outd_test` and `*_outd_audit*`, because the producer tools accept only alphanumeric tags or
  refuse `_test`.

## Residual risk

- On track has never rendered on real data. The path is covered on fakes only (MG-2, and CC-1 since f6be0782).
- The Portfolio clause depends on `objective_sites_unread`. An older backend without the field reads it as 0, so a failed
  board would fall back to the pre-M2 text.
- EV-2 (VALUE, money) is declared, but its only consumer is the Portfolio count.

## Review focus

- The M1 and M2 fixes (`mini.PLAN_NOT_READ`, `read.summary`, `assureDetailText`), and that "no targets" text never
  appears for an unread Site.
- The status `/2` rule order against the B and C goldens.
- The writer-guard change is confined to the new store.
