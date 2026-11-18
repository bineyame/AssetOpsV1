# FC-1 / FC-2 review: Findings cards (task/FC-findings-cards @ 656f99278)

Reviewer: fresh Claude (Opus), independent of the builder. Diff: `git diff main...task/FC-findings-cards`.
Spec: build sheet "Findings cards ruling (2026-11-10)" D-E5.25 to D-E5.28; mockup `v71/findings-cards.html`.

## Verdict

**ACCEPT WITH FINDINGS FIXED ON THE BRANCH.** M1 has to be fixed before merge, because a test in a file this branch
edited is red. The code itself matches the ruling and the mockup. Nothing is High.

## Settled questions

1. **Counts.** `index.py` computes `supported_findings`, `unconfirmed_findings` and `awaiting_verification` over
   `basis`. `basis` is the rows `select_finding_scope` returned, after withholding and with the fuel rows, filtered
   by lens and taken before the state filter. These are the same rows the list pages through when the state filter is
   "all", so the card and the list agree. With a state filter set, the cards still count the whole lens. That is how
   the cards worked before (the old basis_count did the same), and it matches the chips.
   - Frontend: when `coverage.state` is not COMPLETE, every numeric card carries "So far" and the explanation line is
     shown. A count is never shown as complete when coverage is incomplete.
   - `basis_count` and `total_count` are still null unless COMPLETE.
   - "As known at k": awaiting verification uses `scope["k"]`, and HISTORICAL counts as fully analysed in the
     breakdown. Correct. The old historical test was not updated, though (M1).
2. **Golden `summary.claims`.** This is **pre-existing drift, not added by this branch.** CH-5a2b step 1
   (`c10d51658`, 2026-11-05) added `summary["claims"]` to every Findings body. The golden was last touched by
   `c60bd8c07` (2026-11-07), a hand edit of two lines that did not add `claims`. The replay compares whole responses
   (`actual == expected`), and `link_parity.checked` does not strip `claims`, so main's w301 golden replay fails
   today. This matches `733eaf75c`, which moved the w301 golden test (T6) into E2.
   - Regenerating it here is acceptable. The added block is exactly what main already emits (`count.opportunities`,
     NOT_KNOWN, value null), it is a summary key as the FC-2 card allows, and it is unrelated to any change on this
     branch. See L1 for the packet wording.
   - I did not rerun the 14-minute verify. I rely on the packet's "6 passed (843 s)".
3. **Wording.** Matches the mockup's sections A, B and C word for word:
   - the three labels, "Not yet confirmed" and its note, and the "So far: {full} of {applicable} sites fully analysed"
     parts in analysis words;
   - the explanation line;
   - the mini-grid-only note;
   - "Not counted yet" with "Counted once every site is fully analysed".

   "High priority", "Low confidence", "Some data missing" and "Not assessed" are gone from the cards. No system
   words.

   On the null note, the builder followed the mockup: the parts appear on Confirmed findings only. **That is right.**
   The spec's "followed by the same parts" is ambiguous, the mockup is the layout spec, and with FC-2 in place this
   path is reachable only on an older backend body.
4. **Consumers.** Nothing reads these three keys outside the estate Findings page and its tests:
   - Portfolio, tools, finish/self-check scripts and `chain_coherence.py` were checked. `chain_coherence.py` reads
     only `summary.claims` from Findings, which is unchanged.
   - No tool asserts the old card text.
   - Nothing would break the build self-check.
5. **Tests.** The new frontend test pins exact strings for the complete case, the partial-with-numbers case and the
   null case. The new backend partial test compares the counts to the rows, and the packet shows it fails on main
   (`None == 2`). Both are non-vacuous. See L3 for weak spots.

## Findings

**M1 (Medium, acceptance gap). `backend/tests/test_w301_estate_index_postgres.py:500` and `:515` fail on the branch.**
- What is wrong: `test_late_support_change_recurrence_at_exact_cutoff` still asserts that every summary count is
  null, both for a HISTORICAL read one microsecond before the late match (`before`, line 500) and for the
  PENDING_RECOMPUTE live read (`pending`, line 515). Under D-E5.26 those counts are now 0.
- What I saw: line 500 fails, 1 failed / 32 passed. Line 515 would fail next.
- Why it was missed: the packet ran only 4 tests, selected with `-k`. This test is the "as known at k" case.
- Fix: use `COUNTS_ANYWAY` on both lines. Optionally assert that `before` gives (0, 0, 0). Then rerun the whole file.

**L1 (Low). The packet does not explain the golden `claims` change.** It says "the replay evidently tolerates it".
The replay does not tolerate it; main's golden was stale. The packet should cite `c10d51658` (CH-5a2b) as the source
and the T6 deferral (`733eaf75c`), so a reader can see the change was not hidden.

**L2 (Low). Stale comments and register status.**
- `findingIndex.tsx:165` cites "MD-FC-1..4, register R715-R718", but only R715-R717 / MD-FC-1..3 exist.
- The file header (`:5`) still says "Priority and confidence stay `Not assessed`". That is still true of the row
  columns, but no longer of the cards.
- R715-R717 read "open until the owner approves the draft". Once approval is recorded, the coordinator should update
  them at merge.

**L3 (Low, preference). Weak spots in the tests.**
- The backend partial test only checks that `awaiting_verification` is an `int`. The cold estate always gives 0, so
  the mini-grid count is never exercised on a PARTIAL scope.
- No frontend case renders a HISTORICAL partial body.
- Neither blocks the merge.

## Checks run (this revision, 656f99278)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` | clean |
| `npx.cmd vitest run src/estate` | 5 files, 120 passed. It ran, with node_modules junctioned and then removed. |
| `tools/run-host-tests.ps1 -- test_w301_estate_api.py test_w301_estate_index_postgres.py` (assetops_test) | 1 failed (M1), 32 passed, 1695 s |
| `check-agent-workflow.ps1` | passed |
| `check-architecture.ps1` | exit 1, unrelated to this branch (see below) |

`check-architecture.ps1` reported two problems:
- Rule 8 finds no INSERT for six cold/EV `*_consequence_*` tables in `financials/.../postgres_consequence_store.py`.
  The branch does not touch that file, and the string is present in it.
- The chain-structure guard cannot run without `ASSETOPS_GUARD_PYTHON`.

## Not verified

- The 14-minute w301 golden verify (I rely on the packet).
- The full suites (demo-sprint policy).
- Layout evidence. Not run, and low risk: three standard MetricCards with `columns={3}`.
