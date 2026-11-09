# C3 review: two-tier board gap line (D-E4.6)

Reviewer: fresh Claude (Opus 5.5), independent of the builder. Diff: `git diff main...task/E4-C3-gap-line-tiers`
(be33b820f). Spec: build-sheet-OWN-GAPS-2026-11-08.md, "E4 stop rulings", D-E4.6.

## Verdict: ACCEPT WITH NOTES

The logic does what the card asks for the demo case. Kisiwa days where `critical_served` is COMPLETE and another
measure is NO_DATA now read "only partly checked". Days with no rows, or only NO_DATA rows, keep `GAPS_NO_READINGS`.
Nothing that pins text breaks on a fresh prepare. Finding 1 is a Medium: it contradicts a word in the card, but it does
not change the demo line. Fix it on the branch before merge if it is cheap; it does not hold the re-prepare.

## Findings

1. **Medium: LOW is treated as "counted", against the card and the product's own vocabulary.**
   `backend/assetops_backend/site_outcomes/mini.py:135` `_COUNTED_GRADES = {"COMPLETE", "PARTIAL", "LOW"}`;
   pinned in `backend/tests/test_idx_gaps_board.py:59-60`.
   - D-E4.6 says: "Days with no counted measure keep `GAPS_NO_READINGS`".
   - Everywhere else in the product, LOW means "with too little data, not counted" (`chain/vocabulary.py:212, 217,
     298`). `readiness_of` also treats LOW-only days as NONE (`chain/read.py:82-85`).
   - So a gap day holding only LOW and NO_DATA rows would read "only partly checked" on the board. The days line for
     the same day says that data was "not counted".
   - Fix: use `{"COMPLETE", "PARTIAL"}` and flip the LOW case in the test. If the Architect means LOW to count here,
     they should say so in the card.
   - Not demo-visible: the Kisiwa days that trigger the split carry COMPLETE.

2. **Low (Architect wording note, not a builder defect): "only partly checked" counts gap days only.**
   - A day whose weakest grade is PARTIAL or LOW is not a gap, so it is not in the count.
   - Yet that day is also "partly checked" in the estate vocabulary (`days_line.partial`).
   - So "28 of the last 31 days are only partly checked" can leave a reader thinking the other 3 days are fully
     checked, which may be false.
   - The text is the card's. Route it to the Architect for the post-demo copy pass, for example "are missing some
     readings".

3. **Low (residual risk): the PENDING branch hides the split.**
   - `mini.py:377-392`: if any gap day is PENDING, the whole line stays "Not available yet · g of n days are not
     assessed yet", partly-checked days included.
   - This is faithful to the card, which only re-words the "no checked readings" tier. The packet states it, and the
     prefix makes the line provisional.
   - On a real site, though, the latest day is often PENDING. That would bring back a milder form of the
     over-statement D-E4.6 fixes: "not assessed" for days that have COMPLETE measures.
   - Acceptable for now. A future card could split the PENDING count from the others.

4. **Low (stale documentation, no test impact).** `Docs/demo-sprint/implementation-logic-portfolio-sites-findings-actions.html`
   and `.ai/CODE_STATE.md` still describe a single "no checked readings" line. Historical `.agent/POLISH-PC-captures/*`
   text captures show the old Kobo line; they are records, not pins.

## Consumers and pins of the old wording (question 1)

| Consumer | Effect after a fresh prepare | Severity |
|---|---|---|
| `tools/demo_combined_finish.py:40, 299-311` SP-3 (Kobo board, exact `GAPS_TEXT`) | **Holds.** The E3 build's `check.json` shows SP-3 passing with g=11 (gap days = the 31 window days minus the days with evidence), and `listed ∩ assessed = ∅`. So every Kobo gap day is a no-evidence day. Grading has only `operating_hours` periods inside the local day (`chain/grading.py:40-51`), so a no-evidence day cannot hold a COMPLETE/PARTIAL/LOW row. Kobo cannot split. | none |
| Kisiwa board | The line changes (expected). **No finish row, pin or test reads the Kisiwa gap line**: grep across `tools/`, `backend/tests/`, `frontend/src/` and the DS-1a worktree found none. | none |
| `backend/tests/test_idx_gaps_postgres.py:220` | All days are NO_DATA, so it is unchanged. **Ran here: passed.** | none |
| `test_out_b2_mini.py:355-363`, `test_k10_declared_none_board.py:107-128`, `test_out_b2_vocabulary.py:177-181` | No-row, NO_DATA-only or PENDING fixtures. Passed. | none |
| `fixtures/ch5a1_board_contract/kobo_2026-10-31.json`, `kobo_2026-11-01.json` | Their PENDING text ("not assessed yet") is unchanged. | none |
| `frontend/src/shell/__tests__/idxGapsFindingIndex.test.tsx:196` | A literal fixture string, rendered verbatim (`OutcomeBoard.tsx:347-349`). No frontend code parses the text. | none |
| DS-1a `Docs/demo-sprint/demo-script-client.html` | It does not quote the board gap line. Screenshots 13-16 are Kisiwa fuel pages, not the board. The E5/DS-1a refresh re-shoots anyway. | none |

No High.

## Wording (question 4)

- The client language is plain.
- Singular and plural forms are right: "1 ... is only partly checked" and "28 ... are only partly checked". The
  no-readings tier keeps "has/have".
- The " · " join matches the existing pattern, including `GAPS_NONE_DECLARED`, which is appended as a third segment.
- The two-tier form repeats "of the last 31 days" but stays clear.
- The new strings are in `COPY` and pass the vocabulary scan.

## Checks run

- `pytest test_idx_gaps_postgres.py test_idx_gaps_board.py test_out_b2_mini.py test_out_b2_vocabulary.py
  test_k10_declared_none_board.py -q`
  - Setup: worktree PYTHONPATH, `ASSETOPS_TEST_DATABASE_URL` base `assetops_test` at 127.0.0.1:55432 (routed to a
    run-owned `_pt*_test`).
  - Result: **59 passed, 0 skipped**, 75 s.
  - The Postgres module ran; it was not skipped. Free RAM was 2.59 GB at start.
- Frontend `idxGapsFindingIndex` vitest: **not run**. The c3 worktree has no `node_modules`. It is unaffected by
  construction: it uses a literal fixture.
- Architecture and workflow guards were not run. This is a backend-only change of 15 lines.
