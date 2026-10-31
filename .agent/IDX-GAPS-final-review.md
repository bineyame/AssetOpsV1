# IDX-GAPS final slice review (finding-index/2)

Reviewer: fresh Claude Reviewer, 2026-10-31. Branch `task/IDX-GAPS-finding-index-v2`, head `379f73961`, base main
`ca6d7d61b`. Scope: U3 (frontend), U4 (Postgres proofs), records, and the coherence of the whole slice. U1 and U2 were
already accepted in per-unit reviews, so they were not re-reviewed in depth.
Work was done from a `git archive 379f73961` snapshot in the session scratchpad.

## Verdict: ACCEPT

No High or Medium findings. The three Lows below are non-blocking and can go to a follow-up or into DEMO-SPARSE.

## Checks run (what I saw)

| Check | Result |
|---|---|
| `test_idx_gaps_postgres.py` (snapshot, plan2 venv, `assetops_test` URL) | **7 passed** in 125.5 s. The probe printed `revisions 0, end_day (CURRENT, 0, [10-07], []), end_plus_one (PARTIAL, 0, [10-08 UNASSESSED NOT_CURRENT])`, which matches the packet |
| `test_runs_api.py::TestTheShippedFuelLossEventAgainstAPropertylessFoundation`, with `var/sites/mg-001.yaml` copied from plan2 into the snapshot | **4 passed** in 19.2 s |
| Focused U3 vitest `idxGapsFindingIndex.test.tsx` (worktree) | **9 passed** |
| Every vitest file that imports the changed modules (18 files, snapshot) | **18 files, 493 passed** |
| `npx.cmd tsc --noEmit` (snapshot) | exit 0 |
| `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1` (run directly, no `-ExecutionPolicy`) | both passed |
| `node tools/checks/missing-claim-scan.mjs` | passed (43 tagged, 10 baselined) |
| Planted U3 break: `OverviewFindingList.tsx:290`, `partial-empty` branch disabled | **caught**: 1 failed. The test was "never says the day has no Findings when the only Finding was held back" (the read fell through to the proved-empty "No Findings for this day.") |
| Planted U4 break: `finding_index.py:329`, withholding disabled (`if False and hit & gaps.keys()`) | **caught**: P3b failed, 6 passed |
| Planted break 2: `touched` with the 20-min tolerance dropped | `test_idx_gaps_index.py`: **caught** (3 failed: `touched_widens…`, T3, T3b). `test_idx_gaps_postgres.py`: **not caught** (7 passed). See L1 |
| Reviewer probe (scratch, not committed) for the sheet's P3 form, with 10-07 made stale **after** the match | A 10-06 23:45-23:55 Finding is really matched. After late evidence on 10-07, `[10-05, 10-07)` reads PARTIAL with 0 rows, `withheld` true, and 10-06 `EDGE_NEXT_TO_GAP`. `[10-06, 10-07)` reads STALE_PROJECTION with no count |

I restored all the snapshot files byte for byte, ignoring CR line endings, and compared them against the head blob.
Not rerun: the full vitest run and the full backend `-Tier all` run. I cite them below.

## Full backend run (`var/test-results/OPS-03/20261031-102659-a376df`)

- I checked the JUnit file myself: `tests=4565 failures=1 errors=0 skipped=0`, time 2716.5 s, and options `tier=all workers=4
  server=postgres-test`. The single failure is `FileNotFoundError: '/tmp/assetops-worktree/var/sites/mg-001.yaml'`.
- The failure is environmental, and I agree:
  - The test reads `repo_root/var/sites/mg-001.yaml` (`test_runs_api.py:539-552`).
  - `var/` is gitignored (`.gitignore:6`).
  - The slice touches neither `test_runs_api.py`, `runs/`, `sites/` nor `var/`. The diff has no such path.
  - Main has the same dependency, because the test last changed at `0c1625d22`, before `ca6d7d61b`.
  - With the file present, the class passes (4/4).
- Revision: the run is at `6c0c3ad6e`. The only commit between that and head, `379f73961`, changes five records and
  docs files and no code.
- **A full rerun is not needed.**
- Full vitest (3543 passed, 3 known `w1f4VerificationStructure` failures) is the implementer's number at `6c0c3ad6e`. I did
  not rerun it. My 18-file related set is green.

## U3 judgement

- **The PARTIAL Findings page never uses proved-empty words.**
  - The `Partial` view has its own claims: "{n} Findings on the assessed days" and "No Findings on the assessed days".
  - The `NEVER` regexes and the `NOT_A_ZERO` absence are asserted.
  - A PARTIAL read with `total_count === null` falls into the no-count branch, not a zero.
  - In the 1440/390 captures the claim reads "4 Findings on the assessed days", followed by "12 of 16 days … not checked
    yet". There is no proved-empty text and no codes, and the page overflow is ≤ 0.
- **The Overview `partial-empty` branch is justified. It is needed, not optional.**
  - Without it, a PARTIAL read with 0 rows reaches `total_count === 0`. With a token and watermarks, that renders the
    proved-empty "No Findings for this day. Every day this read inspected … was assessed", which is a gap read as zero.
  - My planted break proves this, and the vitest catches it.
  - Using `OVERVIEW_PARTIAL` there is correct. An Overview read is one requested day. A PARTIAL status for one day means
    that day is not itself a gap, so any held-back Finding must reach a neighbour, which is exactly the
    `OVERVIEW_PARTIAL` wording.
  - On the Findings page, using `OVERVIEW_PARTIAL` when g = 0 and nothing is withheld follows Addendum 1 Q5.
- **The board gap line** is rendered verbatim from the backend text (`OutcomeBoard.tsx:345-350`, `v69-chart-note`), and only
  when present. Vitest covers both cases. No "Not available yet" string is authored in the frontend (the scan passed).
- **No browser capture of the board line.** It is acceptable that one was not taken. The packet records it honestly as
  "layout evidence: not run", with the blocking precondition: the producer's Kobo Overview shows "Awaiting evidence
  migration", and the board API returns the text. The line is a single plain paragraph in an existing wrapping note
  class, and it carries no intrinsic-width content, so vitest presence plus class is sufficient for merge. The
  1-line/2-line clamp stays a residual for the walkthrough (see Residual risk).
- **No codes on screen, and the copy matches §3.**
  - The status label, sentence and next step, the claims, the gap paragraph, the withheld sentence and
    `OVERVIEW_PARTIAL` all match exactly.
  - One deviation is disclosed: "is/are" and "it/them" agree with g. The sheet says to pluralise, so this is in scope.
- **Mockup deviations.**
  - R610 covers the board line, R611 the Findings page and R612 the Overview note. All three are D3 copy-honesty rows,
    standing.
  - By the register rule (`mock-departure-register.md:212`, "D3 … has no accepted label"), no `MOCK DEVIATION` badge is
    due. This follows the sprint precedent (R574, R581, R591).
  - R613 (D5, open) describes an estate surface the slice does not change, so no new on-page label is introduced. The
    v70 anchor `outcomes.js:116-124` is correct.

## U4 judgement

- **P1-P5 run on produced Findings.**
  - Every Finding comes from `CaseRunner`: S2 delivery, then the S3 assess, then the S4 match.
  - P1 and P3b assert the matched revisions or episode starts. P3b asserts the cross-midnight head is present in
    `revisions`.
- **The P3 deviation is honest, and P3b is a real withholding proof.**
  - The matcher wrote a Finding spanning 10-06 23:30 to 10-07 00:30, and the read showed CURRENT with 2. After late
    10-07 evidence, the read is PARTIAL with `withheld` true. 10-05's row stays, and 10-06 is named `EDGE_NEXT_TO_GAP`.
  - My planted withholding break fails P3b.
  - P3b proves the reach-into form, not the tolerance-only form. See L1.
- **P5 at composition level is acceptable.**
  - It binds the real index port the way `read.py` does and calls `mini.compose`.
  - It asserts settledness for both board days, plus the exact template and the day list.
  - The b4/e4 Postgres files already exercise the full route on real data, and P5 checks the new rule directly.
- **The residual-risk probe is pinned honestly.**
  - It is labelled in the docstring and an inline comment as an observed behaviour, not a desired one.
  - It asserts the exact tuple I saw printed, so a later fix will surface as a test change.
  - It is correctly not attributed to v2, because v1 reads the same.

## Records

- R610-R613 match §5. They are in the 9-column register shape.
- R595 is marked `resolved by IDX-GAPS (400d1096b)` per Addendum 2 (d), which supersedes the §2 "stays open" note.
  The claim matches the e4 assertions accepted in the U2 review.
- `D-2026-10-31-finding-index-v2` has the 5 lines the sheet asks for: the rule, the verbatim owner quote, the board
  exception, estate unchanged/R613, and the register.
- The packet's moved-assertions list and its v1/v2 comparison table cover the Addendum 2 stop condition.

## Findings

**L1 · Low · `backend/tests/test_idx_gaps_postgres.py:91-147`: the tolerance-only edge withholding is not proved on
real data.**
- **What happens.** P3 makes 10-07 stale before the match, so no Finding is written. P3b's Finding crosses midnight.
  Neither pins the sheet's case: a Finding that ends before midnight and touches 10-07 only through the 20-minute
  tolerance.
- **Evidence.** With the tolerance removed from `touched`, the Postgres file still passes 7/7. Only the unit file
  (T3/T3b) catches it.
- **Why it matters.** The behaviour is correct today (my probe), and the unit tests guard it. But review point U4 asks
  for real matcher output, and the sheet's P3 form is cheaply reachable.
- **Fix.** Add a P3c:
  1. Deliver the 10-05 hour plus the 10-06 23:45-23:59 Candidate, then assess and match. Assert one revision.
  2. Deliver late 10-07 evidence.
  3. Assert that `[10-05, 10-07)` reads PARTIAL with 0 rows, `withheld` true, and gaps
     `{10-06: (CURRENT, EDGE_NEXT_TO_GAP), 10-07: (STALE_PROJECTION, NOT_CURRENT)}`.
  4. Assert that `[10-06, 10-07)` reads with no claim.

  This is not an acceptance gap, because §8 #3 is met by T3/T4 plus P3b.

**L2 · Low (copy) · `frontend/src/sites/SiteFindingIndex.tsx:815`: "those days" has no antecedent when g = 0 and a
Finding is withheld.**
- **What happens.** When no requested day is a gap but a Finding was held back next to a neighbour gap, the gap
  paragraph is omitted. The page then shows only "A Finding that reaches into one of those days is not shown until that
  day is checked."
- **When it happens.** This is the P3b real-data shape: window `[10-05, 10-07)`, where 10-07 is a discovered neighbour.
- **Why it is allowed.** Addendum 1 Q5 prescribes it literally, and the day strip names the day.
- **Fix.** An Architect copy call. For example, use `OVERVIEW_PARTIAL`'s "neighbouring day" phrasing when
  `sentence === null && body.withheld`. This is a preference, not an acceptance gap.

**L3 · Low (hygiene) · `frontend/src/sites/OverviewFindingList.tsx:356`: the hook says "current-rows" on a PARTIAL read.**
- **What happens.** The rows branch keeps `data-overview-finding-list="current-rows"` even when the read is PARTIAL.
- **Why it matters.** It is not on screen, but a test or capture that treats the attribute as "this list is current"
  would be misled.
- **Fix.** Optionally emit `"partial-rows"` (or add a `data-overview-finding-partial` hook on the wrapper) and update
  the one test assertion. This is a preference.

## Residual risk not already named in the packet

- The board gap line clamp (1 line at 1440, ≤ 2 at 390) has never been checked in a browser, because the producer's
  Overview is blocked. Look at it on the combined/DEMO-SPARSE dataset at the walkthrough.
- The DEMO-SPARSE combined dataset will be the first real multi-day PARTIAL data on the board. R595's CO-3 read-back
  stays in DEMO-SPARSE acceptance, as recorded.
