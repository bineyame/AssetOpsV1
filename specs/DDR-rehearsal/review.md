# DDR review

## Round 1: discovery review of the build (Claude reviewer, 2026-11-21)

**Summary (verdict ACCEPT WITH FIXES).** Branch `task/DDR-rehearsal` head `172ee4ca8`, diffed against merge-base
`06a5b9e3e` (holds 3C2 unit 2: `StoreAgreedActions` at `deep_dive/composition.py:12,42`). The checker meets §2.1 to §2.4.
Each gate reads its own store. Output is codes and facts only, a failed read becomes `READ_FAILED`, and stderr is
`DDR_GATE_FAILED G<n> <CODE>`. No key path or key content is printed. The fixtures match §3 cell for cell. The screen
literals are World A's plus §3.4, World B and MB3, and nothing else. D-WK.12 holds. The runbook copies are identical,
the database names are `_test`, and the order follows D-DDR.15. All 12 Postgres tests pass on my run.
**One Medium:** test 4a does not catch a faithful P1. I re-planted it as "G3 checks records exist, not uploads", and
test 4a **passed**. Only test 3's emulated-budget case caught it. Three Lows. One product observation for the Architect.
Fix M1 on the branch, then run a verification re-review of M1 only. The Lows are recommended, not blocking.

### Checks run (this revision, `172ee4ca8`, tree clean before and after each plant)

- No-DB: `pytest tests/test_ddr_rehearsal_check.py tests/test_on1_served_tenant.py` (heavy slot): **24 passed**.
- Postgres: `tools/heavy-slot.sh --db --wait-seconds 3000 -- pwsh -NoProfile -File tools/run-host-tests.ps1 --
  backend/tests/test_ddr_rehearsal_postgres.py`: **12 passed in 143.45 s** (238 s wall with slot wait; under the
  245 s cap).
- Fast check-all (`tools/heavy-slot.sh -- pwsh -NoProfile -File tools/check-all.ps1`): **All 42 guards passed
  (blocking; 0 advisory, 0 warned)**, 144.5 s wall. This includes architecture and agent-workflow.
- By hand:
  - `diff` of the two runbook copies below the source header: identical.
  - `git grep assetops_rehearsal`: every hit ends `_test`, except two history/sweep lines (`DDR rulings.md:99`,
    `ON1 rulings.md:191`), which D-DDR.12 keeps.
  - ON1's `EXPECTED` has 13 entries (MB1), in D-DDR.15 order. Its diff touches only the section 3 table.
  - Fixture SHA-256: profile `3752d604…`, XLSX `2f629a1f…`. Both equal the expectation file's.
  - A scripted diff of the 5c World A fixture against `screen`.

### Findings

**M1 (Medium, acceptance gap, spec §4 test 4a and plant P1).** `backend/tests/test_ddr_rehearsal_postgres.py:270-297`.
- **What is wrong.** The spec says "S4 replaced by writing *the same records* through 3A1's service directly". The test
  writes only `lakeside-power.expense_ledger.json` (line 288), and it does not run S4 at all. So billing, collections
  and budget records are missing too. The case cannot tell "records without an upload" from "no records".
  - I re-planted P1 faithfully: G3 passes when records of each reader's kind exist (`CHARGE`, `RECEIPT`, `EXPENSE`,
    `BUDGET_LINE` via `latest_revisions`), and never reads uploads.
  - Under that plant, test 4a **passed**: G3 raised `READER_MISSING billing-illustrative-1` because no billing records
    exist.
  - Only `test_3_the_emulated_budget_loaded_fails_g3` failed (first gate G4).
  - The builder's P1 (`return` at the top of G3) is a "G3 disabled" plant, not the guide's P1. That explains the
    packet's G4 note.
  - The real G3 does detect the fault, because it reads `held_uploads`. It is the test that does not prove it.
- **Why it matters.** Spec §7 Q3 ("fails when bypassed") rests on test 4a for G3, and the reviewer guide names P1 →
  test 4(a). As written, a records-based G3 passes the shortcut test.
- **Fix.** Ingest every file that S4 would have loaded through `CommercialRecords.ingest`, not only the expense ledger:
  - billing, collections and expenses from `world_history.py records`;
  - the board budget's records from `ddr-board-budget.expected.json`, or the equivalent.

  Then assert G3's facts as well as its code, e.g. `c.failed["G3"] == ("READER_MISSING", {"reader":
  "billing-illustrative-1"})`, with G4 passing when the record set is complete. Re-run the faithful P1 above: test 4a
  must fail.

**L1 (Low, missing test).** `backend/assetops_backend/rehearsal_check.py:60-61` (`SCREEN_KEYS`) and
`backend/tests/test_ddr_rehearsal_check.py:235-246`.
- **What is wrong.** Nothing pins the compared-key list to §3.4. My own plant dropped `"not_available"` from
  `SCREEN_KEYS`, and all 12 no-DB tests still passed. Test 1 cannot catch it either, because dropping a key only
  loosens G9.
- **Why it matters.** It is the risk the packet itself names (G9's keys against §3.4).
- **Fix.** Assert `check.SCREEN_KEYS` equals §3.4's list as a literal, or have 8(c) also change one `not_available`
  row and one `fresh.text`.

**L2 (Low, missing assertion, PF1).** `test_ddr_rehearsal_postgres.py:157-159` and `:257-259`.
- **What is right.** The read records a 500 as the step's exit (`raise_server_exceptions=False`) and does not hide it.
  Test 1 asserts exit 0 on S7, S10 and S12, so a 500 on the rehearsal path fails there.
- **What is wrong.** The emulated-budget case never asserts the 500 it records. When 5c's `fix/5c-backend-r5` lands,
  nothing shows the change.
- **Fix.** Assert `rehearsal.exits["S7"] == 500`, with a comment naming PF1. After the 5c fix, flip it to `== 0`.
  Also assert that G9's line in that case is `READ_FAILED {"store": "build_deep_dive_read"}`.

**L3 (Low, spec ambiguity).** Spec §4 test 9's third clause ("every line naming a rehearsal database reads
`assetops_rehearsal_${REHEARSAL}_test`") has no automated check.
- **Why.** §6 says no other line of `test_on1_served_tenant.py` may change.
- **Status.** It holds today (my grep above).
- **Fix.** Add the check in `test_ddr_rehearsal_check.py`. That is one regex over both runbook copies, outside ON1's
  file. Alternatively, the Architect drops the clause.

**L4 (Low).** `rehearsal_check.py:338-341`: `accepted.setdefault(h.reader, h)` keeps one accepted upload per reader,
the first by upload UUID.
- **Why it matters.** If a reader has a second accepted upload (a re-load, or one by another person), its submitter and
  accepter are never checked, and which upload gets checked is arbitrary.
- **Fix.** Check SUBMITTER and ACCEPTER on every accepted upload of each reader.

### Judged, no finding

- **Gates.** G1 to G10 each read their step's store through the named composition (`STORES`), and `Run.fresh()`
  clears the people cache before every gate.
  - G9 reads `served` only to name a `NOT_CURRENT` reason.
  - G9 and G10 each make their own screen read, built as the route builds it (`ImportedSiteRegistry`,
    `deep_dive_api.py:49-58`).
  - Every Fail carries §2.4's codes and facts: plain-string figures, UTC seconds, ids and JSON paths.
  - An unexpected exception becomes `READ_FAILED` with the gate's store, and the later gates still run (test 8).
  - The key is read through `FileKeyStore`. Only `KEY_STATE` and a code are printed, never the path, the key or the
    exception text (R17).
- **Packet deviations, accepted.**
  - G6's upper bound is the second statement: stricter, and correct for this rehearsal.
  - A failed tenant lookup exits 2 `READ_FAILED`: a code, outside §2.1's list.
  - The checker refuses with `NO_DATABASE` and `NO_KEY_DIR` even when reads are injected.
- **The argparse text.** The `help=` and `description=` strings in `build_parser` are argparse's own CLI text, which is
  the house pattern, and SC-1's scan passes. Strictly it is English in the module. Noted, not a finding.
- **MB2.** G2 compares the stored status with the file's `"ILLUSTRATIVE"` (3A6 sets the status from the database). The
  default is right.
- **MB3.** Four literals, checked against World A:
  - the three Revenue drawer texts end "…budget lines for energy delivered and productive-use price." (World A: "…,
    tariff and productive-use price.");
  - the billing row's fills read "Billing adjustments and Energy on unmapped meters" (World A adds "and Tariff");
  - the budget-lines row has needs "budget lines for energy delivered and productive-use price" and fills "Energy
    delivered and Productive-use price".

  Everything else differs from World A only by §3.4's names, order and fuel text, the setup row after the contractor
  row, and World B's reconciled words and standing (with "(Declared)"). Test 1's G9 PASS at S12 confirms the rehearsed
  body matches.
- **One figure (D-WK.12).** No quantity has two figures beyond the allowed pairs: Kisiwa's notice (−$60.00 against
  −$65.00), plan against actual (tiles, drawers, by-Site rows), and in S7 only the statement against the records
  (absent from `screen`, which is S10/S12's reconciled body). No figure is given for Kobo's stop-70 litres or value:
  the decisions and plan-value tiles read "Not available yet".
- **Fixtures.** The XLSX rows, profile and expected records match §3.1 to §3.3. The generator is byte-stable (test 7).
- **Runbook.** It admits in section 6, before section 7's write, replace and load. Sections 8 to 12 match §6. The intro
  and "step 12" were updated, and the five new shell variables are declared.
- **Test 5.** Only `rehearsal_check.py` and §2.3's read (port, memory, Postgres) are under `backend/assetops_backend/`,
  and nothing is under `contracts/`.
- **Plants.**
  - I read the builder's chain logs (`/opt/assetecon/evidence/DDR-rehearsal/build-2026-11-21/chain*.log`, `G.log`).
    P1 to P4 were applied together in one run (B), and each test 3 case failed.
  - My own plants: P1 (faithful, above) escapes test 4a. The `SCREEN_KEYS` drop escapes every test (L1).

### Product observation for the Architect (not a DDR finding; it comes from 5c's World A wording)

The cash text reads "$8,870.00 was collected against $9,785.00 expected; $668.00 is still outstanding and $150.00 is
paid but in transit".
- $9,785.00 is the revenue target, but $668.00 is worked out from the billed total, $9,688.00.
- So the sentence's own figures do not add up for a reader: 9,785 − 8,870 − 150 = 765.
- This falls inside the plan-against-actual pair, so it is not a D-WK.12 breach. It is worth a look before the owner's
  walk.

### Not verified

- The rehearsal itself and its serve (§5, the coordinator's).
- The other plants, which I did not rerun (I read the builder's logs).
- Tests 3 and 4 were run only as part of the full file.

### Residual risk the packet does not name

- G3's proof of "upload, not records" rests on test 3's emulated case until M1 is fixed.
- The expectation file hard-codes the rendered wording. Any SC-1 vocabulary change on `main` before the rehearsal turns
  G9 into `SCREEN` (the path is named, so it is quick to trace).
- Building an `ImportedSiteRegistry` through `FoundationService(store, slug)` repeats the route's wiring by hand. A
  change in the route's wiring would not reach the checker.
