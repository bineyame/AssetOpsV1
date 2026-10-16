# W1-UX-03 review packet - Evidence, Dispatch and Analysis presentation

Task: `tasks/W1-UX-03-evidence-performance.md` (registry IDs `evidence`, `evidence-analysis`, `dispatch`, `analysis`). Branch `task/W1-UX-03`, base main `b4a89314`. Frontend only; no backend, read-contract, classification, provenance or stale/current policy change. Decisions applied: `D-2026-10-16-w1-ux`, `D-2026-10-16-w1-ux-disclosure`; shared API from `.agent/W1-UX-01-handoff.md` (no fork). USER_REVIEW_REQUIRED: fresh independent slice review is the merge gate; owner sees it in the one combined W1 walkthrough (no per-slice walkthrough).

Reviewer diff: `git diff b4a89314..HEAD -- ':!.agent'`.

## Outcome delivered

- **evidence** (`/sites/{site}/evidence`): the UX-01 conclusion card ("What can we rely on?") is now followed by "Which sources reported, and when": three separate facts - readings received, gateway contact, analysis up to date - each with its own state word (Recorded / Not yet / Needs a look / Not known) and the sentence that one does not make another true, an "as of" bound, and a per-source strip marking when each source's latest accepted reading in the period was taken (a silent source draws no mark and says so). Source table, gateway contact and next-evidence panels are unchanged below.
- **evidence-analysis** (`?view=analysis&day=&revision=`): the view leads with "Which accepted readings sit behind what the readings can support?", then the S2 "How each limit is set" panel and the S3-02b section, now titled "What the readings can support", ahead of the record inspector. The selected assessment shows the question, the existing headline, the shared state line (currentness words, selected day/period as scope, "as of" the read) and a covered/missing strip per needed reading (missing role = hatched "not known" mark), with "What limits it" beside it. Refused, unavailable and not-found reads carry a non-positive state line bounded by the time the answer arrived. Role table, record links and the S3-02b `Technical details` disclosure (rule, versions, record IDs) are preserved; its labels lose implementation words and every value is a single labelled exact reference.
- **dispatch** (`/performance/dispatch?day=&revision=&block=`): Overview leads with a "Why the generator operated" answer card: the question, a headline only as strong as the day read ("From an earlier result that is not current: ..." when stale), the state line (shared label/tone, dispatch sentence, status reasons, scope, as of `current_basis.read_at`), a strip of every assessed 15-minute block by outcome where each block is an exact `revision`+`block` link (selected block marked), the day totals, the meaning and material limitations, a Dispatch > Analysis link and a closed "How this was worked out" with rule versions. The older-rule note no longer prints raw model versions (moved to labelled references). An unstated portion total is "not known", never 0 min.
- **analysis** (`...&view=analysis`): leads with "How the readings lead to the outcome": accepted readings (count, demand, spare capacity, missing inputs) -> the rule applied (plain test, what held the generator on) -> the bounded conclusion for the exact selected period/block with its limits and "says nothing about fuel, savings or money"; with no selection it concludes nothing. Constraint reasons and missing inputs use plain words; confidence and record-series rows are plain, their raw basis moved into the stored-record disclosure. Versions of the period are a visible link list; the stored record and the earlier-results comparison are closed technical disclosures whose values are labelled exact references.
- `AssessmentAnalysis` (Finding Analysis tab and the legacy dispatch path): method version, assessment reference and record-set reference move from default text into a closed `ExactReferences`.

## Migrated call sites (path:line at HEAD)

| Area | Anchor |
| --- | --- |
| Period strip (new, local) | `frontend/src/sites/periodStrip.tsx`, `periodStrip.css` |
| Evidence reporting facts + source strip | `LedgerSiteEvidence.tsx:497` (call), `:565` `ReportingFacts`, `:594` strip |
| Evidence Analysis lead + order | `LedgerSiteEvidence.tsx:167` |
| Claim limit state line / strip | `EvidenceClaimLimit.tsx:523`, `:587` `ProductStatusLine`, `:624` `RoleStrip`; refused/unavailable/no-day `:430`, `:440`, `:456`; Technical `:756` |
| Dispatch state words (wrap shared map; `STATUS_WORDS` -> `STATUS_SENTENCES`) | `PerformanceDispatch.tsx:433` `statusWords`, `:443` `StatusLine`, `dispatchWords.ts:13` |
| Dispatch answer card | `PerformanceDispatch.tsx:302`, `:463` `DispatchReferences`, `:477` `portion`, `:502` `dayHeadline`, `:523` `DayBlockStrip`, `:579` `LimitationSummary` |
| Older-rule references | `PerformanceDispatch.tsx:780` |
| Analysis story / versions / disclosures | `PerformanceDispatch.tsx:1118` `ReadingsToOutcome`, `:1288`, `:1302`, `:1043` |
| Unknown reason fallback | `dispatchWords.ts:125` |
| Finding Analysis references | `assessmentAnalysis.tsx:261` |

## Changed test assertions (each listed with why)

- `performanceDispatch.test.tsx:172-175` status regexes: "Out of date / Reassessment failed / Being assessed / Not assessed" -> the shared labels (UX-01 map owns label and tone); added `expectStateLineVisible` and non-positive tone on all four states (strengthened).
- `performanceDispatch.test.tsx:221` `[data-older-rule]` no longer matches raw "dispatch-3; ... dispatch-3.1" in prose; now asserts the plain sentence has no version and both versions are in a closed exact-reference disclosure, in order.
- `performanceDispatch.test.tsx` fixture `current_basis.read_at` "x" -> a real instant (the state line needs an "as of"; no assertion relaxed).
- `evidenceClaimLimit.test.tsx:164` headline string "this generator run" -> "this period of generator operation" ("run" is a W1-banned word); `:210` reason "Battery discharge capability" -> "Battery output limit" (W1 bans "discharge capability"; v69 wording).
- `t028Screens.test.tsx:210-213, 417-421`: method version, assessment reference and record-set reference asserted inside the closed `analysis-assessment-references` disclosure instead of default text; "(an assessed period without a Finding)" -> "An assessed period without a Finding".
- No fail-closed assertion was removed or weakened. New tests: `evidenceClaimLimit.test.tsx:489+` (W1 scan of five reads including the Technical disclosure; positive only for supported CURRENT; unknown currentness non-positive; missing role not-known mark; four refused/unread states), `performanceDispatch.test.tsx:397+` (answer card, exact block links, disclosure scan, W1 scan, not-known portion, undetermined + late input, Analysis sequence, no-selection), `v01bEvidenceVisual.test.tsx:281-320` (three separate facts with STALE analysis, unknown status, source strip, Analysis view W1 scan).

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Evidence leads with "Which readings can we rely on?" and coverage/source timeline | Met (UX-01 card + reporting facts + source strip). |
| Separate accepted/rejected/duplicate, central contact and analysis freshness; fresh receipt never implies fresh facts or current analysis | Met; tested with STALE analysis beside current contact. |
| Claim-limit card leads with what the selected assessment supports, covered/missing span visual, missing role and selected-window bound beside it | Met. |
| Dispatch leads with generator story, block timeline, selected block and limitation | Met. |
| Analysis evidence -> rule -> bounded conclusion | Met (durable Dispatch Analysis). |
| Detailed tables and direct record links stay in their owning view; few labelled exact references in small disclosure; no revision/cutoff loss | Met; selectors kept in links and address (tests). |
| Preserve S3-02b Technical details; replace default "claim limit" language | Met; default reading has no "claim limit"/"ceiling" (test). |
| Unsupported health grades / source status stay explicit missing states | Unchanged `NotAvailableYet` statements kept. |
| No conclusion from missing battery-limit report, stale analysis or refused read | Met (undetermined/stale/refused tests). |
| Each route opted into W1; non-positive states keep sentence, scope, as of outside the closed disclosure | Met with deviations 1-2 below. |
| 1440/390 app vs v69 captures | See Captures. |

## Checks run (final revision unless noted)

- Full `npm.cmd test` at `022a5002` (final code): 74 files, **1759 passed**, 0 skipped, 208 s-class wall time. An earlier full run at `937ddd27` had 1 failure, the known flake `siteFoundationChange.test.tsx` ("Unable to find ... heading 'Battery reserve change'", under load); rerun alone 8/8 passed. Runs at `f567a00c` and `be9b75b5`: 1759 passed.
- `npx.cmd tsc --noEmit`: clean at `022a5002`.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`: **All 9 guards passed** at `022a5002` (an intermediate run failed the missing-claim guard on a reworded baselined sentence and a new "Not yet available" label; both fixed, see deviation 1).
- `tools/check-agent-workflow.ps1`: passed.
- Mutation proofs (committed first, reverted with `git checkout --`): removing the hatched not-known mark in `PeriodStrip` fails the evidence-analysis missing-role test; injecting a raw `CURRENT` into the Dispatch headline fails the dispatch W1 scan.

## Captures (1440 / 390, `node tools/w1-ux-03-evidence.mjs`, served app vs `mockups/v69/index.html#/<id>`)

Screenshots: `%TEMP%/claude/.../scratchpad/w1ux03-shots` (evidence, at `be9b75b5`) and `.../w1ux03-shots-final` (others, at `937ddd27`; later commit only relabels a closed-disclosure field). Every served fixture dropped, servers stopped.

| Screen | Walkthrough and URL | Claims |
| --- | --- | --- |
| `evidence` | `s2_demo_walkthrough.py run/serve`: `/sites/KOBO-001/evidence` and `?from=2026-09-30T03:00:00Z&to=2026-09-30T15:00:01Z` | 30/30 |
| `evidence-analysis` supported / limited | `s302_claim_limit_walkthrough.py prepare/serve`: `?view=analysis&day=2026-10-06&revision=3f3bc57d-...`, `day=2026-10-11&revision=e8dbda95-...` | 30/30 |
| `evidence-analysis` stale | same, after `late` (STALE_PROJECTION) | 16/16 (first attempt: Chrome page target not exposed; rerun on another CDP port passed) |
| `dispatch`, `analysis` | `s3_dispatch_cases.py run` (producer DB was stale; rebuilt, VERIFY PASSED), `s3_dispatch_walkthrough.py prepare/serve`: `/performance/dispatch?day=2026-10-09&revision=e1cb9f3c-...&block=0` (+`&view=analysis`) | 32/32 |

App vs mock differences (recorded, not defects unless noted):
- `evidence`: mock leads with a capability table; app keeps the honest "Not available yet" capability statement and adds the three reporting facts and source strip; mock source badges (Gap/Good/Limited, "Affects") and ranked next steps have no read and stay "Not available yet". App page is about twice the mock length.
- `evidence-analysis`: mock shows records first, then "How a claim limit is set"; app leads with the limit explanation and the selected-assessment card, then records (packet asks the card to lead). The records list follows the period filter, not the selected assessment day (pre-existing S2 behaviour; not changed here).
- `dispatch`: mock has a PV/load/generator kW chart; app has the block strip and totals (no kW series in the dispatch read). App keeps the full accepted-records table and 12-row coverage table, so the page is long, especially at 390 (in-card table scrollers, no page overflow).
- `analysis`: mock `#/analysis` is the Finding F-104 Analysis; the app route is Performance > Dispatch > Analysis, so only section names align. No raw codes, versions or stage labels in default text at either width after `937ddd27`; at 390 the constraint table scrolls inside its card.
- First capture pass (`be9b75b5`, recorded): the tool measured the wrong disclosure on `evidence-analysis` and flagged the in-card constraint scroller at 390, and showed backend codes in Analysis default text; the tool and the text were fixed in `937ddd27`.

## Known deviations

1. **G-04 baselined sentence.** The Dispatch Analysis "Fuel, money and Finding comparison" sentence contains "claim" (W1-banned) but is pinned verbatim by `tools/checks/missing-claim-baseline.json` (G-04 owns tagging it through `MissingClaim`); rewording fails the missing-claim guard. Kept verbatim; the W1 Analysis scan allows only that word in only that element (`performanceDispatch.test.tsx`, commented).
2. **No read instant.** The "No assessment selected" (no day) and "store not configured" claim-limit states have no read, so their "as of" reads "As of: time not recorded" (never now) and they are not asserted with `expectStateLineVisible`. Refused/unavailable/not-found reads are bounded by the time the answer arrived.
3. The Evidence source strip marks only the latest accepted reading per source: the ledger read has no per-source first time or gap list, so coverage across the period is not drawn (would imply continuity).
4. `assessmentAnalysis.tsx` was migrated, but the `analysis` registry route renders the durable `PerformanceDispatch` Analysis view; AssessmentAnalysis serves the Finding Analysis tab (UX-02 route) and the legacy dispatch path.
5. Dispatch block-strip links have no visible text (accessible name via `aria-label`, readable row summary beside).
6. Pre-existing: `performanceDispatch.test.tsx` "Analysis shows the constraint..." fails when run alone with `-t Analysis` (also on base `b4a89314`); it passes in file and full runs.

## Residual risk / review focus

- Tone choice: a CURRENT read with no positive conclusion (whole day, undetermined, unsupported) shows the CURRENT label with `limited` tone.
- `constraintWords` fallback now says "another recorded reason (in the stored record)" instead of lowercasing the code; affects SelectedPeriod too.
- The dispatch block strip duplicates the existing per-period block chooser (kept for its tests and keyboard flow).
