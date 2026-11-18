# W1-UX-04 review - Action, work, change and verification presentation

Reviewer: fresh independent Claude reviewer. I did not author this slice.
Revision reviewed: `56a63bb6` (build `de7d14ef` plus the closeout commit), detached in `AssetOpsV1-review4`.
Diff reviewed: `git diff b4a89314..56a63bb6 -- ':!.agent'`.

## Verdict: RETURN

The slice is mostly sound. The S6-02b fail-closed tests are intact, and most honest-state rules hold on the new cards. Three Medium findings block the merge:

- Finding 1: a selected historical outcome loses its source qualification and known failures on the Verification card.
- Finding 2: an INCONCLUSIVE outcome with a measured safety failure names the failure but does not show its value and limit.
- Finding 3: the packet records the 390 px measured claims as met, but the shared capture tool cannot measure at 390 px.

All three are small to fix.

## Checks I ran (from `frontend/`, PowerShell)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run` on `siteAction`, `siteActionVerification`, `siteFoundationChange` and `siteWorkActions` | 4 files, 100/100 passed (62 s). This matches the packet's per-file counts: 43 + 24 + 10 + 23. |
| `npx.cmd vitest run` on `t028Vocabulary`, `sharedVisualVocabulary` and `w1Vocabulary` | 3 files, 35/35 passed |

Vitest ran in this session without the esbuild sandbox failure.

I did not run these, so they are unverified by me:
- full `npm.cmd test`
- `npm.cmd run build`
- the registry checker
- `tools/check-all.ps1`
- the served captures, which need Chrome, the walkthrough databases and a dev server

I did look at the builder's PNGs in `%TEMP%\w1ux04-shots\`.

## Test assertion diff (merge-gate check)

I diffed every changed test file against `b4a89314`. Four test files changed, and no shared test helper changed.

| File | Lines removed |
| --- | --- |
| `siteActionVerification.test.tsx` | The import line only. It now also imports `scanDisclosureVocabulary` and `expectStateLineVisible`. The rest is one appended describe block (`:552-692`). |
| `siteWorkActions.test.tsx` | The import line, and `q("details")`, which became `q("[data-disclosure='site-work-basis']")` at `:125-126`. The assertions after the selector are unchanged. The new selector picks the same basis disclosure, now that the card's references come first. |
| `siteFoundationChange.test.tsx` | The import line only, plus an appended block. |
| `siteAction.test.tsx` | Nothing removed; additions only. |

**No fail-closed assertion was weakened.** The S6-02b historical, F1 actual-current, withdrawable-resolution, overlap-hold and test-scoped-label tests all still pass unchanged.

## Honest state: what holds

- **A measured safety failure.** On a current INEFFECTIVE outcome with `GUARDRAIL_FAIL`, the label reads "Trial missed a safety or service limit", never "Target not met". The value and limit appear in the default reading ("measured 60 min, limit 0 min" in the served guardrail PNG). The source and the policy-trial / no-savings note sit beside them.
- **Current VERIFIED.** It keeps "within the sampled limits", the source label and the demonstration note.
- **REASSESSMENT_PENDING.** `showRecord` is false (`SiteActionVerification.tsx:487`). The card has no record, no bars and a waiting tone.
- **Historical selection.**
  - The card reads Historical with "Current state: ..." beside it.
  - `CurrentStrip` (Historical banner, actual current state) still renders above every card on Plan, Evidence and Verification.
  - The selector stays in the address.
- **"Applied".** It is "Applied; effect not yet measured", in a limited tone. The Change card is limited and never positive.
- **Site Work.**
  - The proved zero renders only for a loaded read with `total_count === 0`, with `read_at` as its as-of.
  - A refused or unread list shows no count, no bars and "time not recorded", never the current time.
  - Nothing is shown while the read is loading.
  - No verdict is derived.
- **RESOLVED and holds.** RESOLVED stays withdrawable in the unchanged S6 panels and in `TrialNotice`. The different-Finding hold is visible on the card, with a problem tone and a link to the blocking Action.
- **Default reading.** The state sentence, scope and as-of are outside the closed disclosure on every card. The tests assert this per state.

## Findings

### 1. Medium - a historical outcome on the Verification card drops its source label, demonstration note and known failures

`frontend/src/sites/verificationCards.tsx:101-112`

- **What is wrong.**
  - When `historical` is true, the card renders `ProductStatus` with `currentnessWords("HISTORICAL")` and a single line: "Outcome then: {label}. Current state: ...".
  - Unlike the current branch (`ProductOutcome`, `:114-120`), it never renders:
    - `words.source.label`
    - `words.demonstrationNote`
    - the `KNOWN_FAILURE` reasons
- **Effect.** In the builder's own capture (`s602b/app-verification-historical-narrow.png`), the card headline reads "An earlier outcome, shown as a record: target met within the sampled limits", with no source line. The source qualification ("Registered Lab trial data") appears only in the comparison table much further down. A historical INCONCLUSIVE would also drop its known target failure from the card.
- **Why it matters.** It breaks the rule that VERIFIED keeps its source label, and that known failures stay visible. The source qualification is defined as "always shown beside the outcome" (`productWords.ts` `SourceQualification`). This branch is exactly where an old positive is most likely to be misread.
- **Fix.**
  - In the historical branch, also render the source line and the demonstration note from `words`.
  - Render the known failures, for example by reusing the same children `ProductOutcome` builds.
  - Add an assertion to the existing "selected withdrawn outcome is Historical" test that the card contains `Source:` and the demonstration note.

### 2. Medium - INCONCLUSIVE with a measured safety failure: no value or limit on the card, and the known failure prints twice

`frontend/src/sites/verificationCards.tsx:93-94,114-120`; `frontend/src/ui/ProductStatus.tsx:85-105`; `frontend/src/sites/verificationWords.ts:121-122`

- **How the backend produces this case.** The evaluator returns INCONCLUSIVE with `KNOWN_FAILURE:below_reserve_seconds` whenever any fact is unknown while a guardrail was measured as FAIL (`backend/assetops_backend/actions/verification_rules.py:776-778`).
- **What the card does.** It computes `limits` for that case, but `ProductOutcome` renders limits only when `showsFailedLimit`, which is INEFFECTIVE with `GUARDRAIL_FAIL`. So the measured value and limit never appear. The failure shows only as a name, and its text doubles the prefix: `reasonWords` returns "Known failure: Time below reserve." and `ProductOutcome` adds another "Known failure: ".
- **Test gap.** The test titled "INCONCLUSIVE keeps known failures" (`siteActionVerification.test.tsx:599`) asserts only `/cannot tell|could not conclude/`. It never checks that a known failure is visible.
- **Why it matters.** It breaks two rules:
  - A measured safety or service failure must show its value and limit.
  - Unknown evidence must not hide known failures.

  This is the state the task singles out, and the served INCONCLUSIVE capture was not run, so nothing else caught it.
- **Fix.**
  - Render `limits` on the card whenever `limits.length > 0`, regardless of outcome. Either do it in the card's own children, or widen `showsFailedLimit` in the shared helper to cover INCONCLUSIVE with a measured guardrail FAIL. The shared helper is W1-UX-01 code; keep any change there additive.
  - Pass known failures without the duplicated prefix.
  - Extend the INCONCLUSIVE test case with a FAIL guardrail metric. Assert the "measured ... limit ..." text and the known-failure text in `[data-product-status]`.

### 3. Medium (packet integrity and acceptance evidence) - the 390 px claims were measured at desktop width; this slice neither fixed nor qualified that

`tools/w1-ux-01-evidence.mjs:98-101,186-201`; `.agent/W1-UX-04-review-packet.md:77,107-117`

- **The defect.** It was reported in the W1-UX-05 review, finding 1. `size()` sets the device-metrics override, but the measurement never checks that `innerWidth` or `clientWidth` is near 390. The UX-05 run recorded `clientWidth` 1425 at both widths. `shot()` reapplies the override before capture, so the PNGs are 390 px wide even though the measurement was not taken at 390.
- **What this slice changed.** Its tool edits (the card map, `W1_NO_VISUAL_OK`, `W1_TAB_TRACE`) do not touch this. The slice did not make the defect worse.
- **What the packet claims.** It records "Met: 364/364" for 1440/390, which presents the narrow sideways-scroll, state-box and Tab-reach claims for all nine screens as measured.
- **What the PNGs show.** The 390 Tab walk that reached `/sites/KOBO-002/health` is consistent with a desktop-width layout. The narrow PNGs I opened (Verification historical, Verification guardrail) look correct at 390. That is a visual check, not the measured claim.
- **What must happen.**
  1. This slice: the packet records the narrow measured claims as **not established by measurement** (visual check of the PNGs only), not as met.
  2. Before the combined W1 walkthrough relies on any 390 claim, the coordinator or the UX-01 owner fixes the shared tool:
     - After `size()` and `go()`, wait for `window.innerWidth === width`.
     - Add a claim that fails unless `clientWidth` is within `[width-20, width]`.
     - Rerun the narrow pass for UX-01, UX-04 and UX-05, or replace those passes with the combined walkthrough captures.

  The tool fix is not required on this branch. If the implementer makes it here, rerun the narrow pass and record the measured widths.
- **`W1_NO_VISUAL_OK`.** It can exempt any mock id from the "card has a visual" claim through an environment variable. The packet does not say which runs set it, or for which ids. Record that too.

### 4. Low - Evidence headline names only the later window when both windows are incomplete

`frontend/src/sites/verificationCards.tsx:321`

When both windows are incomplete, the headline says "Some readings are missing from the later window", which understates the gap. The bars beside it show both counts. Fix: name both windows when both are incomplete.

### 5. Low - Evidence and Plan cards on a cutoff selection do not carry the Historical label themselves

`verificationCards.tsx:200-226,299-333`

- **What happens.**
  - The Evidence card shows "Both windows have their readings" in a neutral tone, with a scope sentence saying "selected earlier time".
  - A cutoff-selected Plan that is still current reads "Plan fixed before the later readings".
- **What mitigates it.** The `CurrentStrip` directly above shows the Historical banner and the actual current state (F1). Neither card claims a verdict, so this is not blocking.
- **Optional fix.** Use `currentnessWords("HISTORICAL")` in these cards when `explicit` is set.

### 6. Low - the Action-work and Change step strips show the verification label with no source qualification

`frontend/src/sites/SiteAction.tsx:768`; `frontend/src/sites/SiteFoundationChange.tsx:392`

`outcomeWords(state, reasons, null)` gives the VERIFIED step the detail "Target met within the sampled limits" with no source. The tone downgrade only affects tone, which the step strip does not show. The W1-UX-01 Overview card already does the same (`SiteAction.tsx:392`). A related artefact: a Verification card with no record prints "Source: Where these readings came from is not established", because `null` is passed as the source.

These are summaries, and each links to Verification. Fix in the W1 copy pass: say "see Verification for its source", or pass the source when the read has it.

### 7. Low - one mock capture is blank but was counted as rendered

`%TEMP%\w1ux04-shots\s601b\mock-changes-narrow.png`

This 390 px capture is blank (2.9 KB). The "mock renders" claim passed anyway. The s602b run has a valid `mock-changes` capture, so the comparison exists. This shows the `h1, h2` readiness check is weak. Note it in the packet.

### 8. Low (user-review item, not a defect) - duplication

The new cards sit above the unchanged S6 panels. This repeats the outcome, the failed limits and the source (see the guardrail PNG: the card, then the Outcome panel, then the "Trial missed a safety or service limit" panel). The duplication is what keeps the S6-02b fail-closed tests exact, so it is the right trade for W1. The owner should judge the density in the combined walkthrough. Folding the panels belongs in a later slice with its own test migration, not this fix round.

### 9. Low - the two uncaptured S6-02b cases

`target_miss` and `inconclusive` were not served. That is recorded honestly as not run, with jsdom coverage. However, finding 2 is precisely a defect in the INCONCLUSIVE card that jsdom did not assert. In the fix round, run the `inconclusive` served case (one case at a time is fine) after finding 2 is fixed, or record it as not run again together with the new jsdom assertion.

## Residual risk not named in the packet

- **Known-failure prefix.** The doubled "Known failure:" prefix in `ProductOutcome` affects any other caller that passes `reasonWords` output.
- **Evidence received counts.** They count slots where `slotProblems` is empty. A slot with an unrecognised cell state but no listed problem would count as received. The `complete` flag from the read still drives the state line, so the label cannot read complete falsely.
- **Recommendation as-of.** The "as of" for an available recommendation is the latest input window end. That shows how old the inputs are, not when the page was read.

## Files

- Review: `.agent/W1-UX-04-review.md`
- Key code: `frontend/src/sites/verificationCards.tsx`, `frontend/src/ui/ProductStatus.tsx`, `frontend/src/sites/verificationWords.ts`, `tools/w1-ux-01-evidence.mjs`
