# W1-UX-03 review: Evidence, Evidence Analysis, Dispatch and Analysis presentation

Reviewer: fresh, independent Claude reviewer. I did not author this slice.
Revision reviewed: `c5627f21` (detached), diff `git diff b4a89314..c5627f21 -- ':!.agent'`.
Inputs read: the task packet, umbrella, UX-01 handoff, both Architect answers, the build brief, the review packet and the handoff.

## Verdict: RETURN

One High finding blocks the merge. Finding 1 is a new honest-state regression. The Dispatch Analysis "What can be concluded" step states a stored result that is not current without saying so. It sits beside a state line that reads "Using the latest checked readings". The rest of the slice holds the honest-state rules well. The fix is small.

## Findings

1. **High: Dispatch Analysis concludes from a stored, non-current version without framing it as historical.**
   - **Where.** `frontend/src/sites/PerformanceDispatch.tsx:1179-1183` (`ReadingsToOutcome` conclusion). The selection comes from `:286-288` (`selected = inWindow ?? loaded`).
   - **What is wrong.**
     - The conclusion is framed only by the day's state: `read.status === "CURRENT" && !read.stale`.
     - When the address selects a stored version that is not the day's current one, `inWindow` is null. The Overview marks this case "pinned" with "This is a stored result that is not the current one" (`:774`). Analysis has no such marking.
   - **What I saw.** I wrote a scratch test from the file's own fixtures and deleted it afterwards. It used `?day=2026-10-02&revision=rev-old&view=analysis`, with `rev-old` an older-rule version and the day CURRENT.
     - The conclusion read: "Possibly avoidable, for the period 03:45 to 04:15 UTC."
     - The state line above it read: "Using the latest checked readings. This result uses every accepted record for the day…"
     - `[data-dispatch-pinned]` was absent.
   - **Why it matters.**
     - A superseded, possibly different, outcome reads as the current positive conclusion. That breaks the rule that historical results are framed as historical, and the brief's "no wording may promote … non-current".
     - The slice makes this path easier to reach. "Versions of this period" moved out of the closed stored-record disclosure into a visible panel (`:1286-1298`), and every link there opens exactly this view.
     - The base had no conclusion sentence, so this is new in this slice.
   - **Fix.**
     - In `ReadingsToOutcome` (or `AnalysisView`), treat `selected` as current only when it is in `read.intervals`.
     - Otherwise frame the conclusion as historical, for example "…, from a stored version that is not the current result". Also show the pinned/older-rule notice in Analysis.
     - Add a test with a pinned version and a CURRENT day, asserting the historical framing and the absence of the bare positive sentence.

2. **Low: the narrow-width claim in `tools/w1-ux-03-evidence.mjs` does not check the viewport width.**
   - **Where.** `tools/w1-ux-03-evidence.mjs:208`. It has the same shape as the shared defect in `w1-ux-01-evidence.mjs`.
   - **What is wrong.** "No sideways scroll" passes on `scrollWidth <= clientWidth` and never asserts that `clientWidth` is near 390. If the override did not hold, the "narrow" claims would silently measure desktop width.
   - **Mitigation I verified.** The run logs in the implementer's scratchpad record the actual widths:
     - `w1ux03-shots-final-disp.txt`, `-ea.txt` and `-stale.txt` show `clientWidth` 390 at narrow and 1425 at desktop.
     - This covers dispatch, analysis and the three evidence-analysis cases, so this run did lay out at 390.
     - No saved log covers the `evidence` screen (the `be9b75b5` pass), so its narrow claims are not established by a recorded value.
     - The packet cites counts ("30/30") but no widths.
   - **Fix.**
     - Add a claim that fails unless `innerWidth === width` and `clientWidth` is within `[width-20, width]`, the shared-script fix.
     - Rerun `evidence` at 390, or record it as not established.
     - Cite the measured widths in the packet.

3. **Low: the Gateway contact fact understates mixed states.**
   - **Where.** `frontend/src/sites/LedgerSiteEvidence.tsx:547`.
   - **What is wrong.** Take one CURRENT gateway and one in another non-STALE state. The fact reads "No gateway report has been received yet", which is false for the CURRENT gateway.
   - **Why it is only Low.** It is non-promoting, with tone `not-known`, but it is inaccurate.
   - **Fix.** Use a neutral mixed sentence, for example "Some gateways are in contact; the others' contact is not known."

4. **Low: prose is treated as an exact value in the S3-02b technical disclosure.**
   - **Where.** `EvidenceClaimLimit.tsx:776` ("Rule wording") and `:809` ("What is not inferred"). The reason list does the same with `${code}: ${text}`.
   - **What is wrong.** Whole server sentences are wrapped in the single-value `source-reference` exemption. `D-2026-10-16-w1-ux-disclosure` allows labelled exact values, not exempted explanations. These are server-recorded strings kept verbatim from S3-02b, so the risk is small. They are, however, unscanned prose.
   - **Fix.** Keep them, but scan them, or record them as an Architect-acknowledged deviation.

## Judgement on the named deviations

- **Deviation 1 (the one pinned sentence containing "claim"): acceptable.**
  - The test allowance (`performanceDispatch.test.tsx`, Analysis W1 scan) is narrow. It filters only phrase `claim` whose text is inside `[data-dispatch-gated]`, and asserts at most one such hit.
  - Rewording would fail the G-04 missing-claim baseline. The open item is in the handoff.
- **Deviation 5 (block links named only by aria-label): acceptable.**
  - Each link's accessible name is plain and exact, for example "04:00 to 04:15 UTC: Possibly avoidable" (tested).
  - The row summary gives the counts in visible text.
  - The existing per-period block chooser below gives a visible-text, keyboard path to the same selection.
- **Deviation 2 ("As of: time not recorded" for no-day and store-not-configured): honest.** The time is never invented. The refused, unavailable and not-found states are bounded by the time the answer arrived. That is labelled in a code comment, not on screen, but it bounds the refusal and nothing else.

## Honest-state checks (what holds)

- **Stale Dispatch.**
  - The headline is prefixed "From an earlier result that is not current:" whenever the status is not CURRENT, or `stale` is set.
  - The totals keep the "not current" pinned line. The state line uses the shared non-positive labels (tested for all four non-current states, including tone).
- **Unstated totals.** `portion()` returns null when any period lacks the key, and the result renders "not known" in both the headline and the cards (tested). `operationText` still counts a missing lower bound as 0. That is a valid lower bound, not a claim of zero.
- **Missing inputs.**
  - The claim-limit strip draws a role with no spans as a hatched "not known" mark (tested, with a mutation proof in the packet). Unknown span statuses become "not known".
  - Dispatch `missingWords` and `constraintWords` never echo codes.
- **No selection.** Analysis renders "No period is selected, so nothing is concluded here" (tested).
- **S3-02b claim-limit currentness.**
  - Only CURRENT with `current_positive_claim`, a non-null and non-INDETERMINATE ceiling and a non-WINDOW scope gets the positive tone. Otherwise the tone is limited.
  - HISTORICAL maps to "Earlier version, kept for the record" (neutral). Unknown codes fall back non-positively with the code hidden (tested).
  - The Technical disclosure keeps every field as a labelled exact value.
- **Outside closed panels.** The state sentence, scope and as-of are outside closed panels on all four surfaces (`HeadlineVisualCard` status slot, claim-limit status, dispatch `.dispatch-status`).
- **Evidence.** The three reporting facts are independent. A STALE projection beside current contact reads "Not yet" (tested). Unknown projection codes read "Not known" without the code.

## Changed test assertions (diffed)

Every changed assertion either still asserts the same fact in its new place, or is stricter. None was weakened.

- **`performanceDispatch.test.tsx` status labels.** They change to the shared labels and add `expectStateLineVisible` plus a non-positive tone check (stronger).
- **Older-rule assertion.** It now asserts that the versions are absent from prose and present, in order, in a closed disclosure. The values are still checked.
- **Fixture `read_at` "x" changed to a real instant.** This change is to test data, not to any assertion.
- **`t028Screens.test.tsx`.**
  - The method version, assessment reference and record-set digest are still asserted, now inside the closed disclosure, plus an `open === false` check.
  - Only the `[data-finding-assessment-id]` selector was dropped. The ID itself is still asserted.
- **`evidenceClaimLimit.test.tsx`.** Two string updates for banned words: "run" became "period of generator operation", and "discharge capability" became "output limit". Same meaning.

## Checks I ran (at `c5627f21`, from `frontend/` via PowerShell)

- **`npx.cmd tsc --noEmit`.** Exit 0.
- **Focused vitest, 14 files.** 258 passed, 0 failed, 66.8 s. The files:
  - `performanceDispatch.test.tsx` (29 tests, also run alone and passing)
  - `evidenceClaimLimit.test.tsx`
  - `v01bEvidenceVisual.test.tsx`
  - `t028Screens.test.tsx`
  - `t028Vocabulary.test.tsx`
  - `w1Vocabulary.test.tsx`
  - `sharedVisualVocabulary.test.tsx`
  - `s2LedgerEvidence.test.tsx`
  - `siteEvidenceScreen.test.tsx`
  - `t026Evidence.test.tsx`
  - `t028EvidenceCapability.test.tsx`
  - `overviewDispatchAssessment.test.tsx`
  - `assessmentGraphics.test.tsx`
  - `siteFindingEvidence.test.tsx`

  Vitest ran under this sandbox, unlike the standing note.
- **Scratch test for finding 1.** Run and then deleted. The worktree is clean apart from this review.
- **`tools/check-agent-workflow.ps1`.** Passed.
- **`tools/check-architecture.ps1`.**
  - It first failed for the environment: Rule 8 found no `.venv` in this worktree.
  - With `ASSETOPS_GUARD_PYTHON` pointed at the main checkout's venv, it passed.

## Not verified

- **Full `npm.cmd test` and `npm.cmd run build`.** Not run. I cite the implementer's full run: 1759 passed at `022a5002`. The only later commit, `c5627f21`, touches docs and `.agent` only.
- **`tools/check-all.ps1` beyond the two guards above.** Not run.
- **Served 1440/390 captures and keyboard reach.** Not rerun; they need Chrome, the walkthrough DBs and a dev server.
  - The captures predate the last two code commits. Evidence is at `be9b75b5`; the others are at `937ddd27`.
  - `022a5002` only relabels one field inside the closed stored-record disclosure, so the visuals should be unaffected. The captures still do not depict the final revision.
  - I viewed `app-dispatch-narrow.png`: a 390 px layout with no visible page overflow and tables scrolling inside their cards.

## Residual risk

- **The headline for an unrecognised Dispatch status.** It says "From an earlier result that is not current". That is non-promoting, but for an unknown code it asserts "earlier".
- **Duplicate selection paths.** The block strip and the per-period chooser both select a block. Selection state could drift if one is changed later.
- **Strip clamping.** `PeriodStrip` clamps an instant outside the period to the strip edge. The Evidence source marker uses `last_source_time`, which is only shown when `accepted_in_window > 0`. If the window is cut on another clock, a mark could sit at the edge rather than at its true time.
