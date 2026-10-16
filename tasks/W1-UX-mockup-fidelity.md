# W1-UX — W1 product presentation and v69 fidelity

Status: implementation-ready. Branch per slice `task/W1-UX-01` through `task/W1-UX-05`; this planning branch is `plan/W1-ux-pass`. Frontend only unless an exact backend label is absent; then stop and ask Architect for a bounded read contract. Owner does **one combined W1 walkthrough after all slices**; each slice may merge after fresh independent review under `.agent/owner-walkthrough-policy-2026-10-16.md`. Coordinator commits this plan. No screen or panel promotion follows from copy/layout alone.

## Authority and boundary

Owner words: `.agent/owner-LR01-S501-acceptance-2026-10-15.md`, `owner-S404-S601b-acceptance-2026-10-16.md`, `owner-S405b-acceptance-2026-10-16.md`, `owner-S302b-acceptance-2026-10-16.md`, `owner-T028-presentation-direction-2026-10-04.md` (all in `.agent/`); backlog `.ai/MILESTONE_REVIEW_BACKLOG.md:2254`. Registry `delivery_plan.owner_inputs.W1.approved_manifest_ids` is the exhaustive scope: all delivered/partial product screens plus pending S6-03, S6-02b, S7-01b; `lab` is excluded. Use `frontend/mockups/v69/index.html` and `screen-manifest.json` for the named screen's hierarchy, story, and interaction; illustrative mock values never become live data. Source contracts and `MissingClaim` placements remain authoritative. The mock's question for each screen should become its visible lead, answered only to the strength of the read.

## Gap inventory, app versus v69

Each row names the current component seam; `pending` means inspect the merged UI packet before implementation. The mock reference for every row is `index.html#/<id>` and the matching `screen-manifest.json` entry. Layout work includes hierarchy/spacing at 1440 and 390 px; “detail” means a few labelled exact references in the small disclosure or substantive material in the owning contextual Analysis/Evidence/Plan/History/Verification destination, retaining exact links. A plain “as of <time>” bound always stays in the default reading for current, zero and historical claims.

| Screen ID | App seam and short gap against mock |
| --- | --- |
| `sites` | `frontend/src/sites/SitesIndex.tsx:133-180`: inventory leads with table/state; use “Which site should I open?” and concise site identity and reporting cards; exact IDs/registration detail. No estate health inference. |
| `mini` | `frontend/src/sites/SiteWindowOverview.tsx:209-316,510-597`: fragmented day/objective/money panels; lead with bounded operating answer, visual day timeline and one Finding consequence; status reasons/selection IDs to detail. |
| `foundation` | `frontend/src/sites/StoredFoundationViews.tsx:367-426`: configured topology and obligation labels read like a record; lead with “What is configured?” and a visual equipment summary; revision and mapping references to detail. |
| `readiness` | `frontend/src/sites/ReadinessOverview.tsx:264,512`: configuration and gateway facts compete; lead with “What needs connecting or confirming?” and a source/next-step graphic; raw status basis to detail. Preserve commissioning missing claim. |
| `sld` | `frontend/src/sites/StoredFoundationViews.tsx:494-675`: diagram plus part table; lead with connection/reporting story, visible missing links and clear legend; exact part references to detail. |
| `evidence` | `frontend/src/sites/LedgerSiteEvidence.tsx:377-502,649-737`: source and delivery tables dominate; lead with “What can we rely on?” and coverage/source timeline; receipt/digest details to disclosure. |
| `evidence-analysis` | `frontend/src/sites/EvidenceClaimLimit.tsx:300,509-549,667-728`: selected limit is present but dense; headline which conclusion is supported, show covered/missing span visual; rule/version/IDs remain detail. |
| `dispatch` | `frontend/src/sites/PerformanceDispatch.tsx:291-317,399-416`: block table and assessment vocabulary; lead with why generator operated and selected-block strip; model version/reasons to detail. |
| `analysis` | `frontend/src/sites/assessmentAnalysis.tsx:242-257`: method/revision prose leads; show measurement-to-conclusion sequence and selected limitation; method/version/record count to detail. |
| `finding` | `frontend/src/sites/FindingDetail.tsx:306-445`: many record sections; lead with defensible conclusion and what could change it, causal strip; alternative codes and revisions to detail. |
| `finding-evidence` | `frontend/src/sites/SiteFindingEvidence.tsx:270-331,389-524`: lineage/table first; lead with “Which records support this conclusion?” and visual record trail; IDs/digests to detail. |
| `finding-history` | `frontend/src/sites/SiteFindingHistory.tsx:172-260`: selected revision and history read; lead with “What changed, and when?” as timeline; revision IDs and opaque cutoff tokens to labelled detail; plain historical “as of <time>” stays visible. |
| `sitefindings` | `frontend/src/sites/SiteFindingIndex.tsx:134-178,265-292`: status and basis dominate; lead with scoped Findings and consequence/next action, ranked visual rows; opaque cursor/status codes to labelled detail. Current zero keeps a plain “as of <time>” beside the claim. |
| `financials` | `frontend/src/sites/SiteFinancials.tsx:475-505` and `FindingConsequence.tsx:334`: price/money separated; lead with bounded consequence and basis/limit visual; source/model versions to detail. No amount without current priced read. |
| `assumptions` | `frontend/src/sites/SiteFinancials.tsx:259-405`: schedule/history reads as revision list; lead with price in use and effective-time strip; version/actor/reference to detail. |
| `recommendation` | `frontend/src/sites/SiteRecommendation.tsx:145-203,343-416`: trial and live-computation wording; lead with proposed action, why and success measure; input IDs/live state to detail. |
| `changes` | `frontend/src/sites/SiteFoundationChange.tsx:108-182`: application and Foundation versions foregrounded; lead with what changed and observed effect/unknown; event and version IDs to detail. Await S6-02b effect UI. |
| `action-overview` | `frontend/src/sites/SiteAction.tsx:290-367`: state/origin records; lead with intervention and outcome state; rule and source references to detail. |
| `action-execution` | `frontend/src/sites/SiteAction.tsx:451-537`: “Application”/technical control labels; lead with work done and pending next step; exact event/actor data to detail. |
| `action-history` | `frontend/src/sites/SiteAction.tsx:537-580`: activity log; make chronological change story; event IDs and cutoffs to detail. |
| `action-plan` | Pending `tasks/S6-02b-verification-ui.md` Plan route; compare after merge to mock goal/windows/guardrails layout; exact plan/revision IDs to detail. |
| `action-evidence` | Pending S6-02b Evidence route; show baseline-versus-later coverage/limits visually; slot/record IDs to detail. |
| `verification` | Pending S6-02b Verification route; headline measured outcome and trade-offs, with paired period visual; thresholds/typed reasons to detail. |
| `sitework` | Pending `tasks/S6-03-site-work-list.md` Site Work route; prioritize active work and next step over table plumbing; opaque cursor tokens to labelled detail. Zero only after assessed window, with plain “as of <time>” beside it. |
| `health` | Pending `tasks/S7-01b-health-ui.md` Site Health route; lead with which source needs attention and contact/fact-age visual; diagnostic IDs to detail. Source contact is not equipment condition. |
| `asset` | Pending S7-01b battery route; lead with “Condition cannot yet be judged” and missing-input diagram; asset/binding IDs to detail. Never imply remaining life/warranty. |

## Slice order and common acceptance

1. [W1-UX-01 shared presentation](W1-UX-01-shared-presentation.md): vocabulary, disclosure, headline/visual pattern and scan. Required before screen work.
2. [W1-UX-02 Site and money](W1-UX-02-site-money.md): `sites`, `mini`, Finding family, `financials`, `assumptions`.
3. [W1-UX-03 evidence and performance](W1-UX-03-evidence-performance.md): `evidence`, `evidence-analysis`, `dispatch`, `analysis`.
4. [W1-UX-04 actions and work](W1-UX-04-actions-work.md): `recommendation`, `changes`, Action family, `verification`, `sitework`; starts after S6-02b/S6-03 merge.
5. [W1-UX-05 configuration and health](W1-UX-05-foundation-health.md): `foundation`, `readiness`, `sld`, `health`, `asset`; starts after S7-01b merge.

UX-01 starts only after S6-02b, S6-03 and S7-01b merge. UX-04 is M in two bounded phases; split its second phase if the merged component exceeds that scope. Each packet has at most two phases, focused tests, one full `npm.cmd test` on final revision, 1440/390 served app versus named mock screenshots using per-slice Playwright evidence scripts following `tools/v01a-foundation-evidence.mjs`, with recorded differences; skipped captures are marked **not run** with the blocking precondition, and a fresh reviewer independent of implementation. Keep read/selector/URL/lineage tests and fail-closed assertions; any weakened fail-closed assertion blocks review. Each route opts into the full W1 vocabulary term set as its slice migrates it; all 26 must be opted in before the combined walkthrough. With the exact-reference disclosure closed, tests on every non-positive state assert the plain state sentence, scope and “as of <time>” remain visible outside it. Test unknown charts as a distinct “not known” mark, never a zero bar. No new empty/current/positive state without proof from the read. Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` and relevant `tools/check-all.ps1` guards. Treat unavailable/dirty/withdrawn and the mock's unsupported values as explicit limited states. No per-slice owner walkthrough.

## One combined W1 owner walkthrough

Use the 26-row map below. The coordinator prepares and serves one private case at a time, records its exact tool-printed URL and source qualification, captures supported, limited/pending, stale/withdrawn and proved-zero paths where the read supports them, then drops the guarded case. Compare app and mock at 1440 and 390 px; check keyboard access, exact links and reload. Do not compare numbers across independent cases or imply a common lineage. The owner walks the complete journey once and records acceptance; W1 completes only then.

## Combined walkthrough coverage and authorship

W1-UX-05 closeout writes `.agent/W1-UX-combined-owner-walkthrough.md` with the ordered commands, private DB/work names, tool-printed exact URLs, dataset source qualification, state evidence and 1440/390 captures. The coordinator checks all 26 rows below against that document before scheduling the owner session. Each address below is a route template, not an invented fixture ID: substitute **only** IDs and selectors printed by the named tool's `links`/`serve` step. Prepare and serve one tool at a time; preserve its state-transition commands and drop its guarded private case afterward. `P/S` means run the tool's prepare and serve modes (and links/attest where its packet requires). `T` means use the tool's documented transition after serving. A missing tool or capture is **not run**, with its blocking precondition recorded. Authored, generated and simulated cases must be labelled in the final guide and in screenshots; they are not field readings.

| Screen | Tool and modes | Address after tool substitution | State to show |
| --- | --- | --- | --- |
| `sites` | `v01a_foundation_walkthrough.py` P/S/links | `/sites` | registered/limited |
| `mini` | `s5_overview_walkthrough.py` P/S | `/sites/{site}` | supported/pending |
| `foundation` | `v01a_foundation_walkthrough.py` P/S/links | `/sites/{site}/foundation` | configured/missing |
| `readiness` | `v01a_foundation_walkthrough.py` P/S/links | `/sites/{site}/foundation/readiness` | limited |
| `sld` | `v01a_foundation_walkthrough.py` P/S/links | `/sites/{site}/foundation/sld` | configured/gap |
| `evidence` | `s2_demo_walkthrough.py` P/S | `/sites/{site}/evidence` | accepted/rejected; `s405_provenance_walkthrough.py` P/S/links: labelled source/unknown |
| `evidence-analysis` | `s302_claim_limit_walkthrough.py` P/S/T late | `/sites/{site}/evidence?view=analysis&day={day}&revision={revision}` | supported/limited/stale |
| `dispatch` | `s3_dispatch_walkthrough.py` P/S | `/sites/{site}/performance/dispatch` | supported/limited |
| `analysis` | `s3_dispatch_walkthrough.py` P/S | `/sites/{site}/performance/dispatch?day={day}&revision={revision}&view=analysis` | supported/limited |
| `finding` | `s4_finding_walkthrough.py` P/S | `/sites/{site}/findings/{finding}` | selected/limited |
| `finding-evidence` | `s405_provenance_walkthrough.py` P/S/links | `/sites/{site}/findings/{finding}/evidence?revision_id={revision}` | labelled source/unknown |
| `finding-history` | `s4_finding_walkthrough.py` P/S | `/sites/{site}/findings/{finding}/history?revision_id={revision}` | historical |
| `sitefindings` | `s404_finding_index_walkthrough.py` P/S/T late | `/sites/{site}/findings?from={from}&to={to}` | supported/proved-zero/stale |
| `financials` | `s402b_fuel_cost_walkthrough.py` P/S; `s405_provenance_walkthrough.py` P/S/links | `/sites/{site}/financials?finding_id={finding}&revision_id={revision}` | priced/withheld/unknown source |
| `assumptions` | `s402a_assumptions_walkthrough.py` P/S; `s408_assumption_history_walkthrough.py` P/S/links/close-gate (owner + mixed cases; evidence `s408-assumption-history-evidence.mjs`) | `/sites/{site}/financials/assumptions` (default) and `?recorded_at={T1/T3}` from `links` output | effective/historical price and consequence versions; missing/withheld/closed source, exact Finding link and source label after reload |
| `recommendation` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/findings/{finding}/recommendation?revision_id={revision}` | proposed/limited |
| `changes` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/foundation/changes/{change}` | applied/unknown effect |
| `action-overview` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}` | recorded/pending |
| `action-execution` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}/execution` | applied/failed |
| `action-history` | `s601b_action_walkthrough.py` P/S/links | `/sites/{site}/actions/{action}/history?event_id={event}` | historical |
| `action-plan` | `s602b_verification_walkthrough.py` P/S/capture | `/sites/{site}/actions/{action}/plan?plan_revision_id={plan}` | planned/limited |
| `action-evidence` | `s602b_verification_walkthrough.py` P/S/capture | `/sites/{site}/actions/{action}/evidence?plan_revision_id={plan}&outcome_id={outcome}` | covered/missing |
| `verification` | `s602b_verification_walkthrough.py` P/S/capture | `/sites/{site}/actions/{action}/verification?plan_revision_id={plan}&outcome_id={outcome}` | sampled pass/guardrail fail/withdrawn |
| `sitework` | `s603_site_work_walkthrough.py` P/S/attest | `/sites/{site}/work?from={from}&to={to}` | active/proved-zero |
| `health` | `s701_health_walkthrough.py` P/S/deliver/attest | `/sites/{site}/health` | current contact/old facts/no source |
| `asset` | `s701_health_walkthrough.py` P/S/deliver/attest | tool-printed `/sites/{site}/...` battery asset URL | unknown condition/missing input |

`s502_overview_finding_list_walkthrough.py` P/S/late/settle/gate/drop additionally covers the `mini` Finding row and `sitefindings` bridge at its printed `/sites/{site}` and Finding links, including late and proved-zero states. Its evidence is required in the combined document. The tool-printed URL is authoritative when a pending branch's route differs from the template.

## Architect ruling

Questions answered by `D-2026-10-16-w1-ux` in `.agent/architect-W1-ux-answers.md`. Substantive deeper material belongs in its owning contextual destination, available as the same named tab or view link at 1440 and 390 px. The closed “How this was worked out” disclosure holds only a few labelled exact references. Site, Evidence, Finding, Action, Verification and Analysis are approved domain/destination words with nearby first-use explanations; labels never grant a positive claim. Default prose, graphics and accessibility text exclude raw codes, IDs and implementation vocabulary; Analysis/Evidence prose follows the same rule, while labelled exact reference data remains available. Authored/test data stays explicitly qualified. Honest selected-read state outranks mock presentation.

## Plan fix round 1

Applied the five Medium review fixes and Low carries from `.agent/W1-UX-plan-review.md`: outcome/reason/source verdicts, staged vocabulary ratchet, closed-disclosure visibility, plain as-of bounds, full walkthrough map, corrected anchors and capture/review gates. Status remains implementation-ready.
