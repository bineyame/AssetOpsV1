# S3-02b re-review: fix round 1 (claim-limit section, UI)

Reviewer: a fresh, independent Claude reviewer who did not author the slice or the fix. Reviewed revision `e6492b97`, diff `git diff 12246a6f..e6492b97` (fix commit `e8971255`, closeout `e6492b97`).

## Verdict: ACCEPT

M1 and M2 are closed, and L3 and L4 are addressed. The new echo check fails closed. I found no new fail-open path and no High or Medium finding.

## Prior findings

- **M1 (whole-day coverage read as 0): closed.**
  - `RoleCapability.status` and `covered_minutes` are now optional (`frontend/src/sites/claimLimitClient.ts:40-42`).
  - `roleCoverage()` (`frontend/src/sites/EvidenceClaimLimit.tsx:143-148`) uses the role-level `covered_minutes` when it is present. Otherwise it takes `minutes_by_status.COVERED`, and the total is the sum of `minutes_by_status`.
  - A role with no minutes reads "no readings" rather than "0 min" (`:618`). The row status comes from the same figures when it is absent (`:613`).
  - The test "a whole-day read states its coverage in minutes derived from the spans, never 0" asserts the visible "30 min of 30 min" on every row, and asserts that no row reads "0 min of".
  - I confirmed against `backend/tests/fixtures/s3_claim_limit_api_samples.json` that both window samples carry only `minutes_by_status: {COVERED: 30.0}`, with no `status` or `covered_minutes`.
- **M2 (unframed non-current whole-day list): closed.**
  - When the read is not current and has a per-period list, `[data-claim-limit-earlier-periods]` introduces it as "At the time, this version listed these assessed periods:" (`:529-535`).
  - The per-period list itself is drawn only from `historical_ceiling` when the read is not current (`:492`).
  - The `it.each` test covers both the HISTORICAL sample (`late-revision/withdrawn-window`) and the STALE_PROJECTION sample (`stale-selection/window`). For each it asserts the visible framing and the `earlier` marker, and that no "own level" line appears.
- **L3 (the whole day's own level and period times): addressed.**
  - A CURRENT whole day states its own level (`:523-525`). This applies only when it is current and `support` is non-null.
  - Each period item is labelled "Period HH:MM–HH:MM UTC" from the day's assessed-period list. It falls back to "An assessed period", which the packet's residual risk names.
  - The test is "a current whole day shows its own level and each period's time range".
- **L4 (evidence script could not be reproduced): addressed.**
  - `tools/s302-claim-limit-evidence.mjs` is committed. `node --check` passes, and Node is v24.15, which provides the global `WebSocket` and `fetch` the script uses.
  - It reads the walkthrough `manifest.json` and covers 10 URLs at 1440 and 390. It now also covers the three whole-day reads.
  - It fails on any of these: an unsettled page, sideways scroll, an element past the viewport, a whole-day coverage cell that is 0 or malformed, a missing current level or earlier framing, or a failed keyboard selection.
  - The owner walkthrough has an optional rerun step.
  - I did not run it: it needs the walkthrough servers and Chrome, and no finding required it. The packet's `EVIDENCE PASSED` on `assetops_s302_owner_fx` is therefore the implementer's claim and is unverified by me.

## Echo check (prior residual risk)

`getClaimLimit` (`claimLimitClient.ts:246-252`) turns a `loaded` answer into `unavailable` in two cases:
- the echoed `day` is not the requested day;
- a revision was requested and the echoed `assessment_revision_id` differs from it.

The revision is not compared when none was requested. That is correct, because an UNASSESSED read echoes null.

The unavailable state renders no headline. Two real-client tests cover this, one for another day and one for another revision. Both assert `unavailable` and that no headline appears.

## Fail-open check

- I found no new path that presents a positive or current statement for a non-current read:
  - the own-level line requires `current`;
  - `data-ceiling` and `data-support` are still empty unless the read is current;
  - the derived row status only describes coverage minutes, not a claim.
- The echo check only narrows what is shown.
- `asNumber` turns a non-numeric minute value into 0. For a whole-day read that can only mean that minute value is missing from the server's own `minutes_by_status`; it cannot be read as a false 0 when the role has no data, because a role with no minutes reads "no readings". This was unchanged in this round.

## Findings

None blocking. I raise no wording findings, as instructed.

- **Low (not blocking): test coverage of the CURRENT whole-day case is synthetic.** The test builds that case from the withdrawn-window sample. No served CURRENT WINDOW sample exists in the fixtures. The committed evidence script does reach `window-current` live, and the implementer reports it passed. Optional fix: add a CURRENT window response to the API sample fixture in a later slice.

## Checks run

- **`npx.cmd tsc --noEmit` (frontend):** exit 0.
- **`npx.cmd vitest run src/sites/__tests__/evidenceClaimLimit.test.tsx`:** 1 file, 34 passed, 0 failed, 8.6 s.
- **`node --check tools/s302-claim-limit-evidence.mjs`:** ok.

## Not verified by me

- The full `npm.cmd test` and the production build. The implementer reports 69 files and 1646 passed at `e8971255`; the only change after that revision is in `.agent`.
- The walkthrough and the evidence-script run, including `EVIDENCE PASSED`, and layout at 1440 and 390.
- `check-architecture` and `check-agent-workflow`. The fix touches only `frontend/src/sites`, `tools/` and `.agent/`.
- The backend suite. There is no backend change.
