# FX-COLD-LINKED review (fresh Claude reviewer, 2026-11-10)

Diff: `git diff main...task/FX-COLD-LINKED` (bcdf5389b, packet e679bfbd8/8e45bb542). Spec: D-E5.8 / D-E5.10.

## Verdict: REJECT (one High; fix on the branch, then re-review)

The repeat-visit notice is restored (proved on Postgres), but the same change makes every later clean Cold board
claim the failure day's Findings as its own. The packet's claim that a resolved Finding "keeps `in_window = False`"
holds only for the unit fixture, not for real data.

## Findings

1. **High - a resolved Finding shows as in-window on clean windows (false Protect claim; COH-4 risk).**
   `backend/assetops_backend/site_outcomes/cold.py:249` sets `in_window = start is None or (...)` from
   `episode_bounds`. Real START_RESPONSE episode revisions store NULL bounds
   (`postgres_assessment_store.py:1631-1640`: `x = item if kind == "EXCURSION" else None`, so `ls/us/le/ue` are
   NULL). A start-failure Finding resolved by the new linked read is therefore always `in_window = True`; the
   excursion Finding linked from the same work also came back in-window. Observed on Postgres (scratch wrapper
   around `test_fx_cold_linked_postgres`, board `fx_cold_clean_board`, window 2026-11-09 18:00-19:05, the clean
   run): Protect is NEEDS_ATTENTION, headline "Cold room temperature outside its policy band", subline "Backup did not
   start by itself; cooling stopped...", and both 16:00-window Findings (`c063b874...` start failure, `7b0e2750...`
   excursion) are listed as primary MOVES issues. `cold_findings` returned 0 rows for that window, so all of this
   comes from the linked read. Why it matters: a clean day or window now reports a temperature excursion and backup
   failure that did not happen in it, and the Protect row disagrees with the Findings list for the same window.
   `tools/checks/chain_coherence.py:567-575` (COH-4, "a board Finding is missing from the Findings list for the
   board's window and Site") would fire on every post-failure Cold day board in the F-COH bundle. The estate summary
   reads the same latest contained window, so the Portfolio/summary Protect cell is affected the same way. Under the
   dispatch rule any such finish-check risk is High. Not rerun through `demo_combined_finish` (no build here), so the
   COH-4 failure is inferred from the rule and the observed board, not observed.
   Fix: rows added by the linked read must not count as in-window by default. For example, mark them
   `in_window=False` (the regular read already returns every Finding anchored in `[lo, hi)` when a selection
   exists), or decide in-window from the Finding's anchor rather than from NULL episode bounds. Then they feed only
   the repeat warning, the Cost/CC-3 row and link resolution, as the packet intends. Add the assertion in item 3.

2. **Medium - EV fidelity: same shape, different meaning.** `cold.py:136-151` copies `ev.py:149-162` line for
   line. EV's `_finding` (`ev.py:289-291`) has no window semantics, because the EV list is SUPPORTED-only and not
   window-scoped. Cold's list is anchor-window-scoped (`_finding_ids`, `postgres_assessment_store.py:2479-2486`), so
   every Finding the Cold resolve adds lies outside the window by construction. Copying the block without that
   distinction is the root of item 1. Other divergences: `claims` (cold.py:154) now includes resolved rows. That is
   harmless once item 1 is fixed, since only open in-window excursions read it. The `known` set is keyed from rows,
   not facts, which is equivalent.

3. **Medium - the unit tests do not pin the behaviour that matters.** `backend/tests/test_fx_cold_linked.py:47`
   asserts the Protect subline using `F118` (`test_out_b3_cold_ev.py:61`), whose episode bounds are 06:00-07:00. Real
   start-failure rows have NULL bounds, so the test passes for a reason production does not have. The Postgres test
   (`test_fx_cold_linked_postgres.py:78-82`) checks only the warning count on the boards, not Protect. On question 4:
   the Postgres test is enough proof that the warning is restored. It is not enough proof of the no-false-claim
   side, and on main the unit tests only fail with a TypeError. Add: (a) a stub-port unit test with a resolved row
   whose `episode_bounds` are null, asserting Protect has no FINDING issue and `PROTECT_SUBLINE`; (b) in the Postgres
   test, assert that the `later` board's Protect row lists no FINDING issue and is not the start subline.

4. **Low - by-id read correctness (question 1): sound, with one note.** `linked_finding`
   (`postgres_assessment_store.py:2587-2614`) checks tenant, Site, domain and id. It reuses `_REVISION`
   (`ar.knowledge_cutoff <= :k`, the same cutoff every existing cold Finding read uses) and the same default
   (`known_at`, else the ingestion watermark), so it never shows a revision that the board's own list could not
   show. A Finding with no revision by the cutoff returns None. A closed, NO_LONGER_SUPPORTED or superseded
   Finding comes back at its latest lifecycle, is not `open` (`board.py:28,164`), and does not count toward
   REPEATED. That is honest. Note: the linked read does not follow a split parent to its children, the same as EV.
   Thread visibility stays bounded by `lifecycle_cutoff`/`visible_at` in `read.py:504-505`.

5. **Low - refused re-read (question 1).** Setting `findings_ok = False` and adding `cold_findings` to the failed
   list is the right, honest behaviour. It is the addendum-3 M1 rule EV uses, the board shows "could not be loaded"
   rather than "outside this view", and CC-3 does not claim "None found". Note: `except Exception` also catches a
   `ValueError` from `UUID(finding_id)` (`read.py:354`) on a malformed link id and turns it into a PARTIAL board,
   which F-THREADS `board_faults` would flag. EV has the same exposure, and current ids are UUIDs.

6. **Note - mini 31-60-day gap (question 5): real by construction, low demo severity.** Mini reads Findings from
   `chain_findings` over the 31-day work window, while the repeat rule counts visits over 60 days
   (`outcomes/warnings.py:181-186`). A Kobo or Kisiwa visit linking a Finding anchored 31-60 days before the end of
   the view will not see that Finding open, so the repeat notice can be silently missing there. It only matters for
   a Thursday beat that shows a mini repeat-visit notice over a window ending 31 or more days after the linked
   Finding. I did not check the data for such a pair. Keep mini repeat beats inside 31 days of the Finding, or ask
   the Architect to queue a mini card after the demo.

## Checks run (fxcold worktree PYTHONPATH, plan2 venv, `assetops_test` base; one file at a time)

- `test_fx_cold_linked.py` 3 passed; `test_out_b3_cold_ev.py` 28 passed; `test_out_c_rules.py` 17 passed;
  `test_out_c2_board.py` 13 passed.
- `test_fx_cold_linked_postgres.py` (run through a scratch wrapper that also printed the Protect/Cost rows; all
  original assertions executed): 1 passed, 65 s. That run produced the item 1 evidence.
- `test_out_c3_repeat_visits_postgres.py` 1 passed, 88 s.
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): "Architecture check passed." (exit 0).
- Not run: the full suite (policy), the frontend (no frontend change), `demo_combined_finish` (needs a build).

## Residual risk

- After the item 1 fix, the Action and case rows on clean windows lose the " · linked finding outside this view"
  suffix (they now resolve). That is the intended EV-like behaviour, but it changes board text on post-failure
  windows. CO-1 asserts no OUTSIDE text only on Kobo, so no finish row is known to depend on it.
