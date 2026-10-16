# W1-UX-04 review packet - Action, work, change and verification presentation

Task `tasks/W1-UX-04-actions-work.md`; branch `task/W1-UX-04`, base main `b4a89314`, final build revision `de7d14ef` (closeout commit follows). Frontend only. Reviewer diff: `git diff b4a89314..HEAD -- ':!.agent'`. USER_REVIEW_REQUIRED: a fresh independent review is the merge gate, including the S6-02b fail-closed diff below. The owner sees this slice in the combined W1 walkthrough. Do not merge before that review.

## Outcome delivered

Each of the nine screens now opens with a shared answer card. The card states the question, the answer, a state line (label, sentence, scope, "As of") and one small visual. It also has "What this means" and "What to do", links to the destination screen, and a closed "How this was worked out" panel holding the exact references. Every existing panel is kept below the card. All nine routes are scanned against the W1 vocabulary set, including their closed disclosures.

## Migrated call sites

| Route | Card (`data-headline-card`) | Mounted | Defined |
| --- | --- | --- | --- |
| recommendation | `recommendation` | `frontend/src/sites/SiteRecommendation.tsx:149` | `SiteRecommendation.tsx:643` (`heldAsOf` just above it) |
| changes | `change` | `SiteFoundationChange.tsx:124` | `SiteFoundationChange.tsx:350` |
| action-execution | `action-work` | `SiteAction.tsx:595` | `SiteAction.tsx:731` |
| action-history | `action-history` | `SiteAction.tsx:882` | `SiteAction.tsx:812` |
| action-overview | `action-state` (W1-UX-01) | unchanged | unchanged |
| sitework | `site-work` | `SiteWorkActions.tsx:387` | `SiteWorkActions.tsx:463` |
| verification | `verification` | `SiteActionVerification.tsx:492` | `verificationCards.tsx:65` |
| action-plan | `action-plan` | `SiteActionVerification.tsx:319` | `verificationCards.tsx:185` |
| action-evidence | `action-evidence` | `SiteActionVerification.tsx:324` | `verificationCards.tsx:277` |

The state words are domain-local, in `actionPresentation.tsx`:
- `applicationWords` at :76
- `recommendationWords` at :109
- `trialStep` at :166 (moved from `SiteAction.tsx`)

Labels renamed to plain words:
- "Input digest" became "Input reference" (`SiteRecommendation.tsx:390`).
- "Input fingerprint" became "Input reference" (`SiteActionVerification.tsx:677`).
- "Plan digest" became "Plan content reference" (:1028).
- "Cohort digest", "Input digest" and "Configuration digest" became "Day group reference", "Input reference" and "Configuration reference" (:1361-1365).

Raw codes and values moved into exempt exact references:
- Stored-measure value, limit and unit (`SiteActionVerification.tsx` Stored measures table).
- `cohort_status`.
- In the Site Work basis: order, selection, fence and IDs.

## Honest-state rules

- **Never positive:** Application, Change, Recommendation (including held states) and Site Work never use a positive tone.
- **Verification:**
  - Outcomes use the shared `outcomeWords(outcome, reasons, source_class)`.
  - Failed limits show the measured value, the limit and the unit in plain units, for example "measured 10 min, limit 0 min".
  - Known failures stay visible.
  - A selected earlier outcome reads Historical, with "Current state: ..." beside it.
  - REASSESSMENT_PENDING claims no result and draws no bars.
- **Missing values:**
  - Unknown before/after values are drawn as "not known", never as 0.
  - Failed attempts on Change show "not known" while the events read is pending or refused.
  - A Site Work zero appears only after a loaded bounded read, with `read_at` beside it.
- **As-of sources:**

  | Screen or state | "As of" comes from |
  | --- | --- |
  | Recommendation, accepted | acceptance time |
  | Recommendation, held | the blocking Action's latest recorded step |
  | Recommendation, other states | the latest stored input window end |
  | Change | `recorded_at` |
  | Verification | the outcome's `recorded_at`, else the Action read's cutoff or last event |
  | Plan | `recorded_at` |
  | Evidence | `knowledge_cutoff` |
  | Site Work | `read_at` |

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Each screen answers its user question with headline + visual | Met: the nine cards above (Recommendation and Value bars; Change and a chronological change/effect strip; Work strip; History strip; Site Work state bars; Verification before/after bars; Plan window strip; Evidence received-per-window bars). |
| One Action story across Overview/Plan/Execution/Evidence/History; root and selected historical outcome persist across child links and reload | Met. The S6-02b selection tests are unchanged and pass; the new tests assert that `event_id` and `outcome_id` are kept in the address. |
| Applied / completed / resolved / verified kept distinct; activity never shows effectiveness or savings | Met. Applied is "Applied; effect not yet measured" (limited). The tests assert there is no "saving" or "verified" text on the work, change and site-work cards. |
| A withdrawn older VERIFIED outcome is historical, shown with the current reassessment state | Met: the Verification card's Historical status, and the S6-02b withdrawn tests are unchanged. |
| A guardrail failure is prominent, with value, threshold and unit; unknown required evidence gives "cannot tell yet" without hiding known failures | Met (tests and served captures for guardrail, target miss and INCONCLUSIVE). |
| Site Work proved-zero only after a successful bounded read; no verdict derived | Met. |
| Exact IDs, digests, rule versions and typed codes appear only in labelled exact detail | Met (closed `ExactReferences`, and the existing Dig deeper sections). |
| W1 set opt-in and closed-disclosure check for each non-positive state | Met for every rendered loaded state. Refusal states are the exception: see Known deviations. |
| 1440/390 served capture against v69 | 1440: met (claims below). 390: not established by measurement (visual check of PNGs only); see Fix round 1. |
| No weakened S6-02b fail-closed assertion | Met: the diff of `siteActionVerification.test.tsx` changes only the import line and appends one describe block. |

## Test assertions changed

The diff against main of the four test files removes only these lines.

1. **The import line in four files** (`siteAction`, `siteActionVerification`, `siteFoundationChange`, `siteWorkActions`). Each now also imports `scanDisclosureVocabulary` and `expectStateLineVisible`. Nothing else in those lines changed.
2. **`siteWorkActions.test.tsx:125`**: `q("details")` became `q("[data-disclosure='site-work-basis']")`. The new answer card's exact-reference disclosure is now the first `<details>` on the page, so the test selects the same basis disclosure by name. The assertion itself is unchanged.

All other test changes are additions in new `W1-UX-04` describe blocks:

| Describe block | Location |
| --- | --- |
| Application and History | `siteAction.test.tsx:809` |
| Recommendation (four states) | `siteAction.test.tsx:865` |
| Change | `siteFoundationChange.test.tsx:243` |
| Site Work (rows, proved zero, unread) | `siteWorkActions.test.tsx:306` |
| Verification, Plan and Evidence, plus the different-Finding hold | `siteActionVerification.test.tsx:552` |

## Checks run (revision `de7d14ef`)

| Check | Result |
| --- | --- |
| Full `npm.cmd test` | 74 files, 1756 tests passed, 3.1 min. The earlier run at `9606c357` failed one test: `siteFoundationChange` "shows old/new reserve..." could not find its heading within 5 s, the known load flake. That file passed alone (10/10) and passes in the final run. |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npm.cmd run build` | exit 0 (only the existing chunk-size warning) |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | exit 0 |
| `tools/check-all.ps1 -ExecutionPolicy Bypass` | 9/9 guards PASS |
| Focused tests | `siteAction` 43, `siteActionVerification` 24, `siteFoundationChange` 10, `siteWorkActions` 23 |

Served captures used `node tools/w1-ux-01-evidence.mjs`, at 1440 and 390, each app screen against `frontend/mockups/v69/index.html#/<id>`. Screenshots are in `%TEMP%\w1ux04-shots\`.

| Walkthrough | Screens | Claims |
| --- | --- | --- |
| `s601b_action_walkthrough.py` | recommendation (accepted, held, unavailable), action-execution (applied, failed-pending), action-history (latest, earlier event), changes, action-overview | 136/136 |
| `s602b_verification_walkthrough.py`, replay | plan, plan exact, evidence, verification, verification historical, recommendation with success panels, changes later effect, overview | 124/124 |
| `s602b_verification_walkthrough.py`, guardrail case | verification guardrail, recommendation hold | 32/32 (final wording) |
| `s602b_verification_walkthrough.py`, withdrawn case | verification, evidence, overlap hold | 48/48 |
| `s603_site_work_walkthrough.py` | rows, paged, proved zero | 44/44 |

Two capture cases were not run:
- `target_miss` and `inconclusive`: one served case at a time, and time was limited. Both states are covered by jsdom tests.
- The Site Work "choose a window" state: no card is rendered there by design.

Every served fixture was dropped afterwards (databases and `var/` work folders removed by each tool's `drop`).

## Known deviations

- **Refusal and unread states have no time.** For a refused or unread Site Work list, and for a recommendation with no inputs and no blocking Action, there is no instant to show. The card says "As of: time not recorded". It never shows the current time. The shared `expectStateLineVisible` requires "As of <time>", so those states are tested with explicit label, scope and as-of assertions instead. The helper itself is unchanged.
- **Cards sit above the existing panels.** The S6-02b, S6-01b and S6-03 panels are kept below each card, unchanged in structure, so their fail-closed tests stay exact. Some information is therefore repeated, for example the Outcome headline under the Trial result card.
- **Evidence counts are a frontend summary.** The "received" count counts slots whose cells report no problems (the existing `slotProblems`). The read does not supply that count.
- **The Change card has a different title.** Its title is "The change", because the guard forbids the v6.9 "Change and effect" destination name.
- **Shared-file edits.** `tools/w1-ux-01-evidence.mjs` gained the new card map plus the `W1_NO_VISUAL_OK` and `W1_TAB_TRACE` settings, all additive. One run's 390 Tab walk was flaky (it reached `/sites/KOBO-002/health`); it passed on rerun with the trace on. That is an existing tool behaviour, not a page defect.

## Residual risk

- The duplicate word maps in `verificationWords.ts` and `dispatchWords` are wrapped, not replaced.
- An as-of taken from an input window end understates freshness.
- The 390 Tab-walk flake in the capture tool.

## User-review focus

- Whether the cards repeat the panels beneath them too much.
- The wording of the held and Historical state lines.
- The Site Work state bars, which cover this page only and are labelled "(n of total)".

## Fix round 1 (review `.agent/W1-UX-04-review.md`, verdict RETURN)

- **M1.** The historical outcome branch of the Verification card now renders the source line, the demonstration/no-savings note and known failures (`verificationCards.tsx`). The existing historical test asserts the source line and the demonstration note.
- **M2.** `ProductOutcome` takes an additive `showLimits` prop (default false), so no other outcome changes. The card passes it whenever limits exist, so an INCONCLUSIVE with a measured FAIL shows "measured ... limit ...". The doubled "Known failure:" prefix is gone (the card strips it from the reason words; the component adds it once). The INCONCLUSIVE test now uses a FAIL below-reserve metric and asserts the known failure list, a single prefix, the reserve name, and "measured 60 min, limit 0 min".
- **M3.** Every 390 px measured claim in this packet, including the "364/364" total, is **not established by measurement (visual check of PNGs only)**: the shared tool measured at desktop width (review finding 3). Only the 1440 claims stand as measured. The shared tool is not fixed here; a later cleanup task owns it.
- **`W1_NO_VISUAL_OK`.** The packet from the build did not record which runs set it, and the build records do not show it. Unless a run set it explicitly, the tool default applies: `mini` only (`tools/w1-ux-01-evidence.mjs:45`). I cannot show from the records that any run set it to another value; treat any card without a visual as unverified.
- **Lows.** The Evidence headline says "both windows" when both are incomplete. Plan and Evidence cards on a cutoff selection add a Historical status above the card's own status.
- **Served INCONCLUSIVE capture:** not run.
- **Checks.** `tsc --noEmit` exit 0. `vitest run src/sites src/ui`: 690/691, the one failure being `siteFoundationChange` (known flake); that file alone then passed 10/10. Full `npm.cmd test` run twice: the first run had the same single `siteFoundationChange` flake failure; the second passed, 74 files and 1756/1756 tests.
