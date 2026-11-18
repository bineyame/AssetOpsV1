# IDX-GAPS U1 review · `finding-index/2` (`analytics/finding_index.py`)

Reviewer: fresh Claude reviewer, 2026-10-31. Revision `abcd8b4e4` on `task/IDX-GAPS-finding-index-v2`, base main `ca6d7d61b`.
I reviewed a read-only `git archive` snapshot (the worktree is in use for U2). Spec: `build-sheet-IDX-GAPS.md` U1, §0, §9
and Addendum 1. Owner intent: `architect-sparse-days-proposal-2026-10-31.md`.

## Verdict: REVISE (one Medium, fixed with a one-character change plus a test)

The design is right and almost all of it holds. The one hole is an off-by-equality at the tolerance boundary. Because of
it, a Finding whose matcher dependency reaches a gap day can still be shown. That breaks the U1 review point "the G
rule never lets a row through whose touched days include a gap".

## Findings

### M1 · Medium · `touched` is exclusive at the end edge, but the matcher and `discover` are inclusive
`backend/assetops_backend/analytics/finding_index.py:241`
`and head["episode_end"] > _day_start(d) - CONTINUITY_TOLERANCE`

- **What is wrong.** An episode that ends exactly 20 min before midnight on D is not "touching" D+1 under `touched`.
  The other comparisons treat it as continuous with D+1:
  - `reaches` (`:182`, `>=`) makes `discover` inspect D+1.
  - The matcher's own neighbour dependency treats it as touching D+1. `finding_episode._Site.margin_ok` (`:291-294`)
    uses `w.start <= hi + TOL`, so D+1's window is in its margin.
  - The run continuity test (`dispatch_v3.py:418`, `gap = (b - a) > TOL`) does not count an exact 20-minute gap as a
    break.
  So D+1's data can still extend or merge this Finding.
- **Reproduced.** In memory, with the U1 test fakes: head 2026-10-06 23:00 to 23:40, 10-07 UNASSESSED, window
  `[10-05, 10-07)`. `discovery.days` includes 10-07 and `status` is PARTIAL. **The Finding is shown** with
  `withheld=False`, and 10-06 has no WITHHELD_FINDING entry. `v1.reaches(h, 10-07 00:00)` is True, while
  `touched(h, [10-06, 10-07]) == {10-06}`.
- **Why it matters.** This is the slice's safety rule: never show a Finding whose extent depends on a day not assessed
  yet. Fixtures and real blocks are minute-aligned (`block("...T23:40:00Z")` style), so exact equality is realistic,
  not just theoretical. At the start edge, `touched`'s `<` matches `margin_ok`'s `a < w.end`, so only the end edge is
  wrong.
- **Fix.** Change `>` to `>=` on the end side (`episode_end >= _day_start(d) - CONTINUITY_TOLERANCE`). Add a case to
  `test_touched_widens_by_the_continuity_tolerance` (`tests/test_idx_gaps_index.py:150`): an episode ending
  `at(D6, 23, 40)` touches `{D6, D7}`. Add a T3-style read asserting that it is withheld.
- **Note.** The build sheet's own `touched` snippet uses `>`, so the implementer followed the sheet literally. This is
  a spec-level slip, not a deviation by the builder. Tell the Architect that the sheet's snippet is corrected.
  Optionally make the start side `<=` as well, to match `reaches` exactly: that is harmless over-withholding, a
  preference rather than a requirement.

### L1 · Low · T7's `sfi1-` check uses a fabricated zero hash
`backend/tests/test_idx_gaps_index.py:244`. A `"sfi1-" + "0"*64` token would fail SELECTION_CHANGED under v1 too, so
the test doesn't prove that a *genuine* v1 cursor is refused. I checked this separately: I took a real v1 cursor from
`ca6d7d61b`'s module on the same data and gave it to v2, and v2 refuses it with `SELECTION_CHANGED`. The behaviour is
correct, but the test is weaker than it reads. Optional fix: build the stale token from the v1 basis (no `policy`)
with the `sfi1-` prefix.

### L2 · Low · one line is 152 characters
`finding_index.py:370` (the body's first line, with `policy_version` added). The rest of the file is at most 120
characters. There is no lint config, so this is style only.

## The checks the dispatch asked for

- **Withholding rule.**
  - `gap_days` (`:244-260`) matches the definition. A non-CURRENT day is `(status, NOT_CURRENT)`. A CURRENT day whose
    `candidate_reach` edge faces a neighbour that is not CURRENT or not inspected is `EDGE_NEXT_TO_GAP`.
  - In `read`, eligibility is `touched(h, days) ∩ G` over the inspected days, and WITHHELD_FINDING days are added
    after the loop. They never widen `G` for other heads (per spec).
  - No new I/O: `gap_days` reuses the memoised `window()` reads. `git diff --stat` outside tests shows only
    `finding_index.py`.
  - The only defect is M1.
- **PARTIAL and Q2.**
  - The body carries `policy_version` and `gaps[{day,state,reason}]` sorted by day.
  - `withheld` and WITHHELD_FINDING can only be set inside the PARTIAL branch.
  - `is_current` stays `status == CURRENT`.
  - With a moved fence there is no PARTIAL branch, so the v1 status, no rows, null count, and `gaps` holds G only
    (T6 covers this).
- **Nothing shown today becomes hidden.** I couldn't construct a counterexample.
  - **Argument.** v1 shows rows only when every inspected day is CURRENT and the fence is unchanged. Then `G` has no
    NOT_CURRENT entry, and every EDGE entry needs a neighbour that is not CURRENT or not inspected. `discover`'s fixed
    point stops only when neither boundary day has a candidate reach outward, and it reads the same memoised windows.
    So `G` is empty and v2 takes the v1 path unchanged.
  - **Property check.** I ran a randomised check of v1 (module from `ca6d7d61b`) against v2 on the same fakes: 4000
    cases (2878 v1-CURRENT, 877 v2-PARTIAL), with heads, segments near the edges, mixed states and limits 1-3.
    - Every v1-CURRENT case gave identical v2 page walks, CURRENT status and `gaps == []`.
    - No PARTIAL case showed a head whose `touched ∩ G` was non-empty.
    - The random times avoided the exact `:40` end, which is the M1 boundary.
- **Token and paging (Q3).**
  - The prefix is `sfi2-`, and `"policy"` is in the basis.
  - The basis `rows` are all intersecting heads (`:340`), as in v1.
  - PARTIAL pages over `eligible`, with `total_count = len(eligible)`. The cursor is accepted on CURRENT/PARTIAL, and
    BASIS_NOT_CURRENT is raised otherwise.
  - T7 shows that a PARTIAL cursor walks and fails SELECTION_CHANGED once the gap day turns CURRENT.
- **T1 literals.** I re-derived all 6 `T1_EXPECTED` walks by running v1's module on `ca6d7d61b`: all 6 equal.
- **The moved assertion** (`test_s4_finding_index_postgres.py:233-244`). **Honest and correct.**
  - The requested window `[10-27 01:00, 10-28)` intersects neither stored episode, so rows are empty under both
    versions.
  - 10-27 is CURRENT and matched. Its only edge contact is the CURRENT day 10-26, so it is correctly not a gap.
  - 10-26 is not a gap either. It is CURRENT, and its dispatch read has no Candidate segment at its start, which the
    real-matcher assertion `gaps == [10-25 only]` itself demonstrates.
  - The dirty or failed 10-25 can change 10-27's rows only through an episode spanning all of 10-26. Such an episode
    would either touch 10-25 (and be withheld) or be deferred by the matcher (making 10-26 PENDING, so it would be in
    G).
  - So "0 on the assessed days, 10-25 named" is true. It doesn't make the read less safe; it drops v1's transitive
    over-blanking only.
  - The test pins `total_count == 0`, `withheld is False` and the named gap for both STALE_PROJECTION and FAILED.
    That is an appropriate replacement for the old `assert_no_claim` lines.
- **The implementer's observation (touched ∩ G versus the edge rule).** It holds as described. On real dispatch data,
  the day *after* a cross-midnight block has no Candidate segment at its start, so EDGE fires only on the day before
  the block, in the H1 direction. Continuity across midnight is then protected by `touched` on the stored head
  (±20 min), and by deferral or PENDING for clusters the matcher would not settle. EDGE still does its H1 job: T4 and
  the s4 H1 Postgres test stay green, the one-day window stays PENDING, and the `[D5, D7)` window withholds D6's
  Finding. M1 is exactly a case where this reliance on `touched` matters.

## Checks I ran (snapshot of `abcd8b4e4`, plan2 venv, `assetops_backend.__file__` = the snapshot)

- `docker ps`: no `assetops-ops03-*` container was running. Only `assetopsv1-postgres-test-1` and
  `assetopsv1-postgres-1` were up.
- `pytest tests/test_idx_gaps_index.py tests/test_s4_finding_index_reach.py tests/test_s4_finding_index_postgres.py
  tests/test_s4_deferred_match_postgres.py -q`: **32 passed**, 4 warnings, 148 s. This matches the handoff's 32.
- **Planted break, in memory.** I replaced `finding_index.touched` with intersection only (no tolerance) and ran
  `test_idx_gaps_index.py`: **2 failed**, 14 passed. The failures were `test_touched_widens_by_the_continuity_tolerance`
  and the behavioural `test_t3_finding_next_to_an_unassessed_day_is_withheld`, so the break is caught.
- `tools/check-architecture.ps1` (snapshot, no `-ExecutionPolicy`): passed.
- `tools/check-agent-workflow.ps1`: passed.
- I also ran the v1-vs-v2 probe and the M1 reproduction as scratch scripts outside the repo.

## Not verified

- **Full backend suite.** It is not this unit's gate (that is the U4 merge gate), and I found no implementer
  full-suite evidence for `abcd8b4e4`.
- **`check-all.ps1` 11/11.** I didn't run it; the handoff reports it.
- **No frontend in U1.**

## Residual risk not in the packet

- **Pre-existing, not a regression.** An unmatched cross-midnight Candidate block whose start day is a gap is not
  discovered from the following requested day. That day's read has no start-edge segment, and no head exists. This is
  the mirror of H1, and v1 has the same exposure. v2 lists that day's other rows (PARTIAL or CURRENT) without naming
  the neighbour, unless the matcher deferred the window. I didn't reproduce this against the real matcher. It is worth
  one U4 probe (P3's mirror: block 10-06 23:45 to 10-07 00:15, 10-06 not current, window `[10-07, 10-08)`).
