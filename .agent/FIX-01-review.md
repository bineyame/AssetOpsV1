# FIX-01 final review (estate two revisions)

Reviewer: fresh Claude Reviewer, 2026-10-31. Branch `task/FIX-01-estate-two-revisions` @ 8c3f69ba, against main 9ebb3d1c.
Judged against `.agent/FIX-01-diagnosis.md`, `.agent/FIX-01-packet.md` and the 2026-10-31 FIX-01 and FIX-01/OUT-W Architect
rulings in `AssetOpsV1-plan2/.agent/decisions-while-owner-away-2026-10-30.md`.

## Verdict: ACCEPT

No High or Medium findings. The two Low items below can be fixed on the branch or left; neither blocks merge.

## Correctness

- **Dedupe (`estate/coverage.py:246-271`).** It matches the supersession ruling. The highest `revision_no` wins across
  windows. The same revision id seen in two windows keeps the copy with the latest `(selected_at, seq, selection_id)`;
  that tuple is used only for this, as ruled. A fork, a missing `revision_no`, and two revisions in one window all
  still raise. Migration 0009 declares `revision_no integer NOT NULL` and `UNIQUE (finding_id, revision_no)`
  (`0009_finding_store.py:69,103`), and both adapters cast with `int(...)`. So for real rows the fork and
  missing-number branches cannot be reached. They are defence in depth, which is acceptable. Append-only lineage
  means a larger `revision_no` is always the later head, so the rule is sound.
- **What raises now (blast radius).** The new code raises in a strict subset of the cases where the old code raised.
  The old code raised on any differing revision id for one Finding, whether the copies came from one window or from
  two. The new in-window check fires only in cases that already raised. The cross-window check now fires only on a
  fork or a missing number. For the same revision seen twice, the held copy changes from the last one iterated to
  the latest-selected one. For a single revision id the row fields are the same either way: EV evidence comes from
  that revision's provenance, the cold item is pinned to that revision's assessment, and the consequence lookup is
  per revision id and cutoff. So no day that read 200 before reads differently now. Mini-grid does not go through
  `_windowed`, and the mini branch of `_finding_links` is unchanged.
- **Provenance.** It matches the provenance ruling. `selected_assessment_revision_ids` and the window evidence ids are
  unions over the Site's windows. `rows`, `selected_finding_revision_ids`, the consequences, and the row-level
  `evidence_ids` and `source_provenance` come only from the winner. A superseded revision contributes nothing at row
  level. `test_highest_revision_no_wins_across_windows` asserts that `e-old` is absent.
- **Link (`estate/index.py:96`).** Windows are now matched on `finding_revision_id`. A revision is pinned to one
  assessment and therefore to one window, so the winning link is non-null. If the same revision is held in two
  windows, the link is still null, as before.
- **`latest_window` (`site_outcomes/read.py:144-158`).** Windows are sorted by start, and each window joins the current
  event only when its start is before the event's running maximum end. So windows that only touch at an end stay
  separate events, and identical windows join one event. The winning event is the one with the latest end. Inside
  it, the most recently selected window wins. Probed in memory:
  - A three-way chain (A overlaps B, B overlaps C) forms one event.
  - Of two identical windows, the later `seq` wins.
  - A later separate event beats an older event that holds a recent reselection.
- **Agreement for Depot.** On 6 Oct the Findings row is rev2. Its link opens E [08:00, 09:00). The Portfolio choice
  inside the overlap event is the most recently selected window, which is E (seq 2, the DEFAULT selection). Both
  choices land on E, and OUT-C4 asserts the window is exactly E.
- **Test-double change (`test_post_w6_w3_estate_links.py:92`).** This is legitimate. Both real adapters always set
  `finding_revision_id` (`postgres_estate_read.py:269,309`). Every call in that file uses `FID`/`FRID`, so the double
  does not hide a cross-Finding match.
- **Callers of the new return shape.** `site_selected_windows` now returns dicts, and it has one production caller
  (`read.py:367`, wrapped by `latest_window`). The c3 spy is updated. No other consumer exists.

## Findings

| # | Sev | Where | What | Fix |
|---|---|---|---|---|
| L1 | Low | `.agent/mock-departure-register.md:1` | A UTF-8 BOM (EF BB BF) was added in front of `# V69 mock departure register`, probably during the merge-conflict resolution. Guards still pass, but it is an unrelated byte change and can trip line-1 parsers or diffs. | Re-save the file without the BOM. |
| L2 | Low (test gap, not acceptance) | `backend/tests/test_out_w2_summary_window.py:79-102` | The tests do not cover `latest_window` on a three-way chained overlap or on identical bounds. The logic is correct by inspection and by my probe. Chaining is transitive, so in A[8,10) / B[9:30,12) / C[11,13) with A selected last, A wins even though it does not overlap C. That is one reading of "the group of windows overlapping one another". | Optionally add one chain case and one identical-bounds case so the reading is pinned down. |

## Residual risk (not in the packet)

- **The two rules can in principle disagree.** The Findings head is chosen by the highest `revision_no`. The Portfolio
  window is chosen by the most recent selection in the event. They agree whenever selection order follows revision
  creation, which holds for Depot and for job-driven reassessment. An operator pin that reselects an older window's
  existing assessment, without reassessing it, would make the Portfolio pick that window while Findings keeps the
  newer revision in the other window.
- **The episode filter runs before the dedupe.** If a head revision's episode left the day while an older revision's
  did not, the older revision would be shown. EV cannot hit this, because both revisions sit on the same session
  bounds. Cold is unlikely to, because the episode end only grows.
- **Cold boards with multiple analytics.** On overlapping cold windows from different analytics, the cold Portfolio
  window is now the most recently selected window in the event, where it used to be the one with the latest end. b4
  and c3 are green, and the cold replay yields one window, but no fixture exercises this case.
- **Cold overlap is proven only on synthetic data.** This is a recorded deviation, and I accept it as recorded.

## Checks run (this review)

- Focused non-Postgres pytest (plan2 venv, worktree PYTHONPATH) over `test_fix01_windowed_dedupe`, `test_out_w1_selected_windows`,
  `test_out_w2_summary_window`, `test_post_w6_w3_estate_links`, `test_w301_estate_api` and `test_w301_estate_coverage`:
  **54 passed**. `test_out_b4_read`: 6 passed. There are no non-Postgres w302 or w303 files.
- Breaks planted in memory, with no source edited:
  - `if b > a` changed to `if b < a` in `_windowed`: 5 failed (all four parametrised supersession cases plus
    higher-from-earlier-selection).
  - Touching-end grouping changed from `<` to `<=` in `latest_window`: 1 failed
    (`test_separate_events_later_event_wins_despite_older_selection`).
  - The new tests are not vacuous.
- `tools\check-all.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv, without `-ExecutionPolicy`): **All 11 guards passed**.
  This includes both missing-claim scans, which failed in the packet's earlier run for environmental reasons.
- Not run, by instruction: Postgres, the full backend suite, the frontend and the browser. For the w301/w302/w303,
  `test_fix01_*_postgres`, out_c3, out_c4 and out_b4 results I rely on the packet's per-file Postgres evidence on the
  final head; I did not rerun them.

## Full backend run before merge?

**Not required.** The `_windowed` change only removes refusals. Its new raise is a subset of the old ones, and for an
unchanged revision id the held copy is the same. The new return shape has one production caller, which is updated.
The packet's per-file Postgres evidence covers every estate reader (w301/w302/w303) plus board, warnings and
repeat-visit on the final head. Under the tiered test-suite policy the slice touches no schema or plumbing, so the
regular main safety-net full run, after this merge or the next one, is enough.
