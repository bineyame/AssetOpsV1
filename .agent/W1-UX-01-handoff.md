# W1-UX-01 handoff - the shared presentation API for W1-UX-02..05

Branch `task/W1-UX-01` (base main `3e6dbc88`). Frontend only. Decisions: `D-2026-10-16-w1-ux`, `D-2026-10-16-w1-ux-disclosure`. Every later UX slice uses this API and does not fork it.

## Words: `frontend/src/ui/productWords.ts` (exported from `../ui`)

Words only. The caller passes the code its typed read returned; nothing is derived. Each returns `ProductWords { label, sentence, next?, tone, code, unrecognised }`; `code` is for the exact-reference disclosure only.

| Function | Use for | Notes |
| --- | --- | --- |
| `currentnessWords(code)` | CURRENT, PENDING_REASSESSMENT, REASSESSMENT_PENDING, PENDING, STALE, STALE_PROJECTION, FAILED, UNASSESSED, NOT_ASSESSED, UNKNOWN, HISTORICAL, AUDIT_ONLY | only CURRENT is `positive` |
| `readResultWords(kind)` | `refused`, `unavailable`, `not-found`, `proved-empty` | refused/unavailable say "not empty" |
| `moneyWords(code)` | WITHHELD*, MIXED_OR_UNKNOWN_SOURCE, PENDING_REASSESSMENT, NO_PRICE, UNPRICED | "No current amount can be shown" vs "No price recorded"; never zero |
| `outcomeWords(outcome, reasons, sourceClass)` | NO_PLAN, PENDING, REASSESSMENT_PENDING, VERIFIED, INEFFECTIVE, INCONCLUSIVE | keyed on all three: INEFFECTIVE+`GUARDRAIL_FAIL` -> "Trial missed a safety or service limit" (`showsFailedLimit`), otherwise "Target not met"; demo sources (AUTHORED_DEMONSTRATION, REGISTERED_SIMULATION, SIMULATED) carry `demonstrationNote` (policy trial, no savings or realized benefit); an unestablished source turns VERIFIED's tone to `limited` |
| `limitationWords(code)` | MISSING_READINGS, LATE_EVIDENCE, SOURCE_NOT_COHERENT, SOURCE_NOT_ESTABLISHED, NOT_COMPARABLE, NO_PRICE | cause + next step |
| `sourceQualification(class)` | source label beside an outcome | |
| `asOfText(instant)` / `plainTime(instant)` | "As of 16 Oct 2026, 10:05 UTC" / "16 Oct 2026, 10:05 UTC" | missing -> "As of: time not recorded", never now |

Any unknown code gets `UNRECOGNISED_SENTENCE` ("We cannot explain the limit from this record."), `unrecognised: true`, never positive. Domain states the map does not own stay in the domain module as a local `ProductWords` (see `objectiveWords` CLOSED, `receiptWords`). Add a cross-screen entry here (with a matrix test) rather than a parallel local map; replace the duplicates listed in the survey (dispatchWords `STATUS_WORDS`, findingWords `CURRENTNESS_WORDS`, EvidenceClaimLimit `CURRENTNESS_WORDS`, SiteFindingIndex `STATUS_WORDS`, SiteWindowOverview `FRESHNESS_WORDS`/`MONEY_STATE_WORDS`, FindingConsequence `STATE_HEADLINE`) as your route migrates.

## Components: `frontend/src/ui/ProductStatus.tsx`

- `ProductStatus { words, scope, asOf, children? }` - the state line: label, sentence, children, "scope · As of ...", next step. Always in the default reading.
- `ProductOutcome { words: OutcomeWords, scope, asOf, failedLimits?, knownFailures? }` - adds source, demo note, failed limits (name, measured value, limit, unit) and known failures.
- `ProductLimitation { words }` - one `<li>`.
- `HeadlineVisualCard { dataName, headingId, question, title?, description?, headline, status, visual?, meaning, todo?, destination?, references? }` - question eyebrow, answer, state line, visual, "What this means"/"What to do", destination link, disclosure last. With `title` the panel title is the heading (v69 panel name) and the answer is the lead paragraph.
- `ExactReferences { name, references: {label, value|null}[] }` - the closed "How this was worked out" disclosure; fixed summary; each value in one `data-vocabulary-exempt="source-reference"` `<code>`. Labels must be plain and are scanned. Values only - no method or prose.
- `ValueBars { title, items: {label, key?, value|null, valueText}[] }` - null draws a hatched "not known" mark and text, never a zero bar.
- `StepStrip { title, steps: {label, state: done|waiting|problem|not-known, detail}[] }`.
- Destination links stay with the caller (exact URL, selected Site/period/revision/object selectors).

## Tests and scan: `frontend/src/test/`

- `scanProductVocabulary(root, page, { set: "w1" })` - T028 list plus the W1 set (`productVocabulary.json` `w1`, version 1). Scan `<main>`, not the test container (the location probe holds raw URLs).
- `scanDisclosureVocabulary(root, page)` -> `{violations, scanned, disclosures}`; assert `disclosures > 0` and `scanned > 0`.
- `rawCodes(text)`: case-sensitive closed single-word codes + uppercase-underscore, UUID, digest and version shapes; SOC, UTC, kW, kWh, PV are allow-listed (the T028 gloss rule for SOC/PV still applies separately).
- `expectStateLineVisible(card)` (`productPresentation.ts`) - the shared closed-disclosure acceptance check; repeat it for each of your non-positive states.
- Route opt-in pattern: add a `W1-UX-01:`-style test per migrated route (examples: `s5SiteWindowOverview.test.tsx:347`, `v01bEvidenceVisual.test.tsx:188`, `siteAction.test.tsx:432`). Keep the existing T028 scans. Labels like "Input digest" must become plain ("Input reference").

## Opted-in routes and what is left

Opted in: `mini` (`/sites/{site}`), `evidence` (`/sites/{site}/evidence`, overview view), `action-overview`. The other 23 W1 routes stay on the T028 scan until their slice migrates them. UX-02 owns the rest of `mini` (freshness strip, money card, timeline), UX-04 the other Action views.

## Walkthrough prerequisites (Low C)

- The combined walkthrough document `.agent/W1-UX-combined-owner-walkthrough.md` is owned by whichever UX slice merges last (default UX-05); if another slice merges later, it refreshes the document and its captures.
- `s2_demo_walkthrough.py` has `run|serve|setup` (no `prepare`): use `run`, then `serve`; `run` drops and recreates the fixed DB `assetops_s2demo` (drop it afterwards; the tool has no drop mode).
- `v01a_foundation_walkthrough.py` (and `v01b_lab_evidence_walkthrough.py`) need `tools/s4_finding_cases.py run` first.
- `s5_overview_walkthrough.py prepare` needs `var/sites/kobo-001.yaml` in the worktree (copy it from the main checkout; `var/` is ignored). `tick` within 5 minutes of viewing.
- Capture: `node tools/w1-ux-01-evidence.mjs <out> <mock-id>[:<case>]=<app-url> ...` (one served walkthrough at a time).

## Risks

- The Evidence read has no read instant; the as-of bound uses the latest delivery received (`extent.last_received_at`), which can only understate.
- The Action Overview summary carries no source class; the card says so and points to Verification rather than guessing.
