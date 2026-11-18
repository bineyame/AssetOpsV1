# IDX-GAPS U2 review · U1 fix round `c89ce915c` + U2 board (`728851b12`, `400d1096b`, `a88588312`)

Reviewer: fresh Claude reviewer, 2026-10-31. Diff `abcd8b4e4..a88588312 -- backend`, read from a `git archive
a88588312` snapshot (worktree has since moved to `0b92bf66d`, U3; no backend change after `a88588312` besides the
untracked U4 test). Spec: `build-sheet-IDX-GAPS.md` U1, U2, Addenda 1-3; prior review `IDX-GAPS-U1-review.md`.

## Verdict: ACCEPT

The U1 fixes close M1, L1 and L2. U2 matches the sheet and Addenda 2 and 3. Every planted break was caught. The
Lows below are test and comment hygiene. Fix them on the branch at U4 or closeout; they don't block.

## Findings

### L1 · Low · e4 narrowed the "not realised savings" check further than Addendum 2 (c) needs
`backend/tests/test_out_e4_readback_postgres.py:83-85`.
- **What changed.** v1 asserted the phrase was absent from the whole body. The new test checks only the Grow and
  Protect rows.
- **What it loses.**
  - The non-row parts of the body (headline, subline, warnings, objectives, finding_gaps) are no longer covered.
  - Assure is unconstrained. The addendum says that inside Assure the phrase may appear only in the
    verified-results line.
- **Not needed.** I ran a probe against the real s602b `verified` board (scratch test, deleted afterwards). With the
  Cost row removed, the body has **no** occurrence of the phrase.
- **Fix.** Assert `"not realised savings" not in json.dumps(dict(body, rows=[r for r in body["rows"] if r["category"]
  != "OPTIMIZE_COST"]))`. That still passes, and it is stricter than the addendum. If R594 ever puts the phrase in
  Assure, exempt only the `verified_results` contributor text.

### L2 · Low · stale comments now contradict the restored or changed assertions
- **e4 docstring.** `test_out_e4_readback_postgres.py:7-12` still says the board day's index is UNASSESSED, the
  Finding is outside the view, Cost Earlier is empty and R595 is open. The test now asserts the opposite.
- **b4 comment.** `test_out_b4_board_postgres.py:393-394` still says "Finding index UNASSESSED, so the Day A
  NEEDS_ATTENTION/F01 ... assertions move". Lines 425-436 below it restore the F01 checks.
- **Fix.** Reword both to the v2 reading: PARTIAL, board day assessed, and R595 resolved per Addendum 2 (d).
- **Also.** There is a stray extra blank line at `:436`.

### L3 · Low · the true-v1 comparison is not in a packet yet
- Addendum 2 says "record the comparison in the packet".
- So far it exists only as session-scratch JSONL (`v1true-states.jsonl`, `v2-states.jsonl`) and one line in
  `.agent/IDX-GAPS-phase-handoff.md`.
- The data itself is credible (see below).
- **Fix.** Copy the 5-read table, with states, `failed`, `read_state` and the Earlier moves, into
  `.agent/IDX-GAPS-packet.md` at closeout.

No High or Medium findings.

## U1 fix round (`c89ce915c`)

- **M1, closed.**
  - **Bounds.** `finding_index.py` `touched` now uses `<=` on the start bound and `>=` on the end bound.
  - **Unit cases.** `test_touched_widens_by_the_continuity_tolerance` pins both exact edges, with ±1-minute
    controls:
    - 23:00-23:40 touches {D6, D7}, and 23:39 touches {D6} only.
    - 00:20 touches {D6, D7}, and 00:21 touches {D7} only.
  - **Behavioural case.** T3b reads PARTIAL, shows only F2, withholds the 23:40 Finding, and adds a WITHHELD_FINDING
    entry for 10-06.
  - **Planted break 1.** I reverted the end bound to `>` in memory: 2 tests failed (the touched unit test and T3b).
  - **Planted break 2.** I reverted the start bound to `<`: 1 test failed (the unit test). The start edge has no
    behavioural read, but the unit test pins it. That is enough.
- **L1, closed.** `V1_CURSOR` is a real `sfi1-` token (base64 JSON, `v: 1`, a non-zero hash). It is refused with
  SELECTION_CHANGED on both the all-CURRENT and the PARTIAL data.
- **L2, closed.** The body line is wrapped.

## U2 checks

- **Board settling.**
  - **The rule.** `index_settled` (`mini.py:197-205`) returns True on CURRENT. On PARTIAL it returns True only when no
    `gaps[]` entry has `day == board_day`, whatever that entry's state. So EDGE and WITHHELD on the board day also
    unsettle, which is the sheet's wording and conservative. Every other status, or a missing status, returns False.
  - **The tuple.** `UNSETTLED_INDEX_STATUS` now includes STALE_PROJECTION and UNASSESSED, and keeps STALE.
  - **The day.** `day` is the board's UTC day. `index_settled` is evaluated on the first page body, while the
    status-set check still covers all pages.
  - **Planted break.** I made PARTIAL always settle: 4 tests failed (three in the truth table, plus the b2
    replacement test).
  - **Redundancy.** Reverting the tuple to v1 failed only the constant test, because `index_settled` already refuses
    UNASSESSED. That is defence in depth, not a gap.
- **Wire and policy.**
  - `finding_gaps` passes through `SiteFacts` to `read.py:363`, and is null on cold and EV by default.
  - `POLICY_VERSIONS["finding_index"]` imports `finding_index.POLICY_VERSION`, so the board and the summary share it.
    The summary gains no `finding_gaps`.
  - **On a real Postgres board.** I saw this myself: `policy_versions.finding_index == "finding-index/2"`, and
    `finding_gaps.text == "Not available yet · 27 of 31 days have no assessed readings"`, with 27 ascending days.
  - **Copy.** The text matches §3 exactly, including the `has`/`have` and `is`/`are` forms and the withheld suffix.
- **No gap reads as zero.**
  - The gap count uses the requested days whose state is not CURRENT. A neighbour day outside the window, or an
    EDGE/WITHHELD entry, is never counted.
  - **Planted break.** I counted every gap entry instead: 2 tests failed.
  - **The cases.** An UNASSESSED body is unsettled and carries the 31-of-31 line. A PARTIAL body with the board day
    gapped is unsettled. A PARTIAL body with the board day CURRENT settles on its true rows and shows the line.
  - **Edge case.** The line is None when `g == 0`, even if `withheld` is set by a discovered neighbour. That is
    Addendum 1 Q5, and the board day itself is still protected by `index_settled`.
- **Addendum 2.**
  - **(a)** Cost Earlier is pinned as exactly one tuple, `("ACT-000001", "Verified on test data", COST_DETAIL)`, plus
    its href.
  - **(b)** PROTECT is pinned in its safeguard form: the verification href is checked and the detail is None.
    "outside this view" is absent from all rows.
  - **(c)** See L1.
  - **The "every earlier detail is None" check now skips Cost.** That is justified. The Cost list is pinned
    exactly, detail included, so skipping it hides nothing.
  - **b4 Day A checks.** The restored assertions are byte-identical to the original addendum-6 lines at
    `1e16b31e3:test_out_b4_board_postgres.py:342-349`, and they pass. Only the Cost `state == NEEDS_ATTENTION` line
    remains dropped, and it is named, as are the Day B Must-not-harm and ACT-048 checks.
- **True v1 vs v2 comparison (5 reads), credible.**
  - **The v1 side.** `v1true-states.jsonl` came from the `ca6d7d61b` module (`finding_index_v1.py` in scratch). It
    shows UNASSESSED with 0 rows, settled True: the gap read as zero.
  - **The v2 side.** `v2-states.jsonl` shows PARTIAL with 1, 1, 3, 5 and 3 rows.
  - **What stayed the same.** Category and outcome states, `failed` and `read_state` are identical in all 5 reads.
  - **What moved.** Only the Cost and Protect Earlier lists on the two 11-02 reads, which is the expected R595 move.
  - **Agreement with my run.** It agrees with the passing b4 and e4 tests and with my probe.
- **Addendum 3.**
  - **The mapping.** `FINDING_TITLE` matches `findingWords.ts` `LIFECYCLE_WORDS[*].title` verbatim, and the
    fallback "Generator support review" matches `OverviewFindingList.tsx:358`.
  - **The stored title.** `_findings` uses the mapping. The stored title and the index wire are untouched: no change
    to `analytics/` or the store beyond U1.
  - **The literal test.** It checks presence, not the key-to-title pairing. But the behavioural test catches a swap:
    I swapped SUPPORTED and UNCONFIRMED and the behavioural test failed.
  - **Vocabulary scan.** The titles are in `COPY`, so they are scanned.
  - **Residual.** The lead-Finding sort key `(title, finding_id)` (`mini.py:351`) now sorts on lifecycle titles.
    For SUPPORTED-only sets this is effectively `finding_id` order. It is harmless, but a silent change.
- **Fixture follow-on, correct.**
  - Real v2 bodies always carry `status`. Under the new rule a status-less fake would silently unsettle, so adding
    `"status": "CURRENT", "gaps": []` keeps the original meaning of those tests rather than masking anything.
  - I grepped every MiniPorts fake user (b2, c4, d4, e4 readback, idx_gaps_board). No other fake body lacks
    status in a way that now flips meaning. The w301 and w401 `finding_index` fakes are estate store ports and
    don't apply.
- **s4 bridge-chain assertion.** It is unchanged by U2 or the fix round. It is still honest, as judged in the U1
  review.

## Checks run

- **`docker ps`.** Only `assetopsv1-postgres-test-1` and `assetopsv1-postgres-1` were running; no `assetops-ops03-*`.
- **Focused pytest on the snapshot.**
  - Setup: plan2 venv, the brief's PYTHONPATH, the Postgres URL. `assetops_backend.__file__` resolved to the
    snapshot.
  - Files: `test_idx_gaps_board`, `test_idx_gaps_index`, `test_out_b1_board`, `test_out_b1_status`,
    `test_out_b2_mini`, `test_out_b2_vocabulary`, `test_out_b4_board_postgres`, `test_out_b4_read`,
    `test_out_b4_route`, `test_out_c4_ev_warnings_postgres`, `test_out_c4_mini_ev`, `test_out_d4_board`,
    `test_out_e4_readback`, `test_out_e4_readback_postgres`, `test_s4_finding_index_postgres`,
    `test_s4_finding_index_reach`.
  - Result: **206 passed**, 0 skipped, 4 warnings, 456 s.
- **Planted breaks, in memory.** All six were caught:
  - `touched` end bound exclusive: 2 failed.
  - `touched` start bound exclusive: 1 failed.
  - PARTIAL ignores the board day: 4 failed.
  - Title swap: 1 failed.
  - Gap count includes all entries: 2 failed.
  - v1 unsettled tuple: 1 failed.
- **Probe.** The e4 body with the Cost row removed contains no "not realised savings": 1 passed.
- **Guards.** I ran `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1` in the worktree, without
  `-ExecutionPolicy`. Both passed.
  - **Caveat.** The worktree is at `0b92bf66d`, with U3 frontend and the untracked U4 test. Its backend is identical
    to `a88588312`. The snapshot is not a git repo, so the guards cannot run there.

## Not verified

- **`check-all.ps1` 11/11 at U2.** That is the handoff's claim; I did not run it.
- **Full backend suite.** It is the U4 merge gate; there is no implementer full run for this revision.
- **Frontend.** U3 is out of scope here.
- **Layout evidence.** Not applicable to a backend unit.

## Residual risk

- **Portfolio cells.** They inherit board settledness and carry no gap line, so a mini cell can settle on a PARTIAL
  index with many unassessed days. This is spec-sanctioned (acceptance 7, R613-adjacent), and the board day itself is
  assessed.
- **Withheld Findings with no line.** A withheld Finding whose only gap is a discovered neighbour gives no board line
  (Q5). It is visible on the Findings page only.
