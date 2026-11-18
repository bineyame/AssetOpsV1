# W1-F4 review (Recommendation, Changes, Action x5, Verification, Site Work)

- Reviewer: fresh independent Claude reviewer. Revision reviewed: `983622c0` (code as of `6989f074`), diff `af1aa23e..HEAD -- frontend`.
- Contract: `D-2026-10-17-mockup-layout-spec` (`.agent/architect-W1-fidelity.md`); owner verdict `.agent/owner-W1-walkthrough-verdict-2026-10-17.md`.

## Verdict: RETURN

Panel titles, order and the removal of every answer card are correct on all nine screens, and the S6-02b checks are intact. Two mock structures are still missing (findings 1 and 2), and under the contract they block.

## Findings

1. **High: Verification drops the mock's summary row.** Location: `frontend/src/sites/SiteActionVerification.tsx:382-384`. The `verification` view goes straight from the status strip to `VerificationMetricCards`. v69 (`frontend/mockups/v69/screens.js:352`, `mheader(...)`) puts a five-cell row between those two: Owner, Due / SLA, State, Source and Success criterion. It shows in the mock captures at both 1440 and 390 (`.agent/W1-F4-evidence/s602b/verification-*-mock.png`) but in none of the app captures. That is a grid and prominence mismatch. Every cell is supported or has an honest gap.
   **Fix:**
   - Port the mock's `mheader` as a shared pattern, for example `MetricHeader` in `ui/V69Layout.tsx` with a `.v69-mheader` class in `ui/primitives.css`, laid out 5 across at 1440 and 2 across at 390 as the mock is.
   - Render it after the strip and before the metric cards. Fill the cells this way:
     - State: the outcome state word.
     - Source: the Finding version link.
     - Success criterion: the plan target text, or "No success criteria recorded".
     - Owner: "Not recorded".
     - Due / SLA: "Not set".
   - Add `.v69-mheader` to `LEADING_SELECTOR` in `frontend/src/test/panelStructure.ts:52-53`. This change is additive. Assert the row in `w1f4VerificationStructure.test.tsx` in the stocked, no-outcome and refused variants. In the refused variant, every cell is a gap word.
2. **Medium: the Site Work table does not have the mock's columns or state badge.** Location: `frontend/src/sites/SiteWorkActions.tsx:216-220` and `:241`.
   - v69 `sitework` has the columns Action | Source | Owner | Due | State (badge) | Success criterion. The app has Action | Source | Created | State (plain text) | Latest step.
   - The three missing columns are stated only in a small note under the table. The mock gives them column-level prominence, and the contract says the gap belongs in the slot.
   **Fix:**
   - Use the mock's six columns.
   - Fill Owner and Due with "Not recorded" or "Not set", in the same words as Action scope.
   - Fill Success criterion with "Not recorded" for each row. The index has no plan text.
   - Render State as the `w1f4-action-badge` tone badge that Action scope uses.
   - Keep the created time and the latest-step link as a small second line in the State cell, or in the Action cell, so the window filter's basis stays visible.
   - Drop the "Owners, due dates and success criteria are not recorded" sentence, since the cells now say it.
   - Update `siteWorkActions.test.tsx` and `w1f4ChangesWorkStructure.test.tsx` to assert the six headers and a badge on each row.
3. **Low: History rows keep a second line of raw codes and half-IDs.** Location: `frontend/src/sites/SiteAction.tsx`, History rows. Examples are `DEMO_REVIE…` and `ACTION_FOUNDATION_STALE expected 6b1d26ff-0… current 58798f5f-8…` (see `s601b/action-history-event-1440-app.png`). A truncated ID cannot be read and is internal vocabulary. This line is also most of the 1.46-1.49x height. The packet says failure codes are never truncated, but `DEMO_REVIE…` is truncated. Showing the codes was accepted before F4 and is asserted by existing tests, so this does not block.
   **Fix:** keep the plain meaning in the cell, and move the code and short-ID line into the row's `title` and the closed disclosure. If the codes must stay visible, at least do not truncate them.
4. **Low: a sentence is duplicated on Action scope.** The note reads "No verification plan exists for this work, so no trial outcome can exist yet. No verification plan yet." (`s601b/action-overview-recorded-1440-app.png`). **Fix:** drop the second sentence.
5. **Low: `TrialNotice` is a full-width body-size callout on Plan, Evidence and Verification.** Location: `frontend/src/sites/SiteActionVerification.tsx:497-506`. The mock has no closing callout on these screens, although its doc comment says "the mock's closing notice line". It is a material limit, so it must stay visible. **Fix:** render it at note size (`v69-chart-note`) inside the owning panel, or as a small line under it, and correct the comment.

## Heights (rule: about 1.3x)

- Execution failed (1.73x): the apply control is a working control and stays visible. Acceptable.
- History (1.46-1.49x): this comes from the second reference line. See finding 3. Cutting that line brings it near the rule.
- Action overview (1.37x): the honest notes (trial only, source unverified) are acceptable once the duplicate in finding 4 is removed.
- Verification pair (1.38-1.44x): the pair is stretched by Outcome evidence, whose attempts line, source pass and button are honest state. Acceptable.
- Site Work (1.38x): this is the window form, a working control. Acceptable, and it will change with finding 2.
- Recommendation held and guardrail (1.30-1.39x): the hold sentence is a material limit. Acceptable.

## Checks run (this reviewer, worktree at `983622c0`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` on the four `w1f4*Structure` files: **4 files, 61 passed**.
- `npx.cmd vitest run` on `siteAction`, `siteActionVerification`, `siteFoundationChange` and `siteWorkActions`: **4 files, 102 passed**. Vitest ran in this session; the known sandbox esbuild denial did not occur.
- Not rerun: the full suite (the implementer recorded 2018 passed and 1 known load flake at `6989f074`), `check-all.ps1`, and the captures. I cannot rerun these.
- Assertions:
  - The S6-02b blocks in `siteActionVerification.test.tsx`, everything before line 570, have no diff hunks.
  - The removed assertions in that file belong to the retired answer cards. Each one is re-asserted against the strip or the owning panel, and the trimmed lists are re-asserted in full after "Show all".
  - `panelStructure.ts` is additive only (`expectPlantedPanelRejected`).
- Captures: I compared the 1440 pairs for execution-failed, history-event, overview, recommendation-held, changes, verification-guardrail, evidence-guardrail and sitework-active, and the 390 pairs for history-all and verification-pass.

## Residual risk (not blocking)

- The Changes route has no Foundation subtab row, while the mock shows `Change & effect` as the fourth subtab. This follows the earlier `D-2026-10-02-rendered-tabs-per-capability` and `FoundationSubtabs.tsx`, so it is outside F4's scope. The owner may notice it in the walkthrough.
- The Site Work subtabs show only Actions, while the mock has Actions, Incidents and Maintenance with counts. This is the same capability rule.
- At 390, the wide tables (History, Target and guardrails) scroll inside their containers. The page itself has no overflow.
