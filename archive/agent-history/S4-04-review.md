# S4-04 slice review - Site Finding index read + Site Findings UI

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch
`review/S4-04-slice` at `0e697027` (code revision `38c61cfd`; later commits are closeout/evidence/docs only). Diff
`f8a131e3..HEAD`. USER_REVIEW_REQUIRED stays true: merge and `sitefindings:1#a/#b` promotion wait for the owner
walkthrough.

## Verdict

**Accept.** No High or Medium finding. Phase-1 H1 is fixed on the index side and is proved on real Postgres in both
of its forms. The UI makes a count or a "no Findings" claim only for a `CURRENT` read. I reproduced the walkthrough
prepare and the `initial` browser stage myself. One Low test gap is listed below; fixing it is recommended, not
blocking.

## H1 re-check (phase-1 High)

- `finding_index.py:180-219`. `candidate_reach` derives edge reach from the selected S3 Candidate segments of each
  edge day (start <= day start + 20 min, end >= next day start - 20 min). `discover` grows down or up from either
  that source or a stored episode, repeats to a fixed point and raises `INDEX_CONTINUITY_LIMIT` past the cap. Each
  `dispatch.window` read is cached per day and also feeds `_day`, so discovery and status use the same read.
- This matches the matcher's deferral rule. `plan` skips a cluster when `margin_ok` fails, and `margin_ok` looks at
  windows within 20 min of the cluster bounds. Windows are UTC days, so only adjacent days matter. Clusters are made
  only of CANDIDATE segments (`finding_episode.py:424-436`), so Candidate segments are the right source.
- Test `TestContinuity::test_s3_candidate_near_an_edge_reaches_a_neighbour_the_matcher_skipped` is the phase-1
  probe on real Postgres. It covers a stale D+1 (STALE, no claim, D+1 reason present), the injected cap of 1 reached
  through the S3 edge alone (409), D+1 reassessed with no rematch (PENDING, no claim; this is the second form of
  H1), and the rematch (CURRENT/1, episode 23:10).
- My own mutation: replacing the **up**-edge check with `up = up` fails this test. The **down** edge is covered
  only by inspection (see L1).
- Interaction with `fix/S4-deferred-match`: the test's stage-1 check uses `any(... startswith("2026-10-26"))`, so it
  still holds once D also carries a MATCH_PENDING reason. As defence in depth it is sound either way.

## Findings

### L1 (Low, test gap) - the lower-edge S3 Candidate reach is untested

`backend/assetops_backend/analytics/finding_index.py:192` (`down = down or (start ... <= lo + CONTINUITY_TOLERANCE)`).
I replaced it with `down = down` and the whole `test_s4_finding_index_postgres.py` still passed (10 passed, 91 s),
then reverted. The code is symmetrical with the tested upper edge and correct by inspection, so this is not an
acceptance gap. Still, a regression on the lower edge would bring back the H1 false `CURRENT` zero for a
00:00-00:20 cluster whose previous day is stale. **Fix:** add a pure unit test of `candidate_reach` and `discover`
for both edges, which is cheap, or mirror the real-Postgres probe with a 00:05-00:30 Candidate on D and a stale D-1.

No other findings.

## Implementer deviation: failed job read for the neighbouring day (2026-10-27 read FAILED)

**This is by design (the S3 six-hour bracket). It is not a bug in the index or in the S3 read seam. Severity: none
for S4-04.**

- The S3 worker expands every recompute job by `BRACKET = 6 h` to the UTC-day windows it can affect
  (`assessment_worker.py:62-70`, `day_windows`). The S3 window read lists every live or failed job overlapping the
  window's read range, which is the window plus or minus 6 h (`postgres_assessment_store.py:569-572`,
  `EvidenceQuery.read_range`). The two rules mirror each other on purpose (`D-2026-10-11-s3-phase-2-selection-and-read`
  Q7: every overlapping PENDING/LEASED/FAILED job).
- The walkthrough's staged failure (`tools/s5_overview_walkthrough.py` `FAIL_STAGE`) enqueues a **whole-day** job
  `[D, D+1)`. `day_windows` expands it to D-1, D and D+1. I computed this: a staged job on 2026-10-28 gives
  `['2026-10-27','2026-10-28','2026-10-29']`. A real reading job (10:00-10:30) stays on its own day. The failing
  model therefore really did fail the recompute of D-1 as well, so FAILED is the truthful status for 2026-10-27.
  Moving the fixtures apart was the right workaround.
- Live confirmation on my walkthrough database: 2026-11-04 and 2026-11-06 both read `FAILED` with the same job
  `f08c50a5` as 2026-11-05, and 2026-11-07 reads `UNASSESSED`.
- Side note, owned by S3 and not by S4-04: the read uses `window_end >= :lo` (inclusive), while the worker uses a
  strict bound. A job that ends exactly at D 00:00 minus 6 h is therefore listed for D but not assessed for it. This
  matters only at that exact boundary.
- Walkthrough documentation (not blocking): the owner doc names only 2026-11-05 as the failed day. The two
  neighbouring days also read "Not known" with the same reason. Saying so would avoid confusion if the owner
  browses nearby dates. The handoff's open risk ("job reasons seem to be read across the day margin") can be closed
  with this explanation.

## Verified as correct

- **Only CURRENT carries a claim.** In `SiteFindingIndex.tsx:263-276`, any non-CURRENT body, or a CURRENT body with
  a null `total_count`, shows "Not known/Not current" and "no count ... not a statement that the window has no
  Findings", with no table. "No Findings in this window" appears only for a CURRENT read with `total_count === 0`.
  Each refusal (closed, continuity limit, basis changed, invalid, 401/403, unavailable) is its own state with no
  rows or count. A 404 falls back to the unchanged T028 summary.
- **Restart on basis change.** A 409 `INDEX_BASIS_CHANGED` leads to "This list changed" with a link to the first
  page without the cursor. A scope change re-reads, and stale responses are ignored through the `active` flag.
- **Exact revision links.** The links are `siteFindingHref(site, id, revision_id)`, which gives
  `/sites/{code}/findings/{id}?revision_id=`. The browser run opened the pinned revision `1ba6ca04` and its history.
  Relation links are canonical and unpinned, as allowed.
- **URL state.** `domain/from/to/limit/cursor` live in the query string. A date change navigates with the cursor
  cleared and the limit kept. Page 2 loaded from the address alone.
- **390 layout.** I viewed `s404-initial-narrow-positive.png` from my own run. There is no page-level overflow. The
  rows table scrolls inside its panel, so Related and Amount are off-screen until the table is scrolled. This is
  acceptable, and the owner should see it.
- **Walkthrough safety.** The `--db` name must start with `assetops_s404_owner` and contain only alphanumerics and
  `_`, which closes off SQL injection in DROP/CREATE. The work directory must be `var/s404_owner*`. The tree is a
  `git archive` of HEAD with an import-isolation probe. The API, web and TLS ports are configurable. No schedule is
  installed, and `drop` removes both the database and the work directory.
- Phase-1 items in the earlier review (check order, cursor 409/422, tenant isolation, ordering parity with S5-01
  `choose`, `findings_over` untouched) are unchanged by phase 2.

## Checks run (this review)

- `assetops_backend.__file__` resolved to the review4 worktree. Private database `assetops_r404s_test`, since
  dropped.
- Focused real Postgres: `pytest test_s4_finding_index_postgres.py test_s4_finding_read_postgres.py
  test_s4_finding_episode.py -q`: **50 passed in 147 s**.
- Mutations, each reverted with a clean tree afterwards: up-edge removed fails the H1 test (1 failed); down-edge
  removed lets the whole index file pass (10 passed), which is L1.
- `npx.cmd tsc --noEmit`: clean. `npm.cmd test -- s404SiteFindingIndex.test.tsx`: **15 passed**.
  `t028Screens` and `t028Vocabulary`: **32 passed**. `npm.cmd run build`: **built**, with a chunk-size warning only.
  The frontend runner worked in this worktree. I did not rerun the full frontend suite; I cite the implementer's
  1528 passed at `86a5cb8a`.
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the main venv): **passed**.
  `tools/check-agent-workflow.ps1`: **passed**.
- Walkthrough, using a temporary `.venv` junction and a `var/sites/kobo-001.yaml` copy (both removed afterwards):
  `prepare --db assetops_s404_owner_r4 --work var/s404_owner_r4` on ports 8954-8956 exited 0 after 196 s with
  0 failed checks. Results: empty CURRENT 0; positive CURRENT 3; dirty STALE_PROJECTION; failed FAILED; unassessed
  UNASSESSED; page 1 had 2 rows and a cursor, page 2 had 1 row. `serve` showed the Performance gate OPEN.
  `node tools/s404-finding-index-evidence.mjs ... initial` against Vite on 5454 passed **54/54 claims**, with no
  page overflow at 1440 or 390. Afterwards I ran `drop`, dropped the databases, and removed the junction and the
  yaml.
- Not rerun: the full backend suite. I cite the implementer's run at `38c61cfd`: JUnit 2382 tests, 0 failures, 0
  errors, 0 skipped, 983 s wall. Every later commit touches only `.agent/`, `.ai/` and the task file. Also not
  rerun: the `late`, `settled` and `closed` browser stages (the packet reports 12/12, 14/14 and 14/14), and the
  9/9 run of `check-all.ps1`.

## Residual risk (not already named in the packet)

- Under the contract, a day whose selected Candidate run ends within 20 min of midnight reads not current/Unknown
  until the next day is assessed and matched. This includes the latest assessed day. It is conservative and
  correct, but the owner may find a "Not known" on the most recent day without a near-midnight run.
- Copy for the owner and the W1 plain-language task. Row status shows the transition words "Assessment updated;
  amount unchanged" next to an Amount column that says "No amount shown", which could read as a contradiction.
  Other items: the loading text "Loading the site's findings." is lower case, the date inputs and the button are
  unstyled native controls, and the basis disclosure contains engineering terms (as the packet already notes).
