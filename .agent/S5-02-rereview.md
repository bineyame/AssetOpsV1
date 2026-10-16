# S5-02 re-review - fix round 1

Reviewer: fresh Claude reviewer. It did not author the slice or the fix. Reviewed revision `f5a6903f` (head of
`task/S5-02-overview-finding-list`), fix diff `git diff 087db4e8..f5a6903f`. I checked it against
`.agent/S5-02-review.md` (M1, L1), `D-2026-10-16-s502-parity` (`.agent/architect-S5-02-answers.md`), the packet's
"Fix round 1" section and the updated `.agent/S5-02-owner-walkthrough.md`. Per owner direction, wording and visual
points are out of scope, and only High or Medium findings block.

## Verdict: ACCEPT

No findings.

## M1 - closed as the ruling says

- `frontend/src/sites/OverviewFindingList.tsx:74-76`: `compareParity` now adds a not-compared reason when
  `summary.freshness.state !== "CURRENT"`. This is the ruling's "either read is non-current" condition for the
  Overview. The index side was already gated at `:70`. Any reason returns `not-compared` before the ID comparison
  (`:107`), so a non-current Overview cannot reach `same`, and it cannot reach `different` either. The ruling allows
  neither claim when a read is non-current.
- A current Overview can still claim parity. The existing positive test (CURRENT Overview, matching basis) still
  asserts `same`, and it passes.
- New test `a non-current Overview with otherwise matching reads makes no same claim` covers the case from my original
  scratch check (STALE_PROJECTION plus a DISCOVERED card plus an aligned index). It asserts `not-compared`, the reason
  text, a reload control and no "same" text, and that the index's rows are kept under the index's own authority, as
  the ruling requires.
- The evidence script (`tools/s502-overview-finding-list-evidence.mjs:211-213, 260-261`) now requires `not-compared`
  whenever the Overview's freshness is not CURRENT. That closes the gap where the live run recorded "same" beside a
  stale Overview.

## L1 - closed

`OverviewFindingList.tsx:214-226`: a CURRENT read with `total_count > 0` and no rows now renders `unavailable` with
"Reload both". No count is stated. The guard sits after the non-current and zero-count branches and before the
count/rows render. The new test asserts the state, that no "Showing the first 0" text appears, and that the reload is
present.

## Fail-open check

The fix only adds conditions. One more reason can push parity to `not-compared`, and one more branch can withhold the
count. No existing guard was removed or reordered, and no new path produces `same`, `different`, a count or an empty
claim. The walkthrough's `tick` is a tool-side, explicit schedule pass, `s5_overview_walkthrough.tick`, which the S5-01
walkthrough already uses. It reads freshness from a temporary API on port +20, so it does not clash with the served
API. It changes nothing in product code.

## Walkthrough `tick` step

The step is reachable for a non-developer owner. It is a single command in a new window with the same `PYTHONPATH`
line, and it ends with a line to check (`Positive day Overview freshness: CURRENT []`). It explains that "cannot be
compared" before `tick` is correct. It also explains why the owner should look at the other days first: tick settles
2026-10-27, which then reads "No Findings". The section 4 `settle` row tells the owner to run `tick` again before
expecting "same". One small ordering point, which does not block: the "look at every other day first" sentence comes
after the command block. Because the day table above it is already read by then, the order works as written.

I did not run the walkthrough myself (owner direction). The implementer reports initial 62/62 before tick, then
tick -> CURRENT, late 8/8, settled 10/10 with "same" after tick, and closed 16/16. That is unverified by me.

## Checks run (revision `f5a6903f`, this worktree)

- `npx.cmd vitest run` on s502OverviewFindingList, s5SiteWindowOverview and s404SiteFindingIndex: 3 files, 67 tests
  passed (24/28/15).
- `npx.cmd tsc --noEmit`: exit 0.
- Not run: full `npm.cmd test` (the packet reports 67 files / 1596 tests), `npm.cmd run build`, the architecture and
  workflow checks, and the live walkthrough or evidence script. The fix changes no backend code, so no backend suite
  was run.

## Residual risk

- The live `same` observation now depends on running `tick` within the five-minute freshness horizon. If the owner
  waits too long, the panel correctly shows "cannot be compared". That is expected behaviour, and the walkthrough
  states it.
