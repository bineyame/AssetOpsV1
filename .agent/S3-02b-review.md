# S3-02b review: Evidence Analysis selected claim limit UI

Reviewer: a fresh, independent Claude reviewer who did not author the slice. Reviewed revision `18749240` (`task/S3-02b-claim-limit-ui`), diff `git diff 8b5d8137..18749240 -- ':!.agent'`.

## Verdict: RETURN

There are two Medium findings. Both are on the whole-day (WINDOW) assessment, which the owner reaches from the "Whole day" period link on every assessed day. Everything else in the focus list holds. Fix on the branch, then run a re-review and the owner walkthrough.

## Findings

1. **Medium: a whole-day assessment shows "0 min of 30 min" covered for every reading.**
   - **Where:** `frontend/src/sites/EvidenceClaimLimit.tsx:574-579` (and `:577` for `data-role-status`). The type at `frontend/src/sites/claimLimitClient.ts:39-45` declares the role-level `status` and `covered_minutes` as always present.
   - **What is wrong:** the served WINDOW-scope read does not carry those two fields. Each role has only `spans`, `minutes_by_status` and `evidence_ids`. This shows in `backend/tests/fixtures/s3_claim_limit_api_samples.json` (`late-revision/withdrawn-window`, `stale-selection/window`) and in the live fixture. `asNumber(undefined)` becomes 0, so all five readings show "Generator on or off 0 min of 30 min, Gaps: none", although the data says all 30 minutes are COVERED.
   - **Observed:** in headless Chrome against the walkthrough fixture, for the CURRENT whole day 2026-10-06 (`c52fe3dc…`), the HISTORICAL whole day 2026-10-13 and the STALE whole day 2026-10-15.
   - **Why it matters:**
     - The default reading of a supported read shows a wrong coverage figure that contradicts itself.
     - The test at `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx:226-231` renders exactly this sample, but it asserts only a data attribute, so it passes.
     - The packet's residual risk says the CURRENT WINDOW form is "covered by code only". In fact it is reachable on every day.
   - **Fix:** when the role-level fields are absent, derive covered and total from `minutes_by_status` (the COVERED value and the sum) or from the spans, and make those fields optional in the type. Alternatively, render the window's roles in a separate form. Add a test that asserts the visible coverage text for a WINDOW sample.

2. **Medium: a non-current whole day lists its per-period ceilings without saying they are from that earlier version.**
   - **Where:** `frontend/src/sites/EvidenceClaimLimit.tsx:495-508`; the list item text is at `:503`.
   - **What is wrong:** for a HISTORICAL or STALE_PROJECTION window, the window's `historical_ceiling.ceiling` is null, so `earlierSentence` is null. The `historical_ceiling.interval_ceilings` list then renders as plain "An assessed period: avoidable, fully covered". The interval case says "At the time, this version said: …", but there is no such framing here. The only marker is `data-claim-limit-intervals="earlier"`, which is invisible.
   - **Observed:** live on the 2026-10-13 (HISTORICAL) and 2026-10-15 (STALE) whole-day reads.
   - **Why it matters:** the slice's fail-closed rule is that a non-current read shows only history, recognisably as history. A reader of an out-of-date day sees an unqualified "avoidable, fully covered" under the badge.
   - **Fix:** when `!current`, caption the list the same way as the interval case (for example "At the time, this version listed: …"). Assert the visible framing in the test at `:226`.

3. **Low: the whole day's own claim level is not in the default reading** (`EvidenceClaimLimit.tsx:168-170`, `:503`).
   - The S3-02a handoff asks for WINDOW `support` (the window-level COMPLETE/LIMITED/INDETERMINATE) to be shown as the window's level. Today it appears only in "Technical details".
   - The per-period items carry no period time ("An assessed period"), so with more than one interval they cannot be told apart.
   - Not blocking. This can be folded into the fix for 1 and 2, or into W1 conclusion.

4. **Low: the layout substitute (deviation D1) cannot be reproduced.**
   - The focused CDP measurement that stands in for `tools/layout-evidence.mjs` lived in the implementer's scratchpad and was not committed.
   - The packet correctly records `layout-evidence.mjs` as `not run` with its unmet precondition (no registered Lab run store), so that record is not an error. But nobody else can rerun the 16 measurements.
   - I did not rerun 1440/390.

No internal IDs, enums or rule or model names appear in the default reading outside "Technical details". The only exceptions are fallbacks that print an unknown enum value, which is acceptable. I raise no wording findings, since W1 conclusion covers wording.

## Focus checks (verified)

- **A positive statement only when CURRENT.** Met for INTERVAL.
  - `headline()` states a ceiling only for CURRENT with `current_positive_claim`, or for Indeterminate.
  - `data-ceiling` and `data-support` are empty when the read is not current.
  - Top-level `interval_ceilings` is read only when the read is current (`:464`).
  - For WINDOW, see finding 2.
- **Non-current reads show history only.** For HISTORICAL and STALE INTERVAL reads, the screen shows:
  - the badge;
  - a "no current conclusion" headline;
  - "At the time, this version said: …".

  I saw this live, including on 2026-10-06 after `late`.
- **No selection reads UNASSESSED.**
  - With no day, the section says "No assessment selected" and makes no read.
  - With a day and no revision, it shows the UNASSESSED read and the day's assessed periods.

  I saw both live and in the tests.
- **Every refusal is a plain message with no partial claim.**
  - The ten refusal cases go through the real client in the tests.
  - Live, a revision from another day answers 422 `REVISION_OUTSIDE_WINDOW`. The screen says "belongs to a different day" and shows no headline. The code appears only inside the refusal's Technical details.
- **A stale response is cancelled.**
  - The effect aborts on a change of day or revision and checks `signal.aborted` before setting state.
  - The test resolves the two reads out of order, and the later selection wins.
- **Exact record links.**
  - `recordHref` copies every parameter, so `day`, `revision` and the legacy `assessment` are kept, and it sets `record`.
  - `select()` keeps `assessment` and drops `record`.
  - `assessment` is never read as the selection (tested).
- **Keyboard, reload and Back.**
  - The periods are native `Link`s with `aria-current`.
  - The selection lives only in the URL, so a reload re-reads the same revision.
  - I checked these in code and in the unit test. I did not drive a real keyboard or Back in a browser.
- **Generator Evidence IDs.**
  - They are shown at role level, as "N readings", then "Reading k".
  - Span-level IDs are never attached to a gap or segment, so the screen implies no per-segment attribution.
- **The walkthrough is reachable as written.**
  - I ran it end to end (see Checks run).
  - The written commands and paths are right for `AssetOpsV1-review3`, which has the `.venv` junction and is on this branch.
  - D3: `late` leaves the recompute outstanding, and the full-coverage revision then reads STALE_PROJECTION. Step 4 of the walkthrough describes what I saw, and this satisfies "withdraw currentness".
  - D1: see finding 4.

## Checks run

- **`npm.cmd ci` (frontend):** ok.
- **`npx.cmd tsc --noEmit`:** exit 0.
- **Focused and adjacent tests:** `npx.cmd vitest run` over `evidenceClaimLimit`, `s2LedgerEvidence`, `siteEvidenceScreen`, `v01bEvidenceVisual`, `t028Vocabulary` and `siteFindingEvidence`. Result: 6 files, 106 passed, 0 failed, 16 s. Vitest ran in this session.
- **Not run:** the full `npm.cmd test` and the production build. The implementer's full-suite figure (1639 passed, 1 load flake) is unverified by me.
- **`tools/check-architecture.ps1`:** passed. The first run failed because `ASSETOPS_GUARD_PYTHON` was unset: rule 8 needs an interpreter, and this worktree has no `.venv`. With the variable set to the main venv's python, it passed.
- **`tools/check-agent-workflow.ps1`:** passed.
- **Walkthrough:** private DB `assetops_s302_owner_rv`, work folder `var/s302_owner_rv`, API port 8942, web port 5452.
  - `prepare` took 36 s. It built five cases, both comparisons exited 0, and it returned six `ok` reads plus a 404 `ASSESSMENT_REVISION_NOT_FOUND` for an unknown revision.
  - `serve` with a Vite dev server; I rendered the pages in headless Chrome (`--dump-dom`).
  - `late`: the full-coverage read became STALE_PROJECTION.
  - `attest` printed `ATTEST PASSED … (after late)`.
  - `drop` removed the database and the work folder. The worktree was clean afterwards.
- **Backend suite:** not run, because the slice changes no backend code.

## Residual risk not named in the packet

- On Back (a popstate, which is not a discrete update), the previous revision's loaded read can paint for one frame under the new address before the effect clears it. Nothing persists under the wrong revision. Low. Keying the stored read by `(day, revision)` would close it.
- The client does not check the server's `assessment_revision_id` and `day` echo against what it requested.
