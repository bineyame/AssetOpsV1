# post-W6 W1-mini-Action-b: independent review

Reviewer: fresh Claude reviewer (not the author). 2026-10-25. Branch `task/post-W6-W1-b`, head d78c9133, diff
`git diff main...HEAD -- ':!.agent'` (32 files, merge-base = main 3b4979d0).

## Verdict

**ACCEPT.** There are no High or Medium findings. The four Low findings below are optional and can be fixed on the branch.
Two items are already with the Architect and do not block this verdict: the Evidence requirements and Action history
caps, and confirmation of the Interpretation history fallback and of R395. Merging still depends on those Architect
answers, as the packet says.

## Rulings checked against the code

| Ruling | Result |
|---|---|
| Q19/Q20 (pre-flight 2) | **Domain link:** `dispatchTarget` (SiteFindingIndex.tsx) uses the UTC day of `episode.start`. It adds `revision` only when `assessment_revision_id` is in the row's `interval_assessment_revision_ids`. An invalid start shows plain "Dispatch".<br>**Rest:** the mini-only links are wired in the frame. The panel description matches the mock text word for word. The renewable helper link keeps the helper sentence unchanged and has no Opportunity ID. |
| Q21/Q22 (pre-flight 1) | **Portfolio roll-up:** links to `FINANCIALS_PATH`.<br>**Inspect technical basis:** `technicalBasisHref` links to the Dispatch day only. It never takes a Finding, consequence or primary revision, and the bridge passes no proof. It is omitted when the start is absent or invalid. `?day&view=analysis` matches Dispatch's own link form (PerformanceDispatch.tsx:1614). |
| Q23 (pre-flight 7) | **Defaults:** `history_limit` defaults to 3; an explicit 1-100 is kept.<br>**Stack:** repeated `history_back`, with `0` allowed only at the bottom. A malformed stack or more than 100 entries is rejected and offers "Back to newest" instead of a guessed cursor.<br>**Paging:** "Previous versions" pushes the current cursor and "Next versions" pops it. Cutoff and limit are in every link.<br>**Layout:** compact Version / Fuel price / Recorded amount / Status columns. "Show this version" holds the source and the full record. "Price versions recorded ({total})" is a closed disclosure.<br>**Scroll fallback:** a region labelled "Fuel cost versions" with tabIndex 0; max-height 480 px, or 900 px at ≤640 px; the cue shows only on overflow. |
| Q24 | "Return to financial overview" appears in the form footer, beside the disabled edit. |
| Q25 (pre-flight 6) | The source line, the guard `$railHelper` and the ruled text are byte-identical. Two new fixtures widen the regex: one to the index, one to a prefix lookalike. |
| Q26/Q52 (pre-flight 3) | **Tabs removed** on Recommendation and all five Action views.<br>**Label:** one `MOCK DEVIATION D2 (R383)` line with `data-mock-deviation="R383"`, directly after the retained tabs on overview, Analysis, Evidence and History. There is none on Alternatives, Recommendation or Action. |
| Q27 / Q33 / Q35 (pre-flight 4, 9) | **Open site** is on the Action header.<br>**`/overview`:** an alias for every Site type. It now routes cold and EV to `DomainActionRoute`.<br>**Unknown section:** the ruled body renders the segment as text, then a separate "Open Action overview" link to the bare route. The h1 and the section row stay, with nothing current.<br>**Subtitle:** gets the suffix only when `w1ActionCode(title)` is non-null. |
| Q28 | `ANALYSIS_HELPER_SECTION` is removed; the Alternatives helper stays. |
| Q29/Q30 (pre-flight 5) | **Kinds:** `ActionEventKind` is widened. The badges and meanings are the ruled text. An unknown kind reads "Recorded event" and its meaning is the ruled fallback, never ACCEPTED.<br>**Dedupe:** by resolution ID. Backend `verification.py:948-963` takes `resolution_events` from the same store events, so the IDs match. Row keys are prefixed.<br>**Counts and toggles:** counts come from the de-duplicated union. The chip reads "Latest at read time". The sentence and toggle appear only when there are more than three entries. The raw count appears only in exact references. |
| Q31/Q32/Q34 (pre-flight 8, 11) | **Plan headings:** the CSS is scoped to `.w1f4-verification-plan`; `th scope=row` is kept; primitives.css is untouched.<br>**Chips and source:** `requirementTone(true)` returns `info` and the `.verify-chip--info` rule is scoped. `sourcePair` names a shared source once.<br>**Gaps and conflict note:** `distinctGap` applies per panel. `CONFLICT_CARD_NOTE` shows only when `reads.conflict !== null`; a true failure keeps its failure wording. |
| Q36 (pre-flight 10) | **Mini strip:** links to `/actions`, which matches the mock's `link(global, "Manage in Actions →")`.<br>**Cold and EV:** they use `DomainWorkActionsPage`, which is untouched. |
| Q46 | R384 and R385 labels sit below the Success criteria and Evidence requirements tables. |

## Register and merge (d960eeee)

- **IDs:** R380-R395 are each unique.
- **R383:** byte-identical to the pre-flight ruling 3 row (checked by script).
- **R395:** marked "superseded by R383 ... kept for traceability". The source comment says the same. No other R395
  reference is left in `frontend/src` or `tools`.
- **`SiteAnalyticsFrames.tsx`:** since merge-base = main, the diff against main contains only W1-b hunks, so all of
  W1-a's content is kept.
- **R395 disposition:** sound. It is the same departure, and R383 is the Architect-worded superset. It is still listed
  for Architect confirmation.

## Guards and allowlist (not loosened)

- **Real-file mutation:** I widened the Findings regex in `OperatorShellLayout.tsx` to `\/findings(?:\/.*)?$/` and ran
  `Invoke-NavigationTruthfulnessCheck`. It returned 1 failure ("does not declare the ruled rail selection helper"). I
  restored the file.
- **Fixtures:** both new fixtures use `Edit-Lines`, which throws if its pattern is missing. Each pattern can match only
  the source line, not the doc comment.
- **`test/panelStructure.ts`:** adds only the single selector `[data-mock-deviation="R383"]` to LEADING_SELECTOR. The
  w1f4 "planted extra panel" non-vacuity tests still pass. R384 and R385 sit inside panels, so they need no allowlist
  entry.

## Single-file revert proofs (each reverted to main, then restored; tree clean afterwards)

| File reverted | Test file | Result |
|---|---|---|
| SiteAnalyticsFrames.tsx | siteAction | 13 fail |
| SiteAction.tsx | siteAction | 6 fail / 77 |
| OperatorShellLayout.tsx | operatorRailInventory | 7 fail / 31 |
| SiteFindingIndex.tsx | s404SiteFindingIndex | 9 fail / 39 |
| verificationCards.tsx | siteActionVerification | 1 fail / 32 |

## Checks I ran

- **`npx.cmd tsc --noEmit`:** exit 0.
- **`tools/check-all.ps1 -Python <main venv>`:** 11/11 guards pass.
- **Targeted vitest:** 13 files, 472/472 pass.
  - siteFinancials 95, siteAction 77, s404SiteFindingIndex 39, operatorRailInventory 31, siteActionVerification 32.
  - miniDecisions, w1f4ActionStructure, w1f4ChangesWorkStructure, coldWorkActions, siteDetailRoute,
    w1f4VerificationStructure, operatorRouteFrames and siteWorkActions: 198 together.
- **Stray files:** none of `.venv`, node_modules, caches, `var/`, `dist/`, yaml or db appears in the diff. The `.venv`
  junction is untracked and stays uncommitted.

## Not verified by me

- **Full vitest (3123/3124) and the production build:** I did not run them, by constraint (a full backend suite was
  running). These numbers are the implementer's, at cb87309a with product tree e6af4ff0.
- **Captures:** not rerun.
  - `selection.json` has 142 entries: 118 tagged `w1b` across 11 screens and 24 tagged `q40`, 71 at each width. Every
    `frozen_app` file exists in the diff.
  - Heights and the tab, R383 and rail checks are taken from `consistency.log` and the run.md files.
- **Backend:** no backend tests run. This is a frontend-only slice and backend code is unchanged.

## Findings (all Low)

1. **Stale capture consistency log**
   - **Where:** `.agent/post-W6-W1-b-recapture/consistency.log:36-37`.
   - **What:** it still reports `MISSING (15, 'cold-action', 'all-open', 1440/390)`, and its summary line reads
     `15: [0, 2]`.
   - **Why it matters:** batch-15 was captured later (`batch-15/run.md`; the PNGs, evidence.json and measure.json are
     present). A reader of the log alone would conclude 140/142.
   - **Fix:** rerun the consistency script or annotate the log.
2. **Stale comment**
   - **Where:** `frontend/src/sites/SiteFindingIndex.tsx:942`.
   - **What:** the comment still calls the opportunity helper "the noninteractive line it was before". Since Q20 it
     contains a link.
   - **Fix:** update the comment.
3. **Test name does not match its fixture**
   - **Where:** `frontend/src/sites/__tests__/siteAction.test.tsx`, "with four de-duplicated entries ...".
   - **What:** the fixture produces 5 entries: 3 events, plus r-1 de-duplicated, plus r-2.
   - **Why it matters:** the exact-4 boundary that pre-flight ruling 5 names is not exercised; behaviour is covered by
     `total > 3`.
   - **Fix:** rename the test, or drop r-2 so it asserts "3 of 4".
4. **Cold strip not asserted directly**
   - **What:** pre-flight ruling 10 asks to test the mini link and both other domains. Only EV asserts that "Manage in
     Actions" is absent (`evWorkActions.test.tsx:204`).
   - **Why it matters:** cold goes through the same untouched `DomainWorkActionsPage`, so the risk is negligible.
   - **Fix:** add a one-line absence assertion in coldWorkActions.

## Choices where the rulings were silent

| Choice | Assessment |
|---|---|
| R383 label also shows on the unknown Finding section state | Sound. The tab row is retained there, so the label honestly marks it. The Architect may want R383's screen list to mention it. |
| Paging links carry an explicit limit | Matches "carry the exact cutoff and limit in every link". |
| "Out-of-range" read as more than 100 stack entries | Reasonable. Token shape is also validated. |
| Unknown event kind reads "Recorded event" | Consistent with the Q29 fallback meaning. |
| Evidence row headings unchanged | Correct per the Q31 scope. |

## Residual risk not already in the packet

- **Global CSS through a side import:** `.mock-deviation-line` lives in `w4-mini-decisions.css`, which only
  MiniAlternatives, MiniOpportunity and MiniScenarios import. It reaches the Finding and Action pages only because the
  app has no route-level code splitting. If lazy routes are added later, the R383/R384/R385 lines would lose their
  12 px styling on first paint.
- **Synthetic stress only (with the Architect; evidence noted):**
  - Evidence requirements: 458/956 against a cap of 450/800.
  - Action history at 390: 963 against a cap of 800.
  - Interpretation history after the fallback: 749/1312, within its caps. With every disclosure open, the rows scroll
    inside the region rather than growing the page.
