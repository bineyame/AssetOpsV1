# IDX-GAPS review packet · Finding index `finding-index/2`

Task: `tasks/IDX-GAPS-finding-index-v2.md`. Contract: `AssetOpsV1-plan2/.agent/build-sheet-IDX-GAPS.md` + Addenda 1-3
(Addendum 1 Q1 withdrawn by Addendum 2). Branch `task/IDX-GAPS-finding-index-v2` from main `ca6d7d61b`. Decision
`D-2026-10-31-finding-index-v2`.

## Outcome delivered

One unassessed or pending day no longer blanks a multi-day Site Findings list. The index reads PARTIAL with the rows
from assessed days. `gaps[]` names each day not checked. A Finding that touches a gap day, or a day next to one, is
withheld. The mini board settles its Finding source on PARTIAL only when its own day is not a gap. It shows the backend
gap line "Not available yet · {g} of {n} days ...". The Findings page and the Overview list show the PARTIAL rows and
name the gaps. A v1 CURRENT body is unchanged.

## Commits

U1 `abcd8b4e4`, U1 review fixes `c89ce915c`; U2 `728851b12`, `400d1096b`, `a88588312`; U3 `30cbce0e0`; handoff
`0b92bf66d`; U4 and closeout: see `git log ca6d7d61b..HEAD`.

## Files materially changed

- Backend: `analytics/finding_index.py` (`touched`, `gap_days`, PARTIAL/withholding, `sfi2-`, `policy_version`),
  `site_outcomes/mini.py` (`index_settled`, `finding_gap_line`, `Reads.first`, GAPS_* copy, `FINDING_TITLE`),
  `site_outcomes/board.py` (`SiteFacts.finding_gaps`), `site_outcomes/read.py` (wire `finding_gaps`,
  `policy_versions.finding_index`).
- Frontend: `sites/findingIndexClient.ts` (`-2`, PARTIAL, `listsRows`, `gapDays`), `ui/productWords.ts` (PARTIAL),
  `sites/SiteFindingIndex.tsx` (`Partial` view), `sites/OverviewFindingList.tsx`, `sites/OutcomeBoard.tsx`,
  `sites/outcomeBoardClient.ts`, fixtures `sites/__tests__/findingIndexFixtures.ts`.
- Tests: new `test_idx_gaps_index.py`, `test_idx_gaps_board.py`, `test_idx_gaps_postgres.py`,
  `shell/__tests__/idxGapsFindingIndex.test.tsx`; edited `test_s4_finding_index_postgres.py`, `test_out_b2_mini.py`,
  `test_out_b2_vocabulary.py`, `test_out_d4_board.py`, `test_out_b4_board_postgres.py`,
  `test_out_e4_readback_postgres.py`.
- Records: `.agent/mock-departure-register.md` (R610-R613, R595), `.ai/DECISIONS.md`, `.ai/CODE_STATE.md`,
  `.ai/ACTIVE_CONTEXT.md`.

## Acceptance (§8)

1. v1 CURRENT bodies unchanged: PASS. T1 in `test_idx_gaps_index.py`; every `test_s4_*` CURRENT assertion green.
   P1 also checks the single assessed day still reads CURRENT with `gaps == []`.
2. One missing day no longer blanks the list: PASS. T2 and P1 (real data): PARTIAL, F01 the only row, `gaps ==
   [10-07 UNASSESSED NOT_CURRENT]`. P2 does the same for a pending day: STALE_PROJECTION after late evidence, then
   PENDING after reassessment, CURRENT after the match.
3. A Finding next to a gap is withheld: PASS. T3/T4 cover this, and so does P3b on real matcher output. A matched
   10-06 23:30-10-07 00:30 Finding is withheld once 10-07 goes stale (`withheld` true; 10-06 is
   `EDGE_NEXT_TO_GAP`), and 10-05's Finding stays listed. P3 (the sheet's form) is under Known deviations.
4. A change during the read gives no rows: PASS. T6 covers this. P4 wraps the real Postgres store so the fence moves
   after the snapshot: the v1 status, no rows, no count, and `SELECTION_MOVED_DURING_READ`. The deferred-match
   scenarios still read PENDING (`test_s4_deferred_match_postgres.py` green).
5. The board settles on PARTIAL off its own day and shows the gap line: PASS. `test_idx_gaps_board.py` covers this.
   P5 runs `mini.compose` over a real index for board day 10-06: `finding_index` is not failed, and the line reads
   "Not available yet · 30 of 31 days have no assessed readings". Board day 10-07 is a gap and stays unsettled. An
   UNASSESSED body never settles (`UNSETTLED_INDEX_STATUS`).
6. The Findings page and Overview list show PARTIAL: PASS in vitest (`idxGapsFindingIndex.test.tsx`, 9 tests). This
   covers the 1-row and 0-row forms and the withheld sentence. The proved-empty words never appear. The Overview note
   shows only when PARTIAL. Captures: see Checks.
7. Portfolio follows the board; estate unchanged: PASS by construction. `estate/**` is untouched (§0) and R613 is
   open.
8. Register, decision, full runs: R610-R613 added, R595 resolved, decision recorded. Full runs: see Checks.

## Moved assertions (U1/U2)

- `test_s4_finding_index_postgres.py` bridge-chain dirty neighbour: the v1 result was STALE/FAILED with no claim. v2
  reads PARTIAL with 0 rows and `gaps == [{10-25, <status>, NOT_CURRENT}]`, because the requested day 10-27 is not a
  gap.
- `test_out_e4_readback_postgres.py`, Addendum 2 (a)(b)(c):
  - (a) Cost Earlier holds exactly one ACT-000001 with its full detail string.
  - (b) Protect is in its safeguard form with a verification href and null detail. "outside this view" is absent
    from every row.
  - (c) "not realised savings" appears in Cost, and elsewhere only in Assure.
  - "Every earlier detail None" is narrowed to non-Cost.
- `test_out_b2_mini.py` and `test_out_d4_board.py`: the fake index bodies now carry `status: CURRENT, gaps: []`. The
  b2_mini Finding title now comes from `FINDING_TITLE` (Addendum 3).
- `test_out_b4_board_postgres.py` `two_board_days`, restored unmodified (Addendum 2): Day A F01 MOVES under Cost,
  Protect lists F01 in the safeguard form, and Cost `must_not_harm` is None.
- U2 review Lows (`AssetOpsV1-plan2/.agent/IDX-GAPS-U2-review.md`, ACCEPT): L1, e4 now asserts "not realised savings"
  is absent from the whole board body except the Cost row and Assure's verified-results line. L2 fixes the stale e4
  docstring and the b4 Addendum 6 comment and removes a stray blank line. L3 is the comparison table below.
- Still failing, so left dropped for DEMO-SPARSE CO-1: Day A Cost NEEDS_ATTENTION, the Day B Must-not-harm text and
  href, and ACT-048 on Cost/Protect. The fixture's Action is ACT-000001.

## True v1 vs v2 board comparison (Addendum 2 stop condition)

| b4 read | day | idx v1 → v2 | settled | read_state | states, failed |
|---|---|---|---|---|---|
| guardrail_closed_s2 | 10-06 | UNASSESSED 0 → PARTIAL 1 | T/T | PARTIAL/PARTIAL | identical |
| two_board_days A | 10-06 | UNASSESSED 0 → PARTIAL 1 | T/T | PARTIAL/PARTIAL | identical |
| two_board_days B | 11-02 | same | T/T | AVAILABLE/AVAILABLE | identical |
| estate_finding_rows | 10-21 | UNASSESSED 0 → PARTIAL 5 | T/T | AVAILABLE/AVAILABLE | identical |
| verified_protect (e4) | 11-02 | same | T/T | AVAILABLE/AVAILABLE | identical |

The only row content that moved: on 11-02, ACT-000001 left Protect Earlier ("linked finding outside this view") and
joined Cost Earlier with its detail. That is the R595 move the sheet expected. The data is in the session scratch
files `v1true-states.jsonl` and `v2-states.jsonl` (v1 from `ca6d7d61b` `finding_index.py`).

## Sheet correction

The U1 `touched` snippet used an exclusive `>` at the tolerance bound. Addendum 2 (U1 review M1) made both bounds
inclusive, to match `reaches` and the matcher's `margin_ok`. Built as `finding_index.py` `touched`, with cases at
exactly edge -20 min and edge +20 min.

## U3 choices (not specified by the sheet)

1. Overview list, PARTIAL with 0 rows: a `partial-empty` branch reading "No Findings on the assessed days." plus
   `OVERVIEW_PARTIAL`. It never uses the proved-empty words.
2. Findings page `Gap` block: when no requested day is a gap (only a neighbour or edge day is) and nothing is
   withheld, `OVERVIEW_PARTIAL` shows instead of the gap paragraph. The gap paragraph's last word agrees in number
   with the count ("…concluded about it" when g = 1, "them" otherwise).

## Checks

- Focused backend, U1 + U2 + U4 sets (§6, 14 files incl. `test_idx_gaps_postgres.py`), real Postgres, at the U4
  revision before the Lows: **144 passed** in 387.88 s. After L1/L2: `test_out_e4_readback_postgres.py` +
  `test_out_b4_board_postgres.py` **6 passed** in 142.54 s.
- `tools\check-all.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv) at U4: **All 11 guards passed**.
- U3 vitest (from the handoff): `idxGapsFindingIndex.test.tsx` 9 passed; 21 related files 583 passed; `tsc --noEmit`
  clean; missing-claim scan passed.
- Full `npx vitest run` at `6c0c3ad6e` (266 s): Test Files 1 failed | 144 passed (145); **Tests 3 failed | 3543
  passed (3546)**. The 3 failures are exactly the known `src/sites/__tests__/w1f4VerificationStructure.test.tsx` tests.
- Full backend: `tools\run-backend-suite-in-container.ps1 -Tier all` at `6c0c3ad6e`, run
  `var/test-results/OPS-03/20261031-102659-a376df` (4 workers, postgres-test). Wall time 2719 s (45:17, under the 82-minute cap).
  JUnit: tests 4565, failures 1, errors 0, **skipped 0**. The one failure is environmental, not IDX-GAPS:
  `test_runs_api.py::TestTheShippedFuelLossEventAgainstAPropertylessFoundation::test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`
  failed with `FileNotFoundError: /tmp/assetops-worktree/var/sites/mg-001.yaml`. `var/sites/` is untracked (gitignored) and
  absent from this worktree. With `mg-001.yaml` copied from the main checkout, the class passes locally (4 passed); the copy was
  then removed. The file is untouched by this branch. A rerun on a worktree with `var/sites/` present is the reviewer's to
  confirm if wanted.
- Captures 390/1440 (`.agent/IDX-GAPS-captures/`, script `idxcap.mjs`, claims `idxgaps-claims.json`). Producer:
  `tools/s404_finding_index_walkthrough.py prepare|serve --db assetops_s404_owner_test` (a `_test` name, which the
  producer accepts unedited; dropped afterwards; servers stopped by PID). Window [10-15, 10-31):
  - Findings page PARTIAL: **PASS at 1440 and 390.** The claim reads "4 Findings on the assessed days", with 4 rows
    and the gap paragraph "12 of 16 days in this window are not checked yet, …". No proved-empty words, no codes on
    screen, page overflow ≤ 0 at both widths (`idxgaps-findings-partial-{1440,390}.png`).
  - Mini board gap line: **layout evidence: not run.** On this producer the Kobo Overview shows "Awaiting evidence
    migration", so the board is not rendered (`idxgaps-board-line-*.png` show that state). The board API on the same
    database returns `finding_gaps.text` "Not available yet · 25 of 31 days have no assessed readings" for date 10-15.
    The one-line/two-line clamp is unverified in a browser; the render is proven in vitest
    (`idxGapsFindingIndex.test.tsx`).

## Known deviations

- P3 differs from the sheet's form. Delivering a Candidate block at 10-06 23:45-23:59 also assessed 10-07, which had
  no evidence, as CURRENT, and the matcher then wrote that Finding. So the premise "no evidence on 10-07 → 10-07 not
  CURRENT" does not hold on real data. P3 instead makes 10-07 stale before the match: the matcher skips the edge
  cluster and leaves 10-06 PENDING (a NOT_CURRENT gap, not `EDGE_NEXT_TO_GAP`). [10-06, 10-07) then keeps the v1
  STALE_PROJECTION no-claim body, and [10-05, 10-07) is PARTIAL with 0 rows. `EDGE_NEXT_TO_GAP` on real data is
  proved by P3b.
- P5 runs at composition level (`mini.compose` with the real index port bound as `read.py:231` binds it; the other
  ports refuse), not through the full `outcome-board` route. The full route over the s602b data is covered by the b4
  and e4 Postgres files.
- The Postgres DB name comes from `pg_harness` (`assetops_pt<run>_<tag>_test`), the same as every other Postgres
  file, not `assetops_idx_gaps_test`.

## Residual risk (probe, recorded, not fixed)

`TestResidualRiskProbe` puts an unmatched cross-midnight Candidate block (10-06 23:30-10-07 00:30) on a start day
10-06 that has gone stale. The matcher writes no Finding (0 revisions). The end day 10-07 alone reads **CURRENT, count
0, discovery [10-07], gaps []**. Its own dispatch read lists no Candidate segment in its first minutes, so no edge
pulls the gap start day in. v1 reads it the same way, so this is not introduced here. [10-07, 10-09) reads PARTIAL 0
with only 10-08 named. The probe pins this observation so a fix shows up as a test change.

## User-review focus

The Findings page PARTIAL view, the Overview note, and the board gap line wording on a sparse demo site.
