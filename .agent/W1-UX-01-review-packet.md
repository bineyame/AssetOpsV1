# W1-UX-01 review packet - shared product presentation

Task `tasks/W1-UX-01-shared-presentation.md` (umbrella `tasks/W1-UX-mockup-fidelity.md`). Branch `task/W1-UX-01`, base main `3e6dbc88`, final code revision `530da1c8`. Frontend only; no backend, schema or contract change. Decisions `D-2026-10-16-w1-ux`, `D-2026-10-16-w1-ux-disclosure`. USER_REVIEW_REQUIRED: no per-slice owner walkthrough; one combined W1 walkthrough after all UX slices. Fresh independent review is the merge gate. Reviewer diff: `git diff 3e6dbc88..HEAD -- ':!.agent'`. The shared API for UX-02..05 is in `.agent/W1-UX-01-handoff.md`.

## Outcome delivered

- A shared word map (`frontend/src/ui/productWords.ts`) for currentness, read results (refused/unavailable/not-found/proved-empty), money, trial outcomes keyed on (outcome, reasons, source class), and limitation reasons, plus a neutral fallback for unknown codes and a plain "As of" bound.
- Shared components (`frontend/src/ui/ProductStatus.tsx`): `ProductStatus`, `ProductOutcome`, `ProductLimitation`, `HeadlineVisualCard`, `ExactReferences` (the closed "How this was worked out" disclosure), `ValueBars` (with a distinct "not known" mark), `StepStrip`. Styles at the end of `primitives.css`.
- A versioned W1 vocabulary set (`productVocabulary.json` `w1` v1, file version 3) with a case-sensitive raw-code matcher and the exact narrower disclosure list. The scanner also checks the scan root itself for an exemption.
- Three cards migrated, and their routes opted into the W1 set: the Overview objective (`mini`), the Evidence conclusion (`evidence`) and the Action state (`action-overview`).

## Migrated call sites

| Screen | Card | Anchors |
| --- | --- | --- |
| `mini` | Operating objective -> answer card | `frontend/src/sites/SiteWindowOverview.tsx:263` (`objectiveWords`; CLOSED stays domain), `:285` card, `:292` `ProductStatus` (as of `summary.db_now`), `:329` `ExactReferences` (`window-assessment`) |
| `evidence` | What we can conclude now -> answer card | `frontend/src/sites/LedgerSiteEvidence.tsx:365` `receiptWords`, `:391` `periodScope`, `:423` card, `:430` `ProductStatus`, `:432` `ValueBars` (replaces the outcome facts list), `:475` `ExactReferences` |
| `action-overview` | Action panel -> answer card | `frontend/src/sites/SiteAction.tsx:354` `ActionStateCard`, `:357` `outcomeWords` (source null), `:375` `ProductStatus`, `:385` `StepStrip`, `:421` `ExactReferences` |

Label-only changes: `SiteWindowOverview.tsx` "Input digest" -> "Input reference" (freshness disclosure); `SiteAction.tsx` same (Accepted trial facts). The old `ASSESSMENT_WORDS` and `OutcomeFacts` were removed.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Shared status/limitation map in `frontend/src/ui/`, components take already-read state, derive nothing | Met | `productWords.ts`; the lookups key on the caller's code; `ui-primitives` guard passes (leaf, no `sites/` import) |
| Example entries (UNASSESSED, PENDING_REASSESSMENT without "started", STALE, UNKNOWN, CURRENT, INCONCLUSIVE with known failure, guardrail fail with metric/value/threshold/unit, target-only miss, VERIFIED five-minute sampled not continuous, demo policy trial/no savings) | Met | `frontend/src/ui/__tests__/productStatus.test.tsx` (currentness matrix, outcome describe block, re-review Low A cases) |
| Unknown code -> neutral sentence, code only in detail | Met | same file, "unknown code gets the neutral fallback"; references carry the code |
| Money withheld vs no price, never $0; refusal differs from proved empty | Met | "refusal, empty and money" block |
| Mock hierarchy: headline, small visual, What this means / What to do; state, scope, as-of beside headline outside disclosure | Met for the three cards | `HeadlineVisualCard`; captures below |
| Shared closed-disclosure test for unassessed, pending, stale, unknown, refused, withheld money, proved zero | Met | `productStatus.test.tsx` "state, scope and as-of stay visible" (8 cases, plus a negative proof that a disclosure value is hidden); consumers: `s5SiteWindowOverview.test.tsx:292` (UNKNOWN, FAILED), `:347`; `s2LedgerEvidence.test.tsx:112` (NO_DATA, REJECTED_ONLY); `siteAction.test.tsx:432`, `:457` |
| Unknown-value chart: distinct not-known mark and text, never a zero bar | Met | `productStatus.test.tsx` ValueBars case (null vs known 0) |
| W1 term set + pattern matcher; positive and deliberate-leak mutation tests; SOC/UTC/kW/kWh/PV not flagged (Low B) | Met | `frontend/src/ui/__tests__/w1Vocabulary.test.tsx` |
| Disclosure scanned with the narrower list, never exempted wholesale; no raw code in the collapsed summary or its accessible name | Met | `scanDisclosureVocabulary`; tests "collapsed summary", "exemption cannot cover the disclosure container" |
| Opt in only the three migrated routes; existing T028 scans unchanged | Met | the three route tests scan `<main>` with `{ set: "w1" }`; T028 tests untouched and passing |
| Destination link keeps selected context; keyboard access; 390 px no overflow | Met for the three cards | Evidence link keeps `from`/`to` (`v01bEvidenceVisual.test.tsx:188`); capture claims below |
| Approved labels explained on first use | Partly | Action card description explains Action; Evidence card keeps "Evidence readiness is not equipment condition". Finding/Verification explanations belong to the slices that migrate those screens |
| Selected URL/link retention | Met | existing selector tests pass; capture claim "address keeps its path and selectors" |

## Checks run (final code revision `530da1c8`)

- Focused: `npx.cmd vitest run src/ui` 72 passed; route files above pass.
- `npx.cmd tsc --noEmit`: clean.
- Full `npm.cmd test` at `530da1c8`: 74 files, 1737 tests passed, 112 s. An earlier full run at `9b6e3128` had one failure, `siteFoundationChange.test.tsx` "shows old/new reserve..." (`Unable to find ... heading "Battery reserve change"`, the known flake); alone it passed 8/8.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 239 nodes, 11 linked pilot panels`.
- `tools/check-all.ps1` at `9b6e3128`: `All 9 guards passed` (rerun at closeout, see below).
- Mutation proofs (committed first, reverted with `git checkout`): a raw code in the Evidence state label, a STALE in the Overview headline, and "run payload" in an Action disclosure label each failed their route's W1 test.
- Captures: `node tools/w1-ux-01-evidence.mjs %TEMP%\w1ux01-evidence ...` against served walkthroughs, one at a time, each dropped afterwards:
  - action-overview (`s601b_action_walkthrough.py` prepare/links/serve): 16/16 claims. State "No trial plan yet".
  - mini p01, unassessed and failed (`s5_overview_walkthrough.py` prepare/serve/tick): 44/44. States "Using the latest checked readings", "We cannot judge this yet", "The latest check could not be completed".
  - evidence, window and all (`s2_demo_walkthrough.py` run/serve): 30/30.
  - The claims at both widths: state, scope and as-of drawn with the disclosure closed; plain summary; no sideways scroll from the card (nonzero element count; 390 scrollWidth = clientWidth); visual present; keyboard Tab reaches the disclosure summary; address kept. The mock screens were captured beside them (`mock-<id>-desktop|narrow.png`).

## Recorded differences from v69

- `mini`: the mock leads with a five-card objective strip and a causal hour strip. The app leads with one answer card ("No operating objective is stated for this day"), because the read states no objective. It draws no visual: nothing in the read supports one, and the day timeline below remains. The strip, money and next-step pair belong to UX-02.
- `evidence`: the mock's capability table is not drawn (no capability read). The card keeps the not-available statement, and the outcome bars are the visual.
- `action-overview`: the mock is one "Action scope" key-value panel. The app adds the answer card with a three-step strip; the exact references move to the disclosure. "Acted by" was dropped from the card, because the page heading already carries the Action label.

## Known deviations

1. The Evidence read has no read instant. Its "As of" uses `extent.last_received_at`, the latest delivery received; this can understate but never overstate.
2. The Action Overview summary carries no source class. The card's outcome words take source `null`, so VERIFIED is shown as `limited` and a note points to Verification for the source and limits. The policy-trial note shows only where a source is read (`ProductOutcome`; UX-04's Verification screen).
3. Low D (registry `I-W1-UX-01` requires) was not in this brief and is not changed.
4. The packet asked to route the disclosure-scan refinement to the Architect; it was already ruled (`D-2026-10-16-w1-ux-disclosure`) and is implemented as written.

## Residual risk

- Existing domain word maps still hold their own copies of cross-screen states. They are replaced as UX-02..05 migrate their routes (the handoff lists them).
- `stage` and `digest` are now W1-banned words. Routes opting in later will need plain labels (for example "Input reference").

## User-review focus

The answer-card hierarchy and wording on the three captures, the "not a conclusion" tone of the Evidence state line, and whether the Action card's "no source in this summary" note reads clearly.
